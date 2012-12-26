import logging
from tornado.options import options

import biosignalml.rdf as rdf
import resource


class MetaData(resource.ReST):
#=============================

  SUPPORTED_METHODS = ("GET", "HEAD") ## , "POST", "DELETE", "PUT")

  def get(self, name, **kwds):
  #---------------------------
    # If the resource is a named graph then do we return the graph as RDF?
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
    accept = self._accept_headers()

    # Either not a Recording or ctype not in accept header, so send RDF
    if   'text/turtle' in accept or 'application/x-turtle' in accept: format = rdf.Format.TURTLE
    elif 'application/json' in accept:                                format = rdf.Format.JSON
    else:                                                             format = rdf.Format.RDFXML
    ## 415 Unsupported Media Type if accept is not */* nor something we can serve...

    # check rdf+xml, turtle, n3, html ??
    self.set_header('Vary', 'Accept')      # Let caches know we've used Accept header
    self.set_header('Content-Type', rdf.Format.mimetype(format))
    self.write(options.repository.describe(uri, graph=graph_uri, format=format))


