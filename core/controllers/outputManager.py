'''
outputManager.py

Copyright 2006 Andres Riancho

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

import os

import core.data.constants.severity as severity

from core.controllers.misc.factory import factory
from core.data.constants.encodings import UTF8


class OutputManager(object):
    '''
    This class manages output, it has a list of output plugins and sends the
    events to every plugin on that list.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self, threadpool):
        self._output_plugin_list = []
        self._output_plugins = []
        self._plugins_options = {}
        self._echo = True
        self._threadpool = threadpool
    
    def endOutputPlugins(self):
        for oPlugin in self._output_plugin_list:
            oPlugin.end()

        # This is a neat trick which basically removes all plugin references
        # from memory. Those plugins might have pointers to memory parts that
        # are not required anymore (since someone is calling endOutputPlugins
        # which indicates that the scan is done).
        #
        # If the console or gtkOutput plugins were enabled, I re-enable them
        # since I don't want to loose the capability of seeing my log messages
        # in the linux console or the message box in the GTK ui.
        currently_enabled_plugins = self.getOutputPlugins()
        keep_enabled = [pname for pname in currently_enabled_plugins 
                        if pname in ('console', 'gtkOutput')]
        self.setOutputPlugins( keep_enabled )
            
            
    def logEnabledPlugins(self, enabledPluginsDict, pluginOptionsDict):
        '''
        This method logs to the output plugins the enabled plugins and their configuration.
        
        @parameter enabledPluginsDict: As returned by w3afCore.getAllEnabledPlugins()
                   looks similar to:
                   {'audit':[],'grep':[],'bruteforce':[],'discovery':[],...}
        
        @parameter pluginOptionsDict: As defined in the w3afCore, looks similar to: 
                   {'audit':{},'grep':{},'bruteforce':{},'discovery':{},...}
        '''
        for oPlugin in self._output_plugin_list:
            oPlugin.logEnabledPlugins(enabledPluginsDict, pluginOptionsDict)
    
    def debug(self, message, newLine=True):
        '''
        Sends a debug message to every output plugin on the list.
        
        @parameter message: Message that is sent.
        '''
        self._call_output_plugins_action('debug', message, newLine)
    
    def information(self, message, newLine=True):
        '''
        Sends a informational message to every output plugin on the list.
        
        @parameter message: Message that is sent.
        '''
        self._call_output_plugins_action('information', message, newLine)
    
    def error(self, message, newLine=True):
        '''
        Sends an error message to every output plugin on the list.
        
        @parameter message: Message that is sent.
        '''
        self._call_output_plugins_action('error', message, newLine)
    
    def vulnerability(self, message, newLine=True, severity=severity.MEDIUM):
        '''
        Sends a vulnerability message to every output plugin on the list.
        
        @parameter message: Message that is sent.
        '''
        self._call_output_plugins_action('vulnerability', message,
                                         newLine, severity)
    
    def console(self, message, newLine=True):
        '''
        This method is used by the w3af console to print messages
        to the outside.
        '''
        self._call_output_plugins_action('console', message, newLine)
    
    def logHttp(self, request, response):
        '''
        Sends the request/response object pair to every output plugin
        on the list.
        
        @parameter request: A fuzzable request object
        @parameter response: A httpResponse object
        '''
        for oPlugin in self._output_plugin_list:
            oPlugin.logHttp(request, response)
    
    def echo(self, onOff):
        '''
        This method is used to enable/disable the output.
        '''
        self._echo = onOff

    def setOutputPlugins(self, outputPlugins):
        '''
        @parameter outputPlugins: A list with the names of Output Plugins that
                                  will be used.
        @return: No value is returned.
        '''     
        self._output_plugin_list = []
        self._output_plugins = outputPlugins
        
        for pluginName in self._output_plugins:
            out._addOutputPlugin(pluginName)  
        
        out.debug('Exiting setOutputPlugins()')
    
    def getOutputPlugins(self):
        return self._output_plugins
    
    def setPluginOptions(self, pluginName, PluginsOptions):
        '''
        @parameter PluginsOptions: A tuple with a string and a dictionary with
                                   the options for a plugin. For example:
                                   { console:{'verbosity':7} }
            
        @return: No value is returned.
        '''
        self._plugins_options[pluginName] = PluginsOptions
    
    def _call_output_plugins_action(self, actionname, message, *params):
        '''
        Internal method used to invoke the requested action on each plugin
        in the output plugin list.
        '''
        if self._echo:
            
            if isinstance(message, unicode):
                message = message.encode(UTF8, 'replace')
            
            # TODO: Does it make sense to transform this into a consumer?
            for oplugin in self._output_plugin_list:
                getattr(oplugin, actionname)(message, *params)
    
    def _addOutputPlugin(self, OutputPluginName):
        '''
        Takes a string with the OutputPluginName, creates the object and
        adds it to the self._output_plugin_list
        
        @parameter OutputPluginName: The name of the plugin to add to the list.
        @return: No value is returned.
        '''
        if OutputPluginName == 'all':
            fileList = os.listdir(os.path.join('plugins', 'output'))    
            strReqPlugins = [os.path.splitext(f)[0] for f in fileList
                                            if os.path.splitext(f)[1] == '.py']
            strReqPlugins.remove ('__init__')
            
            for pluginName in strReqPlugins:
                plugin = factory('plugins.output.%s' % pluginName, 
                                 self._threadpool )
                
                if pluginName in self._plugins_options.keys():
                    plugin.setOptions(self._plugins_options[pluginName])
                
                # Append the plugin to the list
                self._output_plugin_list.append(plugin)
        
        else:
            plugin = factory('plugins.output.%s' % OutputPluginName, 
                             self._threadpool )
            if OutputPluginName in self._plugins_options.keys():
                plugin.setOptions(self._plugins_options[OutputPluginName])

                # Append the plugin to the list
            self._output_plugin_list.append(plugin)    

# FIXME THREADING: Need to transform the OM into a consumer
out = OutputManager(None)
