'''
test_context.py

Copyright 2012 Andres Riancho

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

import unittest

from core.data.context.context import (get_context , get_contexts, HtmlText,
                                        ScriptSingleQuote, ScriptText, HtmlComment,
                                        HtmlAttrSingleQuote, HtmlAttrDoubleQuote, HtmlAttr, HtmlAttrDoubleQuote2ScriptText)

class TestContext(unittest.TestCase):
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
            <i HTML_ATTR="foo">ddd</i>
            <h1 a='<' foo=`" ssfdsf ' HTML_ATTR_BACKTICKS`>HTML_TEXT</h1>
            <h1 a='<' foo=" ssfdsf ' HTML_ATTR_DOUBLE_QUOTE">HTML_TEXT</h1>
            <HTML_TAG>123</HTML_TAG>
            <b style="='" foo='fsdfs dfHTML_ATTR_SINGLE_QUOTE'>dddd</b>
            HTML_ATTR_SINGLE_QUOTE
            <!--
            
            Some HTML_COMMENT here
            
            -->
            <img src="HTML_ATTR_DOUBLE_QUOTE" />
            <a href="HTML_ATTR_DOUBLE_QUOTE" />link</a>
            <script>
            var foo = '\\'SCRIPT_SINGLE_QUOTE <h1>HTML_TEXT';
            </script>
        </body>
    </html>
    HTML_ATTR_SINGLE_QUOTE'''


    def _test_all(self):
        for context in get_contexts():
            self.assertEqual(
                    get_context(self.html, context.get_name())[0][0].get_name(), 
                    context.get_name()
                   )
    
    def test_html_inside_js(self):
        self.assertEqual(
                get_context(self.html, HtmlText().get_name())[2][0].get_name(), 
                ScriptSingleQuote().get_name()
               )


    def test_payload(self):
        html = '''
        <html>
            <body>
                &added=blah111%3C1%3E<br>::::: blahPAYLOAD<br>::::: :::::
            </body>
        </html>
        '''
        self.assertTrue(isinstance(get_context(html, 'PAYLOAD')[0][0], HtmlText))

    def test_payload_double_script(self):
        html = '''
        <html>
            <script>foo</script>
                PAYLOAD
            <script>bar</script>
        </html>
        '''
        self.assertTrue(isinstance(get_context(html, 'PAYLOAD')[0][0], HtmlText))

    def test_payload_script_broken_double_open(self):
        html = '''
        <html>
            <script>foo
                PAYLOAD
            <script>bar</script>
        </html>
        '''
        self.assertTrue(isinstance(get_context(html, 'PAYLOAD')[0][0], ScriptText))

    def test_payload_script_broken_double_close(self):
        html = '''
        <html>
            <script>foo</script>
                PAYLOAD
            </script>
        </html>
        '''
        self.assertTrue(isinstance(get_context(html, 'PAYLOAD')[0][0], HtmlText))

    def test_payload_html_inside_comment(self):
        html = '''
        <html>
            <!-- <body>PAYLOAD</body> -->
        </html>
        '''
        self.assertTrue(isinstance(get_context(html, 'PAYLOAD')[0][0], HtmlComment))

    def test_payload_html_inside_script_with_comment(self):
        html = '''
        <html>
            <script>
                <!-- <body>PAYLOAD</body> -->
            </script>
        </html>
        '''
        self.assertTrue(isinstance(get_context(html, 'PAYLOAD')[0][0], ScriptText))

    def test_payload_script_single_quote(self):
        html = '''
        <html>
            <a foo='PAYLOAD'>
                bar
            </a>
        </html>
        '''
        self.assertTrue(isinstance(get_context(html, 'PAYLOAD')[0][0], HtmlAttrSingleQuote))

    def test_payload_script_single_quote(self):
        html = '''
        <html>
            <script foo='PAYLOAD'>
                bar
            </script>
        </html>
        '''
        self.assertTrue(isinstance(get_context(html, 'PAYLOAD')[0][0], HtmlAttrSingleQuote))

    def test_payload_script_single_quote2(self):
        html = '''
        <html>
<script type="text/javascript">//<!--
  init({login:'',foo:'PAYLOAD'})
            </script>
        </html>
        '''
        self.assertTrue(isinstance(get_context(html, 'PAYLOAD')[0][0], ScriptSingleQuote))

    def test_payload_text_can_break(self):
        html = '''
        <html>
            <a>PAYLOAD<</a>
        </html>
        '''
        context = get_context(html, 'PAYLOAD<')[0][0]
        self.assertTrue(context.can_break('PAYLOAD<'))

    def test_payload_src(self):
        html = '''
        <html>
            <img src="PAYLOAD" />
        </html>
        '''
        context = get_context(html, 'PAYLOAD')[0][0]
        self.assertTrue(context.is_executable())

    def test_payload_handler(self):
        html = '''
        <html>
            <a onclick="PAYLOAD">foo</a>
        </html>
        '''
        context = get_context(html, 'PAYLOAD')[0][0]
        self.assertTrue(context.is_executable())

    def test_payload_href(self):
        html = '''
        <html>
            <a href="PAYLOAD">foo</a>
        </html>
        '''
        context = get_context(html, 'PAYLOAD')[0][0]
        self.assertTrue(context.is_executable())

    def test_payload_script_attr_value(self):
        html = '''
        <html>
            <script foo=PAYLOAD foo2=aaa>
                bar
            </script>
        </html>
        '''
        self.assertTrue(isinstance(get_context(html, 'PAYLOAD')[0][0], HtmlAttr))

    def test_payload_js2doublequote(self):
        html = '''
        <html>
        <input type="button" value="ClickMe" onClick="PAYLOAD">
        </html>
        '''
        self.assertTrue(isinstance(get_context(html, 'PAYLOAD')[0][1], ScriptText))

