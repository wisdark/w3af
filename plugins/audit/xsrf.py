'''
xsrf.py

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
from math import log, floor

import core.controllers.outputManager as om
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
from core.controllers.w3afException import w3afException
from core.data.exchangableMethods import isExchangable
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity
from core.controllers.sql_tools.blind_sqli_response_diff import blind_sqli_response_diff
from core.data.fuzzer.fuzzer import createMutants

COMMON_CSRF_NAMES = [
        'csrf_token',
        'token'
        ]

class xsrf(baseAuditPlugin):
    '''
    Find the easiest to exploit xsrf vulnerabilities.
    @author: Taras oxdef@oxdef.info
    '''
    
    def __init__(self):
        baseAuditPlugin.__init__(self)
        self._strict_mode = False
        self._bsqli_response_diff = blind_sqli_response_diff()
        # User configured variables
        self._equalLimit = 0.9
        self._equAlgorithm = 'setIntersection'

    def audit(self, freq):
        '''
        Tests an URL for csrf vulnerabilities.

        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'XSRF plugin is testing: ' + freq.getURL() )
        if not self._is_suitable(freq):
            return
        # Referer/Origin check 
        if self._is_origin_checked(freq):
            om.out.debug('Origin for %s is checked' % freq.getURL())
            return
        # Does request has CSRF token in query string or POST payload?
        if self._contains_csrf_token(freq) and self._is_token_checked(freq):
            om.out.debug('Token for %s is exist and checked' % freq.getURL())
            return
        om.out.debug('%s is vulnerable for CSRF attack!!!' % freq.getURL())

    def _is_suitable(self, freq):
        # For CSRF attack we need request with payload 
        # and with persistant/session cookies
        auth_cookie = bool(len(kb.kb.getData('collectCookies', 'cookies')))
        if not auth_cookie:
            return False
        # Strict mode on/off - do we need to audit GET requests? Not always...
        if freq.getMethod() == 'GET' and not self._strict_mode:
            return False
        # Payload? 
        if (freq.getMethod() == 'GET' and freq.getURI().hasQueryString()) \
            or (freq.getMethod() =='POST' and len(freq.getDc())):
                om.out.debug('%s is suitable for CSRF attack' % freq.getURL())
                return True
        return False

    def _is_origin_checked(self, freq):
        result = False
        fake_ref = 'http://w3af.org/'
        response1 = self._sendMutant(freq, analyze=False)
        response2 = self._sendMutant(freq, analyze=False)
        
        bsqli_resp_diff = self._bsqli_response_diff
        bsqli_resp_diff.setUrlOpener(self._urlOpener)
        bsqli_resp_diff.setEqualLimit(self._equalLimit)
        bsqli_resp_diff.setEquAlgorithm(self._equAlgorithm)

        if (response1.getCode() != response2.getCode()) \
                or not bsqli_resp_diff.equal(response1.getBody(), response2.getBody()):
            return result
        # Ok 2 same requests have 2 same responses
        # let's play with headers
        tmp_ref = freq.getReferer()
        freq.setReferer(fake_ref)
        response_with_fake_ref = self._sendMutant(freq, analyze=False)

        if (response1.getCode() != response_with_fake_ref.getCode()) \
                or not bsqli_resp_diff.equal(response1.getBody(), response_with_fake_ref.getBody()):
            return True

        om.out.debug('Testing for Referer/Origin %s' % freq.getURL())

    def _contains_csrf_token(self, freq):
        om.out.debug('Testing for token in %s' % freq.getURL())
        return True

    def _is_token_checked(self, freq):
        om.out.debug('Testing for checks of token in %s' % freq.getURL())
        return True

    def is_csrf_token(self, key, value):
        # 
        # Entropy based algoritm
        # http://en.wikipedia.org/wiki/Password_strength
        #
        min_length = 4
        min_entropy = 36
        # Check for common CSRF token names
        if key in COMMON_CSRF_NAMES and value:
            return True
        # Check length
        if len(value) < min_length:
            return False
        # Calculate entropy
        total = 0
        total_digit = False
        total_lower = False
        total_upper = False
        total_spaces = False

        for i in value:
            if i.isdigit():
                total_digit = True
                continue
            if i.islower():
                total_lower = True
                continue
            if i.isupper():
                total_upper = True
                continue
            if i == ' ':
                total_spaces = True
                continue
        total = int(total_digit) * 10 + int(total_upper) * 26 + int(total_lower) * 26
        entropy = floor(log(total)*(len(value)/log(2)))
        if entropy >= min_entropy:
            if not total_spaces and total_digit:
                return True
        return False

    def end( self ):
        '''
        This method is called at the end, when w3afCore aint going to use this plugin anymore.
        '''
        pass

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def setOptions( self, OptionList ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return ['grep.collectCookies']

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds Cross Site Request Forgeries (xsrf) vulnerabilities.
        
        The simplest type of xsrf is checked, to be vulnerable, the web application must have sent a permanent
        cookie, and the aplicacion must have query string parameters.
        '''
