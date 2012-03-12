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

import server
frontend_app = server.init_server(True)  # Setup globals

import endpoints.webstream as webstream
import endpoints.metadata  as metadata 
import endpoints.recording as recording

application = tornado.web.Application([
    ( server.STREAMDATA_ENDPOINT,         webstream.StreamDataSocket),
    ( '/stream/echo/',                    webstream.StreamEchoSocket),
    ( server.METADATA_ENDPOINT + '(.*)',  metadata.metadata),
    ( server.RECORDING_ENDPOINT + '(.*)', recording.ReST),
    ( "/static/(.*)" ,                    tornado.web.StaticFileHandler,
                                            {"path": "frontend/static"}),
    ( ".*",                               tornado.web.FallbackHandler,
                                            {'fallback': tornado.wsgi.WSGIContainer(frontend_app) }),
    ],
  gzip = True,
  debug = options.options.debug,
  )

application.listen(options.port, options.host)
logging.info('Starting http://%s:%d/', options.host, options.port)

try:
  tornado.ioloop.IOLoop.instance().start()
except KeyboardInterrupt:
  pass

