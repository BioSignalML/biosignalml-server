######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id: __init__.py,v eeabfc934961 2011/02/14 17:47:59 dave $
#
######################################################


import sys, os
import RDF

import metadata
import fulltext

from utils.config import Options

DEFAULTS = { 'repository':
               { 'base':    'http://repository.biosignalml.org/signal/files',
                 'signals': '~/biosignalml/signal/files',
               },
             'triplestore':
               { 'store':     'postgresql',      # Or 'mysql'
                 'database':  'BioSignalRDF',    # Database in store
                 'host':      '127.0.0.1',       # Database server host
                 'user':      '',                # Database username
                 'password':  '',                # and password
               },
           }

if hasattr(sys, "frozen"): path = os.path.dirname(sys.executable)
else:                      path = os.path.dirname(__file__)
if path == '': path = '.'
options = Options(file='biosignalml.ini', path=path, defaults=DEFAULTS)
if options.repository['base'][-1] not in '#/': options.repository['base'] += '/'


def dbOptions(storeopts, create=False):
#======================================
  opts = storeopts.copy()
  opts['contexts'] = 'yes'
  opts['index-predicates'] = 1
  if create: opts['new'] = 'true'
  return ', '.join([("%s='%s'" % (n, v)) for n, v in opts.iteritems() if n != 'store'])


def openstore():
#===============
  dbopts = options.triplestore
  dbname = dbopts['database']
  dbtype = dbopts['store']
  try:
    store = RDF.Storage(name=dbname, storage_name=dbtype, options_string=dbOptions(dbopts))
  except RDF.RedlandError:
    store = RDF.Storage(name=dbname, storage_name=dbtype, options_string=dbOptions(dbopts, True))
  metadata.initialise(store)

  fulltext.initialise(dbopts)


openstore()

import model as model
