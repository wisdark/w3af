from optsview import OptsView
from optseditor import EditorPage
import gtk
##### Test

class OptMock(dict):
    def __init__(self, name, type, value, **kwargs):
        super(OptMock, self).__init__(kwargs)
        self.update(name=name, type=type, defaultValue=value)

    def __getattr__(self, name):
        if name.startswith('get'):
            propName = name[3].lower() + name[4:]
            def result():
                return self[propName]
            return result

def main():
    def close(*ignore):
        gtk.main_quit()

    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.set_size_request(400, 300)
    window.connect('delete-event', close)
#    table = OptsView()
#    window.add(table)

    options = [
            OptMock('boolOption1', 'boolean', True),
            OptMock('textOption1', 'string', 'test'),
            OptMock('ipOption', 'ip', '127.0.0.1'),
            OptMock('comboOption', 'combo', '1', comboOptions=['1','2','3','4']),
            OptMock('integerOption', 'integer', '123'),
            OptMock('floatOption', 'float', '123.123')
    ]

#    map(table.addOption, options)
    page = EditorPage(options, {})
    window.add(page)

    window.show_all()
    gtk.main()

if __name__=='__main__':
    main()
