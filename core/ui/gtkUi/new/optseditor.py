import gtk
import gobject
from optsview import OptsView

class EditorPage(gtk.VBox):
    __gsignals__ = {
         'edited' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)), 
         'cancelled': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
         'changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
        # that is a dictionaty of the changed options
    }
 
    def __init__(self, optList, values):
        super(EditorPage, self).__init__()
        view = OptsView()
        for opt in optList:
            name = opt.getName()
            value = values[name] if name in values else opt.getDefaultValue()
            view.addOption(opt, value)
        
        view.connect('edited', self.__edited)
        view.connect('changed', self.__changed)
        self._view = view
        self._cache = {}
        self.__fillContent()

    # view callbacks
    def __edited(self, widg, opts):
        self.emit('edited', opts)
        print opts

    def __changed(self, widg, *opt):
        self.emit('changed')
        print opt

    # buttons callbacks
    def __commit(self, *_):
        self._view.commit()

    def __rollback(self, *_):
        self._view.rollback()
        self.emit('cancelled')

    def __fillContent(self):
        self.pack_start(self._view)
        okButton = gtk.Button("Save")
        cancelButton = gtk.Button("Cancel")
        okButton.connect('clicked', self.__commit)
        cancelButton.connect('clicked', self.__rollback)
        self.pack_end(okButton)
        self.pack_end(cancelButton)

gobject.type_register(EditorPage)
