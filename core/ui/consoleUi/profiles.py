'''
profiles.py

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

# Import w3af
import core.controllers.w3afCore
import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException
from core.ui.consoleUi.menu import *

class profilesMenu(menu):
    '''
    Menu to control the profiles.
    @author Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)

    '''
    def _cmd_use(self, params):
        if len(params) != 1:
            om.out.console('Parameter is missed, please see the help:')
            self._help_use()
        else:
            profile = params[0]
            try:
                self._w3af.useProfile(profile)
            except w3afException, e:
                om.out.error(str(e))
                return None
            else:
                om.out.console('The plugins configured by the scan profile have been enabled, and their options configured.')
                om.out.console('Please set the target URL(s) and start the scan.')
                    

    def _cmd_list(self, params):
        if len(params) != 0:
            om.out.console('No parameters expected')
        else:
            try:
                profileList = self._w3af.getProfileList()
            except w3afException, w3:
                om.out.error( str(w3) )
            else:
                for profileInstance in profileList:
                    om.out.console( profileInstance.getName() , profileInstance.getDesc() )

    def _para_use(self, params, part):
        profiles = [str(p.getName()) for p in self._w3af.getProfileList()]
        try:
            result = suggest (profiles, part)
        except Exception, e:
            om.out.console(str(e))
        return result

            
       

