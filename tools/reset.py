import sys
import json

from biosignalml import BSML
from biosignalml.rdf import Format, PRV
from biosignalml.rdf.sparqlstore import StoreException, Virtuoso
from biosignalml.repository import BSMLStore


if __name__ == '__main__':
#=========================

  if len(sys.argv) < 2:
    sys.exit("Usage: %s repository" % sys.argv[0])

  repo = sys.argv[1]

  print("***")
  print("*** This utility will remove all BioSignalML content from the repository at %s ***" % repo)
  print("***")
  print("*** Are your sure? [NO/yes]")
  if sys.stdin.readline() != "yes\n": sys.exit(1)
  print("***")
  print("*** Are your *really* sure? [NO/yes]")
  if sys.stdin.readline() != "yes\n": sys.exit(1)

  store = Virtuoso('http://localhost:8890')

  for g in [ r['g']['value'] for r in json.loads(
               store.query("""select distinct ?g where {
                               graph <%s/provenance> {
                                ?g a bsml:RecordingGraph
                                }
                              } order by ?g""" % repo,
                            format=Format.JSON,
                            prefixes={'bsml': BSML.prefix})
               ).get('results', {}).get('bindings', [])
            ]:
    try:
      store.delete_graph(g)
    except StoreException:  ## Actual graph may not exist
      pass

  store.update("""WITH <%s/provenance>
                  DELETE { ?x ?p ?v } WHERE {
                    ?g a bsml:RecordingGraph ; prv:createdBy ?x .
                    ?x ?p ?v .
                    }""" % repo,
              prefixes={'bsml': BSML.prefix, 'prv': PRV.prefix})
  store.update("""WITH <%s/provenance>
                  DELETE { ?g ?p ?v } WHERE {
                    ?g a bsml:RecordingGraph ; ?p ?v .
                    }""" % repo,
              prefixes={'bsml': BSML.prefix})
