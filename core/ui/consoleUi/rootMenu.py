from core.ui.consoleUi.menu import *
from core.ui.consoleUi.plugins import *
from core.ui.consoleUi.profiles import *
import core.ui.consoleUi.posixterm as term
import core.controllers.miscSettings as ms
from core.ui.consoleUi.session import *

class rootMenu(menu):
    '''
        Main menu
    '''

    def __init__(self, name, console, core, parent=None):
        menu.__init__(self, name, console, core, parent)
        self._addHelp({
            'plugins': 'Enable, disable and configure plugins'
        })
        self._children =\
            {'plugins': pluginsMenu('plugins', self._console, self._w3af, self), \
             'target' : configMenu('target', self._console, self._w3af, self, self._w3af.target),
             'misc-settings' : configMenu('misc-settings', self._console, self._w3af, self, ms.miscSettings()),
             'url-settings' : configMenu('url-settings', self._console, self._w3af, self, self._w3af.uriOpener.settings),
             'profiles' : profilesMenu('profiles', self._console, self._w3af, self),
             'session' : sessionMenu('session', self._console, self._w3af, self)}

    def getChildren(self):
        return self._children

    def _cmd_start(self, params):
        try:
            self._w3af.initPlugins()
            self._w3af.start()
        except Exception, e:
            om.out.console(str(e))
 
