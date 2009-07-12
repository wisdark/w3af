from optseditor import EditorNotebook
from plugintree import PluginTree


class ConfigHub:
    def __init__(self, core):
        self._core = core
        self._tree = None
        self._editor = None

    def getNavigationWidget(self):
        if not self._tree:
            self._tree = PluginTree(self, self._core) 

        return self._tree

    def getEditorWidget(self):
        if not self._editor:
            self._editor = EditorNotebook()

        return self._editor

    def open(self, ptype, pname):
        opts = self._core.getPluginOptions(pname, ptype)
        plugin = self._core.getPluginInstance(pname, ptype)
        defOpts = plugin.getOptions()
        page = self.getEditorWidget().open(plugin.getName(), defOpts, opts)
        print page
        return page

    def __open(self, widg, ptype, pname, editor):
        return self.open(ptype, pname)
