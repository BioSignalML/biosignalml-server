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

import web  # Used for web.net.validip()

import tornado.httpserver
import tornado.websocket
import tornado.wsgi
import tornado.web
import tornado.options

import tornado.auth

import server
frontend_app = server.init_server(True)  # Setup globals

import frontend.webstream
import frontend.repository


application = tornado.web.Application([
    (r'/stream/data/',  frontend.webstream.StreamDataSocket),
    (r'/stream/echo/',  frontend.webstream.StreamEchoSocket),
    (r"/static/(.*)" ,  tornado.web.StaticFileHandler, {"path": "frontend/static"}),
    (r'/metadata/(.*)', frontend.repository.metadata),
    (r".*",             tornado.web.FallbackHandler,   {'fallback': tornado.wsgi.WSGIContainer(frontend_app) }),
    ],
  debug = tornado.options.options.debug,
  )

address = web.net.validip(server.options.repository['bind'])

application.listen(address[1], address[0])

logging.info('Starting http://%s:%d/', address[0], address[1])

try:
  tornado.ioloop.IOLoop.instance().start()
except KeyboardInterrupt:
  pass

