html  = '''
<html>
    <input type="button" style="body{}" value='ClickMe' onClick="1vsdvdfvdfvdfv
'''

html = '''
        <html>
        <input type="button" value="ClickMe" onClick=`'''

ATTR_DELIMETERS = ['"', '`', "'"]
JS_EVENTS = ['onclick', 'ondblclick', 'onmousedown', 'onmousemove', 
            'onmouseout', 'onmouseover', 'onmouseup', 'onchange', 'onfocus', 
            'onblur', 'onscroll', 'onselect', 'onsubmit', 'onkeydown', 
            'onkeypress', 'onkeyup', 'onload', 'onunload']

def get_html_attr(data):
    attr_name = ''
    inside_name = False
    inside_value = False
    open_angle_bracket = data.rfind('<')
    quote_character = None
    open_context = None
    i = open_angle_bracket - 1

    if open_angle_bracket <= data.rfind('>'):
        return False

    for s in data[open_angle_bracket:]:
        i += 1

        if s in ATTR_DELIMETERS and not quote_character:
            quote_character = s
            if inside_value and open_context:
                open_context = i + 1
            continue
        elif s in ATTR_DELIMETERS and quote_character:
            quote_character = None
            inside_value = False
            open_context = None
            continue

        if quote_character:
            continue

        if s == ' ':
            inside_name = True
            inside_value = False
            attr_name = ''
            continue

        if s == '=':
            inside_name = False
            inside_value = True
            open_context = i + 1
            continue

        if inside_name:
            attr_name += s
    attr_name = attr_name.lower()
    return (attr_name, quote_character, open_context)

def _inside_js(data):
    script_index = data.lower().rfind('<script')
    if script_index > data.lower().rfind('</script>') and data[script_index:].count('>'):
        return True
    return False

def _inside_style(data):
    script_index = data.lower().rfind('<style')
    if script_index > data.lower().rfind('</style>') and data[script_index:].count('>'):
        return True
    return False

def _inside_html_attr(data, attrs):
    attr_data = get_html_attr(data)
    if not attr_data:
        return False
    for attr in attrs:
        if attr == attr_data[0]:
            return True
    return False

def _inside_event_attr(data):
    if _inside_html_attr(data, JS_EVENTS):
        return True
    return False

def _inside_style_attr(data):
    if _inside_html_attr(data, ['style']):
        return True
    return False


def crop_js(data, context='tag'):
    if context == 'tag':
        return data[data.lower().rfind('<script')+1:]
    else:
        attr_data = get_html_attr(data)
        if attr_data:
            return data[attr_data[2]:]
    return data

def crop_style(data, context='tag'):
    if context == 'tag':
        return data[data.lower().rfind('<style')+1:]
    else:
        attr_data = get_html_attr(data)
        if attr_data:
            return data[attr_data[2]:]

def inside_js(meth):
    def wrap(self, data):
        if _inside_js(data):
            data = crop_js(data)
            return meth(self, data)
        if _inside_event_attr(data):
            data = crop_js(data, 'attr')
            return meth(self, data)
        return False
    return wrap

def inside_style(meth):
    def wrap(self, data):
        if _inside_style(data):
            data = crop_style(data)
            return meth(self, data)
        if _inside_style_attr(data):
            data = crop_style(data, 'attr')
            return meth(self, data)
        return False
    return wrap

def inside_html(meth):
    def wrap(self, data):
        if _inside_js(data) or _inside_style(data):
            return False
        return meth(self, data)
    return wrap

def match(foo, data):
    print 'match() is calling with data:\n' + data
    return True

f= inside_js(match)
f('123', html)

#print get_html_attr(html)
