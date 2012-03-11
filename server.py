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
import tornado.options

##import rpdb2; rpdb2.start_embedded_debugger('test')

import triplestore.repository as repository

RECORDING_ENDPOINT  = '/recording/'    #: Import and export complete recording files
METADATA_ENDPOINT   = '/metadata/'     #: Get and put RDF metadata
STREAMDATA_ENDPOINT = '/stream/data/'  #: Stream signal data in and out

LOGFORMAT = '%(asctime)s %(levelname)8s %(threadName)s: %(message)s'

DEFAULTS  = { 'repository':
                { 'uri': 'http://devel.biosignalml.org',
                  'host': 'localhost',
                  'port':  8088,
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


  web.config.biosignalml = { }
  web.config.biosignalml['server_base'] = server_base
  web.config.biosignalml['recordings']  = os.path.join(server_base,
                                                       options.repository['recordings'])
  web.config.biosignalml['database']    = os.path.join(server_base,
                                                       options.repository['database'])
  web.config.biosignalml['repository']  = repository.BSMLRepository(options.repository['uri'],
                                                                    options.repository['triplestore'])

  tornado.options.define('recordings', default = web.config.biosignalml['recordings'])
  tornado.options.define('repository', default = web.config.biosignalml['repository'])
  tornado.options.define('debug',      default = (options.logging['log_level'] == 'DEBUG'))

  tornado.options.host = options.repository['host']
  tornado.options.port = int(options.repository['port'])

  import frontend      # Needs to access 'sessions' directory and have both
                       # web.config.biosignalml and repository initialised...

  return frontend.wsgifunc()


if __name__ == '__main__':
#=========================

  init_server()
