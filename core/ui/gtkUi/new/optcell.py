import gtk
import gobject
from collections import defaultdict
import traceback

GPROPERTIES = {
        'value': (gobject.TYPE_PYOBJECT, 'value', 'value',
            gobject.PARAM_READWRITE),
        'type': (gobject.TYPE_STRING, 'value', 'value', '', gobject.PARAM_READWRITE)
}

GSIGNALS = {
        'value-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
            (gobject.TYPE_STRING, gobject.TYPE_PYOBJECT,))
}
   
class RenderMixIn:
    def on_render(self, *params):
        return self.getActor().render(*params)

    def on_get_size(self, *params):
        return self.getActor().get_size(*params)

    def on_start_editing(self, *params):
        result = self.getActor().start_editing(*params)
        return result

class DispatcherValueRenderer(RenderMixIn, gtk.GenericCellRenderer):
    __gproperties__ = GPROPERTIES
    __gsignals__ = GSIGNALS

    def __init__(self):
        super(DispatcherValueRenderer, self).__init__()
        self.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
        self._actors = (
                BooleanValueRenderer(), 
                IPTextValueRenderer(),
                TextValueRenderer())

    def getActor(self):
        for actor in self._actors:
            if actor.relevant():
                actor.connect('value-changed', self.__propagate)
                return actor

    def __propagate(self, widg, path, value):
        self.emit('value-changed', path, value)

    def on_get_size(self, *params):
        act = self.getActor()
        result = act.get_size(*params)
        return result

    def do_set_property(self, prop, value):
        for actor in self._actors:
            actor.set_property(prop.name, value)

    def do_get_property(self, prop):
        return self.getActor().get_property(prop.name)


class BooleanValueRenderer(RenderMixIn, gtk.GenericCellRenderer):
    __gproperties__ = GPROPERTIES
    __gsignals__ = GSIGNALS

    def getActor(self):
        return self._actor

    def __init__(self):
        gtk.GenericCellRenderer.__init__(self)
        self.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
        self._actor = gtk.CellRendererToggle()
        self._actor.set_property('activatable', True)
        self._actor.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
        self.type = None

    def relevant(self):
        return self.type == 'boolean'

    def do_set_property(self, prop, value):
        name = prop.name
        if name=='type':
            self.type = value
        elif name=='value':
            self.value = True if value else False
            return self._actor.set_property('active', self.value)

    def on_start_editing(self, evt, widg, path, *other):
        self.emit('value-changed', path, not self.value)


class TextValueRenderer(RenderMixIn, gtk.GenericCellRenderer):
    __gproperties__ = GPROPERTIES
    __gsignals__ = GSIGNALS

    def getActor(self):
        return self._actor

    def __init__(self):
        super(TextValueRenderer, self).__init__()
        self._actor = gtk.CellRendererText()
        self._actor.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
        self.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
        self._actor.set_property('editable', True)
        self._actor.connect('edited', self.__propagate)

    def __propagate(self, widg, path, value):
        if self.validate(value):
            self.emit('value-changed', path, value)

    def validate(self, value):
        return True

    def relevant(self):
        return True

    def do_set_property(self, prop, value):
        name = prop.name
        if name=='type':
            self.type = value
        else:
            realName = name if name!='value' else 'text'
            return self._actor.set_property(realName, value)


class IPTextValueRenderer(TextValueRenderer):
    def validate(self, value):
        fields = value.split('.')

        if len(fields)!=4:
            return False

        for n,f in enumerate(fields):
            try:
                i = int(f)
                if i>255 or i<0 or (n==0 and i==0):
                    return false
            except:
                return False

        return True

    def relevant(self):
        return self.type=='ip'

class ComboBoxRenderer(RenderMixIn, gtk.GenericCellRenderer):
    def __init__(self):
        super(ComboBoxRenderer, self).__init__()
        self._actor = gtk.CellRendererCombo()
#        self._actor.

gobject.type_register(BooleanValueRenderer)
gobject.type_register(TextValueRenderer)
gobject.type_register(DispatcherValueRenderer)
