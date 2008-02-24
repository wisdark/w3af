'''
menu.py

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

import traceback
        
import core.data.kb.knowledgeBase as kb        
from core.ui.consoleUi.util import *
from core.ui.consoleUi.history import *
from core.ui.consoleUi.help import *
import core.controllers.outputManager as om

class menu:
    '''
    Menu objects handle the commands and completion requests.
    Menus form an hierarchy and are able to delegate requests to their children.
    @author Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
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
        self._history = history()
        
        self._help = help()
        self._keysHelp = help()
        self._w3af = w3af
        self._handlers = {}
        self._paramHandlers = {}
        self._helpHandlers = {}
        self._parent = parent
        self._console = console
        
        commonHelp = {
            'keys' : 'Keys combinations',
            'help': 'Display help', 
            'back': 'Go to the parent menu',
            'assert': 'Check an assertion',
            'exit': 'Exit w3af'
        }

        for cmd in [c for c in dir(self) if c.startswith('_cmd_')]:
            self._handlers[cmd[5:]] =  getattr(self, cmd)

        for cmd in self.getCommands():
            try:
                pHandler = getattr(self, '_para_'+cmd)
                self._paramHandlers[cmd] = pHandler
            except:
                pass

            if cmd not in commonHelp:
                self._help.addHelpEntry(cmd, 'UNDOCUMENTED', 'commands')

            try:
                helpHandler = getattr(self, '_help_'+cmd)
                self._helpHandlers[cmd] = helpHandler
            except:
                pass


        self._help.addHelp(commonHelp, 'common')



        self._keysHelp.addHelp({
            'Ctrl-D': 'Go to the previous menu or exit w3af',
            'Ctrl-W': 'Erase the last word',
            'Ctrl-H': 'Erase the last character',
            'Ctrl-A': 'To the beginning of the line',
            'Ctrl-E': 'To the end of the line'
        }, 'keys')

    def getBriefHelp(self):
        return self._helpTable


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
            compl = self._paramHandlers[command]
            return compl(params, part)
        except Exception, e:    
            return self.suggestParams(command+'/', params, part)


    def getCommands(self):
        '''
        By default, commands are defined by methods _cmd_<command>.
        '''
        return self._handlers.keys()

    def getChildren(self):
        return {} #self.getCommands()

    def getHandler(self, command):
        try:
            return self._handlers[command]
        except:
            return None
            
    def getHelper(self, command):
        try:
            return self._helpHandlers[command]
        except:
            return None

    def execute(self, tokens):

        if len(tokens) == 0:
            return self

#:      context.addToHistory(append)
        command, params = tokens[0], tokens[1:]
        
        first, other = splitPath(command)

        if other is not None:
            children = self.getChildren()
            if first in children:
                subMenu = self.getChildren()[first]
                subCmd = (other and [other] or [])  + params
                result = subMenu.execute( subCmd )
                return result
            else:
                om.out.console("I don't know what to do with %s" % first)
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

    def _cmd_exit(self, tokens):
        return self._console.exit


    def _cmd_help(self, params, brief=False):
        if len(params) == 0:
            table = self._help.getPlainHelpTable(True)
            self._console.drawTable(table)
        else:
            subj = params[0]
            fun = self.getHelper(subj)
            if fun:
                fun()
            else:
                help = self._help.getHelp(subj)
                if help is None:
                    om.out.console("I don't know anything about " + subj)
                else:
                    om.out.console(help)
                    

    def _help_keys(self, params=None):
        table = self._keysHelp.getPlainHelpTable(True)
        self._console.drawTable(table)
        

    def _cmd_assert(self, params):
        exec ('assert ' + ' '.join(params))
        return None


    def _cmd_keys(self, params):
        self._help_keys()
    
    def _getHelpForSubj(self, subj):
        table = self.getBriefHelp()
        if table.has_key(subj):
            return help[subj]
        else:
            return None

           
    def _para_help(self, params, part):
        if len(params) ==0:
            return suggest(self._help.getItems(), part)
        else:
            return []

           
