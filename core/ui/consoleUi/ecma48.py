'''
consoleUi.py

Copyright 2008 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''

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
