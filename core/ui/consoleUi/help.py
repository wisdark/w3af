from string import Template
from xml.dom.minidom import parse

def loadHelp( name, obj=None, vars=None):
    dom = parse('core/ui/consoleUi/help/%s.xml' % name)
    return helpFromDOM( dom, obj, vars )

def helpFromDOM( dom, obj=None, vars=None ):
    def subst(templ):
        if not vars:
            return templ
        return Template(templ).safe_substitute(vars)

    if obj is None:
        obj = help() 
    for catElem in dom.getElementsByTagName('category'):
        catName = str( catElem.getAttribute('name') )
        if not catName:
            catName = 'default'
        for itemElem in catElem.getElementsByTagName('item'):
            itemName = str( itemElem.getAttribute('name') )

            itemName = subst(itemName)
            short = full = None

            for child in itemElem.childNodes:
                isShort = child.nodeName == 'short'
                isFull = child.nodeName == 'full'
                if isShort or isFull:
                    value = str( subst( child.childNodes[0].data ) )
                    if isShort:
                        short = value
                    else:
                        full = value
             
            obj.addHelpEntry( itemName, (short, full), catName )
    return obj
   
     
#def getText(elem):
#    nodelist = elem.childNodes
#    rc = ""
#    for node in nodelist:
#        if node.nodeType == node.TEXT_NODE:
#            rc = rc + node.data
#    return rc

    

class help:
    def __init__(self):
        self._table = {}
        self._subj2Gat = {}
        self._cat2Subj = {}


    def addHelpEntry(self, subj, content, cat=''):

        if type(content) not in (tuple, list): 
            content = (content, None)

        self._table[subj] = content
        self._subj2Gat[subj] = cat
        if cat in self._cat2Subj:
            d = self._cat2Subj[cat]
        else:
            d = []
            self._cat2Subj[cat] = d

        d.append(subj)


    def getCategories(self):
        return self._subj2Gat.keys()

    def addHelp(self, table, cat=''):
        for subj in table:
            self.addHelpEntry(subj, table[subj], cat)


    def getHelp(self, subj):
        if subj not in self._table:
            return (None, None)

        return self._table[subj]


    def getItems(self):
        return self._table.keys()


    def getPlainHelpTable(self, separators=True, cat=None):
        result = []
        
        if cat is not None:
            self._appendHelpTable(result, cat)
        else:
            for g in self._cat2Subj:
                self._appendHelpTable(result, g)
                if separators:
                    result.append([])

            if len(result) and separators:
                result.pop()

        return result


    def _appendHelpTable(self, result, cat):
        items = cat in self._cat2Subj and self._cat2Subj[cat] or self._table
           
        for subj in items:
            result.append([subj, self.getHelp(subj)[0]])
        
