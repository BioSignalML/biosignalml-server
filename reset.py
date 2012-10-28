import sys
import json

from biosignalml.rdf import Format
from biosignalml.rdf.sparqlstore import Virtuoso
from biosignalml.repository import BSMLStore


if __name__ == '__main__':
#=========================

  print "***"
  print "*** This utility will remove all BioSignalML content from the repository ***"
  print "***"
  print "*** Are your sure? [NO/yes]"
  if sys.stdin.readline() != "yes\n": sys.exit(1)
  print "***"
  print "*** Are your *really* sure? [NO/yes]"
  if sys.stdin.readline() != "yes\n": sys.exit(1)

  store = Virtuoso('http://localhost:8890')

  for g in [ r['g']['value'] for r in json.loads(
               store.query("""select distinct ?g where {
                               graph <http://devel.biosignalml.org/provenance> {
                                ?g a bsml:RecordingGraph
                                }
                              } order by ?g""", format=Format.JSON)
               ).get('results', {}).get('bindings', [])
            ]:  store.delete_graph(g)
  store.query("""WITH <http://devel.biosignalml.org/provenance>
                 DELETE { ?x ?p ?v } WHERE {
                   ?g a bsml:RecordingGraph ; prv:createdBy ?x .
                   ?x ?p ?v .
                   }""")
  store.query("""WITH <http://devel.biosignalml.org/provenance>
                 DELETE { ?g ?p ?v } WHERE {
                   ?g a bsml:RecordingGraph ; ?p ?v .
                   }""")
