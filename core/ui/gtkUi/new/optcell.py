import gtk
import gobject
from collections import defaultdict
import traceback
import re

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

CRME = gtk.CELL_RENDERER_MODE_EDITABLE
   
class RenderMixIn:
    '''
    Convenience methods for all the custom renderers
    in this module.
    getActor() method must be implemented by any subclass.
    '''
    def on_render(self, *params):
        return self.getActor().render(*params)

    def on_get_size(self, *params):
        return self.getActor().get_size(*params)

    def on_start_editing(self, *params):
        return self.getActor().start_editing(*params)

class DispatcherValueRenderer(RenderMixIn, gtk.GenericCellRenderer):
    '''
    A dispatching renderer. Contains all the option renderers
    and delegates the control to them depending on the type.
    '''
    __gproperties__ = GPROPERTIES
    __gsignals__ = GSIGNALS

    def __init__(self):
        super(DispatcherValueRenderer, self).__init__()
        self._actors = ( 
                # TODO wouldn't be better to rewrite this as a dict?
                # Will see how this perform, then think.
                BooleanValueRenderer(), 
                IPTextValueRenderer(),
                ComboBoxRenderer(),
                TypedTextValueRenderer('float', float),
                TypedTextValueRenderer('integer', int),
                TypedTextValueRenderer('regex', re.compile),
                TextValueRenderer())

        for a in self._actors:
            a.set_property('mode', CRME) # All renderers are editable
            a.connect('value-changed', self.__propagate)
        self.set_property('mode', CRME)  # And me too

    def getActor(self):
        for actor in self._actors: # choose who will make the job
            if actor.relevant():
                return actor

    def __propagate(self, widg, path, value):
        self.emit('value-changed', path, value)

    def on_get_size(self, *params): 
        '''
        By the moment, when on_get_size() and other on_*() are called,
        all the properties are already set. So getActor() will always work,
        here and in those renderers below.
        '''
        return self.getActor().get_size(*params)

    def do_set_property(self, prop, value):
        for actor in self._actors:
            actor.set_property(prop.name, value)

    def do_get_property(self, prop):
        return self.getActor().get_property(prop.name)


class OptionRenderer(RenderMixIn, gtk.GenericCellRenderer):
    '''
    Basic class for all the option renderers.
    Every subclass will have the fields 'option' and 'type'
    set (type is for the easier access, as anyone needs it)

    super(cls, self).do_set_property() should be used
    by the subclasses
    '''
    __gproperties__ = GPROPERTIES
    __gsignals__ = GSIGNALS

    def do_set_property(self, prop, value):
        if prop.name=='option':
            self.option = value
            self.type = value.getType()


class BooleanValueRenderer(OptionRenderer):
    def __init__(self):
        super(BooleanValueRenderer, self).__init__()
        actor = gtk.CellRendererToggle()
        actor.set_properties(activatable=True, mode=CRME)
        self._actor = actor

    def getActor(self): return self._actor
    def relevant(self): return self.type == 'boolean'

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
    def __init__(self):
        super(TextValueRenderer, self).__init__()
        actor = gtk.CellRendererText()
        actor.set_properties(editable=True, mode=CRME)
        actor.connect('edited', self.__propagate)

        self._actor = actor

    def __propagate(self, widg, path, value):
        if self.validate(value):
            self.emit('value-changed', path, value)

    def getActor(self): return self._actor
    def validate(self, value): return True
    def relevant(self): return True

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

class TypedTextValueRenderer(TextValueRenderer):
    def __init__(self, type, validator):
        super(TypedTextValueRenderer, self).__init__()
        self.__type = type
        self.__validator = validator

    def relevant(self): return self.type == self.__type

    def validate(self, value):
        try:
            self.__validator(value)
            return True
        except:
            return False
        
class ComboBoxRenderer(OptionRenderer):
    def __init__(self):
        super(ComboBoxRenderer, self).__init__()
        actor = gtk.CellRendererCombo()
        actor.set_properties(mode=CRME, editable=True)
        actor.connect('edited', self.__propagate)
        self._actor = actor
        self._store = None

    def __propagate(self, widg, path, value):
        if self._choices and value in self._choices:
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
gobject.type_register(DispatcherValueRenderer)
