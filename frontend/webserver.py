######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id$
#
######################################################


import sys, logging, traceback
import threading, Queue
from time import time
import web, json
from web.wsgiserver import CherryPyWSGIServer

import xslt, xsl
from utils import num, cp1252, xmlescape, nbspescape
import webstream
from sparql import query

SESSION_TIMEOUT = 1200 # seconds  ## num(config.config['idletime'])
WEB_MODULE      = 'repository.frontend'  # We do a "import webpages from repository.frontend"

web.config.debug = False


pagexsl = None   # Initialise once we start running

urls = (
         '/(stream)',   'stream',
         '/query/(.*)', 'query',
         '/(.*)',       'index',
       )

webapp = web.application(urls, globals())

dispatch = [ ('comet/metadata',  'biosignalml.metadata',   'json'),
             ('comet/stream',    'comet.stream',           'json'),
             ('recordings',      'biosignalml.recordings', 'html'),
             ('search',          'biosignalml.search',     'html'),
             ('sparql',          'biosignalml.sparql',     'html'),
             ('logout',          'webpages.logout',        'html'),
             ('login',           'webpages.login',         'html'),
             ('',                'webpages.index',         'html'),
           ]

def get_processor(path):
#=======================
  for p, f, t in dispatch:
    if path == p or path.startswith(p + '/'):
      params = path[len(p)+1:] if path.startswith(p + '/') else ''
      return f.rsplit('.', 1) + [ params, t ]
  return [ 'webpages', 'index', '', 'html' ]


class Session(web.session.Session):
#==================================

  def expired(self):
  #-----------------
    self._killed = True
    self._save()
    user.logout()
    raise web.seeother('/login?expired')

if web.config.get('_session') is None:
  session = Session(webapp, web.session.DiskStore('sessions'),
    initializer={'userlevel': 0, 'loggedin': False, 'menu': None})
  web.config._session = session
else:
  session = web.config._session


def sessionGet(key, default):
#============================
  global session
  ##logging.error('GET: %s, SESS = %s', key, str(session))
  return session.get(key, default)

def sessionSet(key, value):
#==========================
  global session
  session[key] = value
  ##logging.error('SET: %s = %s, SESS = %s', key, value, str(session))

# Needs to be after session declaration otherwise problems with
# circular imports -- see http://effbot.org/zone/import-confusion.htm
import user, menu


class index(object):
#===================

  def _process(self, method, path):
  #--------------------------------
    logging.debug('Request: %s', path)
    if len(path) and path[0] == '/': path = path[1:]
    i = path.find('?')
    if i >= 0: path = path[0:i]
    modname, funname, params, responsetype = get_processor(path)
    logging.debug('Serving %s in %s', funname, modname)

    if responsetype == 'html':
      if not menu.hasaction(funname):
        logging.debug("Function '%s' not in menu", funname)
        raise web.seeother('/login?unauthorised')
        ##raise web.unauthorized
      now = time()
      if now > sessionGet('timeout', now) and not funname in ['login', 'logout']: 
        logging.debug("Session expired: %s > %s", str(now), str(sessionGet('timeout', now)))
        session.expired()
      session['timeout'] = now + SESSION_TIMEOUT

    try:
      webfolder = __import__(WEB_MODULE, globals(), locals(), [modname])
      mod = getattr(webfolder, modname)
      reload(mod)
    except ImportError, msg:
      logging.error("Unable to load module '%s': %s", modname, msg)
    try:
      fun = getattr(mod, funname)
    except Exception:
      logging.error('Can not find %s function in module', funname)
      session.kill()
      fun = mod.index

    get = web.input(_method = 'GET')
    post = web.input(_method = 'POST')
    if responsetype == 'html':
      try:
        xml = fun(get, post, session, params)
      except Exception, msg:
        if str(msg) == "303 See Other": raise
        logging.error('Errors loading page: %s', str(msg))
        logging.error('Error loading page: %s', traceback.format_exc())
        xml = '<page alert="Page can not be loaded... %s"/>' % xmlescape(str(msg))
      html = pagexsl.transform(xml, { } )
##      logging.debug(html)
      return html

    else:    # Return JSON
      try:
        data = fun(get, post, params)
      except Exception, msg:
        if str(msg) == "303 See Other": raise
        logging.error('Errors loading page: %s', str(msg))
        logging.error('Error loading page: %s', traceback.format_exc())
        data = {'message': 'Error: %s' % str(msg)}
      web.header('content-type', 'text/html')
      return json.dumps(data)


  def GET(self, name):
  #-------------------
    return self._process('GET', name)

  def POST(self, name):
  #--------------------
    return self._process('POST', name)


class stream(object):
#===================

  def GET(self, name):
  #------------------
    uri = web.input().uri
    #### Time fragment; metadata only; specific signals...
    logging.debug("Streaming '%s'", uri)
    try:
      web.header('Content-Type','binary/octet-stream')
      web.header('Transfer-Encoding','chunked')
      web.header('Content-Disposition', 'attachment; filename=test.stream')
       
      sendq = Queue.Queue()
      source = webstream.Sender(sendq, uri)
      while source.isAlive() or not sendq.empty():
        try:
          data = sendq.get(True, 0.001)
          # logging.debug("Streaming '%s'", data)
          yield data
        except Empty:
          pass
    except Exception, msg:
      raise    ##############
      yield pagexsl.transform('<page alert="Can not stream signal... %s"/>' % xmlescape(str(msg)))


class WebServer(threading.Thread):
#=================================

  def __init__(self, address, **kwds):
  #-----------------------------------
    threading.Thread.__init__(self, **kwds)
    global pagexsl
    pagexsl = xslt.Engine(xsl.PAGEXSL)
    if web.config.debug: web.webapi.internalerror = web.debugerror
    self._address = web.net.validip(address)
    self._server = None
    self.start()

  def run(self):
  #-------------
    pagexsl.start()
    wsgifunc = webapp.wsgifunc()
    wsgifunc = web.httpserver.StaticMiddleware(wsgifunc)
    ## wsgifunc = web.httpserver.LogMiddleware(wsgifunc)
    self._server = CherryPyWSGIServer(self._address, wsgifunc, numthreads=50)
    logging.debug('Starting http://%s:%d/', self._address[0], self._address[1])
    self._server.start()

  def stop(self):
  #--------------
    logging.debug('Stopping http://%s:%d/', self._address[0], self._address[1])
    if self._server: self._server.stop()
    pagexsl.stop()
    self.join()


if __name__ == "__main__":
#=========================

  from time import sleep
#  import cProfile

  logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)8s: %(message)s')

  def runserver(period):
    logging.debug("Server setup...")
    w = WebServer("127.0.0.1:8081")
    
    try:
      sleep(period)
    except KeyboardInterrupt:
      pass

    logging.debug("Server stopping...")
    w.stop()
    logging.debug("Server stopped...")


  #cProfile.run('runserver(60)')

  runserver(1200)
