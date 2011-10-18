'''
baseAuthPlugin.py

@author: Dmitriy V. Simonov ( dsimonov@yandex-team.com )

'''

from core.controllers.w3afException import w3afException
from core.controllers.basePlugin.basePlugin import basePlugin

class baseAuthPlugin(basePlugin):

    def __init__(self):
        basePlugin.__init__( self )
        self._testOption = False

    def login(self, uriOpener):
        '''
        Login user
        
        '''
        raise NotImplementedError('Plugin is not implementing required method login' )

    def logout(self, uriOpener):
        '''
        Logout user
        
        '''
        raise NotImplementedError('Plugin is not implementing required method logout' )
        
    def isLogged(self, uriOpener):
        '''
        User logged checking
        
        '''
        raise NotImplementedError('Plugin is not implementing required method isLogged' )

    def getType( self ):
        return 'auth'
