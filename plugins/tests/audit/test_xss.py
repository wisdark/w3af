'''
test_xss.py

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

from ..helper import PluginTest, PluginConfig

class TestXSS(PluginTest):
    
    xss_url = 'http://moth/w3af/audit/xss/'
    wavsep_get_xss_url = 'http://localhost:8080/wavsep/active/RXSS-Detection-Evaluation-GET/'
    xss_302_url = 'http://moth/w3af/audit/xss/302/'
    
    _run_configs = {
        'cfg': {
            'target': None,
            'plugins': {
                'audit': (
                    PluginConfig(
                         'xss',
                         ('checkStored', True, PluginConfig.BOOL),
                         ),
                    ),
                'discovery': (
                    PluginConfig(
                        'webSpider',
                        ('onlyForward', True, PluginConfig.BOOL)),
                )
            },
        }
    }
 
    def test_found_wavsep_get_xss(self):
        cfg = self._run_configs['cfg']
        self._scan(self.wavsep_get_xss_url, cfg['plugins'])
        xssvulns = self.kb.getData('xss', 'xss')
        expected = [
            ('Case01-Tag2HtmlPageScope.jsp', 'userinput', ['userinput']),
            ('Case02-Tag2TagScope.jsp', 'userinput', ['userinput']),
            ('Case03-Tag2TagStructure.jsp', 'userinput', ['userinput']),
            ('Case04-Tag2HtmlComment.jsp', 'userinput', ['userinput']),
            ('Case05-Tag2Frameset.jsp', 'userinput', ['userinput']),
            ('Case06-Event2TagScope.jsp', 'userinput', ['userinput']),
            ('Case07-Event2DoubleQuotePropertyScope.jsp', 'userinput', ['userinput']),
            ('Case08-Event2SingleQuotePropertyScope.jsp', 'userinput', ['userinput']),
            ('Case09-SrcProperty2TagStructure.jsp', 'userinput', ['userinput']),
            ('Case10-Js2DoubleQuoteJsEventScope.jsp', 'userinput', ['userinput']),
            ('Case11-Js2SingleQuoteJsEventScope.jsp', 'userinput', ['userinput']),
            ('Case12-Js2JsEventScope.jsp', 'userinput', ['userinput']),
            ('Case13-Vbs2DoubleQuoteVbsEventScope.jsp', 'userinput', ['userinput']),
            ('Case14-Vbs2SingleQuoteVbsEventScope.jsp', 'userinput', ['userinput']),
            ('Case15-Vbs2VbsEventScope.jsp', 'userinput', ['userinput']),
            ('Case16-Js2ScriptSupportingProperty.jsp', 'userinput', ['userinput']),
            ('Case17-Js2PropertyJsScopeDoubleQuoteDelimiter.jsp', 'userinput', ['userinput']),
            ('Case18-Js2PropertyJsScopeSingleQuoteDelimiter.jsp', 'userinput', ['userinput']),
            ('Case19-Js2PropertyJsScope.jsp', 'userinput', ['userinput']),
            ('Case20-Vbs2PropertyVbsScopeDoubleQuoteDelimiter.jsp', 'userinput', ['userinput']),
            ('Case21-Vbs2PropertyVbsScope.jsp', 'userinput', ['userinput']),
            ('Case22-Js2ScriptTagDoubleQuoteDelimiter.jsp', 'userinput', ['userinput']),
            ('Case23-Js2ScriptTagSingleQuoteDelimiter.jsp', 'userinput', ['userinput']),
            ('Case24-Js2ScriptTag.jsp', 'userinput', ['userinput']),
            ('Case25-Vbs2ScriptTagDoubleQuoteDelimiter.jsp', 'userinput', ['userinput']),
            ('Case26-Vbs2ScriptTag.jsp', 'userinput', ['userinput']),
            ('Case27-Js2ScriptTagOLCommentScope.jsp', 'userinput', ['userinput']),
            ('Case28-Js2ScriptTagMLCommentScope.jsp', 'userinput', ['userinput']),
            ('Case29-Vbs2ScriptTagOLCommentScope.jsp', 'userinput', ['userinput']),
            ('Case30-Tag2HtmlPageScopeMultipleVulnerabilities.jsp', 'userinput', ['userinput']),
            ('Case31-Tag2HtmlPageScopeDuringException.jsp', 'userinput', ['userinput']),
            ('Case32-Tag2HtmlPageScopeValidViewstateRequired.jsp', 'userinput', ['userinput']),
        ]
        res = [(str(m.getURL()), m.getVar(), tuple(sorted(m.getDc().keys())))
                for m in (xv.getMutant() for xv in xssvulns)]
        self.assertEquals(
            set([(self.wavsep_get_xss_url + e[0], e[1],tuple(sorted(e[2]))) for e in expected]),
            set(res),
        )

    def test_found_xss(self):
        cfg = self._run_configs['cfg']
        self._scan(self.xss_url, cfg['plugins'])
        xssvulns = self.kb.getData('xss', 'xss')
        expected = [
            ('simple_xss_no_script_2.php', 'text', ['text']),
            ('dataReceptor.php', 'firstname', ['user', 'firstname']),
            ('simple_xss_no_script.php', 'text', ['text']),
            ('simple_xss_no_js.php', 'text', ['text']),
            ('simple_xss_no_quotes.php', 'text', ['text']),
            ('dataReceptor3.php', 'user', ['user', 'pass']),
            ('simple_xss.php', 'text', ['text']),
            ('no_tag_xss.php', 'text', ['text']),
            ('dataReceptor2.php', 'empresa', ['empresa', 'firstname']),
            ('stored/writer.php', 'a', ['a']),
            ('xss_clean.php', 'text', ['text',]),
            ('xss_clean_4_strict.php', 'text', ['text',])
            
        ]
        res = [(str(m.getURL()), m.getVar(), tuple(sorted(m.getDc().keys())))
                for m in (xv.getMutant() for xv in xssvulns)]
        self.assertEquals(
            set([(self.xss_url + e[0], e[1],tuple(sorted(e[2]))) for e in expected]),
            set(res),
        )
           

        
    def test_found_xss_with_redirect(self):
        cfg = self._run_configs['cfg']
        self._scan(self.xss_302_url, cfg['plugins'])
        xssvulns = self.kb.getData('xss', 'xss')
        expected = [
            ('302.php', 'x', ('x',)),
            ('302.php', 'a', ('a',)),
            ('printer.php', 'a', ('a', 'added',)),
            ('printer.php', 'added', ('a', 'added',)),
            ('printer.php', 'added', ('added',)),
            ('printer.php', 'x', ('x', 'added')),
            ('printer.php', 'added', ('x', 'added'))
        ]
        res = [(str(m.getURL()), m.getVar(), tuple(sorted(m.getDc().keys())))
                        for m in (xv.getMutant() for xv in xssvulns)]
        self.assertEquals(
            set([(self.xss_302_url + e[0], e[1], tuple(sorted(e[2]))) for e in expected]),
            set(res),
        )
