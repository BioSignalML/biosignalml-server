######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id$
#
######################################################

"""A web.py application powered by Tornado"""

import os
import urllib
import logging

import tornado.httpserver
import tornado.websocket
import tornado.wsgi
import tornado.web
import tornado.options as options

## import tornado.auth     ## FUTURE
## import rpdb2; rpdb2.start_embedded_debugger('test')

from biosignalml.formats import BSMLRecording


import server
server.init_server()  # Setup globals

import endpoints.webstream as webstream
import endpoints.metadata  as metadata
import endpoints.resource  as resource
import endpoints.sparql    as sparql

import frontend
import frontend.user
import frontend.forms
import frontend.sparql
import frontend.search
import frontend.htmlview


class ContentNegotiate(tornado.web.RequestHandler):
#==================================================

  def __new__(cls, *args, **kwds):
  #-------------------------------
    request = args[1]
    if request.method == 'GET': accept = resource.parse_accept(request.headers)
    else:                       accept = { request.headers.get('Content-Type', ''): 1 }

    if request.headers.get('Upgrade') == 'websocket':
      HandlerClass = webstream.StreamDataSocket

    elif len(accept) == 1 and list(accept.keys())[0].startswith(BSMLRecording.MIMETYPE):
      HandlerClass = resource.Recording

    elif (accept.get('application/rdf+xml', 0) > 0.9
     or accept.get('text/turtle', 0) == 1):
      HandlerClass = metadata.MetaData

    elif (accept.get('text/html', 0) == 1
     or accept.get('application/xhtml+xml', 0) == 1
     or accept.get('application/x-www-form-urlencoded', 0) == 1
     or len(accept) == 1 and accept.get('*/*', 0) == 1):
      HandlerClass = frontend.htmlview.Repository

    else:
      HandlerClass = metadata.MetaData  ## Maybe this case should be to an error page ???

    handler = HandlerClass(*args, **kwds)
  
    if request.path in ['', '/']: handler.full_uri = ''
    else: handler.full_uri = '%s://%s%s' % (request.protocol, request.host, urllib.parse.unquote(request.path))
    ##logging.debug("Negotiate: %s --> %s (%s)", accept, handler, handler.full_uri)
    if len(accept) > 1: handler.set_header('Vary', 'Accept') # Let caches know we've used Accept header

    return handler


application = tornado.web.Application([
    ('/sparql/update/',                   sparql.SparqlUpdate),        # SPARQL endpoint
    ('/sparql/graph/',                    sparql.SparqlGraph),         # SPARQL endpoint
    ('/sparql/',                          sparql.SparqlQuery),         # SPARQL endpoint

    ('/frontend/metadata',                frontend.htmlview.Metadata), # For tooltip popups
    ('/frontend/search/setup',            frontend.search.Template),
    ('/frontend/search/related',          frontend.search.Related),
    ('/frontend/search/query',            frontend.search.Search),
    ('/frontend/search',                  frontend.search.Search),
    ('/frontend/sparql',                  frontend.sparql.Query),      # SPARQL query form
    ('/frontend/snorql/(.*)',             frontend.Snorql,
      {'path': os.path.join(os.path.dirname(__file__), 'SNORQL/snorql') }),
    ('/frontend/users',                   frontend.user.Logout),  ## Placeholder
    ('/frontend/logout',                  frontend.user.Logout),
    ('/frontend/login',                   frontend.user.Login),
    ('/frontend/.*',                      frontend.user.Logout),  ## Catch all other /frontend
    ('/frontend',                         frontend.user.Logout),  ## Catch all other /frontend

    ('.*',                                ContentNegotiate),
    ],
  gzip = True,
  login_url = '/frontend/login',
  static_path = os.path.join(os.path.dirname(__file__), 'frontend/static'),
  template_path = 'frontend/templates',
  ui_methods = { 'boxsize':    frontend.forms.boxsize,
                 'position':   frontend.forms.position,
                 'fieldwidth': frontend.forms.fieldwidth },
  ui_modules = { 'Menu':    frontend.MenuModule,
                 'SubTree': frontend.SubTree },
  cookie_secret = 'a2ojhhjqwbn3knk33d3mzd8ynbw/e;l22s=2gDHHaqq9',
  xsrf_cookies = True,
  debug = options.options.debug,
  )

application.listen(options.port, options.host, xheaders=True)
logging.info('Starting http://%s:%d/', options.host, options.port)

try:
  tornado.ioloop.IOLoop.instance().start()
except KeyboardInterrupt:
  pass

