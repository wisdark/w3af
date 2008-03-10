from core.ui.consoleUi.history import *

#TODO: extract a base class from this one and menu
class callbackMenu:
    
    def __init__(self, name, console, w3af, parent, callback, raw=True):
        self._name = name
        self._parent = parent
        self._callback = callback
        self._history = history()
        self._raw = raw

    def isRaw(self=None):
        #TODO: pull up
        return self._raw

    def getHistory(self):
        #TODO: pull up
        return self._history

    def execute(self, line):
        return self._callback(line)

    def getPath(self):
        #TODO: pull up
        p = self._parent and self._parent.getPath() + '/' or ''
        return p + self._name
