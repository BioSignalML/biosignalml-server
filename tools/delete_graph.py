import sys
import biosignalml.rdf as rdf
from biosignalml.rdf.sparqlstore import Virtuoso


if __name__ == "__main__":
#=========================

  if len(sys.argv) < 3:
    print "Usage: %s store graph_uri" % sys.argv[0]
    exit(1)

  store = Virtuoso(sys.argv[1])
  store.delete_graph(sys.argv[2])
