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


RESOURCE_ENDPOINT   = '/resource/'     #: Import and export resource representations
STREAMDATA_ENDPOINT = '/stream/data/'  #: Stream signal data in and out
SNORQL_ENDPOINT     = '/snorql/'       #: SNORQL browsing of RDF

LOGFORMAT = '%(asctime)s %(levelname)8s %(threadName)s: %(message)s'

DEFAULTS  = { 'uri': 'http://devel.biosignalml.org',
              'host': 'localhost',
              'port':  8088,
              'path': '.',
              'database': './database/repository.db',
              'recordings': './recordings/',
              'sparql_store': 'Virtuoso',
              'sparql_server': 'http://localhost:8890',
              'resource_path': RESOURCE_ENDPOINT,

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


def init_server():
#=================
  args = parse_args()
  config_file = args.config if args.config[0] == '/' else os.path.join(module_path, args.config)
  global options
  options = Options(file=config_file, defaults=DEFAULTS)
  server_base = options.repository['path']

  if options.logging['log_file']:
    filename = os.path.join(server_base, options.logging['log_file'])
    try:            os.makedirs(os.path.dirname(filename))
    except OSError: pass
    logging.basicConfig(format=LOGFORMAT, filename=filename, filemode='a')
  if options.logging['log_level']:
    logging.getLogger().setLevel(options.logging['log_level'])
  console = logging.StreamHandler()
  console.setFormatter(logging.Formatter(LOGFORMAT))
  logging.getLogger().addHandler(console)
  logging.info('Starting BioSignalML repository server...')

  define('recordings', os.path.join(server_base, options.repository['recordings']))
  define('database',
    webdb.Database(os.path.join(server_base, options.repository['database'])))

  if   options.repository['sparql_store'] == 'FourStore': SparqlStore = FourStore
  elif options.repository['sparql_store'] == 'Virtuoso':  SparqlStore = Virtuoso
  else: raise ValueError("Unknown type of SPARQL store")
  define('repository',
    repository.BSMLStore(options.repository['uri'], SparqlStore(options.repository['sparql_server'])))

  define('resource_prefix', options.repository['uri'] + options.repository['resource_path'])
  define('debug',      (options.logging['log_level'] == 'DEBUG'))
  tornado.options.host = options.repository['host']
  tornado.options.port = int(options.repository['port'])
