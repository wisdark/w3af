import unittest
# 
# TODO
#
# 3. expression in CSS

#
html = '''
<html>
    <head>
        <style>
        STYLE_TEXT

        h1 {
            color: "STYLE_DOUBLE_QUOTE";
            color: 'STYLE_SINGLE_QUOTE';
        }

        /*
         STYLE_COMMENT
         * */

        </style>
        <script>
        var foo = '\\'SCRIPT_SINGLE_QUOTE';
        var foo2 = "SCRIPT_DOUBLE_QUOTE <b>";
        SCRIPT_TEXT
        /*

        Some SCRIPT_MULTI_COMMENT  here

        var foo2 = "SCRIPT_DOUBLE_QUOTE <b>";


        */
        // Some SCRIPT_LINE_COMMENT  here 
        </script>
    </head>
    <body>
        <h1 foo="ATTR_DOUBLE_QUOTE">HTML_TEXT</h1>
        <TAG>123</TAG>
        <b style="='" foo='fsdfs dfATTR_SINGLE_QUOTE'>dddd</b>
        ATTR_SINGLE_QUOTE
        <i ATTR_NAME="foo">ddd</i>
        <!--
        
        Some HTML_COMMENT here
        
        -->
        <img src="ATTR_DOUBLE_QUOTE" />
        <a href="ATTR_DOUBLE_QUOTE" />link</a>
        <script>
        var foo = '\\'SCRIPT_SINGLE_QUOTE <h1>HTML_TEXT';
        </script>
    </body>
</html>
ATTR_SINGLE_QUOTE'''

class Context(object):
    name = ''

    def get_name(self):
        return self.name

    def _is_js(self, data):
        if data.lower().rfind('<script') > data.lower().rfind('</script>'):
            return True
        return False

    def _is_style(self, data):
        if data.lower().rfind('<style') > data.lower().rfind('</style>'):
            return True
        return False

    def _is_html(self, data):
        return not (self._is_js(data) or self._is_style(data))

    def need_break(self, data):
        return True

    def can_break(self, data):
        raise 'can_break() should be implemented'
    
    def is_match(self, data):
        raise 'is_match() should be implemented'

    def inside_comment(self, data):
        raise 'inside_comment() should be implemented'


class HtmlContext(Context):
    def inside_comment(self, data):
        if not self._is_html(data):
            return False
        # We are inside <!--...
        if data.rfind('<!--') <= data.rfind('-->'):
            return False
        return True

class ScriptContext(Context):
    
    def inside_comment(self, data):
        return (self._inside_multi_comment(data) or self._inside_line_comment(data))

    def _inside_multi_comment(self, data):
        if not self._is_js(data):
            return False
        # We are inside /*...
        if data.rfind('/*') <= data.rfind('*/'):
            return False
        return True

    def _inside_line_comment(self, data):
        if not self._is_js(data):
            return False
        last_line = data.split('\n')[-1].strip()
        if last_line.find('//') == 0:
            return True
        return False

class StyleContext(Context):

    def inside_comment(self, data):
        if not self._is_style(data):
            return False
        # We are inside /*...
        if data.rfind('/*') <= data.rfind('*/'):
            return False
        return True

    def crop(self, data):
        return data[data.lower().rfind('<style')+1:]

class Tag(HtmlContext):

    def __init__(self):
        self.name = 'TAG'

    def is_match(self, data):
        if not self._is_html(data) or self.inside_comment(data):
            return False
        if data[-1] == '<':
            return True
        return False

    def can_break(self, data):
        for i in [' ', '>']:
            if i in data:
                return True
        return False

class Text(HtmlContext):

    def __init__(self):
        self.name = 'HTML_TEXT'

    def is_match(self, data):
        if not self._is_html(data) or self.inside_comment(data):
            return False
        if data.rfind('<') <= data.rfind('>'):
            return True
        return False

    def can_break(self, data):
        if "<" in data:
            return True
        return False

class Comment(HtmlContext):

    def __init__(self):
        self.name = 'HTML_COMMENT'

    def is_match(self, data):
        if self._is_html(data) and self.inside_comment(data):
            return True
        return False

    def can_break(self, data):
        for i in ['-', '>', '<']:
            if i not in data:
                return False
        return True

class AttrName(HtmlContext):

    def __init__(self):
        self.name = 'ATTR_NAME'

    def is_match(self, data):
        if not self._is_html(data) or self.inside_comment(data):
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

    def can_break(self, data):
        if "=" in data:
            return True
        return False

class ScriptMultiComment(ScriptContext):

    def __init__(self):
        self.name = 'SCRIPT_MULTI_COMMENT'

    def is_match(self, data):
        return self._inside_multi_comment(data)

    def can_break(self, data):
        for i in ['/', '*']:
            if i not in data:
                return False
        return True

class ScriptLineComment(ScriptContext):

    def __init__(self):
        self.name = 'SCRIPT_LINE_COMMENT'

    def is_match(self, data):
        return self._inside_line_comment(data)

    def can_break(self, data):
        for i in ['\n']:
            if i not in data:
                return False
        return True

class ScriptQuote(ScriptContext):

    def __init__(self):
        self.name = None
        self.quote_character = None

    def is_match(self, data):
        if not self._is_js(data) or self.inside_comment(data):
            return False
        data = data.replace('\\"','')
        data = data.replace("\\'",'')
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

    def can_break(self, data):
        if self.quote_character in data:
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

class AttrQuote(HtmlContext):

    def __init__(self):
        self.name = None
        self.quote_character = None

    def is_match(self, data):
        if not self._is_html(data) or self.inside_comment(data):
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

    def can_break(self, data):
        if self.quote_character in data:
            return True
        # 
        # For cases with src and href + javascript scheme
        #
        data = data.lower().replace(' ', '')
        if data.endswith('href=' + self.quote_character):
            return True
        if data.endswith('src=' + self.quote_character):
            return True
        return False

class AttrSingleQuote(AttrQuote):

    def __init__(self):
        self.name = 'ATTR_SINGLE_QUOTE'
        self.quote_character = "'"

class AttrDoubleQuote(AttrQuote):

    def __init__(self):
        self.name = 'ATTR_DOUBLE_QUOTE'
        self.quote_character = '"'

class StyleText(StyleContext):

    def __init__(self):
        self.name = 'STYLE_TEXT'

    def is_match(self, data):
        if not self._is_style(data) or self.inside_comment(data):
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

    def can_break(self, data):
        for i in ['<', '/']:
            if i not in data:
                return False
        return True

class ScriptText(StyleContext):

    def __init__(self):
        self.name = 'SCRIPT_TEXT'

    def is_match(self, data):
        if not self._is_js(data) or self.inside_comment(data):
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

    def can_break(self, data):
        for i in ['<', '/']:
            if i not in data:
                return False
        return True

    def need_break(self, data):
        return False


class StyleComment(StyleContext):

    def __init__(self):
        self.name = 'STYLE_COMMENT'

    def is_match(self, data):
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

    def is_match(self, data):
        if not self._is_style(data) or self.inside_comment(data):
            return False
        data = data.replace('\\"','')
        data = data.replace("\\'",'')
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

AVAILABLE_CONTEXTS = []
AVAILABLE_CONTEXTS.append(AttrSingleQuote())
AVAILABLE_CONTEXTS.append(AttrDoubleQuote())
AVAILABLE_CONTEXTS.append(AttrName())
AVAILABLE_CONTEXTS.append(Tag())
AVAILABLE_CONTEXTS.append(Text())
AVAILABLE_CONTEXTS.append(Comment())
AVAILABLE_CONTEXTS.append(ScriptMultiComment())
AVAILABLE_CONTEXTS.append(ScriptLineComment())
AVAILABLE_CONTEXTS.append(ScriptSingleQuote())
AVAILABLE_CONTEXTS.append(ScriptDoubleQuote())
AVAILABLE_CONTEXTS.append(ScriptText())
AVAILABLE_CONTEXTS.append(StyleText())
AVAILABLE_CONTEXTS.append(StyleComment())
AVAILABLE_CONTEXTS.append(StyleSingleQuote())
AVAILABLE_CONTEXTS.append(StyleDoubleQuote())

def get_context(data, payload):
    '''
    return list of tuples (<context>, index)
    '''
    chunks = data.split(payload)
    tmp = ''
    result = []
    counter = 0

    if len(chunks) == 1:
        raise Exception('Empty results')

    for chunk in chunks[:-1]:
        tmp += chunk
        for context in AVAILABLE_CONTEXTS:
            if context.is_match(tmp):
                result.append((context, counter))
        counter += 1
    return result

class TestContexts(unittest.TestCase):

    def test_all(self):
        for context in AVAILABLE_CONTEXTS:
            self.assertEqual(
                    get_context(html, context.get_name())[0][0].get_name(), 
                    context.get_name()
                    )
    
    def test_html_inside_js(self):
            self.assertEqual(
                    get_context(html, Text().get_name())[1][0].get_name(), 
                    ScriptSingleQuote().get_name()
                    )

if __name__ == '__main__':
    unittest.main()
