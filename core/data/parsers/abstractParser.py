# -*- coding: UTF-8 -*-
'''
abstractParser.py

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

import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException

from core.data.parsers.encode_decode import htmldecode
from core.data.parsers.urlParser import url_object


import re
import urllib


class abstractParser(object):
    '''
    This class is an abstract document parser.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, httpResponse):
        # "setBaseUrl"
        url = httpResponse.getURL()
        redirURL = httpResponse.getRedirURL()
        if redirURL:
            url = redirURL
        
        self._baseUrl = url
        self._baseDomain = url.getDomain()
        self._rootDomain = url.getRootDomain()
        
        # A nice default. Children will typically override it
        self._encoding = 'utf-8'
        
        # To store results
        self._emails = []
        self._re_URLs = []
    
    def findEmails(self, doc_body):
        '''
        @return: A list with all mail users that are present in the doc_body.

        Init,
        >>> from core.data.url.httpResponse import httpResponse as httpResponse
        >>> u = url_object('http://www.w3af.com/')
        >>> response = httpResponse(200, '', {}, u, u)
        >>> a = abstractParser(response)
        
        First test, no emails.
        >>> a.findEmails('')
        []
        
        >>> a = abstractParser(response)
        >>> a.findEmails('abc@w3af.com')
        ['abc@w3af.com']
        
        >>> a = abstractParser(response)
        >>> a.findEmails('<a href="mailto:abc@w3af.com">test</a>')
        ['abc@w3af.com']

        >>> a = abstractParser(response)
        >>> a.findEmails('<a href="mailto:abc@w3af.com">abc@w3af.com</a>')
        ['abc@w3af.com']

        >>> a = abstractParser(response)
        >>> a.findEmails('<a href="mailto:abc@w3af.com">abc_def@w3af.com</a>')
        ['abc@w3af.com', 'abc_def@w3af.com']

        >>> a = abstractParser(response)
        >>> a.findEmails('header abc@w3af-scanner.com footer')
        ['abc@w3af-scanner.com']
        
        >>> a = abstractParser(response)
        >>> a.findEmails('header abc4def@w3af.com footer')
        ['abc4def@w3af.com']
        '''
        # First, we decode all chars. I have found some strange sites where 
        # they encode the @... some other sites where they encode the email,
        # or add some %20 padding... strange stuff... so better be safe...
        enc = self._encoding
        doc_body = urllib.unquote_plus(doc_body.encode(enc))
        
        # Now we decode the HTML special characters...
        doc_body = htmldecode(doc_body).decode(enc)
        
        # Perform a fast search for the @. In w3af, if we don't have an @ we
        # don't have an email
        # We don't support mails like myself <at> gmail !dot! com
        if doc_body.find('@') != -1:
            doc_body = re.sub('[^\w@\-\\.]', ' ', doc_body)

            # NOTE: emailRegex is also used in pks search engine.
            # Now we have a clean doc_body; and we can match the mail addresses!
            emailRegex = '([A-Z0-9\._%-]{1,45}@([A-Z0-9\.-]{1,45}\.){1,10}[A-Z]{2,4})'
            for email, domain in re.findall(emailRegex, doc_body, re.IGNORECASE):
                if email not in self._emails:
                    self._emails.append(email)
                    
        return self._emails

    def _regex_url_parse(self, httpResponse):
        '''
        Use regular expressions to find new URLs.
        
        @parameter httpResponse: The http response object that stores the response body and the URL.
        @return: None. The findings are stored in self._re_URLs as url_objects

        Init,
        >>> from core.data.url.httpResponse import httpResponse as httpResponse
        >>> u = url_object('http://www.w3af.com/')
        >>> response = httpResponse( 200, '', {}, u, u )
        >>> a = abstractParser(response)
        
        Simple, empty result
        >>> a = abstractParser(response)
        >>> response = httpResponse( 200, '', {}, u, u )
        >>> a._regex_url_parse( response )
        >>> a._re_URLs
        []

        Full URL
        >>> a = abstractParser(response)
        >>> response = httpResponse( 200, 'header http://www.w3af.com/foo/bar/index.html footer', {}, u, u )
        >>> a._regex_url_parse( response )
        >>> a._re_URLs[0].url_string
        'http://www.w3af.com/foo/bar/index.html'

        One relative URL
        >>> a = abstractParser(response)
        >>> response = httpResponse( 200, 'header /foo/bar/index.html footer', {}, u, u )
        >>> a._regex_url_parse( response )
        >>> a._re_URLs[0].url_string
        'http://www.w3af.com/foo/bar/index.html'

        Relative with initial "/" , inside an href
        >>> a = abstractParser(response)
        >>> response = httpResponse( 200, 'header <a href="/foo/bar/index.html">foo</a> footer', {}, u, u )
        >>> a._regex_url_parse( response )
        >>> a._re_URLs[0].url_string
        'http://www.w3af.com/foo/bar/index.html'

        Simple index relative URL
        >>> a = abstractParser(response)
        >>> response = httpResponse( 200, 'header <a href="index">foo</a> footer', {}, u, u )
        >>> a._regex_url_parse( response )
        >>> len( a._re_URLs )
        0
        '''
        re_urls = self._re_URLs
        resp_body = httpResponse.getBody()
        #url_regex = '((http|https):[A-Za-z0-9/](([A-Za-z0-9$_.+!*(),;/?:@&~=-])|%[A-Fa-f0-9]{2})+(#([a-zA-Z0-9][a-zA-Z0-9$_.+!*(),;/?:@&~=%-]*))?)'
        url_regex = '((http|https)://([a-zA-Z0-9_:@\-\./]*?)/[^ \n\r\t"\'<>]*)'
        
        for url in re.findall(url_regex, resp_body):
            # This try is here because the _decode_URL method raises an exception
            # whenever it fails to decode a url.
            try:
                decoded_url = self._decode_URL(url_object(url[0]))
            except w3afException:
                pass
            else:
                re_urls.append(decoded_url)
        
        #
        # Now detect some relative URL's (also using regexs)
        #
        def find_relative(doc):
            res = []
            
            # TODO: Also matches //foo/bar.txt and http://host.tld/foo/bar.txt
            # I'm removing those matches manually below
            regex = '((:?[/]{1,2}[A-Z0-9a-z%_\-~\.]+)+\.[A-Za-z0-9]{2,4}(((\?)([a-zA-Z0-9]*=\w*)){1}((&)([a-zA-Z0-9]*=\w*))*)?)'
            relative_regex = re.compile(regex)
            
            for match_tuple in relative_regex.findall(doc):
                
                match_str = match_tuple[0]
                
                # And now I filter out some of the common false positives
                if match_str.startswith('//') or \
                    match_str.startswith('://') or \
                    re.match('HTTP/\d\.\d', match_str) or \
                    re.match('.*?/\d\.\d\.\d', match_str): # Matches
                    #"PHP/5.2.4-2ubuntu5.7", "Apache/2.2.8", "mod_python/3.3.1"
                    continue
                
                url = httpResponse.getURL().urlJoin(match_str)
                url = self._decode_URL(url)
                res.append(url)
            
            return res
        
        re_urls.extend(find_relative(resp_body))
        
        # Finally normalize the urls
        map(lambda u: u.normalizeURL(), re_urls)
        
        self._re_URLs = list(set(re_urls)) 

    def getEmails(self, domain=None):
        '''
        @parameter domain: Indicates what email addresses I want to retrieve:   "*@domain".
        @return: A list of email accounts that are inside the document.
        
        >>> from core.data.url.httpResponse import httpResponse as httpResponse
        >>> u = url_object('http://www.w3af.com/')
        >>> response = httpResponse( 200, '', {}, u, u )
        >>> a = abstractParser(response)
        >>> a._emails = ['a@w3af.com', 'foo@not-w3af.com']
        
        >>> a.getEmails()
        ['a@w3af.com', 'foo@not-w3af.com']

        >>> a.getEmails( domain='w3af.com')
        ['a@w3af.com']

        >>> a.getEmails( domain='not-w3af.com')
        ['foo@not-w3af.com']
                
        '''
        if domain:
            return [i for i in self._emails if domain == i.split('@')[1]]
        else:
            return self._emails
            
    def getForms(self):
        '''
        @return: A list of forms.
        '''        
        raise NotImplementedError('You should create your own parser class '
                                  'and implement the getForms() method.')
        
    def getReferences(self):
        '''
        Searches for references on a page. w3af searches references in every html tag, including:
            - a
            - forms
            - images
            - frames
            - etc.
        
        @return: Two sets, one with the parsed URLs, and one with the URLs that came out of a
        regular expression. The second list if less trustworthy.
        '''
        raise NotImplementedError('You should create your own parser class and'
                                  ' implement the getReferences() method.')
        
    def getComments(self):
        '''
        @return: A list of comments.
        '''        
        raise NotImplementedError('You should create your own parser class and '
                                  'implement the getComments() method.')
    
    def getScripts(self):
        '''
        @return: A list of scripts (like javascript).
        '''        
        raise NotImplementedError('You should create your own parser class and'
                                  ' implement the getScripts() method.')
        
    def getMetaRedir(self):
        '''
        @return: Returns list of meta redirections.
        '''
        raise NotImplementedError('You should create your own parser class and'
                                  ' implement the getMetaRedir() method.')
    
    def getMetaTags(self):
        '''
        @return: Returns list of all meta tags.
        '''
        raise NotImplementedError('You should create your own parser class and'
                                  ' implement the getMetaTags() method.')
        
    def _decode_URL(self, url_object_to_decode):
        '''
        Decode `url_object_to_decode`'s url using urllib's url-unquote
        algorithm. If the url is unicode it will preserve the type as well as
        for strings.
        
        See http://www.blooberry.com/indexdot/html/topics/urlencoding.htm for
        more info on urlencoding.
        
        So, when _decode_URL() is called and take as input 
        u'http://host.tld/%05%44', it is encoded using the instance's _encoding
        then it is applied the unquote routine and finally is decoded back to
        unicode being u'http://host.tld/é' the final result.
        
        Something small to remember:
        >>> urllib.unquote('ind%c3%a9x.html').decode('utf-8').encode('utf-8') \
        == 'ind\xc3\xa9x.html'
        True
        
        Init,
        >>> from core.data.url.httpResponse import httpResponse as httpResponse
        >>> u = url_object('http://www.w3af.com/')
        >>> response = httpResponse( 200, '', {}, u, u )
        >>> a = abstractParser(response)

        Simple, no strange encoding
        >>> u = url_object('http://www.w3af.com/index.html')
        >>> print a._decode_URL( u ).url_string
        http://www.w3af.com/index.html

        Encoded
        >>> u = url_object('http://www.w3af.com/ind%c3%a9x.html')
        >>> print a._decode_URL( u ).url_string
        http://www.w3af.com/indéx.html

        Wrong parameter
        >>> print a._decode_URL( 'http://www.w3af.com/' )
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        ValueError: The "url_object_to_decode" parameter @ _decode_URL of an abstractParser must be of urlParser.url_object type.

        '''
        if not isinstance(url_object_to_decode, url_object):
            msg = ('The "url_object_to_decode" parameter @ _decode_URL of an '
                   'abstractParser must be of urlParser.url_object type.')
            raise ValueError(msg)
        
        url_string = url_object_to_decode.url_string
        enc = self._encoding
        is_unicode = False

        if type(url_string) is unicode:
            is_unicode = True
            url_string = url_string.encode(enc)
                
        urldecoded = urllib.unquote(url_string)   
        
        if is_unicode:
            # Take it back to unicode
            urldecoded = urldecoded.decode(enc)
        
        return url_object(urldecoded)
