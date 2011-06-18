'''
httpResponse.py

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


import copy
import re
import httplib
from lxml import etree

import core.controllers.outputManager as om
from core.data.parsers.urlParser import url_object

# Handle codecs
import codecs
def _returnEscapedChar(exc):
    slash_x_XX = repr(exc.object[exc.start:exc.end])[1:-1]
    return (unicode(slash_x_XX), exc.end)

codecs.register_error("returnEscapedChar", _returnEscapedChar)


DEFAULT_CHARSET = 'utf-8'
CR = '\r'
LF = '\n'
CRLF = CR + LF
SP = ' '


def from_httplib_resp(httplibresp, original_url=None):
    '''
    Factory function. Build a httpResponse object from a httplib.HTTPResponse
    instance
    
    @param httplibresp: httplib.HTTPResponse instance
    @param original_url: Optional 'url_object' instance.
    
    @return: A httpResponse instance
    '''
    resp = httplibresp
    code, msg, hdrs, url_inst, body = (resp.code, resp.msg, resp.info(),
                                       url_object(resp.geturl()), resp.read())
    original_url = original_url or url_inst
    
    charset = getattr(httplibresp, 'encoding', None)
    return httpResponse(code, body, hdrs, url_inst,
                        original_url, msg, charset=charset)


class httpResponse(object):

    def __init__(self, code, read, info, geturl, original_url,
                 msg='OK', id=None, time=0.2, alias=None, charset=None):
        '''
        @param code: 
        @param read: 
        @param info: 
        @param geturl: url_object instance
        @param original_url: url_object instance
        @param msg:
        @param id:  
        @parameter time: The time between the request and the response.
        @param alias: 
        @param charset: 
        '''
        self._charset = charset
        self._body = None
        self._raw_body = read
        self._content_type = ''
        self._dom = None
        self._clear_text_body = None
        
        # Set the URL variables
        # The URL that we really GET'ed
        self._realurl = original_url.uri2url()
        self._uri = original_url
        # Set the info
        self._info = info
        # The URL where we were redirected to (equal to original_url when
        # no redirect)
        self._redirectedURL = geturl
        self._redirectedURI = geturl.uri2url()
        
        # Set the rest
        self.setCode(code)

        # Save the type for fast access, so I don't need to calculate the type
        # each time someone calls the "is_text_or_html" method. This attributes
        # are set in the setHeaders() method.
        self._is_text_or_html_response = False
        self._is_swf_response = False
        self._is_pdf_response = False
        self._is_image_response = False
        self.setHeaders(info)
        
        self._msg = msg
        self._time = time
        self._alias = alias
        
        # A unique id identifier for the response
        self.id = id
        # Defaults to False
        self._fromCache = False
    
    def __contains__(self, string_to_test):
        '''
        Determine if the `string_to_test` is contained by the HTTP response
        body.

        @param string_to_test: String to look for in the body  
        '''
        return string_to_test in self.body
    
    def __repr__(self):

        vals = {'code': self.getCode(),
                'url': str(self.getURL()),
                'id': self.id and ' | id:%s' % self.id or '',
                'fcache': self._fromCache and ' | fromCache:True' or ''}
        return '<httpResponse | %(code)s | %(url)s%(id)s%(fcache)s>' % vals
    
    def setId(self, id):
        self.id = id
    
    def getId(self):
        return self.id

    def setCode(self, code):
        self._code = code
    
    def getCode(self):
        return self._code

    @property
    def body(self):
        if self._body is None:
            self._body, self._charset = self._charset_handling()
            # Free 'raw_body'
            self._raw_body = None
        return self._body
    
    @body.setter
    def body(self, body):
        # Reset body
        self._body = None
        self._raw_body = body
    
    def setBody(self, body):
        '''
        Setter for body.

        @body: A string that represents the body of the HTTP response
        '''
        self.body = body
    
    def getBody(self):
        return self.body

    def getClearTextBody(self):
        '''
        @return: A clear text representation of the HTTP response body. 
        '''
        if self._clear_text_body is not None:
            # We already calculated this, we can return it now.
            return self._clear_text_body
        else:
            # Calculate the clear text body
            dom = self.getDOM()
            
            if not dom:
                # return None if we don't have a DOM
                return None
            else:
                ff = lambda ele: '\n' if (ele.tag == 'br') else (ele.text or '')
                self._clear_text_body = ''.join(map(ff, dom.getiterator()))
                return self._clear_text_body

    def getNormalizedBody(self):
        '''
        @return: A normalized *unicode* representation of the body.
        '''
        dom = self.getDOM()
        if dom:
            return etree.tostring(dom, encoding=unicode,
                                  method='html', xml_declaration=False)
        return u''

    def getDOM(self):
        '''
        I don't want to calculate the DOM for all responses, only for those
        which are needed. This method will first calculate the DOM, and then
        save it for upcoming calls.
        
        @return: The DOM, or None if the HTML normalization failed.
        '''
        if self._dom is None:
            try:
                parser = etree.HTMLParser(recover=True)
                self._dom = etree.fromstring(self.body, parser)
            except Exception:
                msg = ('The HTTP body for "%s" could NOT be parsed by '
                       'libxml2.' % self.getURL())
                om.out.debug(msg)
        return self._dom
    
    @property
    def charset(self):
        if not self._charset:
            self._body, self._charset = self._charset_handling()
            # Free 'raw_body'
            self._raw_body = None
        return self._charset
    
    @charset.setter
    def charset(self, charset):
        self._charset = charset
    
    def setCharset(self, charset):
        self.charset = charset
    
    def getCharset(self):
        return self.charset
    
    def setRedirURL(self, ru):
        self._redirectedURL = ru
    
    def getRedirURL(self):
        return self._redirectedURL

    def setRedirURI(self, ru):
        self._redirectedURI = ru
    
    def getRedirURI(self):
        return self._redirectedURI

    def setHeaders(self, headers):
        '''
        Sets the headers and also analyzes them in order to get the response
        mime type (text/html , application/pdf, etc).

        @parameter headers: The headers dict.
        '''
        # Fix lowercase in header names from HTTPMessage
        if isinstance(headers, httplib.HTTPMessage):
            self._headers = {}
            for header in headers.headers:
                key, value = header.split(':', 1)
                self._headers[key.strip()] = value.strip()
        else:
            self._headers = headers

        #   Set the type, for easy access.
        for key in headers.keys():
            if 'content-type' == key.lower():
                # we need exactly content type but not charset
                self._content_type = headers[key].split(';', 1)[0]
                
                # Text or HTML?
                magic_words = ('text', 'html', 'xml', 'txt', 'javascript')
                for mw in magic_words:
                    if self._content_type.lower().count(mw):
                        self._is_text_or_html_response = True
                        return

                # PDF?
                if self._content_type.lower().count('pdf'):
                    self._is_pdf_response = True
                
                # SWF?
                if self._content_type.lower().count('x-shockwave-flash'):
                    self._is_swf_response = True

                # Image?
                if self._content_type.lower().count('image'):
                    self._is_image_response = True
    
    def getHeaders(self):
        return self._headers

    def getLowerCaseHeaders(self):
        '''
        If the original headers were:
            'Abc-Def: f00N3s'
        This will return:
            'abc-def: f00N3s'
        
        The only thing that changes is the header name.
        '''
        return dict((k.lower(), v) for k, v in self._headers.iteritems())

    def setURL(self, url):
        '''
        >>> url = url_object('http://www.google.com')
        >>> r = httpResponse(200, '' , {}, url, url)
        >>> r.setURL('http://www.google.com/')
        Traceback (most recent call last):
          ...
        TypeError: The URL of a httpResponse object must be of urlParser.url_object type.
        >>> r.setURL(url)
        >>> r.getURL() == url
        True
        '''
        if not isinstance(url, url_object):
            raise TypeError('The URL of a httpResponse object must be of '
                             'urlParser.url_object type.')
        
        self._realurl = url.uri2url()
        
    def getURL(self):
        return self._realurl

    def setURI(self, uri):
        '''
        >>> uri = url_object('http://www.google.com/')
        >>> r = httpResponse(200, '' , {}, uri, uri)
        >>> r.setURI('http://www.google.com/')
        Traceback (most recent call last):
          ...
        TypeError: The URI of a httpResponse object must be of urlParser.url_object type.
        >>> r.setURI(uri)
        >>> r.getURI() == uri
        True
        '''
        if not isinstance(uri, url_object):
            raise TypeError('The URI of a httpResponse object must be of '
                             'urlParser.url_object type.')
        
        self._uri = uri
        self._realurl = uri.uri2url()

    def getURI(self):
        return self._uri

    def setFromCache(self, fcache):
        '''
        @parameter fcache: True if this response was obtained from the
        local cache.
        '''
        self._fromCache = fcache
    
    def getFromCache(self):
        '''
        @return: True if this response was obtained from the local cache.
        '''
        return self._fromCache

    def setWaitTime(self, t):
        self._time = t
    
    def getWaitTime(self):
        return self._time

    def setAlias(self, alias):
        self._alias = alias
        
    def getAlias(self):
        return self._alias

    def info(self):
        return self._info

    def getStatusLine(self):
        '''Return status-line of response.'''
        return 'HTTP/1.1' + SP + str(self._code) + SP + self._msg + CRLF
    
    def getMsg(self):
        return self._msg
    
    def _charset_handling(self):
        '''
        Decode the body based on the header (or metadata) encoding.
        The implemented algorithm follows the logic used by FF:

            1) First try to find a charset using the following search criteria:
                a) Look in the 'content-type' HTTP header. Example:
                    content-type: text/html; charset=iso-8859-1
                b) Look in the 'meta' HTML header. Example:
                    <meta .* content="text/html; charset=utf-8" />
                c) Determine the charset using the chardet module
                d) Use the DEFAULT_CHARSET
            
            2) Try to decode the body using the found charset. If it fails,
            then force it to use the DEFAULT_CHARSET
        
        Finally return the unicode (decoded) body and the used charset.  
        
        Note: If the body is already a unicode string return it as it is.
        '''
        lowerCaseHeaders = self.getLowerCaseHeaders()
        charset = self._charset
        rawbody = self._raw_body
        
        # Only try to decode <str> strings. Skip <unicode> strings
        if type(rawbody) is unicode:
            _body = rawbody
            assert charset is not None, ("httpResponse objects containing "
                             "unicode body must have an associated charset")
        
        elif not 'content-type' in lowerCaseHeaders:
            om.out.debug('hmmm... wtf?! The remote web server failed to send '
                         'the content-type header.')
            _body = rawbody
            charset = charset or DEFAULT_CHARSET
        
        elif not self.is_text_or_html():
            # Not text, save as it is.
            _body = rawbody
            charset = charset or DEFAULT_CHARSET
        else:
            # According to the web server, the body content is text, html,
            # xml or something similar
            
            # Figure out charset to work with
            if not charset:
                # Start with the headers
                charset_mo = re.search('charset=\s*?([\w-]+)',
                                        lowerCaseHeaders['content-type'])
                if charset_mo:
                    # Seems like the response's headers contain a charset
                    charset = charset_mo.groups()[0].lower().strip()
                else:
                    # Continue with the body's meta tag
                    charset_mo = re.search(
                            '<meta.*?content=".*?charset=\s*?([\w-]+)".*?>',
                            rawbody, re.IGNORECASE)
                    if charset_mo:
                        charset = charset_mo.groups()[0].lower().strip()
                    else:
                        try:
                            # TODO: Play here with chardet
                            raise Exception
                        except:
                            charset = DEFAULT_CHARSET


            # Now that we have the charset, we use it!
            # The return value of the decode function is a unicode string.
            try:
                _body = rawbody.decode(charset, 'returnEscapedChar')
            except LookupError:
                # Warn about a buggy charset
                msg = ('Charset LookupError: unknown charset: %s; '
                    'ignored and set to default: %s' % 
                    (charset, self._charset))
                om.out.debug(msg)
                # Forcing it to use the default
                charset = DEFAULT_CHARSET
                _body = rawbody.decode(charset, 'returnEscapedChar')
            
        return _body, charset

    def getContentType(self):
        '''
        @return: The content type of the response
        '''
        return self._content_type

    def is_text_or_html(self):
        '''
        @return: True if this response is text or html
        '''
        return self._is_text_or_html_response
    
    def is_pdf(self):
        '''
        @return: True if this response is a PDF file
        '''
        return self._is_pdf_response
    
    def is_swf(self):
        '''
        @return: True if this response is a SWF file
        '''
        return self._is_swf_response

    def is_image(self):
        '''
        @return: True if this response is an image file
        '''
        return self._is_image_response
            
    def dumpResponseHead(self):
        '''
        @return: A string with:
            HTTP/1.1 /login.html 200
            Header1: Value1
            Header2: Value2
        '''
        dump_head = "%s%s" % (self.getStatusLine(), self.dumpHeaders())
        return dump_head.encode(self.charset)

    def dump(self):
        '''
        Return a DETAILED str representation of this HTTP response object.
        '''
        if not self._is_text_or_html_response:
            body = '<BINARY DATA>'
        else:
            body = self.body.encode(self.charset)
        return "%s%s%s" % (self.dumpResponseHead(), CRLF, body)
        
    def dumpHeaders(self):
        '''
        @return: a str representation of the headers.
        '''
        if self._headers:
            return CRLF.join(h + ': ' + hv  for h, hv in self._headers.items())
        else:
            return ''
        
    def copy(self):
        return copy.deepcopy(self)
