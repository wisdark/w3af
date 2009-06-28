import gtk
import gtk.gdk as gdk
import gobject
from collections import defaultdict
from optcell import BooleanValueRenderer, TextValueRenderer, DispatcherValueRenderer

#helper structure; just a named replacement for tuples
class OptsView(gtk.TreeView):
    __gsignals__ = {
            'option-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                (gobject.TYPE_STRING, gobject.TYPE_PYOBJECT,)) }


    def __init__(self):
        gtk.TreeView.__init__(self)
        self._cache = {}

        # 2nd column will store (optionType, optionValue)
        self._model = gtk.ListStore(\
                gobject.TYPE_STRING, # name
                gobject.TYPE_STRING, # type
                gobject.TYPE_PYOBJECT # value
        )

        self.set_model(self._model)
        self._options = []

        nameCell = gtk.CellRendererText()
        nameCell.set_property('editable', True)
        nameCol = gtk.TreeViewColumn("Option")

        nameCol.pack_start(nameCell)
        nameCol.add_attribute(nameCell, 'text', 0)

        valCol = gtk.TreeViewColumn('Value')
        valCell = DispatcherValueRenderer()
        valCol.pack_start(valCell)
        valCol.add_attribute(valCell, 'type', 1)
        valCol.add_attribute(valCell, 'value', 2)
        valCell.connect('value-changed', self._on_change, 2)

        col = gtk.TreeViewColumn('test')
        cell = BooleanValueRenderer()
        cell.connect('value-changed', self._on_change, 2)

        self.append_column(nameCol)
        self.append_column(valCol)

    def __getOptValue(self, name):
        result = self._cache.get(name, None)
        if result is None:
            result = self._defaults[name]
        return result

    def _on_change(self, widg, path, value, col):
        it = self._model.get_iter_from_string(path)
        name = self._model.get_value(it, 0)
        self.emit('option-changed', name, value)
        self._cache[name] = value
        self._model.set_value(it, col, value)

    def addOption(self, *params):
        if len(params)==1:
            opt = [opt.getName(), opt.getType(), opt.getDefaultValue()]
        else:
            opt = params

        name, otype, value = opt
        self._model.append([name, otype, value])

##### Test
def main():
    def close(*ignore):
        gtk.main_quit()

    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.set_size_request(400, 200)
    window.connect('delete-event', close)
    table = OptsView()
    window.add(table)

    table.addOption('boolOption1', 'boolean', True)
    table.addOption('textOption1', 'string', 'test' * 10)
    table.addOption('ipOption', 'ip', '127.0.0.1')

    window.show_all()
    gtk.main()

if __name__=='__main__':
    main()
