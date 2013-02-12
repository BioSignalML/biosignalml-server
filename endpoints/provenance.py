######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2012  David Brooks
#
######################################################
"""
Serve provenance grapoh as RDF.
"""

import logging

import tornado
from tornado.options import options


import biosignalml.rdf as rdf


class ProvenanceRDF(tornado.web.RequestHandler):
#===============================================

  def check_xsrf_cookie(self):
  #---------------------------
    """Don't check XSRF token for RDF"""
    pass

  def _accept_headers(self):
  #-------------------------
    """
    Parse an Accept header and return a dictionary with
    mime-type as an item key and its parameters as the value.
    """
    return { k[0].strip(): k[1].strip() if len(k) > 1 else ''
               for k in [ a.split(';', 1)
                for a in self.request.headers.get('Accept', '*/*').split(',') ] }

  def get(self, name=None):
  #------------------------
    accept = self._accept_headers()
    if   'text/turtle' in accept or 'application/x-turtle' in accept: format = rdf.Format.TURTLE
    elif 'application/json' in accept:                                format = rdf.Format.JSON
    else:                                                             format = rdf.Format.RDFXML
    ## 415 Unsupported Media Type if accept is not */* nor something we can serve...
    # check rdf+xml, turtle, n3, html ??
    self.set_header('Vary', 'Accept')      # Let caches know we've used Accept header
    self.set_header('Content-Type', rdf.Format.mimetype(format))

    graph_uri = options.repository.provenance_uri()
    if name is None:
      self.write(options.repository.construct('?s ?p ?o', '?s ?p ?o', graph=graph_uri, format=format))
    else:
      if name.startswith('http:'): uri = name
      else: uri = graph_uri + '/' + name
      self.write(options.repository.construct('?s ?p ?o',
                                              '?s ?p ?o FILTER (?s = <%(uri)s> || ?o = <%(uri)s>)' % dict(uri=uri),
                                              graph=graph_uri, format=format))
