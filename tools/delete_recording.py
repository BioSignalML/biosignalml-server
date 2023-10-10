import sys
import json
import urllib.parse as urlparse

from biosignalml import BSML
from biosignalml.rdf import Format, DCT, PRV
from biosignalml.rdf.sparqlstore import StoreException, Virtuoso
from biosignalml.repository import BSMLStore


if __name__ == '__main__':
#=========================

  if len(sys.argv) < 2:
    sys.exit("Usage: %s recording_uri" % sys.argv[0])

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
                              } order by ?g""" % (repo, recording),
                           format=Format.JSON,
                           prefixes={'bsml': BSML.prefix, 'dct': DCT.prefix})
               ).get('results', {}).get('bindings', [])
            ]:
    try:
      store.delete_graph(g)
    except StoreException:  ## Actual graph may not exist
      pass

  store.update("""WITH <%s/provenance>
                  DELETE { ?x ?p ?v } WHERE {
                    ?g a bsml:RecordingGraph ;
                      dct:subject <%s> ;
                      prv:createdBy ?x .
                    ?x ?p ?v .
                    }""" % (repo, recording),
               prefixes={'bsml': BSML.prefix, 'dct': DCT.prefix, 'prv': PRV.prefix})
  store.update("""WITH <%s/provenance>
                  DELETE { ?g ?p ?v } WHERE {
                    ?g a bsml:RecordingGraph ;
                      dct:subject <%s> ;
                      ?p ?v .
                    }""" % (repo, recording),
               prefixes={'bsml': BSML.prefix, 'dct': DCT.prefix})

