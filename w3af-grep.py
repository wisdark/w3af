import core.controllers.w3afCore
from core.data.url.httpResponse import httpResponse
from core.data.request.fuzzableRequest import fuzzableRequest
from core.controllers.coreHelpers.fingerprint_404 import is_404
import cProfile

#
#   Init
#
spam = httpResponse(200, '', {}, 'http://localhost:631/', 'http://localhost:631/')
try:
    spam = httpResponse(200, '', {}, 'http://localhost:631/', 'http://localhost:631/')
    is_404(spam)
except:
    pass

_w3af = core.controllers.w3afCore.w3afCore()
plugins = []
for pname in _w3af.getPluginList('grep'):
    plugins.append( _w3af.getPluginInstance(pname, 'grep') )

#
#   To be profiled
#
def profile_me():
    #for foo in xrange(10):
        for counter in xrange(1,5):
            body = file('test-' + str(counter) + '.html').read()
            response = httpResponse(200, body, {'Content-Type': 'text/html'}, 'http://localhost:631/' + str(counter), 'http://localhost:631/' + str(counter))

            request = fuzzableRequest()

            for pinst in plugins:
                pinst.grep( request, response )

cProfile.run('profile_me()', 'output.stats')
#profile_me()

