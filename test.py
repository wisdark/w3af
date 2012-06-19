TAG = 1
ATTR_NAME = 2
ATTR_DOUBLE_QUOTE = 3 
ATTR_SINGLE_QUOTE = 4
TEXT = 5
COMMENT = 6 
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
        <b foo='fsdfs dfATTR_SINGLE_QUOTE'>dddd</b>
        ATTR_SINGLE_QUOTE
    </body>
</html>
ATTR_SINGLE_QUOTE'''

class HtmlContext(object):
    name = ''

    def get_name(self):
        return name

    def is_match(self, data):
        raise 'is_match() should be implemented'

    def can_break(self, data):
        raise 'can_break() should be implemented'

class AttrSingleQuote(HtmlContext):

    def __init__(self):
        self.name = 'ATTR_SINGLE_QUOTE'

    def is_match(self, data):
        print data
        return True

    def can_break(self, data):
        if "'" in data:
            return True
        else:
            return False

AVAILABLE_CONTEXTS = []
AVAILABLE_CONTEXTS.append(AttrSingleQuote())

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

try:
    print get_context(html, 'ATTR_SINGLE_QUOTE')
except Exception, e:
    print '!!!', e
