######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $ID: e3e37fb on Thu Feb 9 14:13:46 2012 +1300 by Dave Brooks $
#
######################################################


import os, sys
import logging, traceback
from time import time
import web, json

from biosignalml.utils import num, cp1252, xmlescape, nbspescape, unescape


# Needs to be after session declaration otherwise problems with
# circular imports -- see http://effbot.org/zone/import-confusion.htm
import user, menu

# Provide access to these modules:
##import webdb
##import recording


WEB_MODULE = 'frontend'  # We do a "import webpages from frontend"

urls = ( '/(recording)',    '%s.recording.ReST' % WEB_MODULE,
         '/(recording/.*)', '%s.recording.ReST' % WEB_MODULE,
         '/(.*)',           'Index',
       )


if web.config.debug: web.webapi.internalerror = web.debugerror
_webapp = web.application(urls, globals())
_wsgifunc = web.httpserver.StaticMiddleware(_webapp.wsgifunc())

def wsgifunc():
#==============
  return _wsgifunc


SESSION_TIMEOUT = 1800 # seconds  ## num(config.config['idletime'])
web.config.session_parameters['timeout'] = SESSION_TIMEOUT
web.config.session_parameters['ignore_expiry'] = False
web.config.session_parameters['ignore_change_ip'] = False


class Session(web.session.Session):
#==================================

  def expired(self):
  #-----------------
    self._killed = True
    self._save()
    if web.ctx.env['PATH_INFO'] in ['/login', '/logout']: self.session_id = None
    else:                                                 raise web.seeother('/login?expired')

  def get(self, key, default=None):
  #--------------------------------
    return getattr(self, key, default)


if web.config.get('_session') is None:
  session_dir = os.path.join(web.config.biosignalml['server_base'], 'sessions')
  session = Session(_webapp, web.session.DiskStore(session_dir),
    initializer={'userlevel': 0, 'loggedin': False, 'menu': None})
  web.config._session = session
else:
  session = web.config._session


###print "SESS:", session._data

dispatch = [ ('comet/metadata',       'htmlview.metadata',   'json'),   # For tooltip popups
             ('comet/search/setup',   'search.template',     'json'),
             ('comet/search/query',   'search.searchquery',  'json'),
             ('comet/search/related', 'search.related',      'json'),

             ('repository',           'htmlview.repository', 'html'),
             ('searchform',           'search.searchform',   'html'),
             ('sparqlquery',          'sparql.sparqlquery',  'html'),

             ('logout',               'user.logout',         'html'),
             ('login',                'user.login',          'html'),
             ('explore',              'explore.explore',     'html'),
             ('',                     'htmlview.repository', 'html'),
           ]


def get_processor(path):
#=======================
  for p, f, t in dispatch:
    if path == p or path.startswith(p + '/'):
      params = path[len(p)+1:] if path.startswith(p + '/') else ''
      return [ p ] + f.rsplit('.', 1) + [ params, t ]
  raise web.notfound('Page not found')


class Index(object):
#===================

  @staticmethod
  def _call(fun, submitted, session, params):
  #------------------------------------------
    #logging.debug('Session: %s', session)
    try:
      return (fun(submitted, session, params), '')
    except web.HTTPError, msg:
      logging.error('Errors loading page: %s', str(msg))
      raise
    except Exception, msg:
      logging.error('Errors loading page: %s', str(msg))
      logging.error('Error loading page: %s', traceback.format_exc())
    return ('', str(msg))

  def _process(self, method, path):
  #--------------------------------
    #logging.debug('Request: %s', path)
    if len(path) and path[0] == '/': path = path[1:]
    i = path.find('?')
    if i >= 0: path = path[0:i]
    path, modname, funname, params, responsetype = get_processor(path)
    #logging.debug('Serving %s in %s', funname, modname)

    if responsetype == 'html':
      if not menu.hasaction(path, session):
        logging.debug("Function '%s' not in menu", funname)
        raise web.seeother('/login?unauthorised')
        ##raise web.unauthorized

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

    submitted = dict([ (k, unescape(v))
                         for k, v in web.input(_method = method, _unicode=True).iteritems() ])

    if responsetype == 'html':
      html, err = self._call(fun, submitted, session, params)
      if not html: html = '<page alert="Page can not be loaded... %s"/>' % xmlescape(err)
#     if not html: raise Exception(err)
      web.header('Content-Type', 'text/html')
      return html

    else:    # Return JSON
      data, err = self._call(fun, submitted, session, params)
      if not data: data = {'alert': 'Error: %s' % str(err)}
      web.header('Content-Type', 'application/json')
      return json.dumps(data)


  def GET(self, name):
  #-------------------
    return self._process('GET', name)

  def POST(self, name):
  #--------------------
    return self._process('POST', name)


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
