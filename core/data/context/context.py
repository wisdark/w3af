'''
context.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''

class Context(object):
    name = ''

    def get_name(self):
        return self.name

    def is_executable(self, data):
        return True

    def can_break(self, payload):
        raise 'can_break() should be implemented'
    
    def match(self, data):
        raise 'match() should be implemented'

    def inside_comment(self, data):
        raise 'inside_comment() should be implemented'

def normalize_html(meth):
    def wrap(self, data):
        data = data.replace("\\'",'')
        data = data.replace('\\"','')
        new_data = ''
        quote_character = None
        for s in data:
            if s in ['"', "'"]:
                if quote_character and s == quote_character:
                    quote_character = None
                elif not quote_character:
                    quote_character = s
            if s == '<' and quote_character:
                s = '&lt;'
            new_data += s
        return meth(self, new_data)
    return wrap


def inside_html(meth):
    def wrap(self, data):
        script_index = data.lower().rfind('<script')
        if script_index > data.lower().rfind('</script>') and data[script_index:].count('>'):
            return False
        style_index = data.lower().rfind('<style')
        if style_index > data.lower().rfind('</style>') and data[style_index:].count('>'):
            return False
        return meth(self, data)
    return wrap

def inside_js(meth):
    def wrap(self, data):
        script_index = data.lower().rfind('<script')
        if script_index > data.lower().rfind('</script>') and data[script_index:].count('>'):
            return meth(self, data)
        return False
    return wrap

def inside_style(meth):
    def wrap(self, data):
        style_index = data.lower().rfind('<style')
        if style_index > data.lower().rfind('</style>') and data[style_index:].count('>'):
            return meth(self, data)
        return False
    return wrap

class HtmlContext(Context):

    @normalize_html
    @inside_html
    def inside_comment(self, data):
        # We are inside <!--...
        if data.rfind('<!--') <= data.rfind('-->'):
            return False
        return True

class HtmlTag(HtmlContext):

    def __init__(self):
        self.name = 'TAG'

    @normalize_html
    @inside_html
    def match(self, data):
        if self.inside_comment(data):
            return False
        if data[-1] == '<':
            return True
        return False

    def can_break(self, payload):
        for i in [' ', '>']:
            if i in payload:
                return True
        return False

class HtmlText(HtmlContext):

    def __init__(self):
        self.name = 'HTML_TEXT'

    @normalize_html
    @inside_html
    def match(self, data):
        if self.inside_comment(data):
            return False
        if data.rfind('<') <= data.rfind('>'):
            return True
        return False

    def can_break(self, payload):
        if "<" in payload:
            return True
        return False

class HtmlComment(HtmlContext):

    def __init__(self):
        self.name = 'HTML_COMMENT'

    @normalize_html
    @inside_html
    def match(self, data):
        if self.inside_comment(data):
            return True
        return False

    def can_break(self, payload):
        for i in ['-', '>', '<']:
            if i not in payload:
                return False
        return True

class HtmlAttrName(HtmlContext):

    def __init__(self):
        self.name = 'ATTR_NAME'

    @normalize_html
    @inside_html
    def match(self, data):
        if self.inside_comment(data):
            return False

        quote_character = None
        open_angle_bracket = data.rfind('<')
        # We are inside <...
        if open_angle_bracket <= data.rfind('>'):
            return False
        for s in data[open_angle_bracket+1:]:
            if s in ['"', "'"]:
                if quote_character and s == quote_character:
                    quote_character = None
                    continue
                elif not quote_character:
                    quote_character = s
                    continue
        if not quote_character and len(data[open_angle_bracket+1:]):
            return True
        return False

    def can_break(self, payload):
        if "=" in payload:
            return True
        return False

class HtmlAttrQuote(HtmlContext):

    def __init__(self):
        self.name = None
        self.quote_character = None

    @normalize_html
    @inside_html
    def match(self, data):
        if self.inside_comment(data):
            return False
        quote_character = None
        open_angle_bracket = data.rfind('<')
        # We are inside <...
        if open_angle_bracket <= data.rfind('>'):
            return False
        for s in data[open_angle_bracket+1:]:
            if s in ['"', "'"]:
                if quote_character and s == quote_character:
                    quote_character = None
                    continue
                elif not quote_character:
                    quote_character = s
                    continue
        if quote_character == self.quote_character:
            return True
        return False

    def can_break(self, payload):
        if self.quote_character in payload:
            return True
        # 
        # For cases with src and href + javascript scheme
        #
        payload = payload.lower().replace(' ', '')
        if payload.endswith('href=' + self.quote_character):
            return True
        if payload.endswith('src=' + self.quote_character):
            return True
        return False

class HtmlAttrSingleQuote(HtmlAttrQuote):

    def __init__(self):
        self.name = 'ATTR_SINGLE_QUOTE'
        self.quote_character = "'"

class HtmlAttrDoubleQuote(HtmlAttrQuote):

    def __init__(self):
        self.name = 'ATTR_DOUBLE_QUOTE'
        self.quote_character = '"'


class ScriptContext(Context):
    
    @normalize_html
    @inside_js
    def inside_comment(self, data):
        return (self._inside_multi_comment(data) or self._inside_line_comment(data))

    @normalize_html
    @inside_js
    def _inside_multi_comment(self, data):
        # We are inside /*...
        if data.rfind('/*') <= data.rfind('*/'):
            return False
        return True

    @normalize_html
    @inside_js
    def _inside_line_comment(self, data):
        last_line = data.split('\n')[-1].strip()
        if last_line.find('//') == 0:
            return True
        return False

class StyleContext(Context):

    @normalize_html
    @inside_style
    def inside_comment(self, data):
        # We are inside /*...
        if data.rfind('/*') <= data.rfind('*/'):
            return False
        return True

    def crop(self, data):
        return data[data.lower().rfind('<style')+1:]

class ScriptMultiComment(ScriptContext):

    def __init__(self):
        self.name = 'SCRIPT_MULTI_COMMENT'

    def match(self, data):
        return self._inside_multi_comment(data)

    def can_break(self, payload):
        for i in ['/', '*']:
            if i not in payload:
                return False
        return True

class ScriptLineComment(ScriptContext):

    def __init__(self):
        self.name = 'SCRIPT_LINE_COMMENT'

    def match(self, data):
        return self._inside_line_comment(data)

    def can_break(self, payload):
        for i in ['\n']:
            if i not in payload:
                return False
        return True

class ScriptQuote(ScriptContext):

    def __init__(self):
        self.name = None
        self.quote_character = None

    @normalize_html
    @inside_js
    def match(self, data):
        if self.inside_comment(data):
            return False
        quote_character = None
        open_angle_bracket = data.lower().rfind('<script')
        # We are inside <...
        if open_angle_bracket <= data.lower().rfind('</script>'):
            return False
        for s in data[open_angle_bracket+1:]:
            if s in ['"', "'"]:
                if quote_character and s == quote_character:
                    quote_character = None
                    continue
                elif not quote_character:
                    quote_character = s
                    continue
        if quote_character == self.quote_character:
            return True
        return False

    def can_break(self, payload):
        if self.quote_character in payload:
            return True
        return False

class ScriptSingleQuote(ScriptQuote):

    def __init__(self):
        self.name = 'SCRIPT_SINGLE_QUOTE'
        self.quote_character = "'"

class ScriptDoubleQuote(ScriptQuote):

    def __init__(self):
        self.name = 'SCRIPT_DOUBLE_QUOTE'
        self.quote_character = '"'

class StyleText(StyleContext):

    def __init__(self):
        self.name = 'STYLE_TEXT'

    @normalize_html
    @inside_style
    def match(self, data):
        if self.inside_comment(data):
            return False
        quote_character = None
        for s in self.crop(data):
            if s in ['"', "'"]:
                if quote_character and s == quote_character:
                    quote_character = None
                    continue
                elif not quote_character:
                    quote_character = s
                    continue
        if not quote_character:
            return True
        return False

    def can_break(self, payload):
        for i in ['<', '/']:
            if i not in payload:
                return False
        return True

class ScriptText(StyleContext):

    def __init__(self):
        self.name = 'SCRIPT_TEXT'

    @normalize_html
    @inside_js
    def match(self, data):
        if self.inside_comment(data):
            return False
        return True

        quote_character = None
        for s in self.crop(data):
            if s in ['"', "'"]:
                if quote_character and s == quote_character:
                    quote_character = None
                    continue
                elif not quote_character:
                    quote_character = s
                    continue
        if not quote_character:
            return True
        return False

    def can_break(self, payload):
        for i in ['<', '/']:
            if i not in payload:
                return False
        return True

    def is_executable(self, data):
        return False


class StyleComment(StyleContext):

    def __init__(self):
        self.name = 'STYLE_COMMENT'

    def match(self, data):
        return self.inside_comment(data)

    def can_break(self, data):
        for i in ['/', '*']:
            if i not in data:
                return False
        return True

class StyleQuote(StyleContext):

    def __init__(self):
        self.name = None
        self.quote_character = None

    @normalize_html
    @inside_style
    def match(self, data):
        if self.inside_comment(data):
            return False
        quote_character = None
        open_angle_bracket = data.lower().rfind('<style')
        # We are inside <...
        if open_angle_bracket <= data.lower().rfind('</style>'):
            return False
        for s in data[open_angle_bracket+1:]:
            if s in ['"', "'"]:
                if quote_character and s == quote_character:
                    quote_character = None
                    continue
                elif not quote_character:
                    quote_character = s
                    continue
        if quote_character == self.quote_character:
            return True
        return False

    def can_break(self, data):
        if self.quote_character in data:
            return True
        return False

class StyleSingleQuote(StyleQuote):

    def __init__(self):
        self.name = 'STYLE_SINGLE_QUOTE'
        self.quote_character = "'"

class StyleDoubleQuote(StyleQuote):

    def __init__(self):
        self.name = 'STYLE_DOUBLE_QUOTE'
        self.quote_character = '"'


def get_contexts():
    contexts = []
    contexts.append(HtmlAttrSingleQuote())
    contexts.append(HtmlAttrDoubleQuote())
    contexts.append(HtmlAttrName())
    contexts.append(HtmlTag())
    contexts.append(HtmlText())
    contexts.append(HtmlComment())
    contexts.append(ScriptMultiComment())
    contexts.append(ScriptLineComment())
    contexts.append(ScriptSingleQuote())
    contexts.append(ScriptDoubleQuote())
    contexts.append(ScriptText())
    contexts.append(StyleText())
    contexts.append(StyleComment())
    contexts.append(StyleSingleQuote())
    contexts.append(StyleDoubleQuote())
    return contexts

def get_context(data, payload):
    '''
    return list of tuples (<context>, index)
    '''
    chunks = data.split(payload)
    tmp = ''
    result = []
    counter = 0

    for chunk in chunks[:-1]:
        tmp += chunk
        for context in get_contexts():
            if context.match(tmp):
                result.append((context, counter))
        counter += 1
    return result



