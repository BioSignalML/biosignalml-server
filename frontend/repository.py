######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $ID$
#
######################################################


import logging
import tornado.web
from tornado.options import options

from biosignalml.rdf.formats import Format



class metadata(tornado.web.RequestHandler):
#==========================================

  def get(self, name, **kwds):
  #---------------------------
    #logging.debug('GET: %s', self.request.headers)
    ## Build a new RDF Graph that has { <uri> ?p ?o  } UNION { ?s ?p <uri> }
    ## and serialise this??

    graph_uri = options.repository.get_recording_graph_uri(name)
    if graph_uri is not None:
      accept = { k[0].strip(): k[1].strip() if len(k) > 1 else ''
                   for k in [ a.split(';', 1)
                    for a in self.request.headers.get('Accept', '*/*').split(',') ] }
      # check rdf+xml, turtle, n3, html ??
      format = rdf.Format.TURTLE if ('text/turtle' in accept
                                  or 'application/x-turtle' in accept) else rdf.Format.RDFXML
      self.set_header('Content-Type', rdf.Format.mimetype(format))
      self.write(options.repository.construct(
                   '?s ?p ?o', 'graph <%s> { ?s ?p ?o' % graph_uri
                 + ' FILTER (?p != <http://4store.org/fulltext#stem>'
                 + ' && (?s = <%s> || ?o = <%s>)) }' % (name, name), format))
    else:
      self.send_error(404)

