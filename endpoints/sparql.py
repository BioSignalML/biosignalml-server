import logging
from urllib.parse import urlencode
#import urllib.parse as urlparse

import tornado.web
import tornado.ioloop as ioloop
import tornado.httpclient as httpclient

from tornado.options import options

from frontend import user


class SparqlProxy(tornado.web.RequestHandler):
#=============================================

  def __init__(self, *args, **kwds):
  #---------------------------------
    super(SparqlProxy, self).__init__(*args, **kwds)
    self._sparqlstore = options.repository._sparqlstore

  def check_xsrf_cookie(self):
  #---------------------------
    pass

  def header_handler(self, header):
  #--------------------------------
    if ':' in header:
      hdr = header.split(':', 1)
      self.set_header(hdr[0], hdr[1].strip())

  def stream_handler(self, response):
  #----------------------------------
    if len(response):
      self.write(response)
      self.flush()

  def request_handler(self, response):
  #-----------------------------------
    if response.code != 599: self.set_status(response.code)
    else:                    self.set_status(504)  # gateway timeout
    self.finish()
    self.ioloop.stop()
    self.http_client.close()

  def do_request(self, uri=None, body=None):
  #-----------------------------------------
    self.ioloop = ioloop.IOLoop()
    self.http_client = httpclient.AsyncHTTPClient(self.ioloop)
    self.http_client.fetch(
      self._sparqlstore._href + (uri if uri is not None else self.request.uri),
      self.request_handler,
      method = self.request.method,
      headers = self.request.headers,
      body = body,
      streaming_callback = self.stream_handler,
      header_callback = self.header_handler)
    self.ioloop.start()
    self.ioloop.close(True)


class SparqlQuery(SparqlProxy):
#==============================

  @user.capable(user.ACTION_VIEW)
  def get(self):
  #-------------
    self.do_request()

  @user.capable(user.ACTION_VIEW)
  def post(self):
  #--------------
#    logging.debug('ARGS: %s', self.request.arguments)
#    query = dict(urlparse.parse_qsl(self.request.body)).get('query')
#    if (query is not None
#     and query.split()[0].toupper() not in ['ASK', 'DESCRIBE', 'SELECT', 'CONSTRUCT']
#     and user.ACTION_MODIFY ...
#
#    self._capabilities = user.capabilities(self, None)
    self.do_request(body=self.request.body)


class SparqlUpdate(SparqlProxy):
#===============================

  @user.capable(user.ACTION_MODIFY)
  def get(self):
  #-------------
    self.do_request()

  def _get_params(self):
  #---------------------
    return { k: self.get_argument(k) for k in self.request.arguments }

  @user.capable(user.ACTION_MODIFY)
  def post(self):
  #--------------
    params = self._get_params()
    if self._sparqlstore.UPDATE_PARAMETER != 'update':
      params[self._sparqlstore.UPDATE_PARAMETER] = params.pop('update', None)
    self.request.headers['Content-type'] = 'application/x-www-form-urlencoded'
    self.do_request(uri=self._sparqlstore.ENDPOINTS[0], body=urlencode(params))


class SparqlGraph(SparqlUpdate):
#==============================

  @user.capable(user.ACTION_MODIFY)
  def post(self):
  #--------------
    if self._sparqlstore.GRAPH_PARAMETER == 'graph':
      self.do_request(uri='?'.join([self._sparqlstore.ENDPOINTS[1], self.request.query]),
                      body=self.request.body)
    else:                                              # Virtuoso
      params = self._get_params()
      statements = params.pop('data', None)
      logging.debug("GR: %s", params)
      self.request.headers = { 'Content-Type': params.pop('mime-type', None) }
      params[self._sparqlstore.GRAPH_PARAMETER] = params.pop('graph', None)
      self.do_request(uri='?'.join([self._sparqlstore.ENDPOINTS[1], urlencode(params)]),
                      body=statements)

  def _put_delete(self):
  #---------------------
    if self._sparqlstore.GRAPH_PARAMETER == 'graph':
      query = self.request.query
    else:                                              # Virtuoso
      params = self._get_params()
      params[self._sparqlstore.GRAPH_PARAMETER] = params.pop('graph', None)
      query = urlencode(params)
    self.do_request(uri='?'.join([self._sparqlstore.ENDPOINTS[1], query]),
                    body=self.request.body)

  @user.capable(user.ACTION_EXTEND)
  def put(self):
  #-------------
    self._put_delete()

  @user.capable(user.ACTION_DELETE)
  def delete(self):
  #--------------
    self._put_delete()
