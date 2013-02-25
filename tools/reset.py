import sys
import json

from biosignalml.rdf import Format
from biosignalml.rdf.sparqlstore import Virtuoso
from biosignalml.repository import BSMLStore


if __name__ == '__main__':
#=========================

  if len(sys.argv) < 2:
    print "Usage: %s repository" % sys.argv[0]
    exit(1)

  repo = sys.argv[1]

  print "***"
  print "*** This utility will remove all BioSignalML content from the repository at %s ***" % repo
  print "***"
  print "*** Are your sure? [NO/yes]"
  if sys.stdin.readline() != "yes\n": sys.exit(1)
  print "***"
  print "*** Are your *really* sure? [NO/yes]"
  if sys.stdin.readline() != "yes\n": sys.exit(1)

  store = Virtuoso('http://localhost:8890')

  for g in [ r['g']['value'] for r in json.loads(
               store.query("""select distinct ?g where {
                               graph <%s/provenance> {
                                ?g a bsml:RecordingGraph
                                }
                              } order by ?g""" % repo, format=Format.JSON)
               ).get('results', {}).get('bindings', [])
            ]:  store.delete_graph(g)

  store.query("""WITH <%s/provenance>
                 DELETE { ?x ?p ?v } WHERE {
                   ?g a bsml:RecordingGraph ; prv:createdBy ?x .
                   ?x ?p ?v .
                   }""" % repo)
  store.query("""WITH <%s/provenance>
                 DELETE { ?g ?p ?v } WHERE {
                   ?g a bsml:RecordingGraph ; ?p ?v .
                   }""" % repo)
