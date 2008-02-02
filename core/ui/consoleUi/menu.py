import traceback
from core.ui.consoleUi.util import *
from core.ui.consoleUi.history import *

class menu:
    '''
    Menu objects handle the commands and completion requests.
    Menus form an hierarchy and are able to delegate requests to their children.
    '''

    def suggest(self, tokens, part):
        '''
        Suggest the possible completions
        @parameter tokens: list of string
        @parameter part: base for completion
        '''
        if len(tokens)==0:
            return self.suggestCommands(part)
        return self.suggestParams(tokens[0], tokens[1:], part)


    def getPath(self):
        if self._parent is None:
            return self._name
        else:
            return self._parent.getPath() + '/' + self._name

    def getHistory(self):
        return self._history

    def __init__(self, name, console, w3af, parent=None, **other):
        self._name = name
        self._w3af = w3af
        self._parent = parent
        self._console = console
        self._prevContext = None
        self._history = history()
        self._helpTable = {
            'help': 'Display help', 
            'back': 'Go to the parent menu'
        }


    def getBriefHelp(self):
        return self._helpTable

    def _addHelp(self, ext):
        self._helpTable.update(ext)

    def suggestCommands(self, part=''):

        first, rest = splitPath(part)

        if rest is None:
            # the command must be in the current menu
            result = suggest(self.getCommands(), part)
            if self.getChildren() is not None:
                result +=   suggest(self.getChildren(), part)
            return result
        else:
            try:
                # delegate to the children
                subMenu = self.getChildren()[first]
                return subMenu.suggestCommands(rest)
            except:
                return []

    def suggestParams(self, command, params, part):
        first, rest = splitPath(command)    
        if rest is not None:
            try:
                # delegate
                ctx = self.getChildren()[first]
                if rest != '':
                    params = [rest] + params
                return ctx.suggest(params, part)
            except:
                return []

        try:
            compl = getattr(self, '_para_'+command)
            return compl(params, part)
        except Exception, e:    
            return self.suggestParams(command+'/', params, part)


    def getCommands(self):
        '''
        By default, commands are defined by methods _cmd_<command>.
        '''
        return map(lambda s: s[5:], [c for c in dir(self) if c.startswith('_cmd_')])

    def getChildren(self):
        return {} #self.getCommands()

    def getHandler(self, command):
        try:
            return getattr(self, '_cmd_'+command)
        except:
            return None
            

    def execute(self, tokens):
        self._prevContext = self._console._context   

        if len(tokens) == 0:
            return self

#:      context.addToHistory(append)
        command, params = tokens[0], tokens[1:]
        
        first, other = splitPath(command)

        if other is not None:
            try:
                subMenu = self.getChildren()[first]
                subCmd = (other and [other] or [])  + params
                result = subMenu.execute( subCmd )
                return result
            except Exception, e:
                traceback.print_exc()
                return None

        handler = self.getHandler(command)
        if handler is not None:
            try:
                return handler(params)
            except Exception, e:
                traceback.print_exc()
        else:
            return self.execute([command + '/'] + params)


    def _cmd_back(self, tokens):
        return self._console.back


    def _cmd_help(self, params, brief=False):
        if len(params) == 0:
            self._help()
        else:
            subj = params[0]
            try:
                fun = getattr(self, '_help_'+subj)
            except:
                help = self.getBriefHelp()
                if help.has_key(subj):
                    self._console.writeln(help[subj])
                else:
                    self._console.writeln('Nothing is known about ' + subj)

            else:
                fun()


    def _getHelpItems(self):
        list = self.getBriefHelp().keys()
        methods = [m for m in dir(self) if m.startswith('_help_')]
        for f in map(lambda s: s[6:], methods):
            if f not in list:
                list.append(f)

        list.extend([c for c in self.getCommands() if c not in list])

        return list

    def _getHelpForSubj(self, subj):
        table = self.getBriefHelp()
        if table.has_key(subj):
            return help[subj]
        else:
            return None

    def _help(self):
        helpTable = self.getBriefHelp()
        helpItems = self._getHelpItems()
        #firstFieldLen = max([len(s) for s in helpItems]) + 2
        helpLines = []

        for subj in helpItems:
            help = helpTable.has_key(subj) and helpTable[subj] or ''
            helpLines.append([subj, help])

        self._console.drawTable(helpLines)
       
            
    def _para_help(self, params, part):
        if len(params) ==0:
            return suggest(self._getHelpItems(), part)
        else:
            return []

           
