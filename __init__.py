######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id$
#
######################################################


import RDF

import metadata
import fulltext

from config import Options

DEFAULTS = { 'repository':
               { 'import_base': 'http://repository.biosignalml.org/signal/files',
                 'signal_store': './signal/files',
               },
             'triplestore':
               { 'store':     'postgresql',      # Or 'mysql'
                 'database':  'BioSignalRDF',    # Database in store
                 'host':      '127.0.0.1',       # Database server host
                 'user':      '',                # Database username
                 'password':  '',                # and password
               },
           }

options = Options(DEFAULTS)
if options.repository['import_base'][-1] not in '#/':
  options.repository['import_base'] += '/'


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
