import json

from biosignalml.rdf import Format
from biosignalml.rdf.sparqlstore import Virtuoso
from biosignalml.repository import BSMLStore


if __name__ == '__main__':
#=========================

  store = Virtuoso('http://localhost:8890')

  #graphs = json.loads(
  #           store.query("select distinct ?g where { graph ?g { [] a [] } } order by ?g", format=Format.JSON)
  #           ).get('results', {}).get('bindings', [])

  #oldgraphs = [ r['g']['value'] for r in graphs if (r['g']['value']).startswith('http://devel.biosignalml.org/provenance/') ]

  graphs = json.loads(
             store.query("""select distinct ?g where { graph <http://devel.biosignalml.org/provenance> {
                              ?g dct:subject <http://devel.biosignalml.org/resource/physiobank/mitdb/100>
                              } } order by ?g""", format=Format.JSON)
             ).get('results', {}).get('bindings', [])


  oldgraphs = [ r['g']['value'] for r in graphs ]

  print '\n'.join(oldgraphs)

#  for g in oldgraphs:
#    store.delete_graph(g)



  d1 = """WITH <http://devel.biosignalml.org/provenance>
          DELETE { ?x ?p ?v } WHERE {
            ?g dct:subject <http://devel.biosignalml.org/resource/physiobank/mitdb/100> .
            ?g prv:createdBy ?x .
            ?x ?p ?v
            }"""

  d2 = """WITH <http://devel.biosignalml.org/provenance>
          DELETE { ?g ?p ?v } WHERE {
            ?g dct:subject <http://devel.biosignalml.org/resource/physiobank/mitdb/100> .
            ?g ?p ?v
            }"""

  s1 = """select ?x ?p ?v WHERE { graph <http://devel.biosignalml.org/provenance> {
            ?g dct:subject <http://devel.biosignalml.org/resource/physiobank/mitdb/100> .
            ?g prv:createdBy ?x .
            ?x ?p ?v
            }
          }"""


  s2 = """select ?g ?p ?v WHERE { graph <http://devel.biosignalml.org/provenance> {
            ?g dct:subject <http://devel.biosignalml.org/resource/physiobank/mitdb/100> .
            ?g ?p ?v
            }
          }"""

  for r in json.loads(store.query(s2, format=Format.JSON)
             ).get('results', {}).get('bindings', []): print r

  print store.query(d2)
