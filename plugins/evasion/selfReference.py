'''
selfReference.py

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

from core.controllers.basePlugin.baseEvasionPlugin import baseEvasionPlugin
from core.controllers.w3afException import w3afException
from core.data.url.HTTPRequest import HTTPRequest as HTTPRequest

# options
from core.data.options.option import option
from core.data.options.optionList import optionList



class selfReference(baseEvasionPlugin):
    '''
    Add a directory self reference.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self, uri_opener, threadpool):
        baseEvasionPlugin.__init__(self, uri_opener, threadpool)

    def modifyRequest(self, request ):
        '''
        Mangles the request
        
        @parameter request: HTTPRequest instance that is going to be modified by the evasion plugin
        @return: The modified request

        >>> from core.data.parsers.urlParser import url_object
        >>> import re
        >>> sr = selfReference()

        >>> u = url_object('http://www.w3af.com/')
        >>> r = HTTPRequest( u )
        >>> sr.modifyRequest( r ).url_object.url_string
        u'http://www.w3af.com/./'

        >>> u = url_object('http://www.w3af.com/abc/')
        >>> r = HTTPRequest( u )
        >>> sr.modifyRequest( r ).url_object.url_string
        u'http://www.w3af.com/./abc/./'

        >>> u = url_object('http://www.w3af.com/abc/def.htm?id=1')
        >>> r = HTTPRequest( u )
        >>> sr.modifyRequest( r ).url_object.url_string
        u'http://www.w3af.com/./abc/./def.htm?id=1'

        >>> #
        >>> #    The plugins should not modify the original request
        >>> #
        >>> u.url_string
        u'http://www.w3af.com/abc/def.htm?id=1'
        
        '''
        # We mangle the URL
        path = request.url_object.getPath()
        path = path.replace('/','/./' )
        
        # Finally, we set all the mutants to the request in order to return it
        new_url = request.url_object.copy()
        new_url.setPath( path )
        new_req = HTTPRequest( new_url , request.get_data(), 
                               request.headers, request.get_origin_req_host() )
        
        return new_req
    
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
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''        
        return []

    def getPriority( self ):
        '''
        This function is called when sorting evasion plugins.
        Each evasion plugin should implement this.
        
        @return: An integer specifying the priority. 0 is run first, 100 last.
        '''
        return 0

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This evasion plugin adds a directory self reference.
        
        Example:
            Input:      '/bar/foo.asp'
            Output :    '/bar/./foo.asp'
        '''
