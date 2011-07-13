# -*- coding: UTF-8 -*-
'''
test_sgmlparsers.py

Copyright 2011 Andres Riancho

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
from pymock import PyMockTestCase, IfTrue, override, dontcare, at_least

from ..htmlParser import HTMLParser
from ..sgmlParser import SGMLParser
from core.data.parsers.urlParser import url_object
from core.data.url.httpResponse import httpResponse

HTML_DOC = u'''
<html>
    <head>
        %(head)s
    </head>
    <body>
        %(body)s
    </body>
</html>
'''

# Form templates
FORM_METHOD_GET = u'''
<form method="GET" action="/index.php">
    %(form_content)s
</form>
'''
FORM_METHOD_POST = u'''
<form method="POST" action="/index.php">
    %(form_content)s
</form>
'''
FORM_WITHOUT_METHOD = u'''
<form action="/index.php">
    %(form_content)s
</form>
'''
FORM_WITHOUT_ACTION = u'''
<form method="POST">
    %(form_content)s
</form>
'''

# Textarea templates
TEXTAREA_WITH_NAME_AND_DATA = u'''
<textarea name="sample">
    sample_value
</textarea>'''
TEXTAREA_WITH_ID_AND_DATA = u'''
<textarea id="sample">
    sample_value
</textarea>'''
TEXTAREA_WITH_NAME_ID_AND_DATA = u'''
<textarea name="sample" id="sample_id">
    sample_value
</textarea>'''
TEXTAREA_WITH_NAME_EMPTY = u'<textarea name="my_textarea"></textarea>'

# Input templates
INPUT_TEXT_WITH_NAME = u'<input name="foo1" type="text" value="bar">'
INPUT_TEXT_WITH_ID = u'<input id="foo2" type="text" value="bar">'
INPUT_FILE_WITH_NAME = u'<input name="foo3" type="file" value="bar">'
INPUT_SUBMIT_WITH_NAME = u'<input name="foo4" type="submit">'
INPUT_RADIO_WITH_NAME = u'<input name="foo5" type="radio" checked>'
INPUT_CHECKBOX_WITH_NAME = u'<input name="foo6" type="checkbox" checked="true">'
INPUT_HIDDEN = u'<input name="foo7" type="hidden" value="bar">'

# Select templates
SELECT_WITH_NAME = u'''
<select name="vehicle">
    <option value=""></option>
    <option value="car"/>
    <option value="plane"></option>
    <option value="bike"></option>
    </option>
</select>'''
SELECT_WITH_ID = u'''
<select id="vehicle">
    <option value="car"/>
    <option value="plane"></option>
    <option value="bike"></option>
</select>'''
SELECT_WITHOUT_NAME_OR_ID = u'''
<select>
    <option value="car"/>
    <option value="plane"></option>
</select>'''

# Anchor templates
A_LINK_RELATIVE = u'<a href="/index.php">XXX</a>'
A_LINK_ABSOLUTE = u'<a href="www.w3af.com/home.php">XXX</a>'
A_LINK_FRAGMENT = u'<a href="#mark">XXX</a>'

# Other templates
BASE_TAG = u'''
<base href="http://www.w3afbase.com">
<base target="_blank">
'''
META_REFRESH = u'''<meta http-equiv="refresh" content="600">'''
META_REFRESH_WITH_URL = u'''
<meta http-equiv="refresh" content="2;url=http://crawler.w3af.com/">'''
BODY_FRAGMENT_WITH_EMAILS = u'''===>jandalia@bing.com%^&1!
<script>ariancho%40gmail.com<script> name_with_ñ@w3af.it
תגובות_לאתר
'''

URL = url_object('http://w3af.com')

def _build_http_response(url, body_content, headers={}):
    if 'content-type' not in headers:
        headers['content-type'] = 'text/html'
    return httpResponse(200, body_content, headers, url, url, charset='utf-8')

# We subclass SGMLParser to prevent that the parsing process
# while init'ing the parser instance
class _SGMLParser(SGMLParser):
    
    def __init__(self, http_resp):
        # Save "_parse" reference
        orig_parse = self._parse
        # Monkeypatch it!
        self._parse = lambda arg: None
        # Now call parent's __init__
        SGMLParser.__init__(self, http_resp)
        # Restore it
        self._parse = orig_parse
        

class TestSGMLParser(PyMockTestCase):

    def setUp(self):
        PyMockTestCase.setUp(self)
    
    def test_parser_attrs(self):
        body_content = HTML_DOC % {'head':'', 'body':''}
        p = _SGMLParser(_build_http_response(URL, body_content))
        
        # Assert parser has these attrs correctly initialized
        self.assertFalse(getattr(p, '_inside_form'))
        self.assertFalse(getattr(p, '_inside_select'))
        self.assertFalse(getattr(p, '_inside_textarea'))
        self.assertFalse(getattr(p, '_inside_script'))
        
        self.assertEquals(set(), getattr(p, '_tag_and_url'))
        self.assertEquals(set(), getattr(p, '_parsed_urls'))
        self.assertEquals([], getattr(p, '_forms'))
        self.assertEquals([], getattr(p, '_comments_in_doc'))
        self.assertEquals([], getattr(p, '_scripts_in_doc'))
        self.assertEquals([], getattr(p, '_meta_redirs'))
        self.assertEquals([], getattr(p, '_meta_tags'))

    def test_baseurl(self):
        body = HTML_DOC % {'head': BASE_TAG, 'body': ''}
        p = _SGMLParser(_build_http_response(URL, body))
        p._parse(body)
        self.assertEquals(url_object('http://www.w3afbase.com/'), p._baseUrl)
        
    def test_regex_urls(self):
        #self._regex_url_parse(httpresp)
        self.assertTrue(1==0)
    
    def test_meta_tags(self):
        body = HTML_DOC % \
            {'head': META_REFRESH + META_REFRESH_WITH_URL,
            'body': ''}
        p = _SGMLParser(_build_http_response(URL, body))
        p._parse(body)
        self.assertTrue(2, len(p.meta_redirs))
        self.assertTrue("2;url=http://crawler.w3af.com/" in p.meta_redirs)
        self.assertTrue("600" in p.meta_redirs)
        self.assertEquals([url_object('http://crawler.w3af.com/')], p.references[0])
    
    def test_case_sensitivity(self):
        '''
        Ensure handler methods are *always* called with lowered-cased
        tag and attribute names
        '''
        def islower(s):
            il = False
            if isinstance(s, basestring):
                il = s.islower()
            elif isinstance(s, dict):
                il = all(k.islower() for k in s)
            assert il, "'%s' is not lowered-case" % s 
            return il
        
        from itertools import combinations
        from random import choice
        
        tags = (A_LINK_ABSOLUTE, INPUT_CHECKBOX_WITH_NAME, SELECT_WITH_NAME,
                TEXTAREA_WITH_ID_AND_DATA, INPUT_HIDDEN)
        ops = "lower", "upper", "title"
        
        for indexes in combinations(range(len(tags)), 2):
            
            body_elems = []
            
            for index, tag in enumerate(tags):
                ele = tag
                if index in indexes:
                    ele = getattr(tag, choice(ops))()
                body_elems.append(ele)
            
            p = _SGMLParser(_build_http_response(URL, ''))
            args = (IfTrue(islower), IfTrue(islower))
            override(p, 'start').expects(*args).returns(None).at_least(10)
            body = HTML_DOC % {'head': '', 'body': ''.join(body_elems)}
            # Replay
            self.replay()
            p._parse(body)
            # Verify and reset
            self.verify()
            self.reset()
            
    
    def test_find_emails(self):
        body = HTML_DOC % {'head': '', 'body': BODY_FRAGMENT_WITH_EMAILS}
        p = _SGMLParser(_build_http_response(URL, body))
        emails = ['jandalia@bing.com', 'ariancho@gmail.com',
                  u'name_with_ñ@w3af.it']
        self.assertEquals(emails, p.getEmails())


# We subclass HTMLParser to prevent that the parsing process
# while init'ing the parser instance
class _HTMLParser(HTMLParser):
    
    def __init__(self, http_resp):
        # Save "_parse" reference
        orig_parse = self._parse
        # Monkeypatch it!
        self._parse = lambda arg: None
        # Now call parent's __init__
        HTMLParser.__init__(self, http_resp)
        # Restore it
        self._parse = orig_parse


class TestHTMLParser(PyMockTestCase):

    def setUp(self):
        PyMockTestCase.setUp(self)

    def test_forms(self):
        body = HTML_DOC % \
            {'head': '',
             'body': FORM_METHOD_GET % {'form_content': ''} +
                     FORM_WITHOUT_ACTION % {'form_content': ''}
            }
        p = _HTMLParser(_build_http_response(URL, body))
        p._parse(body)
        self.assertEquals(2, len(p.forms))
    
    def test_form_without_meth(self):
        '''
        When the form has no 'method' => 'GET' will be used 
        '''
        body = HTML_DOC % \
                    {'head': '',
                     'body': FORM_WITHOUT_METHOD % {'form_content': ''}
                    }
        p = _HTMLParser(_build_http_response(URL, body))
        p._parse(body)
        self.assertEquals('GET', p.forms[0].getMethod())
    
    def test_form_without_action(self):
        '''
        If the form has no 'content' => httpResponse's url will be used
        '''
        body = HTML_DOC % \
                    {'head': '',
                     'body': FORM_WITHOUT_ACTION % {'form_content': ''}
                    }
        p = _HTMLParser(_build_http_response(URL, body))
        p._parse(body)
        self.assertEquals(URL, p.forms[0].getAction())
    
    def test_inputs_inside_form(self):
        '''
        We expect that the form contains all the inputs (both those declared
        before and after)
        '''        
        body = HTML_DOC % \
            {'head': '',
             'body': (INPUT_TEXT_WITH_NAME + INPUT_TEXT_WITH_ID +
                  INPUT_FILE_WITH_NAME + INPUT_SUBMIT_WITH_NAME +
                  (FORM_WITHOUT_METHOD % {'form_content': ''}) + # form in the middle
                  INPUT_RADIO_WITH_NAME + INPUT_CHECKBOX_WITH_NAME +
                  INPUT_HIDDEN)
            }
        p = _HTMLParser(_build_http_response(URL, body))
        p._parse(body)
        # Only one form
        self.assertTrue(len(p.forms) == 1)
        # Ensure that parsed inputs actually belongs to the form and
        # have the expected values
        f = p.forms[0]
        self.assertEquals(['bar'], f['foo1']) # text input
        self.assertEquals(['bar'], f['foo2']) # text input
        self.assertEquals([''], f['foo3']) # file input
        self.assertEquals([''], f['foo5']) # radio input
        self.assertEquals([''], f['foo6']) # checkbox input
        self.assertEquals(['bar'], f['foo7']) # hidden input
        self.assertEquals('', f._submitMap['foo4']) # submit input
        
    
    def test_inputs_outside_form(self):
        pass
    
    def test_textareas_inside_form(self):
        pass
    
    def test_textarea_outside_form(self):
        pass
    
    def test_selects_inside_form(self):
        pass
    
    def test_selects_outside_form(self):
        pass
    