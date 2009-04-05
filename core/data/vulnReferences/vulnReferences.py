'''
xmlFile.py

Copyright 2006 Andres Riancho

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

from core.controllers.w3afException import w3afException
import core.controllers.outputManager as om

# severity constants for vuln messages
import core.data.constants.severity as severity
import sys
import os.path
# xml
import xml.dom.minidom

class vulnReferences:

    def __init__(self):
        self._xmlfilename = 'core' + os.path.sep + 'data' + os.path.sep
        self._ghdb_file += 'vulnReferences' + os.path.sep + 'vulnReferences.xml'        
        self._vulnarray = []
        self._findingsource = []
        self._w3afid=''
        self._findingname = ''
        self._findinglink = [] 
        self._initialized = False
        self._source = []
        self._url = []
        
    def _init( self ):
        self._initialized = True
        try:
            self._vulnxml = xml.dom.minidom.parse(self._xmlfilename)
        except Exception, e:
            msg = 'Cant open vuln xml file ' + self._xmlfilename + ' for input.'
            msg += ' Exception: "' + str(e) + '".'
            raise w3afException( msg )            
        #parse each of the vulnerabilities and add to list
        vulnerabilities =  self._vulnxml.getElementsByTagName("vulnerability")
        y = 0
        for vulnerability in vulnerabilities:
            vulnid = vulnerability.getElementsByTagName("vulnid")[0].firstChild.data.encode('ascii')
            self._vulnarray.append([vulnid])
            vulnname = vulnerability.getElementsByTagName("vulnname")[0].firstChild.data.encode('ascii')
            self._vulnarray[y].append([vulnname])
            references = vulnerability.getElementsByTagName("reference")
            for reference in references:
                findingsource = reference.getElementsByTagName("source")[0].firstChild.data.encode('ascii')
                findingurl = reference.getElementsByTagName("url")[0].firstChild.data.encode('ascii')
                self._vulnarray[y].append([findingsource])
                self._vulnarray[y].append([findingurl])
            y+=1

    def getRefInfo(self, vulnid, data):
        if not self._initialized:
          self._init()
        for i in range(len(self._vulnarray)):
            if str(self._vulnarray[i][0]) == vulnid:
                om.out.debug("getRefInfo found a vulnid that matched self._vulnarray[i][0]")
                w3afid = str(self._vulnarray[i][0])
                om.out.debug("in getRefInfo w3afid is "+w3afid)
                name =  str(self._vulnarray[i][1][0])
                refsize = len(self._vulnarray[i])
                source = []
                url = []
                if data == "source":
                    for j in range(2,refsize,2):
                        source.append(self._vulnarray[i][j][0])
                    return source
                
                if data == "url":
                    om.out.debug("INSIDE DATA == URL IF STATEMENT")
                    for j in range(3,refsize,2):
                        url.append(self._vulnarray[i][j][0])
                    return url

    def getText(nodelist):
        rc = ""
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                rc = rc + node.data
        return rc

vr = vulnReferences()