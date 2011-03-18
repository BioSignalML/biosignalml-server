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

from repository import options, triplestore, get_recording

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
  loaders = options.loaders
  for extn, cls in loaders.iteritems():
    try:
      _importers[extn] = getattr(fileformats, cls)
      logging.info("Importer for '%s': fileformats.%s", extn, cls)
    except AttributeError:
      logging.error("Unknown importer: fileformats.%s", cls)


class Rest(object):
#==================

  def GET(self, name):
  #-------------------
    paths = name.split('/')
    if len(paths) < 2 or not paths[1]: raise web.NotFound()

    ## Who is our client?
    ## What type of content have they requested???
     
    source = '/'.join(paths[1:])
    rec_uri = options.repository['base'] + source
    recording = get_recording(rec_uri)
    if getattr(recording, 'source', None) is None:
      logging.error("Recording '%s' is not in repository", source)
      raise web.NotFound()
    logging.debug("Streaming '%s'", recording.source)
    try:
      rfile = urllib.urlopen(str(recording.source)).fp
      web.header('Content-Type','binary/octet-stream')
      web.header('Transfer-Encoding','chunked')
      web.header('Content-Disposition', 'attachment; filename=%s' % paths[-1])
      while True:
        data = rfile.read(32768)
        if not data: break
        yield data
      rfile.close()
    except Exception, msg:
      logging.error("Error serving recording: %s", msg)
      raise web.InternalError(msg)


  def POST(self, name):
  #---------------
    paths = name.split('/')
    if len(paths) < 2 or not paths[1]: raise web.NotFound()
    return "<html><body><p>POST: %s</p></body></html>" % paths


  def HEAD(self, name):
  #--------------------
    return "<html><body><p>HEAD: %s</p></body></html>" % name


  def PUT(self, name):
  #-------------------
    paths = name.split('/')
    if len(paths) < 2 or not paths[1]: raise web.NotFound()
    source = '/'.join(paths[1:])

    ctype = web.ctx.get('CONTENT_TYPE', None)
    if ctype and ctype.startswith('application/x-'): format = ctype[14:]
    else:                                            format = 'raw'
    RecordingClass = _importers.get(format)
    if not RecordingClass: raise web.NotFound()

    file_uri = options.repository['base'] + source
    if triplestore.contains(file_uri, rdf.type, BSML.Recording):
      err = "Import error: Recording '%s' is already in repository" % source
      logging.error(err)
      return err + '\n'

    ##file_id   = str(uuid.uuid4()) + '.' + format
    ##file_name = os.path.abspath(os.path.join(options.repository['signals'], file_id))
    file_name = os.path.abspath(os.path.join(options.repository['signals'], source))
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

      graph = Graph(file_uri)
      recording = RecordingClass(file_name, file_uri)
      recording.add_to_RDFmodel(triplestore, bsml_mapping, graph)

      ## Add source, date/time, etc statements.
      triplestore.append(file_uri, dct.dateSubmitted, datetime.utcnow().isoformat())

      recording.close()

    except Exception, msg:
      err = "Import error '%s': %s -> %s" % (msg, '/'.join(paths), file_name)
      logging.error(err)
      return err + '\n'

    logging.debug("Imported %s -> %s", '/'.join(paths), file_name)
    return file_uri + '\n'       ## Do we retirn text/xml with result or error msg ??

