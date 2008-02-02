# Import w3af
import core.controllers.w3afCore
import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException
from core.ui.consoleUi.menu import *

class profilesMenu(menu):
        
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

            
       

