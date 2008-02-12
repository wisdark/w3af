'''
consoleUi.py

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


from shlex import *
import os.path
import traceback
from core.ui.consoleUi.rootMenu import *
from core.ui.consoleUi.util import *
import core.ui.consoleUi.posixterm as term
from core.ui.consoleUi.history import *
import core.ui.consoleUi.tables as tables
import core.controllers.w3afCore
import core.controllers.outputManager as om
import core.controllers.miscSettings as miscSettings
import sys
import random

class consoleUi:
    '''
    This class represents the console. 
    It handles the keys pressed and delegate the completion and execution tasks 
    to the current menu.
    @author Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
    '''

    def __init__(self, scriptFile=None, commands=[]):
        self._scriptFile = scriptFile
        self._commands = commands 
        self._term = term.terminal()
        self._line = [] # the line which is being typed
        self._position = 0 # cursor position
        self._w3af = core.controllers.w3afCore.w3afCore()
        self._context = rootMenu('', self, self._w3af ) # initial menu
        self._handlers = { '\t' : self._onTab, \
            '\r' : self._onEnter, \
            term.KEY_BACKSPACE : self._onBackspace, \
            term.KEY_LEFT : self._onLeft, \
            term.KEY_RIGHT : self._onRight, \
            term.KEY_UP : self._onUp, \
            term.KEY_DOWN : self._onDown, \
            '^C' : self.exit, \
            '^D' : self.exit,
            '^W' : self._delWord,
            '^H' : self._onBackspace,
            '^A' : self._toLineStart,
            '^E' : self._toLineEnd } 
        self._history = historyTable() # each menu has array of (array, positionInArray)
        self._trace = []

    
    def sh(self):
        '''
        Main cycle
        '''
        self._lastWasArrow = False
        self._showPrompt()
        self._active = True
        term.setRawInputMode(True)

        self._executePending()

        while self._active: 
            try:
                c = self._term.getch()
                self._handleKey(c)
            except Exception, e:
                om.out.console(str(e))

        term.setRawInputMode(False)
        print '\n'
        print self._randomMessage()


    def _executePending(self):
        while (self._commands):
            curCmd, self._commands = self._commands[0], self._commands[1:]

            self._paste(curCmd)
            self._onEnter()

    def write(self, s):
        om.out.console(s)
    
    def writeln(self, s=''):
        om.out.console(s+'\n')

    def term_width(self):
        return 80

           
    def drawTable(self, lines, header=False):
        table = tables.table(lines)
        table.draw(self.term_width(), header)
        
        
    def back(self):
        if len(self._trace) == 0:
            return None
        else:
            return self._trace.pop()


    def _initPrompt(self):
        self._position = 0
        self._line = []
        self._showPrompt()


    def exit(self):
        self._active = False

    def _getHistory(self):
        return self._context.getHistory()

    def _setHistory(self, hist):
        path = self._context.getPath()
        self._history[path] = (hist, [])
    
    def _handleKey(self, key):
        try:
            if self._handlers.has_key(key):
                self._handlers[key]()
            else:
                self._paste(key)
        except Exception, e:
            traceback.print_exc() # TODO
        
    def _onBackspace(self):
        if self._position >0:
            self._position -= 1
            del self._line[self._position]
            term.moveDelta(-1,0)
            term.eraseLine()
            self._showTail()

    def _onEnter(self):

       # term.writeln()

        tokens = self._parseLine()
        if len(tokens) > 0:

            self._getHistory().remember(self._line)
    
            # New menu is the result of any command.
            # If None, the menu is not changed.
            term.setRawInputMode(False)
            om.out.console('')
            menu = self._context.execute(tokens)
            term.setRawInputMode(True)
            if menu is not None:
                if callable(menu):
                    
                    # Command is able to delegate the detection 
                    # of the new menu to the console 
                    # (that's useful for back command:
                    # otherwise it's not clear what must be added to the trace)
                    # It's kind of hack, but I had no time 
                    # to think of anything better.
                    # An other option is to allow menu 
                    # objects modify console state directly which I don't like
                    # -- Sasha
                    menu = menu() 
                    
                elif menu != self._context:
                    # Remember this for the back command
                    self._trace.append(self._context)
                if menu is not None:
                    self._context = menu

        self._initPrompt()


    def _delWord(self):
        trimming = True
        filt = None
        while (True):
            if self._position == 0:
                break

            char = self._line[self._position-1]
            if filt is None:
                for f in [str.isspace, str.isalnum, lambda s: not s.isalnum()]:
                    if f(char):
                        filt = f
                        break

            if filt(char):
                self._onBackspace()
            else:
                break

    def _toLineEnd(self):
        term.moveDelta(len(self._line) - self._position, 0)
        self._position = len(self._line)

    def _toLineStart(self):
        term.moveDelta(-self._position, 0)
        self._position = 0

    def _onTab(self):
        '''
            Autocompletion logic is called here
        '''
        line = self._getLineStr()[:self._position] # take the line before the cursor
        tokens = self._parseLine(line)
        if not line.endswith(' ') and len(tokens)>0:
            # if the cursor is after non-space, the last word is used 
            # as a hint for autocompletion
            incomplete = tokens.pop()
        else:
            incomplete = ''

        completions = self._context.suggest(tokens, incomplete)
        prefix = commonPrefix(completions)
        if prefix != '':
            self._paste(prefix)
        elif len(completions) > 0:
            term.writeln()
            for variant in map(lambda c: c[1], completions):
                term.write(variant + ' ')
            term.writeln()
            
            self._showPrompt()

            self._showLine()
        else:
            term.bell()
    
    def _onLeft(self):
        if self._position > 0:
            self._position -= 1
            term.moveDelta(-1,0)
        else:
            term.bell()
    
    def _onRight(self):
        if self._position < len(self._line):
            self._position += 1
            term.moveDelta(1,0)
        else:
            term.bell()

    def _onUp(self):
        history = self._getHistory()
        newLine = history.back(self._line)

        if newLine is not None:
            self._setLine(newLine)
        else:
            term.bell()

    def _onDown(self):
        history = self._getHistory()
        newLine = history.forward()
        if newLine is not None:
            self._setLine(newLine)
        else:
            term.bell()

    def _setLine(self, line):
        term.moveDelta(- self._position, 0)
        term.eraseLine()
        term.write(''.join(line))
        self._line = line
        self._position = len(line)

    def _getLineStr(self):
        return ''.join(self._line)

    def _parseLine(self, line=None):
        if line==None:
            line = self._getLineStr()
        result = []
        parser = shlex(line)
        parser.whitespace_split = True
        while True:
            token = parser.get_token()
            if token == parser.eof:
                break
            result.append(token)

        return result

    def _paste(self, text):

        term.savePosition()
        tail = self._line[self._position:]
        for c in text:
            self._line.insert(self._position, c)
            self._position += 1

        term.write(text)
        term.write(''.join(tail))
        term.restorePosition()  
        term.moveDelta(len(text), 0)
        


    def _showPrompt(self):
        term.write('w3af' + self._context.getPath() + ">>>")
        
    def _showLine(self):
        strLine = self._getLineStr()
        term.write(strLine)
        term.moveDelta(self._position - len(strLine), 0)

    def _showTail(self, afterDel=False):
        '''
            reprint everything that should be after the cursor
        '''
        term.savePosition()
        strLine = self._getLineStr()
        term.write(strLine[self._position:])
        term.restorePosition()


    def _randomMessage(self):
        f = file('core/ui/consoleUi/exitMessages.txt', 'r')
        lines = f.readlines()
        idx = random.randrange(len(lines))
        line = lines[idx]
        return line
        
        

