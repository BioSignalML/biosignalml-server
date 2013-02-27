import sys
import json
import urlparse

from biosignalml.rdf import Format
from biosignalml.rdf.sparqlstore import Virtuoso
from biosignalml.repository import BSMLStore


if __name__ == '__main__':
#=========================

  if len(sys.argv) < 2:
    print "Usage: %s recording_uri" % sys.argv[0]
    exit(1)

  recording = sys.argv[1]
  p = urlparse.urlparse(recording)
  repo = p.scheme + '://' + p.netloc

  store = Virtuoso('http://localhost:8890')

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
