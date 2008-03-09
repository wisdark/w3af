from string import Template
import xml.etree.ElementTree as ET
from xml.dom.minidom import *

class helpRepository:
    def __init__(self, path='core/ui/consoleUi/help.xml'):
        self.__doc = ET.parse(path)
        self.__map = {}
        topics = self.__doc.findall('.//topic')
        for t in topics:
            self.__map[str(t.attrib['name'])] = t


    def loadHelp(self, topic, obj=None, vars=None):
        def subst(templ):
            if not vars:
                return templ
            return Template(templ).safe_substitute(vars)

        if not obj:
            obj = help()
        elt = self.__map[topic]
        for catElt in elt.findall('category'):
            catName = 'name' in catElt.attrib and catElt.attrib['name'] or 'default'
            catName = str(catName)

            for itemElt in catElt.findall('item'):
                itemName = str( itemElt.attrib['name'] )
                itemName = subst(itemName)

                short = itemElt.findtext('short')
                full = itemElt.findtext('full')
                
                if not short:
                    short = itemElt.text

                short = subst(short)
                if full:
                    full = subst(full)

                obj.addHelpEntry(itemName, (short, full), catName)


        return obj

helpMainRepository = helpRepository()

    

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
        
