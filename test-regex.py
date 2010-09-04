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

files = [ file('test-' + str(counter) + '.html').read() for counter in xrange(1,5) ]

def all_in_one():
    for _ in xrange(10000):
        for body in files:
            re.search(regex, body)

def separated():
    for _ in xrange(10000):
        for body in files:
            for sep_regex in dir_indexing_regexes:
                re.search(sep_regex, body)

allone = 1

if allone:
    print 'all'
    all_in_one()
else:
    print 'sep'
    separated()

