import sys
import biosignalml.rdf as rdf
from biosignalml.rdf.sparqlstore import Virtuoso


if __name__ == "__main__":
#=========================

  if len(sys.argv) < 4:
    print "Usage: %s store graph_uri graph_source [format]" % sys.argv[0]
    exit(1)
  if len(sys.argv) == 5: format = rdf.Format.format(sys.argv[4])
  else:                  format = rdf.Format.RDFXML

  store = Virtuoso(sys.argv[1])
  graph = rdf.Graph.create_from_resource(rdf.Uri(sys.argv[3]), format, base=rdf.Uri(sys.argv[3]))
  ##print graph.serialise(format=rdf.Format.TURTLE)
  store.extend_graph(sys.argv[2], graph.serialise(format=rdf.Format.RDFXML), format=rdf.Format.RDFXML)
