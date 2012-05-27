######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id: __init__.py,v eeabfc934961 2011/02/14 17:47:59 dave $
#
######################################################


import os
import logging

import RDF as librdf
import json

from tornado.options import options

import biosignalml.formats

from biosignalml import BSML, Recording, Signal, Event, Annotation
from biosignalml.utils import xmlescape

from biosignalml.rdf import RDF, DCTERMS, OA
from biosignalml.rdf import Uri, Node, Resource, BlankNode, Graph, Statement
from biosignalml.rdf import Format

from fourstore import FourStore as TripleStore
from provenance import Provenance


class Repository(object):
#========================
  '''
  An RDF repository.

  :param base_uri:
  :param store_uri:
  '''
  def __init__(self, base_uri, store_uri):
  #---------------------------------------
    self.uri = base_uri
    self._triplestore = TripleStore(store_uri)
    self._provenance = Provenance(self._triplestore, self.uri + '/provenance')

  def __del__(self):
  #-----------------
    logging.debug('Repository shutdown')
    del self._provenance
    del self._triplestore

  def update(self, uri, triples):
  #------------------------------
    self._triplestore.update(uri, triples)

  def replace_graph(self, uri, rdf, format=Format.RDFXML):
  #-------------------------------------------------------
    #### graph.append(Statement(graph.uri, DCTERMS._provenance, self._provenance.add(graph.uri)))

    # If graph already present then rename (to new uuid()) and add
    # provenance...

    # add version statement to graph ??
    # What about actual recording file(s)? They should also be renamed...

    self._triplestore.replace_graph(uri, rdf, format=format)

    #for k, v in provenance.iter_items():
    #  self._provenance.add(self.uri, content-type, hexdigest, ...)
    #self._triplestore.insert(self._provenace, triples...)


  def extend_graph(self, uri, rdf, format=Format.RDFXML):
  #---------------------------------------------------
    self._triplestore.extend_graph(uri, rdf, format=format)


  def delete_graph(self, uri):
  #---------------------------
    self._triplestore.delete_graph(uri)
    #self._provenance.delete_graph(uri)
    ## Should this set provenance...


  def query(self, sparql, header=False, html=False, abbreviate=False):
  #-------------------------------------------------------------------
    return QueryResults(self, sparql, header, html, abbreviate)


  def construct(self, template, where, params={ }, graph=None, format=Format.RDFXML):
  #----------------------------------------------------------------------------------
    return self._triplestore.construct(template, where, params, graph, format)


  def describe(self, uri, format=Format.RDFXML):
  #---------------------------------------------
    return self._triplestore.describe(uri, format)

  def ask(self, query, graph=None):
  #--------------------------------
    return self._triplestore.ask(query, graph)

  def get_subjects(self, prop, obj, graph=None):
  #---------------------------------------------
    if isinstance(obj, Resource) or isinstance(obj, Uri):
      obj = '<%s>' % obj
    elif not isinstance(obj, Node):
      obj = '"%s"' % obj
    return [ r['s']['value'] for r in
                  self._triplestore.select('?s', '?s <%(prop)s> %(obj)s',
                                            params = dict(prop=prop, obj=obj),
                                            graph = graph) ]

  def get_object(self, subj, prop, graph=None):
  #--------------------------------------------
    for r in self._triplestore.select('?o', '<%(subj)s> <%(prop)s> ?o',
                                      params = dict(subj = subj, prop=prop),
                                      graph = graph):
      if   r['o']['type'] == 'uri':           return Resource(Uri(r['o']['value']))
      elif r['o']['type'] == 'bnode':         return BlankNode(r['o']['value'])
      elif r['o']['type'] == 'literal':       return r['o']['value']
      elif r['o']['type'] == 'typed-literal': return r['o']['value'] ## check datatype and convert...
    return None

  def make_graph(self, uri, template, where=None, params=None, graph=None):
  #------------------------------------------------------------------------
    '''
    Construct a RDF graph from a query against the repository/

    :rtype: :class:`~biosignalml.rdf.Graph`
    '''
    if where is None: where = template
    ttl = self.construct(template, where, params, graph, Format.TURTLE)
    #logging.debug("Statements: %s", ttl)  ###
    return Graph.create_from_string(uri, ttl, Format.TURTLE)

  def get_type(self, uri, graph):
  #------------------------------
    return self.get_object(uri, RDF.type, graph)

  def check_type(self, uri, type, graph=None):
  #-------------------------------------------
    return self.ask('<%s> a <%s>' % (str(uri), str(type)), graph)


class BSMLRepository(Repository):
#================================
  '''
  An RDF repository containing BioSignalML metadata.
  '''

  def has_recording(self, uri):
  #----------------------------
    ''' Check a URI refers to a Recording. '''
    return self._provenance.has_current_resource(uri, BSML.Recording)

  def has_signal(self, uri):
  #-------------------------
    ''' Check a URI refers to a Signal. '''
    return self._provenance.has_current_resource(uri, BSML.Signal)

  def has_signal_in_recording(self, sig, rec):
  #-------------------------------------------
    ''' Check a URI refers to a Signal in a given Recording. '''
    return (self._provenance.has_current_resource(rec, BSML.Recording)
        and self._provenance.has_current_resource(uri, BSML.Signal))

  def recordings(self):
  #--------------------
    '''
    Return a list of URI's of the Recordings in the repository.

    :rtype: list[:class:`~biosignalml.rdf.Uri`]
    '''
    return self._provenance.get_current_resources(BSML.Recording)

  def get_recording_and_graph_uri(self, uri):
  #------------------------------------------
    """
    Get the URIs of the recording and its Graph that contain the object.

    :param uri: The URI of some object.
    :rtype: tuple(:class:`~biosignalml.rdf.Uri`, :class:`~biosignalml.rdf.Uri`)
    """
    return self._provenance.get_current_resource_and_graph(uri, BSML.Recording)

  def get_recording(self, uri):
  #----------------------------
    '''
    Get the Recording from the graph that an object is in.

    :param uri: The URI of some object.
    :param graph_uri: The URI of a named graph containing statements
      about the object.
    :rtype: :class:`~biosignalml.Recording`
    '''
    #logging.debug('Getting: %s', uri)
    rec_uri, graph_uri = self.get_recording_and_graph_uri(uri)
    #logging.debug('Graph: %s', graph_uri)
    if graph_uri is not None:
      rclass = biosignalml.formats.CLASSES.get(
                 str(self.get_object(rec_uri, DCTERMS.format, graph=graph_uri)),
                 Recording)
      graph = self.make_graph(graph_uri, '<%(uri)s> ?p ?o', params=dict(uri=rec_uri), graph=graph_uri)
      return rclass.create_from_graph(rec_uri, graph)
    else:
      return None

  def get_recording_with_signals(self, uri):
  #-----------------------------------------
    """
    Get the Recording with its Signals from the graph
      that an object is in.

    :param uri: The URI of some object.
    :param graph_uri: The URI of a named graph containing statements
      about the object.
    :rtype: :class:`~biosignalml.Recording`
    """
    rec = self.get_recording(uri)
    if rec is not None:
      for sig_uri in self.get_subjects(BSML.recording, rec.uri, graph=rec.graph.uri):
        graph = self.make_graph(rec.graph.uri, '<%(uri)s> ?p ?o', params=dict(uri=sig_uri), graph=rec.graph.uri)
        rec.add_signal(Signal.create_from_graph(sig_uri, graph, units=None))
    return rec

#  def signal_recording(self, uri):
#  #-------------------------------
#    return self.get_object(uri, BSML.recording)

  def get_signal(self, uri, graph_uri=None):
  #-----------------------------------------
    '''
    Get a Signal from the repository.

    :param uri: The URI of a Signal.
    :param graph_uri: An optional URI of the graph to query.
    :rtype: :class:`~biosignalml.Signal`
    '''
    rec_uri, graph_uri = self.get_recording_and_graph_uri(uri)
    graph = self.make_graph(graph_uri, '<%(uri)s> ?p ?o',
                            where = ' <%(uri)s> <%(reln)s> <%(rec)s> .'
                                  + ' <%(uri)s> a  <%(stype)s> .'
                                  + ' <%(uri)s> ?p ?o',
                            params = dict(uri=uri,
                                          rec=rec_uri,
                                          stype=BSML.Signal,
                                          reln=BSML.recording),
                            graph = graph_uri
                            )
    return Signal.create_from_graph(uri, graph, units=None)  # units set from graph...

#  def signal(self, sig, properties):              # In context of signal's recording...
#  #---------------------------------
#    if self.check_type(sig, BSML.Signal):
#      r = [ [ Graph.make_literal(t, '') for t in self.get_objects(sig, p) ] for p in properties ]
#      r.sort()
#      return r
#    else: return None

  def get_annotation(self, uri, graph_uri=None):
  #---------------------------------------------
    '''
    Get an Annotation from the repository.

    :param uri: The URI of an Annotation.
    :rtype: :class:`~biosignalml.Annotation`
    '''
    if graph_uri is None:
      rec_uri, graph_uri = self.get_recording_and_graph_uri(uri)
    graph = self.make_graph(uri, '<%(u)s> ?p ?o',
                            where = 'graph <%(g)s> { <%(u)s> a <%(t)s> . <%(u)s> ?p ?o }',
                            params = dict(g=graph_uri, u=uri, t=BSML.Annotation))
    graph.add_statements(self.make_graph(uri, '?b ?p ?o',
      where = 'graph <%(g)s> { <%(u)s> a <%(t)s> . <%(u)s> <%(b)s> ?b . ?b ?p ?o }',
      params = dict(g=graph_uri, u=uri, t=BSML.Annotation, b=OA.hasBody)) )
#    print body.serialise(rdf.Format.TURTLE)
    return Annotation.create_from_graph(uri, graph) if len(graph) else None

  def get_annotation_by_content(self, uri):
  #----------------------------------------
    '''
    Get an Annotation from the repository identified by its body content.

    :param uri: The URI of the body of an Annotation.
    :rtype: :class:`~biosignalml.Annotation`
    '''
    rec_uri, graph_uri = self.get_recording_and_graph_uri(uri)
    for r in self._triplestore.select('?a', 'graph <%(g)s> { ?a a <%(t)s> . ?a <%(b)s> <%(u)s> }',
                                      params = dict(g=graph_uri, t=BSML.Annotation, b=OA.hasBody, u=uri) ):
      return self.get_annotation(r['a']['value'], graph_uri)

  def annotations(self, uri):
  #--------------------------
    '''
    Return a list of all Annotations about a subject.

    :param uri: The URI of the subject.
    :rtype: list[:class:`~biosignalml.Annotation`]
    '''
    rec_uri, graph_uri = self.get_recording_and_graph_uri(uri)
    return [ (r['a']['value'])
      for r in self._triplestore.select('?a',
        'graph <%(g)s> { ?a a <%(t)s> . ?a <%(tg)s> <%(u)s> . ?a <%(tm)s> ?tm }',
        params = dict(g=graph_uri, t=BSML.Annotation, tg=OA.hasTarget, u=uri, tm=OA.annotated),
        order = '?tm') ]


class SparqlHead(object):
#========================
  import pyparsing as parser

  uri = parser.QuotedString('<', endQuoteChar='>')
  head = parser.ZeroOrMore(
      parser.Group(parser.Keyword('base', caseless=True) + uri)
    | parser.Group(parser.Keyword('prefix', caseless=True)
       + parser.Group(parser.Combine(
           parser.Optional(parser.Word(parser.alphas, parser.alphanums)) + parser.Suppress(':')
           ) + uri))
         )
  @staticmethod
  def parse(sparql):
  #-----------------
    return SparqlHead.head.parseString(sparql)

"""([(['prefix', (['owl', 'http://www.w3.org/2002/07/owl#'], {})], {}),
     (['prefix', (['rdfs', 'http://www.w3.org/2000/01/rdf-schema#'], {})], {}),
     (['prefix', (['tl', 'http://purl.org/NET/c4dm/timeline.owl#'], {})], {}),
     (['prefix', (['rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'], {})], {}),
     (['prefix', (['xsd', 'http://www.w3.org/2001/XMLSchema#'], {})], {}),
     (['prefix', (['dc', 'http://purl.org/dc/terms/'], {})], {}),
     (['prefix', (['evt', 'http://purl.org/NET/c4dm/event.owl#'], {})], {}),
     (['base', 'http://repository.biosignalml.org/recording/'], {}),
     (['prefix', (['bsml', '%s' % BSML.uri], {})], {}),
     (['prefix', (['text', 'http://4store.org/fulltext#'], {})], {})
    ], {})"""



class QueryResults(object):
#==========================

  def __init__(self, repo, sparql, header=False, html=False, abbreviate=False):
  #----------------------------------------------------------------------------
    self._repobase = repo.uri
    self._set_prefixes(sparql)
    self._header = header
    self._html = html
    self._abbreviate = abbreviate
    #logging.debug('SPARQL: %s', sparql)
    try:
      self._results = json.loads(repo._triplestore.query(sparql, Format.JSON))
    except Exception, msg:
      self._results = { 'error': str(msg) }

  def _set_prefixes(self, sparql):
  #-------------------------------
    self._base = None
    self._prefixes = { }
    header = SparqlHead.parse(sparql)
    for h in header:
      if h[0] == 'base':
        self._base = h[1]
      else:       # 'prefix'
        self._prefixes[h[1][0]] = h[1][1]
    #logging.debug('PFX: %s', self._prefixes)

  def abbreviate_uri(self, uri):
  #-----------------------------
    for name, prefix in self._prefixes.iteritems():
      if uri.startswith(prefix): return '%s:%s' % (name, uri[len(prefix):])
    if self._base and uri.startswith(self._base): return '<%s>' % uri[len(self._base):]
    return '<%s>' % uri

  def _add_html(self, result):
  #---------------------------
    rtype = result.get('type')
    value = result.get('value')
    if   rtype == 'uri':
      uri = self.abbreviate_uri(value) if self._abbreviate else uri
      if uri[0] == '<':
        uri = uri[1:-1]
        LT = '&lt;'
        GT = '&gt;'
      else:
        LT = GT = ''
      if value.startswith(self._repobase):
        result['html'] = ('%s<a href="%s" uri="%s" class="cluetip">%s</a>%s'
                       % (LT,
                          '/repository/' + value[len(options.resource_prefix):],
                          value, uri,
                          GT))
                 ## '/repository/' is web-server path to view objects in repository
      ## Following needs work...
#      elif value.startswith('http://physionet.org/'): ########### ... URI to a Signal, Recording, etc...
#        result['html'] = ('%s<a href="%s" uri="%s" class="cluetip">%s</a>%s'
#                       % (LT,
#                          '/repository/' + value.replace(':', '%3A', 1),
#                          value, uri,
#                          GT))
#                 ## '/repository/' is web-server path to view objects in repository
      else:
        result['html'] = '%s%s%s' % (LT, uri, GT)
    elif rtype == 'bnode':
      result['html'] = '_:' + value
    #elif rtype == 'literal':
    #  return value              ## set @lang, ^^datatype (or convert to data type) ??
    #elif rtype == 'typed-literal':
    #  return value
    else:
      result['html'] = xmlescape(value)

    return result

  def __iter__(self):
  #------------------
    #logging.debug('DATA: %s', self._results)
    # self._results are as per http://www.w3.org/TR/rdf-sparql-json-res/
    #                      and http://www.w3.org/TR/sparql11-results-json/
    if   self._results.get('boolean', None) is not None:
       yield self._results['boolean']
    elif self._results.get('head'):
      cols = self._results.get('head')['vars']
      rows = self._results.get('results', {}).get('bindings', [ ])
      if self._header: yield cols
      for r in rows:
        if self._html: yield [ self._add_html(r[c]) for c in cols ]
        else:          yield [                r[c]  for c in cols ]
    else:
      yield self._results
