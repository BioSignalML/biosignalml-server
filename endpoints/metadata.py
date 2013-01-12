import logging

import tornado.web
from tornado.options import options

import biosignalml.rdf as rdf
from biosignalml import BSML
from biosignalml.formats import HDF5Recording

import resource
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
    uri = name.split('#')[0]
    graph_uri = repo.get_resource_graph_uri(uri)
    if graph_uri is None:
      if name == '':
        graph_uri = repo.uri
        uri = ''
      elif repo.has_provenance(uri):
        graph_uri = uri
        uri = ''
    accept = resource.parse_accept(self.request.headers)
    if   'text/turtle' in accept or 'application/x-turtle' in accept: format = rdf.Format.TURTLE
    elif 'application/json' in accept:                                format = rdf.Format.JSON
    else:                                                             format = rdf.Format.RDFXML
    ## 415 Unsupported Media Type if accept is not */* nor something we can serve...
    self.set_header('Vary', 'Accept')      # Let caches know we've used Accept header
    self.set_header('Content-Type', rdf.Format.mimetype(format))
    self.write(options.repository.describe(uri, graph=graph_uri, format=format))


  @user.capable(user.ACTION_MODIFY)
  def put(self, **kwds):
  #---------------------
    if hasattr(self, 'full_uri'): name = self.full_uri
    else: name = self.request.uri.split('/', 2)[2]

    uri = name.split('#')[0]

    ## Get user via token or cookie, check we know them, get what they are allowed to do...
    user = "dave@bcs.co.nz"
    ##replace = True   ## Depends on user's capability

    """
    check name doesn't exist?? Or authorisation to overwrite??

    check name is valid i.e. uri doesn't clash with reserved repository paths

    check name is inside respository's domain...
    """

    g = rdf.Graph.create_from_string(rec_uri, self.request.body,
     self.request.headers.get('Content-Type', rdf.Format.RDFXML))
    if not g.contains(rdf.Statement(rec_uri, rdf.RDF.type, BSML.Recording)):
      raise TypeError("Metadata doesn't describe a bsml:Recording")
    if not g.contains(rdf.Statement(rec_uri, rdf.DCT.format, HDF5Recording.MIMETYPE)):
      raise ValueError("Metadata doesn't describe an HDF5 recording")

    rec = HDF5Recording.create_from_graph(rec_uri, g)
    rec.close()

    # Actual HDF5 gets assigned a name and created when data is first
    # streamed to it.
##    g.append(rdf.Statement(rec_uri, BSML.dataset, fname))


    graph_uri = options.repository.add_recording_graph(rec_uri, g.serialise(), user)

    # Don't set hdf5 metadata block -- thisis for export_hdf5 (see below).

    self.set_status(201)      # Created
    self.set_header('Location', str(graph_uri))


  @user.capable(user.ACTION_MODIFY)
  def post(self, **kwds):
  #----------------------
    if hasattr(self, 'full_uri'): rec_uri = self.full_uri
    else: rec_uri = self.request.uri.split('/', 2)[2]

    logging.debug('POST: name=%s, hdr=%s', rec_uri, self.request.headers)

    ## Checks on user as above...  ###

    rec_graph, rec_uri = options.repository.get_graph_and_recording_uri(rec_uri)
    if rec_graph is None:
      raise KeyError('Unknown resource graph in repository')
    options.repository.extend_graph(rec_graph,
      self.request.body,
      self.request.headers.get('Content-Type', rdf.Format.RDFXML))

    self.set_status(200)      # OK
    self.set_header('Location', str(rec_uri))


    """
    ===>  Need a "export_hdf5 URI" utility


    What about a new dataset in HDF5 file?? Or will append create this??

    """



