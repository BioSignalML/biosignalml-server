######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $Id$
#
######################################################


from datetime import datetime

import rdfmodel
from metadata import dct


class ProvenanceGraph(rdfmodel.Graph):
#=====================================

  def __init__(self, rdfmodel, uri):
  #---------------------------------
    super(ProvenanceGraph, self).__init__(uri)
    self._rdfmodel = rdfmodel

  def add(self, uri, format):
  #--------------------------
    self._rdfmodel.append(uri, dct.dateSubmitted, datetime.utcnow().isoformat(), self)
    self._rdfmodel.append(uri, dct.format,        format,                        self)

  def remove(self, uri):
  #---------------------
    ## 'dct.dateRemoved' is not a DC Terms property...
    self._rdfmodel.append(uri, dct.dateRemoved, datetime.utcnow().isoformat(), self)



## Instead keep transactions:
"""
:transactionN
  a prov:Transaction ;
  dct:created "date-time" ;
  dct:source  <uri> ;
  dct:author "etc" ;
  dct:format "format" ;
  prov:action prov:Added ;
  .   

select ?what ?who ?when ?format from <provenence-graph> where {
  ?t dct:source <uri> .
  ?t a prov:Transaction .
  ?t prov:action ?what .
  ?t dct:created ?when .
  ?t dct:author ?who .
  optional { ?t dct:format ?format }
  }
"""
