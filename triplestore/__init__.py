######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $ID: a20277b on Thu Jul 7 16:40:26 2011 +1200 by Dave Brooks $
#
######################################################


from biosignalml.rdf import Format


class TripleStore(object):
#=========================

  def __init__(self, href):
  #------------------------
    self._href = href

  def query(self, sparql, format=Format.RDFXML):
  #---------------------------------------------
    pass

  def ask(self, where, graph=None):
  #--------------------------------
    pass

  def select(self, fields, where, graph=None, distinct=False, limit=None):
  #-----------------------------------------------------------------------
    pass

  def construct(self, template, where, graph=None, params = { }, format=Format.RDFXML):
  #------------------------------------------------------------------------------------
    pass

  def describe(self, uri, format=Format.RDFXML):
  #---------------------------------------------
    pass

  def insert(self, graph, triples):
  #--------------------------------
    '''
    Insert a list of triples into a graph.
    '''
    pass

  def delete(self, graph, triples):
  #--------------------------------
    '''
    Delete a list of triples from a graph.
    '''
    pass

  def update(self, graph, triples):
  #--------------------------------
    '''
    Remove all statements about the (subject, predicate) pairs in a list
    of triples from the graph then insert the triples.
    '''
    pass

  def extend_graph(self, graph, rdf, format=Format.RDFXML):
  #--------------------------------------------------------
    '''
    Extend an existing graph, creating one if not present.
    '''
    pass

  def replace_graph(self, graph, rdf, format=Format.RDFXML):
  #---------------------------------------------------------
    '''
    Replace an existing graph, creating one if not present.
    '''
    pass

  def delete_graph(self, graph):
  #-----------------------------
    '''
    Delete an existing graph from the store.
    '''
    pass
