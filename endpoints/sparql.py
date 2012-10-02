import logging
import httplib2

import tornado.web
import tornado.ioloop as ioloop
import tornado.httpclient as httpclient

from tornado.options import options


class sparql(tornado.web.RequestHandler):
#==========================================

  def check_xsrf_cookie(self):
    pass
  
  def header_handler(self, header):
    hdr = header.split(':', 1)
    self.set_header(hdr[0], hdr[1].strip())
    
  def stream_handler(self, response):
    if len(response):
      self.write(response)
      self.flush()
    
  def request_handler(self, response):
    if response.code != 599: self.set_status(response.code)
    else:                    self.set_status(504)  # gateway timeout
    self.finish()
    self.ioloop.stop()
    self.http_client.close()

  def do_query(self, body=None):
    self.ioloop = ioloop.IOLoop()
    self.http_client = httpclient.AsyncHTTPClient(self.ioloop)
    self.http_client.fetch(
      options.repository._sparqlstore._href + self.request.uri,
      self.request_handler,
      method = self.request.method,
      headers = self.request.headers,
      body = body,
      streaming_callback = self.stream_handler,
      header_callback = self.header_handler)
    self.ioloop.start()

  def get(self):
    self.do_query()
  
  def post(self):
    self.do_query(self.request.body)
