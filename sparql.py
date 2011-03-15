######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id$
#
######################################################


import logging
import web, json
from web.wsgiserver import CherryPyWSGIServer

from repository import triplestore

urls = ('/query/(.*)', 'Query')
server = web.application(urls, globals())

web.config.debug = False


def xmlescape(s):
#===============
  return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


class Query(object):
#==================

  def _process(self, method, path):
    data = web.input(_method = method)
    logging.debug('Request: %s %s %s', method, path, str(data))

    sparql = str(data.get('query', ''))
    logging.debug('SPARQL: %s', sparql)

    cols = [ 'error' ]
    words = sparql.split()
    for w in words:
      if w[0] == '?' and w[1:] not in cols: cols.append(w[1:])

    results = triplestore.query(sparql)
##    logging.debug('--> %s', results)

    hdr = False
    body = ['<table border="1">']
    for r in results:
      if r:
        if not hdr:
          body.append('<tr>')
          for c in cols:
            if c in r: body.append('<th>%s</th>' % xmlescape(c))
          body.append('</tr>\n')
          hdr = True
        body.append('<tr>')
        for c in cols:
          if c in r: body.append('<td>%s</td>' % xmlescape(str(r[c])))
        body.append('</tr>\n')
    body.append('</table>\n')

    return '<html><body><h1>%d results:</h1>%s</body></html>' % (len(results), ''.join(body))


    """
    if modname != 'comet':
      try:
        xml = fun(get, post, session)
      except Exception, msg:
        if str(msg) == "303 See Other": raise
        logging.error('Errors loading page: %s', str(msg))
        logging.error('Error loading page: %s', traceback.format_exc())
        xml = '<page alert="Page can not be loaded... %s"/>' % xmlescape(str(msg))
      html = pagexsl.transform(xml, branding)
      return html

    else:    # Return JSON
      try:
        data = fun(get, post)
      except Exception, msg:
        if str(msg) == "303 See Other": raise
        logging.error('Errors loading page: %s', str(msg))
        logging.error('Error loading page: %s', traceback.format_exc())
        data = {'message': 'Error: %s' % str(msg)}
      web.header('content-type', 'text/html')
      return json.dumps(data)
    """

  def GET(self, name):
  #==================
    return self._process('GET', name)

  def POST(self, name):
  #===================
    return self._process('POST', name)



class WebServer(object):
#======================
  def __init__(self, address, **kwds):
    #if config.DEBUG: web.webapi.internalerror = web.debugerror
    self._address = web.net.validip(address)
    self._server = None

    wsgifunc = server.wsgifunc()
    wsgifunc = web.httpserver.StaticMiddleware(wsgifunc)
    ## wsgifunc = web.httpserver.LogMiddleware(wsgifunc)

    self._server = CherryPyWSGIServer(self._address, wsgifunc, numthreads=50)

    logging.debug('Starting http://%s:%d/', self._address[0], self._address[1])
    try:
      self._server.start()
    except KeyboardInterrupt:
      self._server.stop()


if __name__ == "__main__":
#========================
  from time import sleep

  logging.basicConfig(level=logging.DEBUG)

  w = WebServer("127.0.0.1:8081")
