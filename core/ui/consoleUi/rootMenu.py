'''
rootMenu.py

Copyright 2008 Andres Riancho

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

from core.ui.consoleUi.menu import *
from core.ui.consoleUi.plugins import *
from core.ui.consoleUi.profiles import *
import core.ui.consoleUi.posixterm as term
import core.controllers.miscSettings as ms
from core.ui.consoleUi.session import *


class rootMenu(menu):
    '''
    Main menu
    @author Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
    '''

    def __init__(self, name, console, core, parent=None):
        menu.__init__(self, name, console, core, parent)
#        self._addHelp({
#            'plugins': 'Enable, disable and configure plugins'
#        })
        self._help.addHelpEntry('plugins', 'Enable, disable and configure plugins', 'commands')
        self._help.addHelp({'start': 'Run the scan'}, 'commands')

        self._children =\
            {'plugins': pluginsMenu('plugins', self._console, self._w3af, self), \
             'target' : configMenu('target', self._console, self._w3af, self, self._w3af.target),
             'misc-settings' : configMenu('misc-settings', self._console, self._w3af, self, \
                 ms.miscSettings(), True),
             'url-settings' : configMenu('url-settings', self._console, self._w3af, self, self._w3af.uriOpener.settings, True),
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
 
