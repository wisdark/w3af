import copy
from core.ui.consoleUi.menu import *
from core.ui.consoleUi.config import *
from core.controllers.misc.parseOptions import parseXML
import core.controllers.outputManager as om

class pluginsMenu(menu):
    '''
        List of plugins.
    '''

    def __init__(self, name, console, w3af, parent):
        menu.__init__(self, name, console, w3af, parent)
        types = w3af.getPluginTypes()
        children = {}
        for t in types:
            children[t] = pluginsTypeMenu(t, self._console, self._w3af, self)
        self._children = children
    
    def getChildren(self):
        return self._children

    def _cmd_list(self, params):
        try:
            type = params[0]
            subMenu = self._children[type]
        except:
            self._cmd_help(['list'])
        else:
            subMenu._cmd_list(params[1:])

        return None

    def _help_list(self):
        return 'Usage: list pluginType ' + \
                'where pluginType is one of ' + ', '.join(self._children.keys())

    
    def _para_list(self, params, part):
        return suggest(self._children.keys(), part)

        
class pluginsTypeMenu(menu):
    '''
        Common menu for all types of plugins. 
        The type of plugins is defined by the menu's own name.
    '''
    def __init__(self, name, console, w3af, parent):
        menu.__init__(self, name, console, w3af, parent)
        plugins = w3af.getPluginList(name)
        self._plugins = {} # name to number of options
        for p in plugins:
            options = parseXML(self._w3af.getPluginInstance(p, self._name).getOptionsXML())
            self._plugins[p] = len(options)
        self._configs = {}
      

    def suggestCommands(self, part):
        return suggest(self._plugins.keys() + ['all'], part, True) + \
            suggest(self.getCommands(), part)

    def suggestParams(self, command, params, part):
        if command in self.getCommands():
            return menu.suggestParams(self, command, params, part)
        
        return suggest(self._plugins.keys() + ['all'], ','.join(params + [part]), True)

    def execute(self, tokens):
        if len(tokens)>0:
            command, params = tokens[0], tokens[1:]
            #print "command: " + command + "; " + str(self.getCommands())
            if command in self.getCommands():
                return menu.execute(self, tokens)
            else:
                self.enablePlugins(','.join(tokens).split(','))
        else:
            return self

    def enablePlugins(self, list):
        enabled = copy.copy(self._w3af.getPlugins(self._name))
        
        for plugin in list:
            if plugin.startswith('!'):
                p = plugin[1:]
                if p == 'all':
                    enabled = []
                elif p in enabled:
                    enabled.remove(p)
            elif plugin == 'all':
                enabled = self._plugins.keys()
            elif plugin in self._plugins.keys() and plugin not in enabled:
                enabled.append(plugin)

        self._w3af.setPlugins(enabled, self._name)
        
    def _cmd_list(self, params):
        #print 'list : ' + str(params)
        filter = len(params)>0 and params[0] or 'all'

        all = self._plugins.keys()
        enabled = self._w3af.getPlugins(self._name)

        if filter == 'all':
            list = all
        elif filter == 'enabled':
            list = enabled
        elif filter == 'disabled':
            list = [p for p in all if p not in enabled]
        else:
            list = []
                        
        list.sort()
        table = [['Plugin name', 'Status', 'Description']]

        for pluginName in list:
            row = []
            plugin = self._w3af.getPluginInstance(pluginName, self._name)
#            try:
#                optionsXML = plugin.getOptionsXML()
#                options = parseXML(optionsXML)
#            except:
#                options = {}
    
            optCount = self._plugins[pluginName]
            row.append(pluginName)
            status = pluginName in enabled and 'Enabled' or ''
            row.append(status)
            optInfo = optCount>0 and '\n(%i options)' % optCount or ''
            row.append(str(plugin.getDesc()) + optInfo)

            table.append(row)
        self._console.drawTable(table, True)

    def _help_list(self):
        om.out.console( "Usage: list [all | enabled | disabled] ; default is all")
        
    def _cmd_config(self, params):
        
        if len(params) ==0:
            self._help_config()
            return

        name = params[0]
        if self._configs.has_key(name):
            config = self._configs[name]
        else:
            config = configMenu(name, self._console, self._w3af, self, self._w3af.getPluginInstance(params[0], self._name))
            self._configs[name] = config

        return config

    def _para_config(self, params, part):
        if len(params) > 0:
            return []

        return suggest([p for p in self._plugins.keys() \
            if self._plugins[p] > 0], part)
                
    def _help_config(self):
        om.out.console("Usage: command <plugin> ");

    def _para_list(self, params, part=''):
        if len(params)==0:
            return suggest(['enabled', 'all', 'disabled'], part)
        return []


