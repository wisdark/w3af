import sys

CSI = '\x1B['

CSI_EL = CSI + '%iK'
EL_FW = 0
EL_BACK = 1
EL_WHOLE = 2

CSI_SCP = CSI + 's'
CSI_RCP = CSI + 'u'

CSI_CUU = CSI + '%iA'
CSI_CUD = CSI + '%iB'
CSI_CUF = CSI + '%iC'
CSI_CUB = CSI + '%iD'


def eraseLine(where=0):
	sys.stdout.write( CSI_EL % where)

def savePosition():
	sys.stdout.write( CSI_SCP )

def restorePosition():
	sys.stdout.write(CSI_RCP)

def _moveDelta(delta, pos_code, neg_code):
	if delta != 0:
		code = delta > 0 and pos_code or neg_code
		sys.stdout.write (code % abs(delta))

def moveDelta(dx=1, dy=0):
	_moveDelta(dx, CSI_CUF, CSI_CUB)
	_moveDelta(dy, CSI_CUD, CSI_CUU)



def moveBack(steps=1):
	print CSI_CUB % steps

def moveForward(steps=1):
	print CSI_CUF % steps

def moveBack(steps=1):
	print CSI_CUB % steps

def moveBack(steps=1):
	sys.stdout.write( CSI_CUB % steps)
