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
import urlparse
import httplib
import hashlib
from datetime import datetime

import tornado.web as web
from tornado.options import options

import biosignalml.rdf as rdf
from biosignalml.utils import xmlescape
from biosignalml.model import BSML
from biosignalml.formats import BSMLRecording, RAWRecording
from biosignalml.formats import CLASSES as RECORDING_CLASSES

KnownSchemes = [ 'http', 'urn' ]


"""
Media Fragment handling (also check for '?t='
    mtag = str(self.about).rfind('#t=')
    if mtag >= 0:
      from biosignalml.timeline import Instant, Interval
      try:
        times = re.match('(.*?)(,(.*))?$', str(self.about)[mtag+3:]).groups()
        start = float(times[0]) if times[0] else 0.0
        end = float(times[2])
        self._time = Instant(None, start) if start == end else Interval(None, start, end=end)
      except ValueError:
        pass
"""

def raise_error(handler, code, msg=None):
#========================================
  handler.set_status(code)
  handler.set_header('Content-Type', 'text/xml')
  ### Return JSON...
  handler.write(('<bsml>\n <error>%s</error>\n</bsml>\n' % xmlescape(msg)) if msg else '')
  handler.finish()


def parse_accept(headers):
#-------------------------
  """
  Parse an Accept header and return a dictionary with
  mime-type as an item key and 'q' parameter as the value.
  """
  return { k[0].strip(): float(k[1].strip()[2:])
                           if (len(k) > 1 and k[1].strip().startswith('q=')) else 1
             for k in [ a.split(';', 1)
              for a in headers.get('Accept', '*/*').split(',') ] }


class FileWriter(object):
#========================

  def __init__(self, fname, uri, cls):
  #----------------------------------
    self.fname = fname
    self.uri = uri
    self.Recording = cls
    self._output = open(fname, 'wb')
    self._sha = hashlib.sha512()

  def write(self, data):
  #---------------------
    self._sha.update(data)
    try:
      self._output.write(data)
    except IOError, msg:
      raise_error(400, msg="%s: %s -> %s" % (msg, self.uri, self.fname))

  def close(self):
  #---------------
    self._output.close()

  def hexdigest(self):
  #-------------------
    return self._sha.hexdigest()


class Recording(web.RequestHandler):
#===================================

  SUPPORTED_METHODS = ("GET", "HEAD", "POST", "DELETE", "PUT")

  _extns = { }
  for mtype, cls in RECORDING_CLASSES.iteritems():
    for extn in cls.EXTENSIONS:
      if extn in _extns:
        raise ValueError("Duplicate extension: %s", extn)
      _extns[extn] = mtype

  def check_xsrf_cookie(self):
  #---------------------------
    """Don't check XSRF token for POSTs."""
    pass

#  def write_error(self, status_code, **kwds):
#  #------------------------------------------
#    self.finish("<html><title>%(code)d: %(message)s</title>"
#                "<body>%(code)d: %(message)s</body></html>" % {
#            "code": status_code,
#            "message": httplib.responses[status_code],
#            })

  def _write_error(self, status, msg=None):
  #----------------------------------------
    logging.error("Error %d: %s", status, '' if msg is None else msg)
    raise_error(self, status, msg)

  @staticmethod
  def _get_names(name):
  #--------------------
    tail = name.split('#', 1)
    fragment = tail[1] if len(tail) > 1 else ''
    head = tail[0]
    parts = head.split('/')
    name = parts[-1].rsplit('.', 1)
    parts[-1] = name[0]     # Have removed extension
    uri = '/'.join(parts)
    if ':' in head and head.split(':', 1)[0] in KnownSchemes:
      return (uri, fragment)
    else:
      return (options.repository_uri + head, fragment)


##  @user.capable(user.ACTION_VIEW)
  def get(self, **kwds):
  #---------------------
    name = self.full_uri

    uri, fragment = self._get_names(name)

    graph_uri, rec_uri = options.repository.get_graph_and_recording_uri(uri)
    logging.debug('GET: name=%s, req=%s, uri=%s, rec=%s, graph=%s',
                        name, self.request.uri, uri, rec_uri, graph_uri)
    if graph_uri is None:
      if name == '':
        graph_uri = options.repository.uri
        uri = ''
      elif options.repository.has_provenance(uri):
        graph_uri = uri
        uri = ''
      else:
        self.send_error(404)
##        self._write_error(404, msg="Recording unknown for '%s'" % uri)
        return
    accept = parse_accept(self.request.headers)

    if BSML.Recording in options.repository.get_types(uri, graph_uri):
      recording = options.repository.get_recording(rec_uri, with_signals=False, open_dataset=False,
                                                                                graph_uri=graph_uri)
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
        # Tornado's defaults to sending with ChunkedTransferEncoding
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


  def _get_length(self):
  #---------------------
    self._stream.read_until('\r\n', self._got_length)

  def _got_length(self, data):
  #------------------------------
    assert data[-2:] == '\r\n', 'Bad chunk length'
    self._chunk_length = int(data[:-2], 16)
    if self._chunk_length > 0:
      self._stream.read_bytes(self._chunk_length + 2, self._read_callback,
                              streaming_callback=self._got_data)
    else:
      self._finished_read()

  def _got_data(self, data):
  #-------------------------
    l = min(len(data), self._chunk_length)
    self._file.write(data[:l])
    self._chunk_length -= l
    if self._chunk_length == 0:
      assert data[-2:] == '\r\n', 'Bad data chunk'
      self._get_length()

  def _read_callback(self, data):
  #------------------------------
    assert len(data) == 0, 'Data outside chunk??'

  def _chunked_read(self):
  #-----------------------
    if (self.request.headers.get('Transfer-Encoding') == 'chunked'
    and self.request.headers.get('Expect') == '100-continue'
    and not 'Content-Length' in self.request.headers):
      self._stream = self.request.connection.stream
      self._auto_finish = False
      self._get_length()
      self.request.write("HTTP/1.1 100 (Continue)\r\n\r\n")
      return True
    return False

##  @user.capable(user.ACTION_EXTEND)
    ## Provenance will take care of multiple versions but need to check user can replace....
  def put(self, **kwds):
  #---------------------
    """
    Import a recording into the repository.

    """
    u = urlparse.urlparse(self.full_uri)
    path, extn = os.path.splitext(u.path)
    if extn != '': extn = extn[1:]
    rec_uri = urlparse.urlunparse((u.scheme, u.netloc, path, '', '', ''))
    ctype = self.request.headers.get('Content-Type')
    if ctype == BSMLRecording.MIMETYPE and extn != '':
      ctype = Recording._extns.get(extn, RAWRecording.MIMETYPE)
    RecordingClass = RECORDING_CLASSES.get(ctype)
    if RecordingClass is None:
      self._write_error(415, msg="Unsupported recording format: %s" % ctype)
      return
    if options.repository.has_recording(rec_uri):
      self._write_error(409, msg="Recording already exists in repository")
      return
    fname = os.path.join(options.recordings_path, str(uuid.uuid1()) + '.' + RecordingClass.EXTENSIONS[0])
    self._file = FileWriter(fname, rec_uri, RecordingClass)
    if not self._chunked_read():
      self._file.write(self.request.body)
      self._finished_read()

  def _finished_read(self):
  #------------------------
    self._file.close()
    ## We've streamed a file to somewhere on our file system
    ## Now open the file and put metadata into triplestore
    try:
      recording = self._file.Recording(self._file.uri, dataset=self._file.fname, digest=self._file.hexdigest())
      options.repository.store_recording(recording)
      recording.close()
      logging.debug("Imported %s -> %s", self._file.uri, self._file.fname)
    except Exception, msg:
      self._write_error(415, msg=str(msg))
      return

    # Or do we return HTML? RDF/XML of provenance? And include location in provenance...
    # OR a <status>Added...</status> message ???
    # OR <added>...</added>  ??
    # Content-type: XML? application/x-bsml+xml ???
    ## Return 200 OK since we are providing content
    ## Otherwise return Created()

    self.set_header('Content-Type', 'text/xml')
    self.set_status(201)      # Created
    location = str(recording.uri)
    self.set_header('Location', location)
    #self.set_header('Location', str(recording.uri))
    self.write('\n'.join(['<bsml>',
                          ' <created',
                          '  class="recording"',
                          '  uri="%s"'      % location, ## recording.uri
                          '  mimetype="%s"' % recording.MIMETYPE,
                          '  />',
                          '</bsml>', '']))
    self.finish()


##  @user.capable(user.ACTION_MODIFY)
  def post(self, **kwds):
  #-----------------------
    name = self.full_uri
    raise web.HTTPError(501, "POST not implemented...")
    rec_uri = self._get_names(name)[0]
    if rec_uri: self.write("<html><body><p>POST: %s</p></body></html>" % rec_uri)


##  @user.capable(user.ACTION_DELETE)
  def delete(self, **kwds):
  #------------------------
    name = self.full_uri
    rec_uri, fragment = self._get_names(name)
    if rec_uri is None: return
    recording = options.repository.get_recording(rec_uri, with_signals=False, open_dataset=False)
    if recording.dataset is None:
      self._write_error(404, msg="Recording '%s' is not in repository" % rec_uri)
      return
    if fragment:
      self._write_error(404, msg="Cannot delete fragment of '%s'" % rec_uri)
      return

    self._write_error(501, msg="DELETE not fully implemented...")
    ## Need to consider what happens to RDF graphs...
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
