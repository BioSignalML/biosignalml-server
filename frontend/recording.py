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
import hashlib
from datetime import datetime

from utils import xmlescape
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

# Raising web.errors in web.py sets Content-type to text/html.
# If we are returning <biosigml> then we should raise web.HTTPError
# directly, setting Content-type to text/xml or application/x-biosigml+xml


class HTTPError(web.HTTPError):
#==============================
  
  def __init__(self, status, message=None):
  #----------------------------------------
    if message is None: message = status.split(" ", 1)[1].lower()
    headers = {'Content-Type': 'text/html'}
    web.HTTPError.__init__(self, status, headers, message)


class BadRequest(HTTPError):             # Missing from web.py
#===========================

  def __init__(self, message=None):
  #--------------------------------
    status = '400 Bad Request'
    HTTPError.__init__(self, status, message)


class Conflict(HTTPError):               # Missing from web.py
#=========================

  def __init__(self, message=None):
  #--------------------------------
    status = '409 Conflict'
    HTTPError.__init__(self, status, message)


class UnsupportedMediaType(HTTPError):   # Missing from web.py
#=====================================
  
  def __init__(self, message=None):
  #--------------------------------
    status = '415 Unsupported Media Type'
    HTTPError.__init__(self, status, message)


_importers = { }

def initialise():
#================
  global _importers
  loaders = repository.options.loaders
  for extn, cls in loaders.iteritems():
    if extn[0] != '/': container = False
    else:
      container = True
      extn = extn[1:]
    try:
      _importers[extn] = (getattr(fileformats, cls), container)
      logging.info("Importer for '%s': fileformats.%s", extn, cls)
    except AttributeError:
      logging.error("Unknown importer: fileformats.%s", cls)


def log_error(msg):
#==================
  logging.error(msg)
  return '\n'.join(['<biosigml>',
                    ' <error>%s</error>' % xmlescape(msg),
                    '</biosigml>', ''])


class Rest(object):
#==================

  @staticmethod
  def _pathname(name):
  #------------------
    paths = name.split('/')
    if len(paths) < 2 or not paths[1]:
      raise web.NotFound(log_error("Cannot find '%s'" % name))
    tail = paths[-1].split('#', 1)
    fragment = tail[1] if len(tail) > 1 else ''
    paths[-1] = tail[0]
    return ('/'.join(paths[1:]), tail[0], fragment)


  def GET(self, name):
  #-------------------
    source, filename, fragment = self._pathname(name)
    rec_uri = repository.base + source

    ## From browser with Tabulator...
    ## env['HTTP_ACCEPT'] == 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    ## From curl
    ##    'HTTP_ACCEPT': '*/*'
    accept = { k[0]: k[1] if len(k) > 1 else ''
                for k in [ a.split(';', 1)
                  for a in web.ctx.environ.get('HTTP_ACCEPT', '*/*').split(',') ] }
    if 'application/xml' in accept:  ## Really need 'startswith()' (and look for rdf...)
      web.header('Content-Type','application/rdf+xml')  # Or lookup what original was
      yield repository.describe(rec_uri).serialise('rdfxml')
      return

    # Also we may be GETting a signal, not a recording
    # - check rdf:type. If Signal then find/open bsml:recording
    source, filename, fragment = self._pathname(name)
    rec_uri = repository.base + source
    recording = repository.get_recording(rec_uri)
    if recording.source is None:
      raise web.NotFound(log_error("Recording '%s' is not in repository" % source))
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
      raise web.InternalError(log_error("Error serving recording: %s" % msg))


  def PUT(self, name):
  #-------------------
    ctype = web.ctx.environ.get('CONTENT_TYPE', 'application/x-raw')
    if not ctype.startswith('application/x-'):
      raise UnsupportedMediaType(log_error("Invalid Content-Type: '%s'" % ctype))
    format = ctype[14:]

    # Can we also PUT RDF content ???

    RecordingClass, container = _importers.get(format, (None, None))
    if not RecordingClass:
      raise UnsupportedMediaType(log_error("Unknown Content-Type: '%s'" % ctype))

    source = self._pathname(name)[0]

    ##file_id   = str(uuid.uuid4()) + '.' + format
    ##file_name = os.path.abspath(os.path.join(repository.storepath, file_id))
    file_name = os.path.abspath(os.path.join(repository.storepath, source))
    if getattr(RecordingClass, 'normalise_name', None):
      file_name = RecordingClass.normalise_name(file_name)
    print file_name
    file_uri = repository.base + file_name[len(os.path.abspath(repository.storepath))+1:]
    if container: file_uri = os.path.split(file_uri)[0]
    print file_uri
    if repository.triplestore.contains(file_uri, rdf.type, BSML.Recording):
      raise Conflict(log_error("Recording '%s' is already in repository" % file_uri))

    try:    os.makedirs(os.path.dirname(file_name))
    except: pass
    try:
      output = open(file_name, 'wb')
      rfile = web.ctx.env['wsgi.input']
      sha = hashlib.sha512()
      while True:
        data = rfile.read(32768)       ##
        if not data: break             ## Can we detect broken stream and raise error ???
        sha.update(data)
        output.write(data)
      output.close()

      recording = RecordingClass(file_name, file_uri)
      recording.add_to_RDFmodel(repository.triplestore, bsml_mapping, Graph(file_uri))
      recording.close()
      # Include location in provenance?? See below.
      repository.provenance.add(recording.uri,
        ## Past a list of (property, value) tuples??
        ctype, sha.hexdigest())

    except Exception, msg:
      raise BadRequest(log_error("%s: %s -> %s" % (msg, source, file_name)))

    logging.debug("Imported %s -> %s", source, file_name)

    location = '%s://%s/%s' % (web.ctx.environ['wsgi.url_scheme'],
                               web.ctx.environ['HTTP_HOST'],
                               name)
    # Does web.ctx give us the original URL ???
    body = '\n'.join(['<biosigml>',
                      ' <recording',
                      '  uri="%s"'      % recording.uri,
                      '  location="%s"' % location,
                      '  content="%s"'  % ctype,
                      '  />',
                      '</biosigml>', ''])
    # Or do we return HTML? RDF/XML of provenance? And include location in provenance...
    # OR a <status>Added...</status> message ???
    # OR <added>...</added>  ??
    raise web.Created(body, {'Location': location, 'Content-Type': ctype})


  def POST(self, name):
  #--------------------
    source = self._pathname(name)[0]
    return "<html><body><p>POST: %s</p></body></html>" % source


  def DELETE(self, name):
  #----------------------
    ###print name, web.ctx.environ
    source, filename, fragment = self._pathname(name)
    rec_uri = repository.base + source
    recording = repository.get_recording(rec_uri)
    if recording.source is None:
      raise web.NotFound(log_error("Recording '%s' is not in repository" % rec_uri))
    if fragment:
      raise web.NotFound(log_error("Cannot delete fragment of '%s'" % rec_uri))

    try:
      file_name = urllib.urlopen(str(recording.source)).fp.name
      if file_name != '<socket>': os.unlink(file_name)
    except IOError:
      pass
    ## But if multiple files in the recording?? eg. SDF, WFDB, ...

    repository.triplestore.remove_graph(Graph(rec_uri))
    repository.provenance.remove(rec_uri)

    logging.debug("Deleted '%s' (%s)", rec_uri, recording.source)
    raise web.OK('\n'.join(['<biosigml>',
                            ' <status>Deleted %s</status>' % rec_uri,
                            '</biosigml>', '']))
    # OR <deleted>...</deleted> ???


  def HEAD(self, name):
  #--------------------
    return "<html><body><p>HEAD: %s</p></body></html>" % name
