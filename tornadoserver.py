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
import logging

import tornado.httpserver
import tornado.websocket
import tornado.wsgi
import tornado.web
import tornado.options as options

## import tornado.auth     ## FUTURE
## import rpdb2; rpdb2.start_embedded_debugger('test')

import server
server.init_server()  # Setup globals

import endpoints.provenance as provenance
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


class Snorql(tornado.web.StaticFileHandler):
#===========================================

  def check_xsrf_cookie(self):
  #---------------------------
    """Don't check XSRF token for ReST POSTs."""
    pass

  def parse_url_path(self, url_path):
  #----------------------------------
    return url_path if url_path else 'index.html'

def ContentNegotiate(*args, **kwds):
#===================================
  request = args[1]
  accept = resource.parse_accept(request.headers)
  if (accept.get('application/rdf+xml', 0) > 0.9
   or accept.get('text/turtle', 0) == 1):
    HandlerClass = metadata.MetaData
  elif (accept.get('text/html', 0) == 1
   or accept.get('application/xhtml+xml', 0) == 1
   or len(accept) == 1 and accept.get('*/*', 0) == 1):
    HandlerClass = frontend.htmlview.Repository
  else:
    HandlerClass = metadata.MetaData
  handler = HandlerClass(*args, **kwds)
  if request.path in ['', '/']: handler.full_uri = ''
  else:                         handler.full_uri = '%s://%s%s' % (request.protocol,
                                                                  request.host, request.uri)
  #logging.debug('full URI %s', handler.full_uri)
  if len(accept) > 1: handler.set_header('Vary', 'Accept') # Let caches know we've used Accept header
  return handler


application = tornado.web.Application([
    ( server.STREAMDATA_ENDPOINT + '(.*)', webstream.StreamDataSocket),
    ( '/stream/echo/',                    webstream.StreamEchoSocket),

##    ('(' + server.RESOURCE_ENDPOINT + '.*)',  resource.ReST),
## This is supposedly reserved but we have existing recordings here...

    ('/metadata/.*',                      metadata.MetaData),
    ('/provenance/(.*)',                  provenance.ProvenanceRDF),
    ( server.SNORQL_ENDPOINT + '(.*)',    Snorql,
      {'path': os.path.join(os.path.dirname(__file__), 'SNORQL/snorql') }),
    ( '/sparql/',                         sparql.sparql),

    ('/frontend/metadata',                frontend.htmlview.Metadata), # For tooltip popups
    ('/frontend/logout',                  frontend.user.Logout),
    ('/frontend/login',                   frontend.user.Login),
    ('/frontend/users',                   frontend.user.Logout),  ## Placeholder
    ('/frontend/search/query',            frontend.search.Search),
    ('/frontend/search/setup',            frontend.search.Template),
    ('/frontend/search/related',          frontend.search.Related),
    ('/frontend/search',                  frontend.search.Search),
    ('/frontend/sparql',                  frontend.sparql.Query),
    ('/frontend/',                        frontend.user.Logout),  ## Catch all other /frontend
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

