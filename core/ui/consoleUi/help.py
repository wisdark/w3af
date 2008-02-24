class help:
    def __init__(self):
        self._table = {}
        self._commonTable = {}


    def addHelpEntry(self, subj, content, group=''):

        if group in self._table:
            groupDict = self._table[group]
        else:
            groupDict = {}
            self._table[group] = groupDict

        groupDict[subj] = content
        self._commonTable[subj] = content


    def getCategories(self):
        return self._table.keys()

    def addHelp(self, table, group=''):
        for subj in table:
            self.addHelpEntry(subj, table[subj], group)


    def getHelp(self, subj):
        try:
            return self._commonTable[subj]
        except:
            return None

    def getItems(self, group=None):
        if group:
            return self._table[group].keys()
        else:
            return self._commonTable.keys()


    def getPlainHelpTable(self, separators=True, group=None):
        result = []
        
        if group is not None:
            self._appendHelpTable(result, group)
        else:
            for g in self._table:
                self._appendHelpTable(result, g)
                if separators:
                    result.append([])

            if len(result) and separators:
                result.pop()

        return result


    def _appendHelpTable(self, result, groupName):
        if groupName in self._table:
            group = self._table[groupName]
            
            for subj in group:
               result.append([subj, group[subj]])
        
