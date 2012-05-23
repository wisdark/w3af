'''
sslCertificate.py

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
import socket
import select
import re
from OpenSSL import SSL, crypto
from datetime import date

try:
    from ndg.httpsclient.subj_alt_name import SubjectAltName
    from pyasn1.codec.der import decoder as der_decoder
    SUBJ_ALT_NAME_SUPPORT = True
except ImportError, e:
    SUBJ_ALT_NAME_SUPPORT = False

import core.controllers.outputManager as om
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
from core.controllers.w3afException import w3afException
from core.data.bloomfilter.bloomfilter import scalable_bloomfilter

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

class sslCertificate(baseAuditPlugin):
    '''
    Check the SSL certificate validity( if https is being used ).
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)
        self._already_tested_domains = scalable_bloomfilter()
        self._min_expire_days = 30

    def audit(self, freq):
        '''
        Get the cert and do some checks against it.

        @param freq: A fuzzableRequest
        '''
        url = freq.getURL()
        if 'HTTPS' != url.getProtocol().upper():
            return
        domain = url.getDomain()
        # We need to check certificate only once per host
        if domain in self._already_tested_domains:
            return
        # Create the connection
        socket_obj = socket.socket()
        try:
            socket_obj.connect((domain , url.getPort()))
            ctx = SSL.Context(SSL.SSLv23_METHOD)
            ssl_conn = SSL.Connection(ctx, socket_obj)
            # Go to client mode
            ssl_conn.set_connect_state()
            # If I don't send something here, the "get_peer_certificate"
            # method returns None. Don't ask me why!
            self.ssl_wrapper(ssl_conn, ssl_conn.send, ('GET / HTTP/1.1\r\n\r\n', ), {})
        except Exception, e:
            om.out.error('Error in audit.sslCertificate: "' + repr(e)  +'".')
            return
        # Get the cert
        cert = ssl_conn.get_peer_certificate()
        # Perform the analysis
        self._analyze_cert(cert, ssl_conn, domain)
        self._already_tested_domains.add(domain)
        # Print the SSL information to the log
        desc = 'This is the information about the SSL certificate used in the target site:\n'
        desc += self._dump_X509(cert)
        om.out.information(desc)
        i = info.info()
        i.setPluginName(self.getName())
        i.setName('SSL Certificate')
        i.setDesc(desc)
        kb.kb.append(self, 'certificate', i)

    def ssl_wrapper(self, ssl_obj, method, args, kwargs):
        '''
        This is a method that calls SSL functions, wrapping them around
        try/except and handling WantRead and WantWrite errors.
        '''
        while True:
            try:
                return apply( method, args, kwargs )
                break
            except SSL.WantReadError:
                select.select([ssl_obj],[],[],10.0)
            except SSL.WantWriteError:
                select.select([],[ssl_obj],[],10.0)

    def _analyze_cert(self, cert, ssl_conn, host):
        '''
        Analyze the cert.

        @parameter cert: The cert object from pyopenssl.
        @parameter ssl_conn: The SSL connection.
        @parameter host: target hostname.
        '''
        self._verify_expiration(cert, ssl_conn, host)
        self._verify_name(cert, ssl_conn, host)

    def _verify_expiration(self, cert, ssl_conn, host):
        server_digest_SHA1 = cert.digest('sha1')
        server_digest_MD5 = cert.digest('md5')
        # Check for expired
        if cert.has_expired():
            v = vuln.vuln()
            v.setPluginName(self.getName())
            v.setSeverity(severity.LOW)
            v.setName('Expired SSL certificate')
            v.setDesc('The certificate with MD5 digest: "' + server_digest_MD5 + '" has expired.')
            kb.kb.append(self, 'expired', v)
        # Check for soon expire
        valid_date = cert.get_notAfter()
        # valid_date is ASN1 GENERALIZEDTIME string
        # YYYYMMDDhhmmssZ
        expire_days = (date(int(valid_date[0:4]), int(valid_date[4:6]), 
            int(valid_date[6:8])) - date.today()).days
        if expire_days < self._min_expire_days:
            v = info.info()
            v.setPluginName(self.getName())
            v.setName('Expired SSL certificate')
            v.setDesc('The certificate with MD5 digest: "' + server_digest_MD5 + '" will expire soon.')
            kb.kb.append(self, 'soon_expire', v) 

    def _verify_alt_names(self, cert, ssl_conn, host):
        dns_names = []
        general_names = SubjectAltName()
        for i in range(cert.get_extension_count()):
            ext = cert.get_extension(i)
            if ext.get_short_name() == 'subjectAltName':
                ext_data = ext.get_data()
                decoded_data = der_decoder.decode(ext_data, asn1Spec=general_names)
                for name in decoded_data:
                    if isinstance(name, SubjectAltName):
                        for entry in range(len(name)):
                            component = name.getComponentByPosition(entry)
                            dns_names.append(str(component.getComponent()))
        if host in dns_names:
            return True
        return False

    def _verify_name(self, cert, ssl_conn, host):
        server_digest_SHA1 = cert.digest('sha1')
        server_digest_MD5 = cert.digest('md5')
        peer = cert.get_subject()
        issuer = cert.get_issuer()
        ciphers = ssl_conn.get_cipher_list()
        cn = str(peer.commonName)
        # Check that the certificate is self issued
        if peer == issuer:
            v = vuln.vuln()
            v.setSeverity(severity.LOW)
            v.setPluginName(self.getName())
            v.setName('Self issued SSL certificate')
            desc = 'The certificate is self issued'
            v.setDesc( desc )
            om.out.information(desc)
            kb.kb.append(self, 'si_cert', v)
        # hostname == subject/CN
        if host == cn:
            return
        # hostname is in subjectAltName/dNSName
        if SUBJ_ALT_NAME_SUPPORT\
                and self._verify_alt_names(cert, ssl_conn, host):
            return
        cert_invalid = True
        # Wildcard certificates
        # TODO Strange code...
        if re.match(r"\*", cn):
            wildcard_invalid = True
            # The leftmost component should start with '*.' and CountOf(*)==1
            if re.match (r"^\*\.", cn) and (cn.count('*') == 1):    
                # there should be three components (at least two dots)
                # but not ending with dot 
                if (cn.count('.') >= 2): # and not re.match (r"\.$",cn)):
                    wildcard_invalid = False
            if wildcard_invalid:
                v = vuln.vuln()
                v.setSeverity(severity.LOW)
                v.setPluginName(self.getName())
                v.setName('Potential wildcard SSL manipulation')
                desc = 'The certificate is not using wildcard(*) properly'
                desc += 'Certificate wildcard: '
                desc += cn
                v.setDesc(desc)
                kb.kb.append(self, 'version', v)
            else:
                tmpstr = cn
                tmpstr2 = tmpstr.replace("*","",1)
                tmphostregexp = tmpstr2.join("\$")
                if re.search(tmphostregexp, host):
                    cert_invalid = False
        if cert_invalid: 
            v = vuln.vuln()
            v.setPluginName(self.getName())
            v.setSeverity(severity.LOW)
            v.setName('Invalid name of the certificate')
            desc = 'The certificate presented by this website ('
            desc += host
            desc += ') was issued for a different website\'s address ('
            desc += cn + ')'
            v.setDesc(desc)
            om.out.information(desc)
            kb.kb.append(self, 'cn', v)

    def _dump_X509(self, cert):
        '''
        Dump X509
        '''
        res = ''
        res += "- Digest (SHA-1): " + cert.digest("sha1") +'\n'
        res += "- Digest (MD5): " + cert.digest("md5") +'\n'
        res += "- Serial#: " + str(cert.get_serial_number()) +'\n'
        res += "- Version: " + str(cert.get_version()) +'\n'

        expired = cert.has_expired() and "Yes" or "No"
        res += "- Expired: " + expired + '\n'
        res += "- Subject: " + str(cert.get_subject()) + '\n'
        res += "- Issuer: " + str(cert.get_issuer()) + '\n'

        # Dump public key
        pkey = cert.get_pubkey()
        typedict = {crypto.TYPE_RSA: "RSA", crypto.TYPE_DSA: "DSA"}
        res += "- PKey bits: " + str(pkey.bits()) +'\n'
        res += "- PKey type: %s (%d)" % (typedict.get(pkey.type(), "Unknown"), pkey.type()) +'\n'

        res += '- Certificate dump: \n' + crypto.dump_certificate(crypto.FILETYPE_PEM, cert)

        # Indent
        res = res.replace('\n', '\n    ')
        res = '    ' + res
        return res

    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Set minimal amount of days before expiration of the certificate for alerting'
        h1 = 'If the certificate will expire in period of minExpireDays w3af will show alert about it'
        o1 = option('minExpireDays', self._min_expire_days, d1, 'integer', help=h1)
        ol = optionList()
        ol.add(o1)
        return ol

    def setOptions(self, optionsMap):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().

        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        '''
        self._min_expire_days = optionsMap['minExpireDays'].getValue()

    def getPluginDeps(self):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return []

    def getLongDesc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin audits SSL certificate parameters.
        
        One configurable parameter exists:
            - minExpireDays
         
        Note: It's only usefull when testing HTTPS sites.
        '''
