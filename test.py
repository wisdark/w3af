import random
import unittest

SCRIPT = 7
CDATA = 8

html = '''
<html>
    <head>
        <style></style>
        <script></script>
    </head>
    <body>
        <h1 foo="ATTR_DOUBLE_QUOTE">TEXT</h1>
        <TAG>123</TAG>
        <b style="='" foo='fsdfs dfATTR_SINGLE_QUOTE'>dddd</b>
        ATTR_SINGLE_QUOTE
        <i ATTR_NAME="foo">ddd</i>
        <!--
        
        Some COMMENT here
        
        -->
    </body>
</html>
ATTR_SINGLE_QUOTE'''

class HtmlContext(object):
    name = ''

    def get_name(self):
        return self.name

    def is_match(self, data):
        raise 'is_match() should be implemented'

    def can_break(self, data):
        raise 'can_break() should be implemented'

class Tag(HtmlContext):

    def __init__(self):
        self.name = 'TAG'

    def is_match(self, data):
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
        self.name = 'TEXT'

    def is_match(self, data):
        if data.rfind('<') <= data.rfind('>'):
            return True
        return False

    def can_break(self, data):
        if "<" in data:
            return True
        return False

class Comment(HtmlContext):

    def __init__(self):
        self.name = 'COMMENT'

    def is_match(self, data):
        # We are inside <!--...
        if data.rfind('<!--') <= data.rfind('-->'):
            return False
        return True

    def can_break(self, data):
        for i in ['-', '>', '<']:
            if i not in data:
                return False
        return True

class AttrName(HtmlContext):

    def __init__(self):
        self.name = 'ATTR_NAME'

    def is_match(self, data):
        quote_character = None
        open_angle_bracket = data.rfind('<')
        # We are inside <...
        if open_angle_bracket <= data.rfind('>'):
            return False
        # We are not inside <!--...
        if data.rfind('<!--') > data.rfind('-->'):
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

class AttrSingleQuote(HtmlContext):

    def __init__(self):
        self.name = 'ATTR_SINGLE_QUOTE'

    def is_match(self, data):
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
        if quote_character == "'":
            return True
        return False

    def can_break(self, data):
        if "'" in data:
            return True
        return False

class AttrDoubleQuote(HtmlContext):

    def __init__(self):
        self.name = 'ATTR_DOUBLE_QUOTE'

    def is_match(self, data):
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
        if quote_character == '"':
            return True
        return False

    def can_break(self, data):
        if '"' in data:
            return True
        return False


AVAILABLE_CONTEXTS = []
AVAILABLE_CONTEXTS.append(AttrSingleQuote())
AVAILABLE_CONTEXTS.append(AttrDoubleQuote())
AVAILABLE_CONTEXTS.append(AttrName())
AVAILABLE_CONTEXTS.append(Tag())
AVAILABLE_CONTEXTS.append(Text())
AVAILABLE_CONTEXTS.append(Comment())

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

    def test_attr_single_quote(self):
        self.assertEqual(
                get_context(html, 'ATTR_SINGLE_QUOTE')[0][0].get_name(), 
                AttrSingleQuote().get_name()
                )
 
    def test_tag(self):
        self.assertEqual(
                get_context(html, 'TAG')[0][0].get_name(), 
                Tag().get_name()
                )  

    def test_attr_name(self):
        self.assertEqual(
                get_context(html, 'ATTR_NAME')[0][0].get_name(), 
                AttrName().get_name()
                )  

    def test_text(self):
        self.assertEqual(
                get_context(html, 'TEXT')[0][0].get_name(), 
                Text().get_name()
                )  

    def test_comment(self):
        self.assertEqual(
                get_context(html, 'COMMENT')[0][0].get_name(), 
                Comment().get_name()
                )

    def test_attr_double_quote(self):
        self.assertEqual(
                get_context(html, 'ATTR_DOUBLE_QUOTE')[0][0].get_name(), 
                AttrDoubleQuote().get_name()
                )
if __name__ == '__main__':
    unittest.main()
