import sys
import json

from biosignalml.rdf import Format
from biosignalml.rdf.sparqlstore import Virtuoso
from biosignalml.repository import BSMLStore


if __name__ == '__main__':
#=========================

  store = Virtuoso('http://localhost:8890')

  if len(sys.argv) < 3:
    print "Usage: %s repository recording_uri" % sys.argv[0]
    exit(1)

  (repo, recording) = tuple(sys.argv[1:3])

  for g in [ r['g']['value'] for r in json.loads(
               store.query("""select distinct ?g where {
                               graph <%s/provenance> {
                                ?g a bsml:RecordingGraph ;
                                   dct:subject <%s>
                                }
                              } order by ?g""" % (repo, recording), format=Format.JSON)
               ).get('results', {}).get('bindings', [])
            ]:  store.delete_graph(g)

  store.query("""WITH <%s/provenance>
                 DELETE { ?x ?p ?v } WHERE {
                   ?g a bsml:RecordingGraph ;
                      dct:subject <%s> ;
                      prv:createdBy ?x .
                   ?x ?p ?v .
                   }""" % (repo, recording))
  store.query("""WITH <%s/provenance>
                 DELETE { ?g ?p ?v } WHERE {
                   ?g a bsml:RecordingGraph ;
                      dct:subject <%s> ;
                      ?p ?v .
                   }""" % (repo, recording))
