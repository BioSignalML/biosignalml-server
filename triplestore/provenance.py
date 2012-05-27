######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $Id$
#
######################################################


from biosignalml.rdf import Uri, Graph, Statement
from biosignalml.rdf import RDF, RDFG, PRV
from biosignalml.utils import utctime_as_string


class Provenance(Graph):
#=======================

  def __init__(self, store, uri):
  #------------------------------
    Graph.__init__(self, uri)
    self._store = store

  def add_graph(self, graph, agent, ancestor=None):
  #------------------------------------------------
    self.append(Statement(graph, RDF.type, PRV.DataItem))
    self.append(Statement(graph, RDF.type, RDFG.Graph))
    if ancestor: self.append(Statement(graph, PRV.precededBy, ancestor))
    createdby = self.uri.make_uri()
    self.append(Statement(graph, PRV.createdBy, createdby))
    self.append(Statement(createdby, RDF.type, PRV.DataCreation))
    self.append(Statement(createdby, PRV.performedBy, agent))
    self.append(Statement(createdby, PRV.completedAt, '"%s"^^xsd:dateTime'
                                                    % utils.utctime_as_string()))

    # now is when we lock and update store...

  def delete_graph(self, graph):
  #-----------------------------
    ## 'DCTERMS.dateRemoved' is not a DCTERMS Terms property...
    self.append(Statement(uri, DCTERMS.dateRemoved, datetime_to_isoformat(utctime()) ))
    ## ANd need to updayte the store...


#    def transaction(self, resource, action, comment):
    #------------------------------------------------

    #self._store.insert(self, triples...)

## Also store md5/sha hashes of file objects...

  def get_current_resources(self, rtype):
  #--------------------------------------
    '''
    Return a list of URI's in a given class that are in graphs which have provenance.

    :param rtype: The class of resource to find.
    :rtype: list[:class:`~biosignalml.rdf.Uri`]
    '''
    return [ Uri(r['r']['value']) for r in self._store.select(
      '?r',
      '''graph <%(pgraph)s> { ?g a <%(gtype)s> MINUS { ?p <%(preceded)s> ?g }}
         graph ?g { ?r a <%(rtype)s> }''',
      params=dict(pgraph=self.uri,
                  gtype=RDFG.Graph,
                  preceded=PRV.precededBy,
                  rtype=rtype),
      distinct=True,
      order='?r')
      ]

  def get_current_resource_and_graph(self, uri, rtype):
  #----------------------------------------------------
    """
    Return the resource and graph URIS where the graph has provenance, contains a specific object,
     and the resource is of the given type.

    :param uri: The URI of an object.
    :param rtype: The class of resource the graph has to have.
    :rtype: tuple(:class:`~biosignalml.rdf.Uri`, :class:`~biosignalml.rdf.Uri`)
    """
    for r in self._store.select(
      '?r ?g',
      '''graph <%(pgraph)s> { ?g a <%(gtype)s> MINUS { ?p <%(preceded)s> ?g }}
         graph ?g { ?r a <%(rtype)s> . <%(obj)s> a ?t }''',
      params=dict(pgraph=self.uri,
                  gtype=RDFG.Graph,
                  preceded=PRV.precededBy,
                  rtype=rtype,
                  obj=uri)): return (Uri(r['r']['value']), Uri(r['g']['value']))
    return (None, None)

    def has_current_resource(self, uri, rtype):
    #------------------------------------------
      return self._store.ask(
        '''graph <%(pgraph)s> { ?g a <%(gtype)s> MINUS { ?p <%(preceded)s> ?g }}
           graph ?g { ?r a <%(rtype)s> . <%(obj)s> a ?t }''',
        params=dict(pgraph=self.uri,
                    gtype=RDFG.Graph,
                    preceded=PRV.precededBy,
                    rtype=rtype,
                    obj=uri))


"""
Need to include basic provenance (created, by??) with recording...

<resource/rec> dc:hasProvenance <resource/guid> .

class Provenance(object):
#========================

  def __init__(self, uri):
  #-----------------------
    self.uri = uri
    self.statements = ['<%s> {' % self.uri]
    self.agent = 'file://' + os.path.abspath(__file__)

  def __str__(self):
  #---------------
    return '\n  '.join(self.statements + ['}'])

  def add_graph(self, graph):
  #--------------------------
    self.statements.append('<%s> a prv:DataItem, rdfg:Graph ;' % graph)
    self.statements.append('  prv:createdBy [ a prv:DataCreation ;')
    self.statements.append('                  prv:performedBy <%s> ;' % self.agent)
    self.statements.append('                  prv:completedAt "%s"^^xsd:dateTime ;'
                                                % utils.datetime_to_isoformat(utils.utctime()))
    self.statements.append('                ] .')




prefix prv: <http://purl.org/net/provenance/ns#>
prefix rdfg: <http://www.w3.org/2004/03/trix/rdfg-1/>

select ?g ?r where {
  graph ?g { ?r a bsml:Recording }
  graph <http://devel.biosignalml.org/provenance>
    { ?g a rdfg:Graph MINUS { ?p prv:precededBy ?g } }
  }

<http://devel.biosignalml.org/provenance> {
  <mitdb/100V2> a prv:DataItem, rdfg:Graph ;
    prv:precededBy <mitdb/100V1> ;
    prv:createdBy [ a prv:DataCreation ;
                    prv:performedBy <http://www.bcs.co.nz/Users/dave> ;
                    prv:completedAt "2012-05-16T05:18Z"^^xsd:dateTime ;
                  ] .
  }




Access everything via <provenance> graph:


<rec_uri> a bsml:Recording ;
          prov:hasGraphs <rec_graph/1>, <rec_graph/2>, <rec_graph/3> ;
          prov:currentGraph <rec_graph/3> ;
          .

<rec_graph/1> a prov:NamedGraph ;
              dc:created "..."^^xsd:DateTime ;
              dc:creator "..." ;
              dc:replacedBy <rec_graph/2>
              prov:version 1 ;
              prov:validFrom "..."^^xsd:DateTime ;
              prov:validUntil "..."^^xsd:DateTime ;
              .

<rec_graph/3> a prov:NamedGraph ;
              dc:created "..."^^xsd:DateTime ;
              dc:creator "..." ;
              dc:replaceds <rec_graph/2>
              prov:version 3 ;
              prov:validFrom "..."^^xsd:DateTime ;
              .


<del_uri> a bsml:Recording ;
          prov:hasNamedGraphs <del_graph/1> ;
          .
          .

<del_graph/1> a prov:NamedGraph ;
              dc:created "..."^^xsd:DateTime ;
              dc:creator "..." ;
              prov:version 1 ;
              prov:validFrom "..."^^xsd:DateTime ;
              prov:validUntil "..."^^xsd:DateTime ;
              .

"""



## Instead keep transactions:
"""
:transactionN
  a prov:Transaction ;
  dcterms:created "date-time" ;  now
  dcterms:creator ... ;          user/machine/  mark@www
  dcterms:source  <uri> ;        resource
  rdfs:comment "..." ;
  prov:action prov:Added ;   action

These should be about the graph...
  dcterms:versionOf
  dcterms:replaces/modifies
  dcterms:hasVersion

This should be in the graph, pointing to provenance statement.
  dcterms:provenance


  .


<graph_uri> dcterms:replaces <prev_graph_uri>



select ?what ?who ?when ?format from <provenence-graph> where {
  ?t dcterms:source <uri> .
  ?t a prov:Transaction .
  ?t prov:action ?what .
  ?t dcterms:created ?when .
  ?t dcterms:creator ?who .
  } order by ?when
"""


"""

Provenance is like Recording -- both are Metadata objects with a NamedGraph??


Abstract v's concrete (realisation, representation)

Native (or natural ??) programmatic interface to a signal file.
along with a mapping to ontological terms.




<hhj>
  a bsml:Recording ;
  dcterms:provenance
  bsml:added [ a dcterms:ProvenanceStement ;
               dcterms:created "2011-03-07T15:38" ;
               dcterms:creator "dave@djbmac" ;
               rdfs:comment "imported to repo..."
              ] .

"""
