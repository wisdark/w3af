'''
symfony.py

Copyright 2011 Andres Riancho and Carlos Pantelides

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

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

from core.data.bloomfilter.bloomfilter import scalable_bloomfilter

import re


class symfony(baseGrepPlugin):
    '''
    Grep every page for traces of the Symfony framework.
      
    @author: Carlos Pantelides (carlos.pantelides@yahoo.com ) based upon 
    work by Andres Riancho ( andres.riancho@gmail.com ) and help from
    Pablo Mouzo (pablomouzo@gmail.com)
    '''
    
    def __init__(self, uri_opener, threadpool):
        baseGrepPlugin.__init__(self, uri_opener, threadpool)
        
        # Internal variables
        self._already_inspected = scalable_bloomfilter()
        self._override = False
        
    def grep(self, request, response):
        '''
        Plugin entry point.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None, all results are saved in the kb.
        
        Init
        >>> from functools import partial
        >>> from core.data.url.httpResponse import httpResponse
        >>> from core.data.request.fuzzableRequest import fuzzableRequest
        >>> from core.controllers.misc.temp_dir import create_temp_dir
        >>> from core.data.parsers.urlParser import url_object
        >>> o = create_temp_dir()
        >>> emptyBody=''
        >>> unprotectedBody='<html><head></head><body><form action="login" method="post"><input type="text" name="signin" id="signin" /></form></body></html>'
        >>> protectedBody='<html><head></head><body><form action="login" method="post"><input type="text" name="signin" id="signin" /><input type="hidden" name="signin[_csrf_token]" value="069092edf6b67d5c25fd07642a54f6e3" id="signin__csrf_token" /></form></body></html>'
        >>> symfonyHeaders={'set-cookie': 'symfony=sfasfasfa', 'content-type': 'text/html'}
        >>> noSymfonyHeaders={'content-type': 'text/html'}
        >>> url = url_object('http://www.w3af.com/')
        >>> http_resp = partial(httpResponse, code=200, geturl=url, original_url=url)

        Symfony detection, positive
        >>> response = http_resp(read=emptyBody, info=symfonyHeaders)
        >>> a = symfony()
        >>> a.symfonyDetected(response)
        True
   
        Symfony detection, negative
        >>> response = http_resp(read=emptyBody, info=noSymfonyHeaders)
        >>> a = symfony()
        >>> a.symfonyDetected(response)
        False

        Symfony detection, override
        >>> a._override = True
        >>> a.symfonyDetected(response)
        True

        CSRF detection, positive
        >>> response = http_resp(read=protectedBody, info=symfonyHeaders)
        >>> a.csrfDetected(response.getDOM())
        True

        CSRF detection, negative
        >>> response = http_resp(read=unprotectedBody, info=symfonyHeaders)
        >>> a.csrfDetected(response.getDOM())
        False
        
        Symfony plus CSRF detection, positive plus negative
        >>> kb.kb.save('symfony','symfony',[])
        >>> response = http_resp(read=protectedBody, info=symfonyHeaders)
        >>> request = fuzzableRequest(url, method='GET')
        >>> a.grep(request, response)
        >>> len(kb.kb.getData('symfony', 'symfony'))
        0

        Symfony plus CSRF detection, positive plus positive
        >>> response = http_resp(read=unprotectedBody, info=symfonyHeaders)
        >>> a = symfony()
        >>> a.grep(request, response)
        >>> len(kb.kb.getData('symfony', 'symfony'))
        1
        '''
        url = response.getURL()
        if response.is_text_or_html() and url not in self._already_inspected:
            
            # Don't repeat URLs
            self._already_inspected.add(url)

            if self.symfonyDetected(response):
                dom = response.getDOM()
                if dom and not self.csrfDetected(dom):
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setName('Symfony Framework')
                    i.setURL(url)
                    i.setDesc('The URL: "%s" seems to be generated by the '
                      'Symfony framework and contains a form that perhaps '
                      'has CSRF protection disabled.' % url)
                    i.setId(response.id)
                    kb.kb.append(self, 'symfony', i)

    def symfonyDetected(self, response):
        if self._override:
            return True
        for header_name in response.getHeaders().keys():
            if header_name.lower() == 'set-cookie' or header_name.lower() == 'cookie':
                if re.match('^symfony=', response.getHeaders()[header_name]):
                    return True
        return False      
    
    def csrfDetected(self, dom):
        forms = dom.xpath('//form')
        if forms:
            csrf_protection_regex_string = '.*csrf_token'
            csrf_protection_regex_re = re.compile( csrf_protection_regex_string, re.IGNORECASE )
            for form in forms:
                inputs = form.xpath('//input[@id]')
                if inputs:
                    for input in inputs:
                        if csrf_protection_regex_re.search(input.attrib["id"]):
                            return True
        return False

    def setOptions( self, optionsMap ):
        self._override = optionsMap['override'].getValue()
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Skip symfony detection and search for the csrf (mis)protection.'
        o1 = option('override', self._override, d1, 'boolean')
        
        ol = optionList()
        ol.add(o1)
        return ol
        
        
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.printUniq( kb.kb.getData( 'symfony', 'symfony' ), 'URL' )

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return []
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin greps every page for traces of the Symfony framework and the lack of csrf protection.
        '''
