'''
config.py

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
from core.controllers.misc.parseOptions import parseXML
        
class configMenu(menu):
    '''
    Generic menu for configuring the configurable items.
    It is used to configure plugins and set url and misc settings.
    @author Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
    '''

    def __init__(self, name, console, w3af, parent, configurable):
        menu.__init__(self, 'config:' + name, console, w3af, parent)
        self._configurable = configurable
        self._options = parseXML(self._configurable.getOptionsXML())
        self._memory = {}
        for o in self._options.keys():
            self._memory[str(o)] = [str(self._options[o]['default'])]
       

    def _cmd_view(self, params):
        #col1Len = max([len(o) for o in self._options.keys()]) + 4
        #col2Len = 16
            table = [['Setting', 'Value', 'Description']]
            table += [[o, self._options[o]['default'], self._options[o]['desc']] \
                for o in self._options.keys()]           
            self._console.drawTable(table, True)

    def _cmd_set(self, params):
        if len(params) != 2:
            self._console.writeln('Error')
        elif not self._options.has_key(params[0]):
            self._console.writeln('Unknown option: ' + params[0])
        else:
            name = params[0]
            value = params[1]
            self._options[name]['default'] = value
            mem = self._memory[name]
            if value not in mem:
                mem.append(value)
            self._configurable.setOptions(self._options)
    

    def _para_set(self, params, part):
        if len(params) == 0:
            result = suggest(map(str, self._options.keys()), part)
            return result
        elif len(params) == 1:
            return suggest(self._memory[params[0]], part)
        else:
            return []

