######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $ID: e4ba890 on Wed Jun 8 16:55:26 2011 +1200 by Dave Brooks $
#
######################################################

import urllib
import httplib2
import json
import logging

from biosignalml.rdf import Format

from triplestore import TripleStore


class FourStore(TripleStore):
#============================

  def __init__(self, href):
  #------------------------
    super(FourStore, self).__init__(href)
    self._http = httplib2.Http()

  def _request(self, endpoint, method, **kwds):
  #--------------------------------------------
    try:
      response, content = self._http.request(self._href + endpoint, method=method, **kwds)
    except AttributeError:
      raise Exception("Can not connect to 4store -- check it's running")
    #logging.debug('Request -> %s', response)
    if response.status not in [200, 201]: raise Exception(content)
    return content

  def query(self, sparql, format=Format.RDFXML):
  #---------------------------------------------
    ##logging.debug('4s %s: %s', format, sparql)
    try:
      return self._request('/sparql/', 'POST',
                           body=urllib.urlencode({'query': sparql}),
                           headers={'Content-type': 'application/x-www-form-urlencoded',
                                    'Accept': Format.mimetype(format)} )
    except Exception, msg:
      logging.error('4store: %s, %s', msg, sparql)
      raise

  def ask(self, where, graph=None):
  #--------------------------------
    return json.loads(self.query('ask where { %(graph)s { %(where)s } }'
                                  % { 'graph': ('graph <%s>' % str(graph)) if graph else '',
                                      'where': where,
                                    }, Format.JSON)
                                )['boolean']

  def select(self, fields, where, graph=None, distinct=False, limit=None):
  #-----------------------------------------------------------------------
    return json.loads(self.query('select%(distinct)s %(fields)s where { %(graph)s { %(where)s } }%(limit)s'
                                  % { 'distinct': ' distinct' if distinct else '',
                                      'fields': fields,
                                      'graph': ('graph <%s>' % str(graph)) if graph else '',
                                      'where': where,
                                      'limit': (' limit %s' % limit) if limit else '',
                                    }, Format.JSON
                                )
                     ).get('results', {}).get('bindings', [])

  def construct(self, template, where, graph=None, params = { }, format=Format.RDFXML):
  #------------------------------------------------------------------------------------
    return self.query('construct { %(tplate)s } where { %(graph)s { %(where)s } }'
                       % { 'tplate': template % params,
                           'graph': ('graph <%s>' % str(graph)) if graph else '',
                           'where': where % params,
                         }, format
                     )

  def describe(self, uri, format=Format.RDFXML):
  #-----------------------------------------------
    return self.query('describe <%(uri)s>' % { 'uri': uri }, format)


  def insert(self, graph, triples):
  #--------------------------------
    if len(triples) == 0: return
    sparql = ('insert data { graph <%(graph)s> { %(triples)s } }'
                % { 'graph': str(graph),
                    'triples': ' . '.join([' '.join(list(s)) for s in triples ]) })
    ##logging.debug('Insert: %s', sparql)
    content = self._request('/update/', 'POST',
                            body=urllib.urlencode({'update': sparql}),
                            headers={'Content-type': 'application/x-www-form-urlencoded'})
    if 'error' in content: raise Exception(content)

  def delete(self, graph, triples):
  #--------------------------------
    if len(triples) == 0: return
    sparql = ('delete data { graph <%(graph)s> { %(triples)s } }'
                % { 'graph': graph,
                    'triples': ' . '.join([' '.join(list(s)) for s in triples ]) })
    content = self._request('/update/', 'POST',
                            body=urllib.urlencode({'update': sparql}),
                            headers={'Content-type': 'application/x-www-form-urlencoded'})
    if 'error' in content: raise Exception(content)

  def update(self, graph, triples):
  #--------------------------------
    if len(triples) == 0: return
    last = (None, None)
    ##logging.debug('UPDATE: %s', triples)
    for s, p, o in sorted(triples):
      if (s, p) != last:
        sparql = ('delete { graph <%(g)s> { %(s)s %(p)s ?o } } where { %(s)s %(p)s ?o }'
                    % {'g': str(graph), 's': s, 'p': p} )
        content = self._request('/update/', 'POST',
                                body=urllib.urlencode({'update': sparql}),
                                headers={'Content-type': 'application/x-www-form-urlencoded'})
        if 'error' in content: raise Exception(content)
        last = (s, p)
    self.insert(graph, triples)  ###### DUPLICATES BECAUSE OF 4STORE BUG...


  def extend_graph(self, graph, rdf, format=Format.RDFXML):
  #--------------------------------------------------------
    #logging.debug('Extend <%s>: %s', graph, rdf)
    self._request('/data/', 'POST',
                  body=urllib.urlencode({'data': rdf,
                                         'graph': str(graph),
                                         'mime-type': Format.mimetype(format),
                                        }),
                  headers={'Content-type': 'application/x-www-form-urlencoded'})

  def replace_graph(self, graph, rdf, format=Format.RDFXML):
  #-----------------------------------------------------------
    #logging.debug('Replace <%s>: %s', graph, rdf)
    self._request('/data/' + str(graph), 'PUT', body=rdf, headers={'Content-type': Format.mimetype(format)})

  def delete_graph(self, graph):
  #-----------------------------
    #logging.debug('Delete <%s>', graph)
    self._request('/data/' + str(graph), 'DELETE')


  def fulltext(self):
  #------------------
    '''
    Enable stemming of rdfs:label, rdfs:comment, and dc:description text
    in 4store. See http://4store.org/trac/wiki/TextIndexing.
    '''
    self.extend_graph('system:config',
     """@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix dc:   <http://purl.org/dc/elements/1.1/> .
        @prefix dcterms: <http://purl.org/dc/terms/> .
        @prefix text: <http://4store.org/fulltext#> .

        rdfs:label      text:index text:stem .
        rdfs:comment    text:index text:stem .
        dc:description  text:index text:stem .
        dcterms:description text:index text:stem .""")


if __name__ == '__main__':
#=========================

  import os, sys
  import argparse

  parser = argparse.ArgumentParser(description="Test and setup a 4store triplestore")
  parser.add_argument("-d", "--debug", dest="debug", action="store_true",
                    help="Enable debug trace")
  parser.add_argument("--fulltext", dest="fulltext", action="store_true",
                    help="Configure the store for full text indexing")
  parser.add_argument("--test", dest="test", action="store_true",
                    help="Run some simple tests")
  parser.add_argument("store", metavar="URI", help="URI of the triplestore")
  args = parser.parse_args()

  if args.debug: logging.getLogger().setLevel(logging.DEBUG)

  store = FourStore(args.store)

  if args.test:

    print 'ASK:\n',      store.ask('?s ?p ?o')
    print '\nQUERY:\n',  store.query('select ?s ?p ?o where { ?s ?p ?o } limit 10')
    print 'SELECT:\n', store.select('?s ?p ?o', '?s ?p ?o', limit=10)

    store.insert('<http://example.com/G>',
                   [ '<http://example.com/s> <http://example.com/p> "o"' ])
    print '\nGRAPH SELECT:\n',    store.select('?s ?p ?o', 'graph <http://example.com/G> { ?s ?p ?o }')
    print '\nGRAPH CONSTRUCT:\n', store.construct('?s ?p ?o', 'graph <http://example.com/G> { ?s ?p ?o }')


    store.extend_graph('http://example.com/G', '<http://example.com/S> <http://example.com/P> "b" .')
    print 'EXTENDED:\n', store.construct('?s ?p ?o', 'graph <http://example.com/G> { ?s ?p ?o }')


    store.replace_graph('http://example.com/G', '<http://example.com/S> <http://purl.org/dc/terms/description> "There are lots of mice!" .')
    print 'REPLACED:\n', store.construct('?s ?p ?o', 'graph <http://example.com/G> { ?s ?p ?o }')


    store.delete_graph('http://example.com/G')
    print 'DELETED:\n',  store.construct('?s ?p ?o', 'graph <http://example.com/G> { ?s ?p ?o }')

  elif args.fulltext:

    store.fulltext()
