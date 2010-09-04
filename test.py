from core.data.dom.dom_helpers import get_text
import xml.dom.minidom
a = xml.dom.minidom.parseString('<a><b>aaa</b><b>ccc</b><j>fk</j></a>')
b = a.getElementsByTagName('a')

print get_text(b)


