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
                gobject.TYPE_PYOBJECT, # option object
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
        valCol.add_attribute(valCell, 'option', 2)
        valCol.add_attribute(valCell, 'value', 3)
        valCell.connect('value-changed', self._on_change, 3)

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
            opt = params[0]
            opt = [opt.getName(), opt.getType(), opt, opt.getDefaultValue()]
        else:
            opt = params

        self._model.append(opt)

##### Test

class OptMock:
    def __init__(self, name, type, default, *choices):
        self.name = name
        self.type = type
        self.default = default
        if choices:
            self.choices = choices[0]

    def getType(self):
        return self.type

    def getDefaultValue(self):
        return self.default

    def getComboOptions(self):
        return self.choices

    def getName(self):
        return self.name


def main():
    def close(*ignore):
        gtk.main_quit()

    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.set_size_request(400, 200)
    window.connect('delete-event', close)
    table = OptsView()
    window.add(table)

    table.addOption(OptMock('boolOption1', 'boolean', True))
    table.addOption(OptMock('textOption1', 'string', 'test' * 10))
    table.addOption(OptMock('ipOption', 'ip', '127.0.0.1'))
    table.addOption(OptMock('comboOption', 'combo', '1', ['1','2','3','4']))
    table.addOption(OptMock('regexOption', 'regex', 'http://.*google.*'))
    table.addOption(OptMock('integerOption', 'integer', '123'))
    table.addOption(OptMock('floatOption', 'float', '123.123'))

    window.show_all()
    gtk.main()

if __name__=='__main__':
    main()
