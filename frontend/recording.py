######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $Id$
#
######################################################


import logging
import uuid
import web
import os
import urllib
from datetime import datetime

from model.mapping import bsml_mapping
from rdfmodel import Graph
from metadata import rdf, rdfs, dct
from bsml import BSML

import repository

import fileformats


"""
/recording/label/...
/recording/uuid/...
/recording/uuid/metadata/...

stream v's native (raw)
"""


_importers = { }

def initialise():
#================
  global _importers
  loaders = repository.options.loaders
  for extn, cls in loaders.iteritems():
    try:
      _importers[extn] = getattr(fileformats, cls)
      logging.info("Importer for '%s': fileformats.%s", extn, cls)
    except AttributeError:
      logging.error("Unknown importer: fileformats.%s", cls)


def log_error(msg):
#==================
  logging.error(msg)
  return msg + '\n'


class Rest(object):
#==================

  @staticmethod
  def _pathname(name):
  #------------------
    paths = name.split('/')
    if len(paths) < 2 or not paths[1]: raise web.NotFound()
    return ('/'.join(paths[1:]), paths[-1])


  def GET(self, name):
  #-------------------
    # Also we may be GETting a signal, not a recording
    # - check rdf:type. If Signal then find/open bsml:recording
    source, filename = self._pathname(name)
    rec_uri = repository.base + source
    recording = repository.get_recording(rec_uri)
    if recording.source is None:
      log_error("Recording '%s' is not in repository" % source)
      raise web.NotFound()
    logging.debug("Streaming '%s'", recording.source)
    try:
      rfile = urllib.urlopen(str(recording.source)).fp
      web.header('Content-Type','binary/octet-stream')  # Or lookup what original was
      web.header('Transfer-Encoding','chunked')
      web.header('Content-Disposition', 'attachment; filename=%s' % filename)
      while True:
        data = rfile.read(32768)
        if not data: break
        yield data
      rfile.close()
    except Exception, msg:
      log_error("Error serving recording: %s" % msg)
      raise web.InternalError(msg)


  def PUT(self, name):
  #-------------------
    ctype = web.ctx.environ.get('CONTENT_TYPE', 'application/x-raw')
    if not ctype.startswith('application/x-'):
      return log_error("Invalid Content-Type: '%s'" % ctype)
    format = ctype[14:]

    # Can we also PUT RDF content ???

    RecordingClass = _importers.get(format)
    if not RecordingClass: raise web.NotFound()

    source = self._pathname(name)[0]
    file_uri = repository.base + source
    if repository.triplestore.contains(file_uri, rdf.type, BSML.Recording):
      return log_error("Import error: Recording '%s' is already in repository" % source)

    ##file_id   = str(uuid.uuid4()) + '.' + format
    ##file_name = os.path.abspath(os.path.join(repository.storepath, file_id))
    file_name = os.path.abspath(os.path.join(repository.storepath, source))
    try:    os.makedirs(os.path.dirname(file_name))
    except: pass

    try:
      output = open(file_name, 'wb')
      rfile = web.ctx.env['wsgi.input']
      while True:
        data = rfile.read(32768)
        if not data: break
        output.write(data)
      output.close()

      recording = RecordingClass(file_name, file_uri)
      recording.add_to_RDFmodel(repository.triplestore, bsml_mapping, Graph(file_uri))
      recording.close()
      repository.provenance.add(file_uri, ctype)

    except Exception, msg:
      return log_error("Import error '%s': %s -> %s" % (msg, source, file_name))

    logging.debug("Imported %s -> %s", source, file_name)

    location = '%s://%s/%s' % (web.ctx.environ['wsgi.url_scheme'],
                               web.ctx.environ['HTTP_HOST'],
                               name)
    # Does web.ctx give us the original URL ???
    raise web.Created(file_uri, {'Location': location, 'Content-Type': ctype})

  def POST(self, name):
  #--------------------
    source = self._pathname(name)[0]
    return "<html><body><p>POST: %s</p></body></html>" % source


  def DELETE(self, name):
  #----------------------
    ###print name, web.ctx.environ
    source, filename = self._pathname(name)
    rec_uri = repository.base + source
    recording = repository.get_recording(rec_uri)
    if recording.source is None:
      log_error("Recording '%s' is not in repository" % source)
      raise web.NotFound()

    file_name = urllib.urlopen(str(recording.source)).fp.name
    if file_name != '<socket>': os.unlink(file_name)
    ## But if multiple files in the recording?? eg. SDF, WFDB, ...

    repository.triplestore.remove_graph(Graph(rec_uri))
    repository.provenance.remove(rec_uri)

    logging.debug("Deleted '%s'", recording.source)
    raise web.OK


  def HEAD(self, name):
  #--------------------
    return "<html><body><p>HEAD: %s</p></body></html>" % name
