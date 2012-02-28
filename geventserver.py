#!/usr/bin/python
"""A web.py application powered by gevent"""

import logging

import gevent.monkey ; gevent.monkey.patch_all()
import gevent.pywsgi
from ws4py.server.geventserver import WebSocketServer
from ws4py.server.wsgi.middleware import WebSocketUpgradeMiddleware

import web

## import rpdb2; rpdb2.start_embedded_debugger('test')

import server
application = server.init_server(True)


import frontend.webstream

streams = { '/stream/data/': frontend.webstream.StreamDataSocket,
            '/stream/echo/': frontend.webstream.StreamEchoSocket
          }


class StreamUpgrade(WebSocketUpgradeMiddleware):
#===============================================

  def __call__(self, env, resp):
  #-----------------------------
    if env['PATH_INFO'] in streams:
      websocket_class = streams[env['PATH_INFO']]
      self.protocols = [websocket_class.protocol]
      self.websocket_class = websocket_class
      return WebSocketUpgradeMiddleware.__call__(self, env, resp)
    else:
      return application(env, resp)


class BioSignalMLServer(WebSocketServer):
#========================================

  def __init__(self, address, *args, **kwargs):
  #--------------------------------------------
    gevent.pywsgi.WSGIServer.__init__(self, address, *args, **kwargs)
    self.application = StreamUpgrade(handler=self.handler)



address = web.net.validip(server.options.repository['bind'])
logging.debug('Starting http://%s:%d/', address[0], address[1])

server = BioSignalMLServer(address, application)
server.serve_forever()
