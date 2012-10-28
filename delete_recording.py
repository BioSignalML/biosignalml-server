import sys
import json

from biosignalml.rdf import Format
from biosignalml.rdf.sparqlstore import Virtuoso
from biosignalml.repository import BSMLStore


if __name__ == '__main__':
#=========================

  store = Virtuoso('http://localhost:8890')

  if len(sys.argv) < 2:
    print "Usage: %s recording_uri" % sys.argv[0]
    exit(1)

  for g in [ r['g']['value'] for r in json.loads(
               store.query("""select distinct ?g where {
                               graph <http://devel.biosignalml.org/provenance> {
                                ?g a bsml:RecordingGraph ;
                                   dct:subject <%s>
                                }
                              } order by ?g""" % sys.argv[1], format=Format.JSON)
               ).get('results', {}).get('bindings', [])
            ]:  store.delete_graph(g)
  store.query("""WITH <http://devel.biosignalml.org/provenance>
                 DELETE { ?x ?p ?v } WHERE {
                   ?g a bsml:RecordingGraph ;
                      dct:subject <%s> ;
                      prv:createdBy ?x .
                   ?x ?p ?v .
                   }""" % sys.argv[1])
  store.query("""WITH <http://devel.biosignalml.org/provenance>
                 DELETE { ?g ?p ?v } WHERE {
                   ?g a bsml:RecordingGraph ;
                      dct:subject <%s> ;
                      ?p ?v .
                   }""" % sys.argv[1])
