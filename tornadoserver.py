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

import tornado.auth

import server
frontend_app = server.init_server(True)  # Setup globals

import frontend.webstream
import frontend.repository


application = tornado.web.Application([
    (r'/stream/data/',  frontend.webstream.StreamDataSocket),
    (r'/stream/echo/',  frontend.webstream.StreamEchoSocket),
    (r"/static/(.*)" ,  tornado.web.StaticFileHandler, {"path": "frontend/static"}),
    (r".*",             tornado.web.FallbackHandler,   {'fallback': tornado.wsgi.WSGIContainer(frontend_app) }),
    (r'/metadata/(.*)',  frontend.metadata.metadata),
    ],
  debug = options.options.debug,
  )

application.listen(options.port, options.host)
logging.info('Starting http://%s:%d/', options.host, options.port)

try:
  tornado.ioloop.IOLoop.instance().start()
except KeyboardInterrupt:
  pass

