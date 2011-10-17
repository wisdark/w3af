'''
baseAuthPlugin.py

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

from core.controllers.w3afException import w3afException
from core.controllers.basePlugin.basePlugin import basePlugin
import core.controllers.outputManager as om

from core.data.parsers.urlParser import url_object
import core.data.request.httpPostDataRequest as httpPostDataRequest
import core.data.kb.knowledgeBase as kb

import copy


class baseAuthPlugin(basePlugin):

    def __init__(self):
        basePlugin.__init__( self )
        self._testOption = False

    def userLogin(self, *args, **kwargs ):
        '''
        Login user
        
        @author: Dmitriy V. Simonov ( dsimonov@gmail.com )
        '''
        raise NotImplementedError('Plugin is not implementing required method userLogin' )

    def userLogout(self, settings):
        '''
        Logout user
        
        @author: Dmitriy V. Simonov ( dsimonov@gmail.com )
        '''
        raise NotImplementedError('Plugin is not implementing required method userLogout' )
        
    def isUserLogged(self, *args, **kwargs ):
        '''
        User logged checkink
        
        @author: Dmitriy V. Simonov ( dsimonov@gmail.com )
        '''
        raise NotImplementedError('Plugin is not implementing required method isUserLogged' )

    def getType( self ):
        return 'auth'
