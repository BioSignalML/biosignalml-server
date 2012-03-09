######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $ID: ef480c7 on Wed Mar 7 13:10:14 2012 +1300 by Dave Brooks $
#
######################################################


import logging
import tornado.web
from tornado.options import options

from biosignalml import BSML
import biosignalml.rdf as rdf


class metadata(tornado.web.RequestHandler):
#==========================================

  def get(self, name, **kwds):
  #---------------------------
    ##logging.debug('GET: "%s" %s', name, self.request.headers)
    ## Build a new RDF Graph that has { <uri> ?p ?o  } UNION { ?s ?p <uri> }
    ## and serialise this??
    if name == '': graph_uri = options.repository.uri
    else:          graph_uri = options.repository.get_recording_graph_uri(name)
    accept = { k[0].strip(): k[1].strip() if len(k) > 1 else ''
                 for k in [ a.split(';', 1)
                  for a in self.request.headers.get('Accept', '*/*').split(',') ] }
    # check rdf+xml, turtle, n3, html ??
    format = rdf.Format.TURTLE if ('text/turtle' in accept
                                or 'application/x-turtle' in accept) else rdf.Format.RDFXML
    self.set_header('Content-Type', rdf.Format.mimetype(format))
    if graph_uri is not None:
      self.write(options.repository.construct('?s ?p ?o',
                                              'graph <%(graph)s> { ?s ?p ?o'
                                            + ' FILTER (?p != <http://4store.org/fulltext#stem>'
                                            + ' && (?s = <%(name)s> || ?o = <%(name)s>)) }',
                                              { 'graph': graph_uri, 'name': name},
                                              format))

  @property
  def _format(self):
  #-----------------
    return (rdf.Format.TURTLE if self.request.headers.get('Content-Type')
                                   in ['text/turtle', 'application/x-turtle']
                              else
            rdf.Format.RDFXML)

  @staticmethod
  def _node(n):
  #------------
    if   n.is_resource(): return '<%s>' % str(n)
    elif n.is_blank():    return '_:%s' % str(n)
    elif n.is_literal():
      l = [ '"%s"' % n.literal[0] ]
      if   n.literal[1]: l.append('@%s'  % n.literal[1])
      elif n.literal[2]: l.append('^^%s' % n.literal[2])
      return ''.join(l)

  def post(self, name, **kwds):
  #----------------------------
    ##logging.debug('POST: %s\n%s', name, self.request.body)
    graph = rdf.Graph.create_from_string(self.request.body, self._format, name)
    graph_uri = options.repository.get_recording_graph_uri(name)
    if graph_uri is None:
      rec = graph.get_object(name, BSML.recording)
      if rec is not None:
        graph_uri = options.repository.get_recording_graph_uri(rec.uri)
    if graph_uri is not None:
      options.repository.update(graph_uri,
        [ (self._node(s.subject), self._node(s.predicate), self._node(s.object)) for s in graph ] )
      # return...  ???
    else:
      self.send_error(404)

  def put(self, name, **kwds):
  #----------------------------
    ##logging.debug('PUT: %s %s\n%s', name, self._format, self.request.body)
    if (rdf.Graph.create_from_string(self.request.body, self._format, name)
          .contains(rdf.Statement(name, rdf.RDF.type, BSML.Recording))):
      # ask ??
      # and (name BSML.format BSML.BioSignalML)
      # if not in repository and source not set, or in repository but with no source
      # then create new HDF5 (i.e. BioSignalML) file and set as source

      if options.repository.has_recording(name):
        # And if existing recording, do we have authority to replace it...
        self.send_error(401)  ## Unauthorised
      else:
        options.repository.replace_graph(name, self.request.body, self._format)
      # return...  ???
    else:
      self.send_error(404)

#  def delete(self, name, **kwds):
#  #------------------------------
#    if options.repository.is_recording(name):
#      options.repository.delete_graph(name)
#      # return...  ???
#    else:
#      self.send_error(404)
