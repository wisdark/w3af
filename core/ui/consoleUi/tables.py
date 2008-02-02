
import core.controllers.outputManager as om
from core.ui.consoleUi.util import formatParagraph


class table:
    def __init__(self, rows):
        '''
        @param rows: array of arrays
        Every row is array of string (string per column)
        '''
        self._rows = rows
        self._colsNum = len(self._rows[0])
        self._colsRange = range(self._colsNum)
        self._separator = '|'
        

    def draw(self, termWidth, header = False):
        if len(self._rows) == 0:
            return
  
        self._initRelWidthes(termWidth)
        self._justify()        
        sl = len(self._separator)
        self._tableWidth = sum(self._widthes) + \
            self._colsNum * (sl + 2) + sl

        self.drawBr()
        for row in self._rows:
            self.drawRow(row)
            if header:
                self.drawBr()
            header = False
        self.drawBr()
            

    def _initRelWidthes(self, termWidth):
 
        ls = len(self._separator)
        space = termWidth - self._colsNum*(ls + 2) - ls # Useful space
            
        #maximal length of content for every column
        maxLengths = [max([max(map(len, row[i].split('\n'))) for row in self._rows]) \
            for i in self._colsRange]
        sumMaxLen = sum(maxLengths)

        # We calculate the widthes in the proportion to they longest line
        # later we justify it with the justify function
        relativeLengths = [float(ml)/sumMaxLen for ml in maxLengths]
        self._widthes = [int(rl*space) for rl in relativeLengths]
                

    def _justify(self):
        '''
        This function reallocates widthes between columns.
        @param shift is array which contain lack or plenty of space in the column.
        Lack of space happens when a longest word in a column does not fit into originally allocated space.
        This function acts as Robin Hood: it takes excess of space from the "richest" column and gives it 
        to the poorest ones.
        '''
        minLengths = [max([max(map(len, row[i].split()+[''])) for row in self._rows]) \
            for i in range(self._colsNum)]
        shifts = [w - mw for mw,w in zip(minLengths , self._widthes)]
#        length = len(shifts)
        borrow = zip(self._colsRange, shifts)
        borrow.sort(lambda a,b: cmp(a[1], b[1]))
        delta = [0]*self._colsNum

        donorIdx = self._colsNum-1
        recIdx = 0
        while True:

            curDonation = borrow[donorIdx][1]
            curRec = borrow[recIdx][1]
                
            if curRec >= 0 or curDonation <=0:
                break

            curDelta = min(curDonation, -curRec)
            curDonation -= curDelta
            curRec += curDelta
            delta[borrow[donorIdx][0]] -= curDelta
            delta[borrow[recIdx][0]] += curDelta

            if curDonation == 0:
                donorIdx -=1

            if curRec == 0:
                recIdx += 1
                    
        for i in self._colsRange:
            self._widthes[i] += delta[i]


    def drawBr(self, char='-'):
        ls = len(self._separator)
        om.out.console(self._separator + char*(self._tableWidth-2*ls) + self._separator)

    def drawRow( self, row ):
        columns = [formatParagraph(col, w) for col, w in zip(row, self._widthes)]
        emptyLines = [' ' * w for w in self._widthes]
        maxHeight = max(map(len, columns))
        columns = [col + [er]*(maxHeight - len(col)) for (col, er) in zip(columns, emptyLines)]
    #    width = sum(widthes) + (len(columns)-1)*3 + 4
        s = self._separator
        for rowNum in range(0, maxHeight):
            om.out.console(s + ' '
                + (' ' + s + ' ').join([col[rowNum] for col in columns]) + ' ' + s)            
