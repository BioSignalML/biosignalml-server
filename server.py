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

import tornado.options
from tornado.options import define

##import rpdb2; rpdb2.start_embedded_debugger('test')

from biosignalml.rdf.sparqlstore import Virtuoso, FourStore

import biosignalml.repository as repository
import frontend.webdb as webdb

VERSION = '0.4.1pre'

LOGFORMAT = '%(asctime)s %(levelname)8s %(threadName)s: %(message)s'

DEFAULTS  = { 'uri': 'http://devel.biosignalml.org',
              'host': 'localhost',
              'port':  8088,
              'path': '.',
              'database': './database/repository.db',
              'recordings': './recordings/',
              'sparql_store': 'Virtuoso',
              'sparql_server': 'http://localhost:8890',
              'log_file': './log/biosignalml.log',
              'log_level': 'DEBUG', # 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
            }

if hasattr(sys, "frozen"): module_path = os.path.dirname(sys.executable)
else:                      module_path = os.path.dirname(__file__)
if module_path == '': module_path = '.'

options = { }

class Options(object):
#====================

  def __init__(self, file, defaults = { } ):
  #-----------------------------------------
    cfg = ConfigParser.SafeConfigParser(defaults, dict)
    cfg.optionxform = str   # Preserve case (default method translates to lowercase)
    cfg.read(file)
    for s in cfg.sections(): setattr(self, s, dict(cfg.items(s, True)))


def init_server():
#=================

  define("config", help=("The name of the configuration file. Default is"
                         " '%s/biosignalml.ini'; relative names are with"
                         " respect to '%s/'.") % (module_path, module_path),
                   default="biosignalml.ini",
                   metavar="CONFIG")
  del tornado.options.options['logging']
  define('logging', 'none') # Default to our settings
  tornado.options.parse_command_line()
  cfile = tornado.options.options.config
  config_file = cfile if cfile.startswith('/') else os.path.join(module_path, cfile)

  global options
  options = Options(file=config_file, defaults=DEFAULTS)
  server_path = options.repository['path']

  if options.logging['log_file']:
    filename = os.path.join(server_path, options.logging['log_file'])
    try:            os.makedirs(os.path.dirname(filename))
    except OSError: pass
    logging.basicConfig(format=LOGFORMAT, filename=filename, filemode='a')
  if options.logging['log_level']:
    logging.getLogger().setLevel(options.logging['log_level'])
  console = logging.StreamHandler()
  console.setFormatter(logging.Formatter(LOGFORMAT))
  logging.getLogger().addHandler(console)
  logging.info('Starting BioSignalML server v%s', VERSION)

  define('recordings_path', os.path.join(server_path, options.repository['recordings']))
  define('database',
    webdb.Database(os.path.join(server_path, options.repository['database'])))

  if   options.repository['sparql_store'] == 'FourStore': SparqlStore = FourStore
  elif options.repository['sparql_store'] == 'Virtuoso':  SparqlStore = Virtuoso
  else: raise ValueError("Unknown type of SPARQL store")
  define('repository_uri', options.repository['uri'])
  sparqlstore = SparqlStore(options.repository['sparql_server'])
  define('sparql_store', sparqlstore)
  define('repository', repository.BSMLUpdateStore(options.repository['uri'], sparqlstore))
  define('debug',      (options.logging['log_level'] == 'DEBUG'))
  tornado.options.host = options.repository['host']
  tornado.options.port = int(options.repository['port'])
