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
        self._delta = {}  # to store the values between commits
        self._optsInd = {} # model indicies to find a row fast

    def isUnsaved(self):
        return len(self._delta)>0

    def commit(self):
        if not self._delta: # nothing to do
            return
        self._baseline.update(self._delta)
        self.emit('edited', dict(self._delta))
        self._delta.clear()

    def rollback(self):
        for r in self._model:
            name = r[0]
            r[2] = self._baseline[name]
        self._delta.clear()
        self.emit('restored')

    def resetDefaults(self):
        for r in self._model:
            name = r[0]
            opt = r[1]
            value = opt.getDefaultValue()
            self.setOptionValue(name, value)

    def setOptionValue(self, name, value):
        if name not in self._optsInd:
            return

        idx = self._optsInd[name]
        row = self._model[idx]
        oldValue = row[2]
        if value==oldValue: return # nothing to do 

        baseValue = self._baseline[name]

        if value == baseValue:  
            if name in self._delta:
                del self._delta[name]
                if not self._delta: # changed everything back
                    self.rollback()
                    return
        else:
            self._delta[name] = value

        self._model[idx][2] = value
        self.emit('changed', name, value)

    def __getOptValue(self, name):
        result = self._delta.get(name, None)
        if result is None:
            result = self._defaults[name]
        return result

    def _on_change(self, widg, path, value, col):
        it = self._model.get_iter_from_string(path)
        name = self._model.get_value(it, 0)
        self.setOptionValue(name, value)

    def addOption(self, opt):
        value = opt.getValue()
        name = opt.getName()
        self._baseline[name] = value
        self._optsInd[name] = len(self._model)
        self._model.append([name, opt, value])

gobject.type_register(OptsView)
