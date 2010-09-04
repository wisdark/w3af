import string
import re
split = re.compile('[^\w]')

letters = {}
for l in string.letters:
    letters[l] = 1


def fast_word_split( in_string ):
    splitted_body = split.split(in_string)
    return splitted_body

def fast_word_split( in_string ):
    res = []
    for letter in in_string:
        if letter not in letters:
            res.append('')
        else:
            res[-1] += letter
    return res

in_string = file('test-1.html').read()
for i in xrange(10000):
    fast_word_split( in_string )


