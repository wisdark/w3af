'''
posixterm.py

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

#import core.controllers.outputManager as om
import sys
import tty
import termios

from ecma48 import *

KEY_UP = '\x1B[A'
KEY_DOWN = '\x1B[B'
KEY_RIGHT = '\x1B[C'
KEY_LEFT = '\x1B[D'

KEY_BACKSPACE = '\x7F'

ctrlCodes = range(1,27)
ctrlCodes.remove(9)
ctrlCodes.remove(13)

extKeys = [KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT]
longestSequence = 5

def getch(buf=None):

    ch = read(1)
    if buf is not None:
        buf.append(ch)
        strval = ''.join(buf)
        if strval in extKeys or len(strval) >= longestSequence:
            result = strval
        else:
            result = getch(buf)
    elif ch == '\x1B':
        result = getch(['\x1B'])
    elif ord(ch) in ctrlCodes:
        result = '^' + chr(ord(ch)+64)
    else:
        result = ch

    return result

def write(s):
    sys.stdout.write(s)

def writeln(s=''):
    sys.stdout.write(s+'\n\r')

def bell():
    sys.stdout.write('\x07')

class terminal:

    def __init__(self):
        self._buf = None
        self._extKeys = [KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT]
        self._longestSequence = 5 # max(map(len, self._extKeys))

        self._ctrlCodes = range(1,27)
        self._ctrlCodes.remove(9)
        self._ctrlCodes.remove(13)


    def getch(self):
        ch = read(1)
        if self._buf is not None:
            self._buf.append(ch)
            strval = ''.join(self._buf)
            if strval in self._extKeys or len(strval) >= self._longestSequence:
                result = strval
                self._buf = None
            else:
                result = self.getch()
        elif ch == '\x1B':
            self._buf = ['\x1B']
            result = self.getch()
        elif ord(ch) in self._ctrlCodes:
            result = '^' + chr(ord(ch)+64)
        else:
            result = ch

        return result

    def write(self, s):
        sys.stdout.write(s)


def setRawInputMode_win( raw ):
    '''
    Sets the raw input mode, in windows.
    '''
    pass
    
def read_win( amt ):
    res = ''
    for i in xrange( amt ):
        res += msvcrt.getch()
    return res
    
oldSettings = None
def setRawInputMode_unix( raw ):
    '''
    Sets the raw input mode, in linux.
    '''
    global oldSettings
    if raw and oldSettings is None:
        fd = sys.stdin.fileno()
        try:
            oldSettings = termios.tcgetattr(fd)
            tty.setraw(sys.stdin.fileno())
        except Exception, e:
            om.out.console('termios error: ' + str(e) )
    elif not (raw or oldSettings is None):
        try:
            termios.tcsetattr( sys.stdin.fileno() , termios.TCSADRAIN, oldSettings )
            oldSettings = None
        except Exception, e:
            om.out.console('termios error: ' + str(e) )

def read_unix( amt ):
    return sys.stdin.read( amt )


def wrapper( fun ):
    try:
        setRawInputMode(True)
        fun()
    finally:
        setRawInputMode(False)

try:
    import tty, termios
except:
    # We arent on unix !
    try:
        import msvcrt
    except:
        # We arent on windows nor unix
        raise w3afException('w3af support for OS X aint available yet! Please contribute.')
    else:
        setRawInputMode = setRawInputMode_win
        read = read_win
else:
    setRawInputMode = setRawInputMode_unix
    read = read_unix
