######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id$
#
######################################################

"""A web.py application powered by gevent"""

import logging

import tornado.httpserver
import tornado.websocket
import tornado.wsgi
import tornado.web
import tornado.options as options

## import tornado.auth     ## FUTURE
## import rpdb2; rpdb2.start_embedded_debugger('test')

import server
frontend_app = server.init_server(True)  # Setup globals

import endpoints.webstream as webstream
import endpoints.metadata  as metadata 
import endpoints.recording as recording

import frontend.htmlview
application = tornado.web.Application([
    ( server.STREAMDATA_ENDPOINT,         webstream.StreamDataSocket),
    ( '/stream/echo/',                    webstream.StreamEchoSocket),
    ( server.METADATA_ENDPOINT + '(.*)',  metadata.metadata),
    ( server.options.repository['recording_prefix'] + '(.*)', recording.ReST),
    ( "/static/(.*)" ,                    tornado.web.StaticFileHandler,
                                            {"path": "frontend/static"}),
    ('/comet/metadata',                   frontend.htmlview.Metadata), # For tooltip popups
    ('/repository/(.*)',                  frontend.htmlview.Repository),
    ('/repository',                       frontend.htmlview.Repository),
    ( ".*",                               tornado.web.FallbackHandler,
                                            {'fallback': tornado.wsgi.WSGIContainer(frontend_app) }),
    ],
  gzip = True,
  template_path = 'frontend/templates',
  ui_modules = { 'Menu':    frontend.htmlview.MenuModule,
                 'SubTree': frontend.htmlview.SubTree },
  cookie_secret = 'a2ojhhjqwbn3knk33d3mzd8ynbw/e;l22s=2gDHHaqq9',
  debug = options.options.debug,
  )

application.listen(options.port, options.host)
logging.info('Starting http://%s:%d/', options.host, options.port)

try:
  tornado.ioloop.IOLoop.instance().start()
except KeyboardInterrupt:
  pass

