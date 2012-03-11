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

import frontend.webstream
import frontend.metadata
import frontend.recording

application = tornado.web.Application([
    ( server.STREAMDATA_ENDPOINT,         frontend.webstream.StreamDataSocket),
    ( '/stream/echo/',                    frontend.webstream.StreamEchoSocket),
    ( server.METADATA_ENDPOINT + '(.*)',  frontend.metadata.metadata),
    ( server.RECORDING_ENDPOINT + '(.*)', frontend.recording.ReST),
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

