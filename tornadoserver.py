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
import endpoints.resource  as resource
import endpoints.sparql    as sparql

import frontend
import frontend.user
import frontend.forms
import frontend.sparql
import frontend.search
import frontend.htmlview
application = tornado.web.Application([
    ( server.STREAMDATA_ENDPOINT,         webstream.StreamDataSocket),
    ( '/stream/echo/',                    webstream.StreamEchoSocket),
    ( server.RESOURCE_ENDPOINT + '(.*)',  resource.ReST),
    ('/provenance/(.*)',                  provenance.ProvenanceRDF),
    ('/provenance',                       provenance.ProvenanceRDF),
    ( '/sparql/',                         sparql.sparql),
    ('/comet/metadata',                   frontend.htmlview.Metadata), # For tooltip popups
    ('/repository/(.*)',                  frontend.htmlview.Repository),
    ('/repository',                       frontend.htmlview.Repository),
    ('/',                                 frontend.htmlview.Repository),
    ('',                                  frontend.htmlview.Repository),
    ('/logout',                           frontend.user.Logout),
    ('/login',                            frontend.user.Login),
    ('/search',                           frontend.search.Search),
    ('/comet/search/query',               frontend.search.Search),
    ('/comet/search/setup',               frontend.search.Template),
    ('/comet/search/related',             frontend.search.Related),
    ('/sparqlquery',                      frontend.sparql.Query),
    ],
  gzip = True,
  login_url = '/login',
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

