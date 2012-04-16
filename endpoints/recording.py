######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $ID: 51e97a9 on Thu Mar 1 20:34:33 2012 +1300 by Dave Brooks $
#
######################################################
"""
Import and export recordings.

Recording files are transferred as the body of HTTP messages, with the `Content-Type`
header giving the recording's format. Chunked transfers are used if supprted (i.e. the
transport is HTTP/1.1).

"""

import logging
import uuid
import os
import urllib
import hashlib
from datetime import datetime

from tornado.options import options
import httpchunked

from biosignalml.utils import xmlescape
from biosignalml.model import BSML

import biosignalml.formats
import biosignalml.rdf as rdf

import metadata


def raise_error(handler, code, msg=None):
#========================================
  handler.set_status(code)
  handler.set_header('Content-Type', 'text/xml')
  handler.write(('<bsml>\n <error>%s</error>\n</bsml>\n' % xmlescape(msg)) if msg else '')
  handler.finish()


class FileWriter(object):
#========================

  def __init__(self, fname, uri, source, cls):
  #-------------------------------------------
    self._fname = fname
    self._output = open(fname, 'wb')
    self._sha = hashlib.sha512()
    self._uri = uri
    self._source = source
    self.Recording = cls

  def write(self, data):
  #---------------------
    logging.debug('Writing %d bytes', len(data))
    self._sha.update(data)
    try:
      self._output.write(data)
    except IOError, msg:
      raise_error(400, msg="%s: %s -> %s" % (msg, name, self._fname))


class ReST(httpchunked.ChunkedHandler):
#======================================

  _mimetype = { }
  _class = { }

  for name, cls in biosignalml.formats.CLASSES.iteritems():
    _mimetype[name] = cls.MIMETYPE
    _class[cls.MIMETYPE] = cls

  def _get_names(self, name):
  #--------------------------
    tail = name.rsplit('#', 1)
    fragment = tail[1] if len(tail) > 1 else ''
    head = tail[0]
    if head.startswith('http:'):
      return (head, head.replace('/', '_'), fragment)
    else:
      return (options.recording_prefix + head, head, fragment)

  def _write_error(self, status, msg=None):
  #----------------------------------------
    raise_error(self, status, msg)


  def get(self, name, **kwds):
  #----------------------------

    logging.debug('GET: %s, %s', name, self.request.uri)

    uri, filename, fragment = self._get_names(name)
    rec_uri = options.repository.get_recording_graph_uri(uri)
    if rec_uri is None:
      self._write_error(404, msg="Recording unknown for '%s'" % uri)
      return

    accept = metadata.acceptheaders(self.request)
    self.set_header('Vary', 'Accept')      # Let caches know we've used Accept header
    objtype = options.repository.get_type(uri, rec_uri)
    if objtype == BSML.Recording:
      recording = options.repository.get_recording(uri, rec_uri)
      ctype = ReST._mimetype.get(str(recording.format), 'application/x-raw')
## Should we set 'Content-Location' header as well?
## (to actual URL of representation returned).
      if ctype in accept: # send file
        if recording.source is None:
          self._write_error(404, msg="Missing recording source: '%s'" % source)
          return
        filename = str(recording.source)
        logging.debug("Streaming '%s'", filename)
        try:
          rfile = urllib.urlopen(filename).fp
          self.set_header('Content-Type', ctype)
          self.set_header('Content-Disposition', 'attachment; filename=%s' % filename)
          while True:
            data = rfile.read(32768)
            if not data: break
            self.write(data)
            self.flush()             ## This will chunk output
          rfile.close()
          self.finish()
        except Exception, msg:
          self._write_error(500, msg="Error serving recording: %s" % msg)
        return
    # Either not a Recording or ctype not in accept header, so send RDF
    format = rdf.Format.TURTLE if ('text/turtle' in accept
                                or 'application/x-turtle' in accept) else rdf.Format.RDFXML
    # check rdf+xml, turtle, n3, html ??
    self.set_header('Content-Type', rdf.Format.mimetype(format))
    self.write(options.repository.construct('?s ?p ?o',
                                            '?s ?p ?o FILTER (?p != <http://4store.org/fulltext#stem>'
                                                      + ' && (?s = <%(uri)s> || ?o = <%(uri)s>))',
                                            rec_uri, { 'uri': uri }, format))


  def put(self, name, **kwds):
  #---------------------------
    """
    Import a recording into the repository.

    """
    logging.debug("URI, NM: %s, %s", self.request.uri, name)  #############
    logging.debug("HDRS: %s", self.request.headers)
    ctype = self.request.headers.get('Content-Type', 'application/x-raw')
    if not ctype.startswith('application/x-'):
      self._write_error(415, msg="Invalid Content-Type: '%s'" % ctype)
      return

    RecordingClass = ReST._class.get(ctype)
    if not RecordingClass:
      self._write_error(415, msg="Unknown Content-Type: '%s'" % ctype)
      return

    rec_uri, fname, fragment = self._get_names(name)

    ##file_id   = str(uuid.uuid4()) + '.' + format
    ##file_name = os.path.abspath(os.path.join(options.repository.storepath, file_id))

    file_name = os.path.abspath(os.path.join(options.recordings, fname))

    #if container: file_uri = os.path.split(file_uri)[0]

    logging.debug('URI: %s, FILE: %s', rec_uri, file_name)

    if options.repository.check_type(rec_uri, BSML.Recording):
      self._write_error(409, msg="Recording '%s' is already in repository" % rec_uri)
      return

    try:            os.makedirs(os.path.dirname(file_name))
    except OSError: pass

    writer = FileWriter(file_name, rec_uri, name, RecordingClass)
    if not self.have_chunked(writer, self.finished_put):
      writer.write(self.request.body)
      self.finished_put(writer)


  def finished_put(self, writer):
  #------------------------------
    writer._output.close()
    recording = writer.Recording.open(writer._fname, uri=writer._uri, digest=writer._sha.hexdigest())
    options.repository.replace_graph(recording.uri, recording.metadata_as_graph().serialise())
    recording.close()


    logging.debug("Imported %s -> %s (%s)", writer._source, writer._fname, writer._uri)

    # Or do we return HTML? RDF/XML of provenance? And include location in provenance...
    # OR a <status>Added...</status> message ???
    # OR <added>...</added>  ??
    # Content-type: XML? application/x-bsml+xml ???
    ## Return 200 OK since we are providing content
    ## Otherwise return Created()

    self.set_header('Content-Type', 'text/xml')
    self.set_status(200)
    location = '%s://%s/%s' % (self.request.protocol, self.request.host, writer._source)
    self.set_header('Location', location)
    #self.set_header('Location', str(recording.uri))
    self.write('\n'.join(['<bsml>',
                          ' <created',
                          '  class="recording"',
                          '  uri="%s"'      % location, ## recording.uri
                          '  mimetype="%s"' % writer.Recording.MIMETYPE,
                          '  />',
                          '</bsml>', '']))


  def post(self, name, **kwds):
  #-----------------------------
    logging.debug('POST: %s', self.request.headers)
    rec_uri = self._get_names(name)[0]
    if source: self.write("<html><body><p>POST: %s</p></body></html>" % rec_uri)


  def delete(self, name, **kwds):
  #------------------------------
    rec_uri, fname, fragment = self._get_names(name)
    if rec_uri is None: return
    recording = options.repository.get_recording(rec_uri)
    if recording.source is None:
      self._write_error(404, msg="Recording '%s' is not in repository" % rec_uri)
      return
    if fragment:
      self._write_error(404, msg="Cannot delete fragment of '%s'" % rec_uri)
      return

    try:
      file_name = urllib.urlopen(str(recording.source)).fp.name
      if file_name != '<socket>': os.unlink(file_name)
    except IOError:
      pass
    ## But if multiple files in the recording?? eg. SDF, WFDB, ...

    options.repository.remove_graph(rec_uri)
    logging.debug("Deleted '%s' (%s)", rec_uri, recording.source)

    self.set_header('Content-Type', 'text/xml')
    sel.set_status(200)
    self.write('\n'.join(['<bsml>',
                          ' <deleted uri="%s"/>' % rec_uri,
                          '</bsml>', '']))


  def head(self, name, **kwds):
  #----------------------------
    self.write("<html><body><p>HEAD: %s</p></body></html>" % name)
