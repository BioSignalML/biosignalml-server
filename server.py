######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id$
#
######################################################


import sys, os
import argparse
import ConfigParser
import signal
import logging
import web

##import rpdb2; rpdb2.start_embedded_debugger('test')

import biosignalml.repository as repository

LOGFORMAT = '%(asctime)s %(levelname)8s %(threadName)s: %(message)s'

DEFAULTS  = { 'repository':
                { 'uri': 'http://devel.biosignalml.org',
                  'bind': 'localhost:8082',
                  'path': '.',
                  'database': './database/repository.db',
                  'recordings': './recordings/',
                  'triplestore': 'http://localhost:8083'
                },
              'logging':
                { 'log_file': './log/biosignalml.log',
                  'log_level': 'DEBUG', # 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
                },
            }

if hasattr(sys, "frozen"): module_path = os.path.dirname(sys.executable)
else:                      module_path = os.path.dirname(__file__)
if module_path == '': module_path = '.'

options = { }

class Options(object):
#====================

  def __init__(self, file, defaults = { } ):
  #-----------------------------------------
    cfg = ConfigParser.SafeConfigParser()
    cfg.optionxform = str   # Preserve case (default method translates to lowercase)
    cfg.read(file)
    for s in cfg.sections(): setattr(self, s, dict(cfg.items(s, defaults.get(s, None))) )


def parse_args():
#================
  parser = argparse.ArgumentParser(
    description="Start a HTTP interface to a BioSignalML repository."
    )
  parser.add_argument("-c", "--config", dest="config",
                    help="""The name of the configuration file. Default is
                            '%s/biosignalml.ini'; relative names are with
                            respect to '%s/'.""" % (module_path, module_path),
                    default="biosignalml.ini",
                    metavar="CONFIG")
  return parser.parse_args()


def init_server(wsgi = False):
#=============================
  args = parse_args()
  config_file = args.config if args.config[0] == '/' else os.path.join(module_path, args.config)
  global options
  options = Options(file=config_file, defaults=DEFAULTS)
  server_base = options.repository['path']

  if options.logging['log_file']:
    logging.basicConfig(format=LOGFORMAT,
                        filename=os.path.join(server_base, options.logging['log_file']),
                        filemode='a')
  if options.logging['log_level']:
    logging.getLogger().setLevel(options.logging['log_level'])
###  if not wsgi:
  console = logging.StreamHandler()
  console.setFormatter(logging.Formatter(LOGFORMAT))
  logging.getLogger().addHandler(console)
###
  logging.info('Starting BioSignalML repository server...')

  web.config.biosignalml = { }
  web.config.biosignalml['server_base'] = server_base
  web.config.biosignalml['recordings']  = os.path.join(server_base,
                                                       options.repository['recordings'])
  web.config.biosignalml['database']    = os.path.join(server_base,
                                                       options.repository['database'])
  web.config.biosignalml['repository']  = repository.BSMLRepository(options.repository['uri'],
                                                                    options.repository['triplestore'])
  web.config.debug = (options.logging['log_level'] == 'DEBUG')

  import frontend      # Needs to access 'sessions' directory and have both
                       # web.config.biosignalml and repository initialised...

  if wsgi:
    return frontend.wsgifunc()
  else:
    import threading
    from time import sleep
    from web.wsgiserver import CherryPyWSGIServer

    class WebServer(threading.Thread):
    #=================================

      def __init__(self, address, **kwds):
      #-----------------------------------
        version = CherryPyWSGIServer.version[9:].split('.')
        if version[0] < '3' or version[0] == '3' and version[1] < '2':
          raise Exception("Require CherryPy/3.2.0 or greater")
        # svn co http://svn.cherrypy.org/tags/cherrypy-3.2.0/cherrypy/wsgiserver
        threading.Thread.__init__(self, **kwds)
        self._address = web.net.validip(address)
        self._server = None

      def run(self):
      #-------------
        wsgifunc = frontend.wsgifunc()
        ## wsgifunc = web.httpserver.LogMiddleware(wsgifunc)
        self._server = CherryPyWSGIServer(self._address, wsgifunc, numthreads=50)
        logging.debug('Starting http://%s:%d/', self._address[0], self._address[1])
        self._server.start()

      def stop(self):
      #--------------
        logging.debug('Stopping http://%s:%d/', self._address[0], self._address[1])
        if self._server: self._server.stop()

    def interrupt(signum, frame):
    #============================
      raise KeyboardInterrupt

    web_server = WebServer(options.repository['bind'])
    signal.signal(signal.SIGHUP, interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    web_server.start()  # start threads...
    try:
      while True: sleep(0.1)
    except KeyboardInterrupt:
      pass
    web_server.stop()   # notify threads we are shutting down
    web_server.join()   # wait for threads to finish...

  logging.info('Shutdown BioSignalML repository server...')


if __name__ == '__main__':
#=========================

  init_server()
