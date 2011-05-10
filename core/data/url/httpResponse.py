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
    return (unicode(slash_x_XX) , exc.end)

codecs.register_error("returnEscapedChar", _returnEscapedChar)


DEFAULT_CHARSET = 'utf-8'
CR = '\r'
LF = '\n'
CRLF = CR + LF
SP = ' '

class httpResponse(object):

    def __init__(self, code, read, info, geturl, original_url,
                 msg='OK', id=None, time=0.2, alias=None, charset=None):
        '''
        @parameter time: The time between the request and the response.
        '''
        if not isinstance(geturl, url_object):
            raise TypeError('The geturl.__init__() parameter of a httpResponse'
                            ' object must be of urlParser.url_object type.')

        if not isinstance(original_url, url_object):
            raise TypeError('The original_url.__init__() parameter of a '
                'httpResponse object must be of urlParser.url_object type.')
        
        self._charset = charset
        self._content_type = ''
        self._dom = None
        self._clear_text_body = None
        
        # Set the URL variables
        # The URL that we really GET'ed
        self._realurl = original_url.uri2url()
        self._uri = original_url
        # Set the info
        self._info = info
        # The URL where we were redirected to (equal to original_url when no redirect)
        self._redirectedURL = geturl
        self._redirectedURI = geturl.uri2url()
        
        # Set the rest
        self.setCode(code)

        # Save the type for fast access, so I don't need to calculate the type each time
        # someone calls the "is_text_or_html" method. This attributes are set in the
        # setHeaders() method.
        self._is_text_or_html_response = False
        self._is_swf_response = False
        self._is_pdf_response = False
        self._is_image_response = False
        self.setHeaders(info)
        
        self.setBody(read)
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
        return string_to_test in self._body
    
    def __repr__(self):
        res = '< httpResponse | %s | %s ' % (self.getCode() , self.getURL())

        # extra info
        if self.id is not None:
            res += ' | id:' + str(self.id)

        if self._fromCache != False:
            res += ' | fromCache:True'

        # aaaand close...
        res += ' >'
        return res
    
    def getId(self):
        return self.id
    
    def getRedirURL(self):
        return self._redirectedURL
    
    def getRedirURI(self):
        return self._redirectedURI
    
    def getCode(self):
        return self._code
    
    def getAlias(self):
        return self._alias
    
    def getBody(self):
        return self._body
    
    def info(self):
        return self._info

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
                self._dom = etree.fromstring(self._body, parser)
            except Exception:
                msg = 'The HTTP body for "%s" could NOT be ' \
                'parsed by libxml2.' % self.getURL()
                om.out.debug(msg)
        return self._dom
    
    def getNormalizedBody(self):
        '''
        @return: A normalized body *string* representation.
        '''
        dom = self.getDOM()
        if dom:
            dom = etree.tostring(dom, encoding=unicode,
                                 method='html', xml_declaration=False)
        return dom or ''
    
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
        
    def getURL(self):
        return self._realurl

    def getURI(self):
        return self._uri
    
    def getWaitTime(self):
        return self._time
    
    def getMsg(self):
        return self._msg
    
    def getCharset(self):
        return self._charset
    
    def setRedirURL(self, ru):
        self._redirectedURL = ru
    
    def setRedirURI(self, ru):
        self._redirectedURI = ru
    
    def setCode(self, code):
        self._code = code
    
    def setBody(self, body):
        '''
        This method decodes the body based on the header(or metadata) encoding
        and afterwards, it creates the necesary metadata to speed up string
        searches inside the body string.

        @body: A string that represents the body of the HTTP response
        '''
        # Sets self's `_body` and `_charset` attributes 
        self._charset_handling(body)
        
        if type(self._body) is str:
            print

    def _charset_handling(self, body):
        '''
        This method decodes the body based on the header(or metadata) encoding.
        
        This is one of the most important methods, because it will decode any
        string (usually HTTP response body contents) and return a unicode
        object. If `body` is unicode this method will only figure out the
        right encoding; it won't try to decode anything.         

        @body: A <unicode> or <str> object that represents the body of the
            HTTP response
        '''
        # A sample header just to remember how they look like:
        # "content-type: text/html; charset=iso-8859-1"
        lowerCaseHeaders = self.getLowerCaseHeaders()
        
        if not 'content-type' in lowerCaseHeaders:
            om.out.debug('hmmm... wtf?! The remote web server failed to send '
                         'the content-type header.')
            self._body = body
            self._charset = self._charset or DEFAULT_CHARSET
        
        elif not self.is_text_or_html():
            # Not text, save as it is.
##            self._body = body
            self._body = u''
            self._charset = self._charset or DEFAULT_CHARSET
        else:
            # According to the web server, the body content is text, html,
            # xml or something similar
            
            ## Figure out charset to work with ##
            charset = self._charset
            
            if not charset:
                            
                # Start with the headers
                charset_mo = re.search('charset=\s*?([\w-]+)',
                                        lowerCaseHeaders['content-type'])
                if charset_mo:
                    # Seems like the response's headers contain a charset
                    charset = charset_mo.groups()[0].lower().strip()
                else:
                    # Continue with the body's meta tag. Sth like this:
                    # <meta http-equiv="Content-Type" content="text/html; 
                    # charset=utf-8">
                    charset_mo = re.search(
                            '<meta.*?content=".*?charset=\s*?([\w-]+)".*?>',
                            body, re.IGNORECASE)
                    if charset_mo:
                        charset = charset_mo.groups()[0].lower().strip()
                    else:
                        try:
                            # TODO: Play here with chardet
                            raise Exception
                        except:
                            charset = DEFAULT_CHARSET

            # Only try to decode <string> objects
            if type(body) is str:

                # Now that we have the charset, we use it! (and save it)
                # The return value of the decode function is a unicode obj.
                try:
                    body = body.decode(charset, 'returnEscapedChar')
                except LookupError:
                    # warn about a buggy charset
                    msg = ('Charset LookupError: unknown charset: %s; '
                        'ignored and set to default: %s' % 
                        (charset, self._charset))
                    om.out.debug(msg)
                    
                    # Use the default
                    charset = DEFAULT_CHARSET
                    body = body.decode(charset, 'returnEscapedChar')
           
            self._body = body
            # Overwrite charset
            self._charset = charset

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
            
    def setURL(self, url):
        '''
        >>> u = url_object('http://www.google.com')
        >>> r = httpResponse(200, '' , {}, u, u)
        >>> r.setURL('http://www.google.com/')
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        ValueError: The URL of a httpResponse object must be of urlParser.url_object type.
        >>> u = url_object('http://www.google.com')
        >>> r = httpResponse(200, '' , {}, u, u)
        >>> r.setURL( url_object('http://www.google.com/') )
        '''
        if not isinstance(url, url_object):
            raise ValueError('The URL of a httpResponse object must be of '
                             'urlParser.url_object type.')
        
        self._realurl = url.uri2url()
    
    def setURI(self, uri):
        '''
        >>> u = url_object('http://www.google.com')
        >>> r = httpResponse(200, '' , {}, u, u)
        >>> r.setURI('http://www.google.com/')
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        ValueError: The URI of a httpResponse object must be of urlParser.url_object type.
        >>> u = url_object('http://www.google.com')
        >>> r = httpResponse(200, '' , {}, u, u)
        >>> r.setURI( url_object('http://www.google.com/') )
        '''
        if not isinstance(uri, url_object):
            raise ValueError('The URI of a httpResponse object must be of '
                             'urlParser.url_object type.')
        
        self._uri = uri
        self._realurl = uri.uri2url()
        
    def setWaitTime(self, t):
        self._time = t

    def getFromCache(self):
        '''
        @return: True if this response was obtained from the local cache.
        '''
        return self._fromCache
        
    def setFromCache(self, fcache):
        '''
        @parameter fcache: True if this response was obtained from the local cache.
        '''
        self._fromCache = fcache

    def getStatusLine(self):
        '''Return status-line of response.'''
        return 'HTTP/1.1' + SP + str(self._code) + SP + self._msg + CRLF

    def dumpResponseHead(self):
        '''
        @return: A string with:
            HTTP/1.1 /login.html 200
            Header1: Value1
            Header2: Value2
        '''
        return "%s%s" % (self.getStatusLine(), self.dumpHeaders())

    def dump(self):
        '''
        Return a DETAILED str representation of this HTTP response object.
        '''
        return "%s%s%s" % (self.dumpResponseHead(), CRLF, self.getBody())
        
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
