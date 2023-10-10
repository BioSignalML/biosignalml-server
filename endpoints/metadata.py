import logging

import tornado.web
from tornado.options import options

from biosignalml import BSML
import biosignalml.rdf as rdf
import biosignalml.formats as formats

from .resource import parse_accept
from frontend import user


class MetaData(tornado.web.RequestHandler):
#==========================================

  SUPPORTED_METHODS = ("GET", "HEAD", "PUT", "POST") ##, "DELETE")

  def check_xsrf_cookie(self):
  #---------------------------
    """Don't check XSRF token for POSTs."""
    pass

  @user.capable(user.ACTION_VIEW)
  def get(self, **kwds):
  #----------------------
    if hasattr(self, 'full_uri'): name = self.full_uri
    else: name = self.request.uri.split('/', 3)[3]  # Starts with '/frontend/rdf/'
    # If the resource is a named graph then do we return the graph as RDF?
    repo = options.repository
    uri = name.split('#', 1)[0].split('?', 1)[0]
    graph_uri = repo.get_resource_graph_uri(uri)
    if graph_uri is None:
      if uri == '': graph_uri = repo.uri
      elif repo.has_provenance(uri):
        graph_uri = uri
        uri = ''
    accept = parse_accept(self.request.headers)
    if   'text/turtle' in accept or 'application/x-turtle' in accept: format = rdf.Format.TURTLE
    elif 'application/json' in accept:                                format = rdf.Format.JSON
    else:                                                             format = rdf.Format.RDFXML
    ## 415 Unsupported Media Type if accept is not */* nor something we can serve...
    self.set_header('Vary', 'Accept')      # Let caches know we've used Accept header
    self.set_header('Content-Type', rdf.Format.mimetype(format))
    self.write(options.repository.describe(uri, graph=graph_uri, format=format))

  @user.capable(user.ACTION_EXTEND)
  def put(self, **kwds):
  #---------------------
    if not hasattr(self, 'full_uri'):
      self.set_status(405)   # Method not allowed
      return
    rec_uri = self.full_uri.split('#', 1)[0].split('?', 1)[0]
    ## check uri doesn't exist?? Or authorisation to overwrite??
    try:
      g = rdf.Graph.create_from_string(rec_uri, self.request.body,
       self.request.headers.get('Content-Type', rdf.Format.RDFXML))
    except Exception as msg:
      logging.error('Cannot create RDF graph -- syntax errors? %s', msg)
      self.set_status(400)
      return
    if not g.contains(rdf.Statement(rec_uri, rdf.RDF.type, BSML.Recording)):
      logging.error("Metadata doesn't describe a bsml:Recording")
      self.set_status(400)
      return

    format = str(g.get_object(rec_uri, rdf.DCT.format))
    if format is None or format == formats.BSMLRecording.MIMETYPE:
      RecordingClass = formats.HDF5Recording
      g.set_subject_property(rec_uri, rdf.DCT.format, formats.HDF5Recording.MIMETYPE)
    else:
      RecordingClass = formats.CLASSES.get(format)
      if RecordingClass is None:
        logging.error("Repository doesn't support requested Recording class")
        self.set_status(400)
        return
    rec = RecordingClass.create_from_graph(rec_uri, g)
    rec.close()

    # Actual file gets assigned a name and created when data is first streamed to it.
    # Don't set hdf5 metadata block -- this is for export_hdf5 (see below).

    graph_uri = options.repository.add_recording_graph(rec_uri, g.serialise(), self.user)
    self.set_status(201)      # Created
    self.set_header('Location', str(graph_uri))


  @user.capable(user.ACTION_MODIFY)
  def post(self, **kwds):
  #----------------------
    if not hasattr(self, 'full_uri'):
      self.set_status(405)   # Method not allowed
      return
    uri = self.full_uri.split('#', 1)[0].split('?', 1)[0]
    rec_graph, rec_uri = options.repository.get_graph_and_recording_uri(uri)
    if rec_graph is None:
      logging.error('Unknown resource in repository: %s', uri)
      self.set_status(404)
      return
    try:
      options.repository.extend_graph(rec_graph,
        self.request.body,
        self.request.headers.get('Content-Type', rdf.Format.RDFXML))
    except Exception as msg:
      logging.error('Cannot extend RDF graph -- syntax errors? %s', msg)
      self.set_status(400)
      return
    self.set_status(200)      # OK
    self.set_header('Location', str(rec_uri))
