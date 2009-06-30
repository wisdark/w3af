import gtk
import gtk.gdk as gdk
import gobject
from collections import defaultdict
from optcell import BooleanValueRenderer, TextValueRenderer, DispatcherValueRenderer

#helper structure; just a named replacement for tuples
class OptsView(gtk.TreeView):
    __gsignals__ = {
# changed is emitted every time any property edited.
# properties are considered saved when "edited" is emitted
# "changed" and "restored" are for the purpose of "Unsaved" handling
            'changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                (gobject.TYPE_STRING, gobject.TYPE_PYOBJECT,)), 
            'restored' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
            'edited' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                (gobject.TYPE_PYOBJECT,)),
        }


    def __init__(self):
        gtk.TreeView.__init__(self)

        self._model = gtk.ListStore(\
                gobject.TYPE_STRING, # name
                gobject.TYPE_PYOBJECT, # option object
                gobject.TYPE_PYOBJECT # value
        )

        self.set_model(self._model)

        nameCell = gtk.CellRendererText()
        nameCell.set_property('editable', True)
        nameCol = gtk.TreeViewColumn("Option")

        nameCol.pack_start(nameCell)
        nameCol.add_attribute(nameCell, 'text', 0)

        valCol = gtk.TreeViewColumn('Value')
        valCell = DispatcherValueRenderer()
        valCol.pack_start(valCell)
        valCol.add_attribute(valCell, 'option', 1)
        valCol.add_attribute(valCell, 'value', 2)
        valCell.connect('value-changed', self._on_change, 2)

        self.append_column(nameCol)
        self.append_column(valCol)

        self._baseline = {} # values for rollback
        self._cache = {}  # to store the values between commits

    def commit(self):
        self._baseline.update(self._cache)
        self.emit('edited', dict(self._cache))
        self._cache.clear()

    def rollback(self):
        for r in self._model:
            name = r[0]
            r[2] = self._baseline[name]
        self._cache.clear()

    def resetDefaults(self):
        for r in self._model:
            opt = r[1]
            name = r[0]
            value = opt.getDefaultValue()
            if self._baseline[name] != value: # otherwise nothing to change
                self._cache[name] = value

    def __getOptValue(self, name):
        result = self._cache.get(name, None)
        if result is None:
            result = self._defaults[name]
        return result

    def _on_change(self, widg, path, value, col):
        it = self._model.get_iter_from_string(path)
        name = self._model.get_value(it, 0)
        #self.emit('option-changed', name, value)
        self.emit('changed', name, value)
        self._cache[name] = value
        self._model.set_value(it, col, value)

    def addOption(self, opt, value=None):
        if value is None: value = opt.getDefaultValue()
        name = opt.getName()
        self._baseline[name] = value
        self._model.append([name, opt, value])

gobject.type_register(OptsView)
