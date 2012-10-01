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
import httplib
import hashlib
from datetime import datetime

from tornado.options import options
import httpchunked

from biosignalml.utils import xmlescape
from biosignalml.model import BSML

import biosignalml.formats
import biosignalml.rdf as rdf

KnownSchemes = [ 'http', 'urn' ]


def raise_error(handler, code, msg=None):
#========================================
  handler.set_status(code)
  handler.set_header('Content-Type', 'text/xml')
  ### Return JSON...
  handler.write(('<bsml>\n <error>%s</error>\n</bsml>\n' % xmlescape(msg)) if msg else '')
  handler.finish()


class FileWriter(object):
#========================

  def __init__(self, fname, uri, cls):
  #----------------------------------
    self.fname = fname
    self.output = open(fname, 'wb')
    self.sha = hashlib.sha512()
    self.uri = uri
    self.Recording = cls

  def write(self, data):
  #---------------------
    logging.debug('Writing %d bytes', len(data))
    self.sha.update(data)
    try:
      self._output.write(data)
    except IOError, msg:
      raise_error(400, msg="%s: %s -> %s" % (msg, name, self._fname))


class ReST(httpchunked.ChunkedHandler):
#======================================

  SUPPORTED_METHODS = ("GET", "HEAD", "POST", "DELETE", "PUT", "OPTIONS", "PATCH")

  _mimetype = { }
  _class = { }
  _extns = { }

  for name, cls in biosignalml.formats.CLASSES.iteritems():
    _mimetype[name] = cls.MIMETYPE
    _class[cls.MIMETYPE] = cls
    for extn in cls.EXTENSIONS:
      _extns[extn] = cls.MIMETYPE

  def check_xsrf_cookie(self):
  #---------------------------
    """Don't check XSRF token for ReST POSTs."""
    pass

  def write_error(self, status_code, **kwds):
  #------------------------------------------
    self.finish("<html><title>%(code)d: %(message)s</title>"
                "<body>%(code)d: %(message)s</body></html>" % {
            "code": status_code,
            "message": httplib.responses[status_code],
            })

  def _write_error(self, status, msg=None):
  #----------------------------------------
    raise_error(self, status, msg)

  def _accept_headers(self):
  #-------------------------
    """
    Parse an Accept header and return a dictionary with
    mime-type as an item key and 'q' parameter as the value.
    """
    return { k[0].strip(): float(k[1].strip()[2:])
                             if (len(k) > 1 and k[1].strip().startswith('q=')) else 1
               for k in [ a.split(';', 1)
                for a in self.request.headers.get('Accept', '*/*').split(',') ] }

  def _get_names(self, name):
  #--------------------------
    tail = name.rsplit('#', 1)
    fragment = tail[1] if len(tail) > 1 else ''
    head = tail[0]
    parts = head.split('/')
    name = parts[-1].rsplit('.', 1)
    parts[-1] = name[0]     # Have removed extension
    uri = '/'.join(parts)
    if ':' in head and head.split(':', 1)[0] in KnownSchemes:
      return (uri, fragment)
    else:
      return (options.resource_prefix + head, fragment)


  def get(self, name, **kwds):
  #---------------------------

    # If the resource is a named graph then do we return the graph as RDF?

    uri, fragment = self._get_names(name)
    rec_uri, graph_uri = options.repository.get_recording_and_graph_uri(uri)
    logging.debug('GET: name=%s, req=%s, uri=%s, rec=%s, graph=%s',
                        name, self.request.uri, uri, rec_uri, graph_uri)
    if graph_uri is None:
      if name == '':
        graph_uri = options.repository.uri
        uri = ''
      elif options.repository.graph_has_provenance(uri):
        graph_uri = uri
        uri = ''
      else:
        self.send_error(404)
##        self._write_error(404, msg="Recording unknown for '%s'" % uri)
        return
    accept = self._accept_headers()

    if BSML.Recording in options.repository.get_types(uri, graph_uri):
      recording = options.repository.get_recording(rec_uri)
      ## logging.debug('REC %s: %s', recording, accept)  #####################
      ctype = getattr(recording, 'format')
## Should we set 'Content-Location' header as well?
## (to actual URL of representation returned).
      # only send recording if '*/*' or content type match
      if accept.get(ctype, 0) > 0: # send file
        if recording.dataset is None:
          self._write_error(404, msg="Missing recording dataset: '%s'" % rec_uri)
          return
        filename = str(recording.dataset)  ### ' '.join([str(f) for f in recording.dataset])   #### Why????
        logging.debug("Sending '%s'", filename)
        try:
          rfile = urllib.urlopen(filename).fp
          self.set_header('Vary', 'Accept')      # Let caches know we've used Accept header
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
    # Check for extension...
    # Check Q value
    # Send HTML if requested...

    # Either not a Recording or ctype not in accept header, so send RDF
    if   'text/turtle' in accept or 'application/x-turtle' in accept: format = rdf.Format.TURTLE
    elif 'application/json' in accept:                                format = rdf.Format.JSON
    else:                                                             format = rdf.Format.RDFXML
    ## 415 Unsupported Media Type if accept is not */* nor something we can serve...

    # check rdf+xml, turtle, n3, html ??
    self.set_header('Vary', 'Accept')      # Let caches know we've used Accept header
    self.set_header('Content-Type', rdf.Format.mimetype(format))
    self.write(options.repository.describe(uri, graph=graph_uri, format=format))

  def _format(self):
  #-----------------
    ctype = self.request.headers.get('Content-Type')
    if ctype in ['text/turtle', 'application/x-turtle']:
      return rdf.Format.TURTLE
    elif ctype == 'application/rdf+xml':
      return rdf.Format.RDFXML
    else:
      return None

  @staticmethod
  def _node(n):
  #------------
    if   n.is_resource(): return '<%s>' % str(n)
    elif n.is_blank():    return '_:%s' % str(n)
    elif n.is_literal():
      l = [ '"%s"' % n.literal[0] ]
      if   n.literal[1]: l.append('@%s'    % n.literal[1])
      elif n.literal[2]: l.append('^^<%s>' % n.literal[2])
      return ''.join(l)

  def put(self, name, **kwds):
  #---------------------------
    """
    Import a recording into the repository.

    """
    #logging.debug("URI, NM: %s, %s", self.request.uri, name)  #############
    #logging.debug("HDRS: %s", self.request.headers)
    rec_uri, fragment = self._get_names(name)
    ctype = self.request.headers.get('Content-Type')
    if ctype is None:
      ctype = ReST._extns.get(extn, 'application/x-raw')

    ## PUT of RDF in RDFXML, RDF/JSON and Turtle formats...

    if not ctype.startswith('application/x-'):
      self._write_error(415, msg="Invalid Content-Type: '%s'" % ctype)
      return
    RecordingClass = ReST._class.get(ctype)
    if not RecordingClass:
      self._write_error(415, msg="Unknown Content-Type: '%s'" % ctype)
      return
    file_name = os.path.abspath(os.path.join(options.recordings,
                                str(uuid.uuid1()) + '.' + RecordingClass.EXTENSIONS[0]))
    logging.debug('URI: %s, FILE: %s', rec_uri, file_name)

    ## Provenance will take care of multiple versions but need to check user can replace....
      return
    ## Also check u = rec_uri...
    try: os.makedirs(os.path.dirname(file_name))
    except OSError: pass
    newfile = FileWriter(file_name, rec_uri, RecordingClass)
    if not self.have_chunked(newfile, self.finished_put):
      newfile.write(self.request.body)
      self.finished_put(newfile)

  def finished_put(self, newfile):
  #-------------------------------
    newfile.output.close()
    logging.debug("Imported %s -> %s (%s)", newfile.dataset, newfile.uri, newfile.fname)
    recording = newfile.Recording.open(newfile.uri, fname=newfile.fname, digest=newfile.sha.hexdigest())
    options.repository.store_recording(recording)
    recording.close()

    # Or do we return HTML? RDF/XML of provenance? And include location in provenance...
    # OR a <status>Added...</status> message ???
    # OR <added>...</added>  ??
    # Content-type: XML? application/x-bsml+xml ???
    ## Return 200 OK since we are providing content
    ## Otherwise return Created()

    self.set_header('Content-Type', 'text/xml')
    self.set_status(200)
    location = str(recording.uri)
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

    self._write_error(501, msg="POST not implemented...")

    rec_uri = self._get_names(name)[0]
    if rec_uri: self.write("<html><body><p>POST: %s</p></body></html>" % rec_uri)


  def delete(self, name, **kwds):
  #------------------------------
    rec_uri, fragment = self._get_names(name)
    if rec_uri is None: return
    recording = options.repository.get_recording(rec_uri)
    if recording.dataset is None:
      self._write_error(404, msg="Recording '%s' is not in repository" % rec_uri)
      return
    if fragment:
      self._write_error(404, msg="Cannot delete fragment of '%s'" % rec_uri)
      return

    self._write_error(501, msg="DELETE not fully implemented...")
    return

    try:
      file_name = urllib.urlopen(str(recording.dataset)).fp.name
      if file_name != '<socket>': os.unlink(file_name)
    except IOError:
      pass
    ## But if multiple files in the recording?? eg. SDF, WFDB, ...
# Instead of deleting the graph we could add a provenance entry to say the record was deleted
# that isn't of type rdfg:Graph and is prv:precededBy the recording's graph...
    options.repository.remove_graph(recording.graph)
# With versioning we don't want to just remove latest version...
# Best to do as above -- make the graph a predecessor of a non-bsml:RecordingGraph.

    logging.debug("Deleted '%s' (%s)", rec_uri, recording.dataset)

    self.set_header('Content-Type', 'text/xml')
    sel.set_status(200)
    self.write('\n'.join(['<bsml>',
                          ' <deleted uri="%s"/>' % rec_uri,
                          '</bsml>', '']))


  def head(self, name, **kwds):
  #----------------------------
    self.write("<html><body><p>HEAD: %s</p></body></html>" % name)

  def patch(self, name, **kwds):
  #-----------------------------
      self.set_status(201)
      self.finish()
