'''
clickJacking.py

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

import core.controllers.outputManager as om
from core.data.options.option import option
from core.data.options.optionList import optionList
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin


class clickJacking(baseGrepPlugin):
    '''
    Grep every page for X-Frame-Options header.

    @author: Taras (oxdef@oxdef.info)
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)

    def grep(self, request, response):
        '''
        Plugin entry point, identify which requests generated a 500 error.

        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None
        '''
        if not response.is_text_or_html():
            return
        # 
        # TODO need to check here for auth cookie!
        #
        headers = response.getHeaders()
        for header_name in headers:
            if header_name.lower() == 'x-frame-options'\
                    and headers[header_name].lower() in ('deny', 'sameorigin'):
                        return
        v = vuln.vuln()
        v.setPluginName(self.getName())
        v.setURL(response.getURL())
        v.setId(response.id)
        v.setSeverity(severity.MEDIUM)
        v.setName('Possible ClickJacking attack' )
        msg = 'URL: "' + v.getURL()+'"'
        msg += ' has no protection (X-Frame-Options header) against ClickJacking attack'
        v.setDesc(msg)
        kb.kb.append(self, 'clickJacking', v)

    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = optionList()
        return ol

    def setOptions(self , o):
        '''
        Do nothing, I don't have options.
        '''
        pass

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.

        The real job of this plugin is done here, where I will try to see if one
        of the clickJacking responses were not identified as a vuln by some of my audit plugins
        '''
        self.printUniq(kb.kb.getData( 'clickJacking', 'clickJacking' ), 'URL')

    def getPluginDeps(self):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []

    def getLongDesc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin greps every page for X-Frame-Options header and so
        for possible ClickJacking attack against URL.

        Additional information: https://www.owasp.org/index.php/Clickjacking
        '''
