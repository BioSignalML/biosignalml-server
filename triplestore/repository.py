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

from biosignalml import BSML, Recording, Signal

from biosignalml.utils import xmlescape

from biosignalml.model.mapping import bsml_mapping

from biosignalml.rdf import RDF, DCTERMS
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

## First param is a base URI, used when generating Turtle and to check that
## results belong to us. Better to drop it, and pass it directly to the methods
## that require a base.
  def __init__(self, base_uri, store_uri):
  #---------------------------------------
    self.base = base_uri
    if self.base[-1] not in '#/': self.base += '/'
    self.triplestore = TripleStore(store_uri)
    self.provenance = Provenance(self.triplestore, self.base + 'provenance')

  def __del__(self):
  #-----------------
    logging.debug('Repository shutdown')
    del self.provenance
    del self.triplestore

  def add_graph(self, graph):
  #--------------------------
    #### graph.append(Statement(graph.uri, DCTERMS.provenance, self.provenance.add(graph.uri)))

    # If graph already present then rename (to new uuid()) and add
    # provenance...

    # add version statement to graph ??
    # What about actual recording file(s)? They should also be renamed...

    self.triplestore.replace_graph(graph, graph.serialise('turtle'), format=Format.TURTLE)

    #for k, v in provenance.iter_items():
    #  self.provenance.add(self.uri, content-type, hexdigest, ...)
    #self.triplestore.insert(self.provenace, triples...)

  def remove_graph(self, uri):
  #---------------------------
    self.triplestore.remove_graph(str(uri))
    self.provenance.remove(str(uri))
    ## Should this set provenance...


  def query(self, sparql, header=False, html=False, abbreviate=False):
  #-------------------------------------------------------------------
    return QueryResults(self, sparql, header, html, abbreviate)


  def construct(self, template, where, params = { }, format=Format.RDFXML):
  #------------------------------------------------------------------------
    return self.triplestore.construct(template, where, params, format)


  def describe(self, uri, format=Format.RDFXML):
  #---------------------------------------------
    return self.triplestore.describe(uri, format)


  def get_subjects(self, prop, obj):
  #---------------------------------
    if isinstance(obj, Resource) or isinstance(obj, Uri):
      obj = '<%s>' % obj
    elif not isinstance(obj, Node):
      obj = '"%s"' % obj
    return [ r['s']['value'] for r in
                  self.triplestore.select('?s', '?s <%s> %s' % (str(prop), obj)) ]

  def get_object(self, subj, prop):
  #--------------------------------
    for r in self.triplestore.select('?o', '<%s> <%s> ?o' % (str(subj), str(prop))):
      if   r['o']['type'] == 'uri':           return Resource(Uri(r['o']['value']))
      elif r['o']['type'] == 'bnode':         return BlankNode(r['o']['value'])
      elif r['o']['type'] == 'literal':       return r['o']['value']
      elif r['o']['type'] == 'typed-literal': return r['o']['value'] ## check datatype and convert...
    return None

  def make_graph(self, template, where, params = { }):
  #---------------------------------------------------
    '''
    Construct a RDF graph from a query againt the repository/

    :rtype: :class:`~biosignalml.rdf.Graph`
    '''
    ttl = self.construct(template, where, params, Format.TURTLE)
    #logging.debug("Statements: %s", ttl)  ###
    return Graph.create_from_string(ttl, Format.TURTLE, Uri(self.base))

  def get_type(self, uri):
  #-----------------------
    return self.get_object(uri, RDF.type)

  def check_type(self, uri, type):
  #-------------------------------
    return self.triplestore.ask('<%s> a <%s>' % (str(uri), str(type)))


class BSMLRepository(Repository):
#================================
  '''
  An RDF repository containing BioSignalML metadata.
  '''

  def is_recording(self, uri):
  #---------------------------
    ''' Check a URI refers to a Recording. '''
    return self.check_type(uri, BSML.Recording)

  def is_signal(self, uri):
  #------------------------
    ''' Check a URI refers to a Signal. '''
    return self.check_type(uri, BSML.Signal)

  def recordings(self):
  #--------------------
    '''
    Return a list of all the Recordings in the repository.

    :rtype: list[:class:`~biosignalml.Recording`]
    '''
    return [ Recording(r['r']['value'])
               for r in self.triplestore.select('?r', 'graph ?r { ?r a <%s> }' % BSML.Recording) ]

  def get_recording_uri(self, uri):
  #--------------------------------
    '''
    Get the URI of the Recording in the graph that the object is in.

    :param uri: The URI of some object.
    :rtype: :class:`~biosignalml.rdf.Uri`
    '''
    for r in self.triplestore.select('?g', 'graph ?g { ?g a <%s> . <%s> a ?t }' % (BSML.Recording, uri)):
      return Uri(r['g']['value'])
    return None

  def get_recording(self, uri):
  #----------------------------
    '''
    Get the Recording in the graph that the object is in.

    :param uri: The URI of some object.
    :rtype: :class:`~biosignalml.Recording`
    '''
    #logging.debug('Getting: %s', uri)
    if self.get_type(uri) != BSML.Recording: uri = self.get_object(uri, BSML.recording)
    #logging.debug('Recording: %s', uri)
    if uri:
      graph = self.make_graph('<%(uri)s> ?p ?o',
                              '{ <%(uri)s> ?p ?o }', { 'uri': str(uri) })
      return Recording.create_from_graph(str(uri), graph, bsml_mapping())
    else:
      return None

  def get_recording_with_signals(self, uri):
  #-----------------------------------------
    '''
    Get the Recording that the URI is part of.

    :param uri: The URI of the Recording.
    :rtype: :class:`~biosignalml.Recording`
    '''
    '''
    Get a list of all Signals in a Recording.

    :param uri: The URI of a Recording.
    :rtype: list[:class:`~biosignalml.Signal`]
    '''
    rec = self.get_recording(uri)
    if rec is not None:
      for sig in self.get_subjects(BSML.recording, rec.uri):
        graph = self.make_graph('<%(uri)s> ?p ?o',
                                'graph <%(rec)s> { <%(uri)s> ?p ?o }',
                                { 'rec': str(rec.uri), 'uri': str(sig) })
        rec.add_signal(Signal.create_from_graph(str(sig), graph, bsml_mapping()))
    return rec

#  def signal_recording(self, uri):
#  #-------------------------------
#    return self.get_object(uri, BSML.recording)

  def get_signal(self, uri):
  #-------------------------
    '''
    Get a Signal from the repository.

    :param uri: The URI of a Signal.
    :rtype: :class:`~biosignalml.Signal`
    '''
    graph = self.make_graph('<%(uri)s> ?p ?o',
                            '<%(uri)s> a  <%(type)s> . <%(uri)s> ?p ?o',
                             { 'uri': str(uri), 'type': str(BSML.Signal) })
    return Signal.create_from_graph(uri, graph, bsml_mapping())

#  def signal(self, sig, properties):              # In context of signal's recording...
#  #---------------------------------
#    if self.check_type(sig, BSML.Signal):
#      r = [ [ Graph.make_literal(t, '') for t in self.get_objects(sig, p) ] for p in properties ]
#      r.sort()
#      return r
#    else: return None


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
    self._repobase = repo.base
    self._set_prefixes(sparql)
    self._header = header
    self._html = html
    self._abbreviate = abbreviate
    #logging.debug('SPARQL: %s', sparql)
    try:
      self._results = json.loads(repo.triplestore.query(sparql, Format.JSON))
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

  def _abbreviate_uri(self, uri):
  #------------------------------
    for name, prefix in self._prefixes.iteritems():
      if uri.startswith(prefix): return '%s:%s' % (name, uri[len(prefix):])
    if self._base and uri.startswith(self._base): return '<%s>' % uri[len(self._base):]
    return '<%s>' % uri

  def _add_html(self, result):
  #---------------------------
    rtype = result.get('type')
    value = result.get('value')
    if   rtype == 'uri':
      uri = self._abbreviate_uri(value) if self._abbreviate else uri
      if uri[0] == '<':
        uri = uri[1:-1]
        LT = '&lt;'
        GT = '&gt;'
      else:
        LT = GT = ''
      if value.startswith(self._repobase):
        result['html'] = ('%s<a href="%s" uri="%s" class="cluetip">%s</a>%s'
                       % (LT,
                          '/repository/' + value[len(self._repobase + 'recording/'):],
                          value, uri,
                          GT))
                 ## '/repository/' is web-server path to view objects in repository
      ## Following needs work...
      elif value.startswith('http://physionet.org/'): ########### ... URI to a Signal, Recording, etc...
        result['html'] = ('%s<a href="%s" uri="%s" class="cluetip">%s</a>%s'
                       % (LT,
                          '/repository/' + value.replace(':', '%3A', 1),
                          value, uri,
                          GT))
                 ## '/repository/' is web-server path to view objects in repository
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
