import gtk
import gobject
from collections import defaultdict
import traceback

GPROPERTIES = {
        'value': (gobject.TYPE_PYOBJECT, 'value', 'value',
            gobject.PARAM_READWRITE),
        'option': (gobject.TYPE_PYOBJECT, 'option', 'option',
            gobject.PARAM_READWRITE),
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
                ComboBoxRenderer(),
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


class OptionRenderer(RenderMixIn, gtk.GenericCellRenderer):
    __gproperties__ = GPROPERTIES
    __gsignals__ = GSIGNALS

    def do_set_property(self, prop, value):
        if prop.name=='option':
            self.option = value
            self.type = value.getType()


class BooleanValueRenderer(OptionRenderer):
#    __gproperties__ = GPROPERTIES
#    __gsignals__ = GSIGNALS

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
        if name=='value':
            self.value = True if value else False
            self._actor.set_property('active', self.value)
        else:
            super(BooleanValueRenderer, self).do_set_property(prop, value)

    def on_start_editing(self, evt, widg, path, *other):
        self.emit('value-changed', path, not self.value)


class TextValueRenderer(OptionRenderer):

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
        if prop.name=='value':
            self._actor.set_property('text', value)
        else:
            super(TextValueRenderer, self).do_set_property(prop, value)


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


class ComboBoxRenderer(OptionRenderer):
    def __init__(self):
        super(ComboBoxRenderer, self).__init__()
        actor = gtk.CellRendererCombo()
        actor.set_properties(\
                mode=gtk.CELL_RENDERER_MODE_EDITABLE, editable=True)
      #  self._actor.connect('changed', self.__changed)
        actor.connect('edited', self.__propagate)
        self._actor = actor
        self._store = None

        self.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
        self._cachedChange = None

    def __propagate(self, widg, path, value):
        if value in self._choices:
            self.emit('value-changed', path, value)

    def relevant(self):
        return self.type=='combo'

    def getActor(self):
        if self._choices is None:
            store = gtk.ListStore(gobject.TYPE_STRING)
            choices = [] # a cache for the simpler access
            self._actor.set_property('model', store)
            self._actor.set_property('text-column', 0)

            for s in self.option.getComboOptions():
                store.append([s])
                choices.append(s)

            self._choices = choices

        return self._actor

    def do_set_property(self, prop, value):
        name = prop.name
        if name=='value':
            self._choices = None # the new lifecycle has started
            self._actor.set_property('text', str(value))
        else:   
            super(ComboBoxRenderer, self).do_set_property(prop, value)


gobject.type_register(OptionRenderer)
#gobject.type_register(BooleanValueRenderer)
#gobject.type_register(TextValueRenderer)
gobject.type_register(DispatcherValueRenderer)
