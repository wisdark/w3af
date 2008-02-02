from core.ui.consoleUi.menu import *

class sessionMenu(menu):
    
    def _cmd_save(self, params):    
        if len(params) != 1:
            om.out.console("Missing parameters")
            self._help_save()
        else:
            try:
                self._w3af.saveSession(params[0])
            except Exception, e:
                om.out.console(str(e))

    
    def _cmd_resume(self, params):
        if len(params) != 1:
            om.out.console("Missing parameters")
            self._help_resume()
        else:
            try:
                self._w3af.resumeSession(params[0])
            except Exception, e:
                om.out.console(str(e))



    def _help_save(self):
        om.out.console("Usage: save <session_name>")

    def _help_resume(self):
        om.out.console("Usage: resume <session_name>")
            

       
