import re

dir_indexing_regexes = []
dir_indexing_regexes.append("<title>Index of /") 
dir_indexing_regexes.append('<a href="\\?C=N;O=D">Name</a>') 
dir_indexing_regexes.append("Last modified</a>")
dir_indexing_regexes.append("Parent Directory</a>")
dir_indexing_regexes.append("Directory Listing for")
dir_indexing_regexes.append("<TITLE>Folder Listing.")
dir_indexing_regexes.append('<table summary="Directory Listing" ')
dir_indexing_regexes.append("- Browsing directory ")
dir_indexing_regexes.append('">\\[To Parent Directory\\]</a><br><br>')
dir_indexing_regexes.append('<A HREF=".*?">.*?</A><br></pre><hr></body></html>')
dir_indexing_regexes.sort()
regex = '(' + '|'.join(dir_indexing_regexes) + ')'

words = ['Index', 'Name<', 'Last m', 'irectory', 'Listing', '<hr></body></html>']
words.sort()
regex_w = '(' + '|'.join(words) + ')'

files = [ file('test-' + str(counter) + '.html').read() for counter in xrange(1,5) ]

def all_in_one():
    for _ in xrange(10000):
        for body in files:
            res = re.search(regex_w, body)
            if res:
                print res.group(0)
                re.search(regex, body)

def worded():
    for _ in xrange(10000):
        for word in words:
            for body in files:
                if word in body:
                    re.search(regex, body)

all_in_one()

