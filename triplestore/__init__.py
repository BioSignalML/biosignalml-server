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

  def ask(self, where, params=None, graph=None):
  #---------------------------------------------
    pass

  def select(self, fields, where, graph=None, params=None, order=None, distinct=False, limit=None):
  #------------------------------------------------------------------------------------------------
    '''
    Get all items from a graph or repository.

    :param fields: The variables to be returned from the matched pattern.
    :type fields: str
    :param where: The graph pattern to match.
    :type where: str
    :param params: A dictionary of string format substitutions applied to the `where` argument.
    :param graph: The URI of an optional graph to query within.
    :param order: The variable(s) to optional order the results.
    :param distinct: Ensure result sets are distinct.
    :param limit: Optionally limit the number of result sets.
    :type limit: str
    :return: A list of dictionaries, keyed by selected field names, where each value
     is a dictionary about the result field, as per the 'bindings' list described in
     http://www.w3.org/TR/rdf-sparql-json-res/.
    :rtype: list
    '''
    pass

  def construct(self, template, where, params=None, graph=None, format=Format.RDFXML):
  #-----------------------------------------------------------------------------------
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
