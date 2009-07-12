import gtk
import gtk.gdk as gdk
import gobject as go
from collections import defaultdict

class PluginTree(gtk.TreeView):
#    __gsignals__ = { 
#         'open' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, \
#                 (gobject.TYPE_STRING,gobject.TYPE_STRING))
#    }

    def __init__(self, hub, core, *params):
        super(PluginTree, self).__init__(*params)
        self._hub = hub
        self._core = core
        self._model = gtk.TreeStore(str, str, go.TYPE_BOOLEAN, gdk.Pixbuf)
        column = gtk.TreeViewColumn('Plugin')
        cr = gtk.CellRendererText()
        column.pack_start(cr)
        column.add_attribute(cr, 'text', 0)
        self.append_column(column)
        self.set_model(self._model)

        self._rootsByType = {}
        self._indicies = defaultdict(dict)
        self._byPath = {}
        self.__fillModel()
        self.connect('row-activated', self.__open)

    def __fillModel(self):
        core = self._core
        types = core.getPluginTypes()
        map(self.__fillType, sorted(types))
            
    def __fillType(self, ptype):
        print ptype
        plugins = self._core.getPluginList(ptype)
        activated = set(self._core.getEnabledPlugins(ptype))

        allActive = (len(activated) == len(plugins))
        root = self._model.append(None, [ptype, ptype, allActive, None])
        self._rootsByType[ptype] = root

        dlg = gtk.Dialog()
        editPix = dlg.render_icon(gtk.STOCK_EDIT, gtk.ICON_SIZE_MENU)

        for pname in plugins:
            #print ' ', pname
            isActive = allActive or pname in activated
            instance = self._core.getPluginInstance(pname, ptype)
            isEditable = bool(len(instance.getOptions()))

            pix = isEditable and editPix or None

            idx = self._model.append(root, [pname, pname, isActive, pix])
            self._indicies[ptype][pname] = idx
            self._byPath[self._model.get_path(idx)] = (ptype, pname)
            

    def __open(self, widg, path, column):
        typeAndName = self._byPath[path]
        page = self._hub.open(*typeAndName)
        page.connect('edited', self.__restored, path)
        page.connect('restored', self.__restored, path)
        page.connect('changed', self.__changed, path)
#        self.emit('open-plugin', *self._byPath[path])


    def __restored(*_):
        pass

    def __changed(*_):
        pass

#    def setEditor(self, editor):
#        self._editor

    def addPlugin(self, plugin, options):
        optDict = {}
        for o in options:
            optDict[o.getName()] = o.getDefaultValue()
            
        self_model.append([plugin.getName(), plugin.getName(), \
                False, False, None])



    def pluginEdited(self, *p):
        pass

    def pluginRestored(self, *p):
        pass
