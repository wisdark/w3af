'''
xss.py

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
from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
from core.controllers.w3afException import w3afException
from core.data.constants.browsers import (ALL, INTERNET_EXPLORER_6,
                                          INTERNET_EXPLORER_7, NETSCAPE_IE,
                                          FIREFOX, NETSCAPE_G, OPERA)
from core.data.fuzzer.fuzzer import createMutants, createRandAlNum
from core.data.options.option import option
from core.data.options.optionList import optionList
import core.controllers.outputManager as om
import core.data.constants.severity as severity
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
from core.data.context.context import get_context

class xss(baseAuditPlugin):
    '''
    Find cross site scripting vulnerabilities.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    @author: Taras ( oxdef@oxdef.info )
    '''
    
    def __init__(self):
        baseAuditPlugin.__init__(self)
        self._fuzzableRequests = []
        self._xssMutants = []
        # User configured parameters
        self._check_stored_xss = True
        self.payloads = [
                'RANDOMIZE</->',
                'RANDOMIZE/*',
                'RANDOMIZE"',
                "RANDOMIZE'"
                ]

    def audit(self, freq):
        '''
        Tests an URL for XSS vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug('XSS plugin is testing: ' + freq.getURL())
        # Save it here, so I can search for permanent XSS
        self._fuzzableRequests.append(freq)
        # This list is just to test if the parameter is echoed back
        fake_mutants = createMutants(freq, ['',])
        for mutant in fake_mutants:
            if self._check_stored_xss or self._is_echoed(mutant):
                self._search_xss(mutant)

    def _report_vuln(self, mutant, response, mod_value):
        v = vuln.vuln(mutant)
        v.setPluginName(self.getName())
        v.setId(response.id)
        v.setName('Cross site scripting vulnerability')
        v.setSeverity(severity.MEDIUM)
        msg = 'Cross Site Scripting was found at: ' + mutant.foundAt() 
        v.setDesc(msg)
        v.addToHighlight(mod_value)
        kb.kb.append(self, 'xss', v)

    def _search_simple_xss(self, mutant):
        payload = self._prepare_xss_test(''.join(self.payloads))
        oldValue = mutant.getModValue() 
        mutant.setModValue(payload)
        response = self._uri_opener.send_mutant(mutant)
        mod_value = mutant.getModValue()

        if payload in response.getBody():
            self._report_vuln(mutant, response, mod_value)
            return True
        # restore the mutant values
        mutant.setModValue(oldValue)
        return False

    def _search_xss(self, mutant):
        '''
        Analyze the mutant for reflected XSS. We get here because we
        already verified and the parameter is being echoed back.
        
        @parameter mutant: A mutant that was used to test if the parameter
            was echoed back or not
        '''
        # For the first search for simple XSS
        if self._search_simple_xss(mutant):
            return
 
        xss_strings = [self._prepare_xss_test(i) for i in self.payloads]
        mutant_list = createMutants(
                            mutant.getFuzzableReq(),
                            xss_strings,
                            fuzzableParamList=[mutant.getVar()]
                            )

        # In the mutant, we have to save which browsers are vulnerable
        # to that specific string
        for mutant in mutant_list:
            # Only spawn a thread if the mutant has a modified variable
            # that has no reported bugs in the kb
            if self._has_no_bug(mutant):
                args = (mutant,)
                kwds = {'callback': self._analyze_result }
                self._run_async(meth=self._uri_opener.send_mutant, args=args,
                                                                    kwds=kwds)
        self._join()

    def _analyze_result(self, mutant, response):
        '''
        Do we have a reflected XSS?
        
        @return: None, record all the results in the kb.
        '''
        # Add to the stored XSS checking
        self._addToPermanentXssChecking(mutant, response.id)
        with self._plugin_lock:
            mod_value = mutant.getModValue()
            
            if not self._has_no_bug(mutant):
                return

            for context, i in get_context(response.getBody(), mod_value):
                if not context.need_break(response.getBody()) or context.can_break(mod_value):
                    self._report_vuln(mutant, response, mod_value)
                    return
       
    def end(self):
        '''
        This method is called to check for permanent Xss. 
        Many times a xss isn't on the page we get after the GET/POST of
        the xss string. This method searches for the xss string on all
        the pages that are available.
        
        @return: None, vulns are saved to the kb.
        '''
        if self._check_stored_xss:
            for fuzzable_request in self._fuzzableRequests:
                response = self._uri_opener.send_mutant(fuzzable_request,
                                                         cache=False)
                for mutant, mutant_response_id in self._xssMutants:
                    # Remember that httpResponse objects have a faster "__in__" than
                    # the one in strings; so string in response.getBody() is slower than
                    # string in response                    
                    mod_value = mutant.getModValue()
                    for context, i in get_context(response.getBody(), mod_value):
                        if not context.need_break(response.getBody()) or context.can_break(mod_value):
                            v = vuln.vuln(mutant)
                            v.setPluginName(self.getName())
                            v.setURL(fuzzable_request.getURL())
                            v.setDc(fuzzable_request.getDc())
                            v.setMethod(fuzzable_request.getMethod())
                            
                            v['permanent'] = True
                            v['write_payload'] = mutant
                            v['read_payload'] = fuzzable_request
                            v.setName('Permanent cross site scripting vulnerability')
                            v.setSeverity(severity.HIGH)
                            msg = 'Permanent Cross Site Scripting was found at: ' + response.getURL()
                            msg += ' . Using method: ' + v.getMethod() + '. The XSS was sent to the'
                            msg += ' URL: ' + mutant.getURL() + '. ' + mutant.printModValue()
                            v.setDesc(msg)
                            v.setId([response.id, mutant_response_id])
                            v.addToHighlight(mutant.getModValue())

                            om.out.vulnerability(v.getDesc())
                            kb.kb.append(self, 'xss', v)
                            break
        
        self.printUniq(kb.kb.getData('xss', 'xss'), 'VAR')

    def _is_echoed(self, mutant):
        '''
        Verify if the parameter we are fuzzing is really being echoed
        back in the HTML response or not. If it isn't echoed there is
        no chance we are going to find a reflected XSS here.
        
        Also please note that I send a random alphanumeric value, and
        not a numeric value, because even if the number is echoed back
        (and only numbers are echoed back by the application) that won't
        be of any use in the XSS detection.
        
        @parameter mutant: The request to send.
        @return: True if variable is echoed
        '''
        # Create a random number and assign it to the mutant modified
        # parameter
        rndNum = str(createRandAlNum(5))
        oldValue = mutant.getModValue() 
        mutant.setModValue(rndNum)
        # send
        response = self._uri_opener.send_mutant(mutant)
        # restore the mutant values
        mutant.setModValue(oldValue)
        # Analyze and return response
        res = rndNum in response
        om.out.debug('The variable %s is %sbeing echoed back.' %
                     (mutant.getVar(), '' if res else 'NOT '))
        return res

    def _prepare_xss_test(self, data):
        return data.replace("RANDOMIZE", createRandAlNum(4))
    
    def _addToPermanentXssChecking(self, mutant, response_id):
        '''
        This is used to check for permanent xss.
        
        @parameter mutant: The mutant objects
        @parameter response_id: The response id generated from sending the mutant
        
        @return: No value is returned.
        '''
        self._xssMutants.append((mutant, response_id))
 
    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Identify stored cross site scripting vulnerabilities'
        h1 = 'If set to True, w3af will navigate all pages of the target one more time,'
        h1 += ' searching for stored cross site scripting vulnerabilities.'
        o1 = option('checkStored', self._check_stored_xss, d1, 'boolean', help=h1)
        ol = optionList()
        ol.add(o1)
        return ol
        
    def setOptions(self, optionsMap):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        '''
        self._check_stored_xss = optionsMap['checkStored'].getValue()
        
    def getPluginDeps(self):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return []

    def getLongDesc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds Cross Site Scripting (XSS) vulnerabilities.
        
        Two configurable parameters exist:
            - checkStored
            
        To find XSS bugs the plugin will send a set of javascript strings to every parameter, and search for that input in
        the response. The parameter "checkStored" configures the plugin to store all data sent to the web application 
        and at the end, request all pages again searching for that input
        '''
