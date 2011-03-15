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


from bsml import BSML
from model import Recording, Signal
from model.mapping import bsml_mapping

from metadata import rdf, rdfs, dct
from rdfmodel import RDFModel, make_literal
from utils.config import Options

import fulltext


DEFAULTS = { 'repository':
               { 'base':    'http://repository.biosignalml.org/recordings',
                 'signals': '~/biosignalml/recordings',
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


def _dbOptions(storeopts, create=False):
#=======================================
  opts = storeopts.copy()
  opts['contexts'] = 'yes'
  opts['index-predicates'] = 1
  if create: opts['new'] = 'true'
  return ', '.join([("%s='%s'" % (n, v)) for n, v in opts.iteritems() if n != 'store'])


def _openstore():
#================
  dbopts = options.triplestore
  dbname = dbopts['database']
  dbtype = dbopts['store']
  try:
    store = RDF.Storage(name=dbname, storage_name=dbtype, options_string=_dbOptions(dbopts))
  except RDF.RedlandError:
    store = RDF.Storage(name=dbname, storage_name=dbtype, options_string=_dbOptions(dbopts, True))
  fulltext.initialise(dbopts)
  return RDFModel(store)


triplestore = _openstore()


def recordings():
#===============
  return [ Recording(s)
    for s, g in triplestore.get_sources_context(rdf.type, BSML.Recording) if s == g ]

def get_recording(uri):
#=====================
  return Recording.create_from_RDFmodel(uri, triplestore, bsml_mapping)

def get_recording_signals(uri):
#==============================
  rec = get_recording(uri)
  rec.signals_from_RDFmodel(triplestore, bsml_mapping)
  return rec


def signal_recording(uri):
#=========================
  return triplestore.get_property(uri, BSML.recording)


def get_signal(uri):
#===================
  return Signal.create_from_RDFmodel(uri, triplestore, bsml_mapping)


def signal(sig, properties):              # In context of signal's recording...
#===========================
  if triplestore.contains((sig, rdf.type, BSML.Signal)):
    r = [ [ make_literal(t, '') for t in triplestore.get_targets(sig, p) ] for p in properties ]
    r.sort()
    return r
  else: return None
