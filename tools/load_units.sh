python ./delete_graph.py http://localhost:8890 http://ontologies.biosignalml.org/units
python ./load_graph.py   http://localhost:8890 http://ontologies.biosignalml.org/units  \
  http://www.sbpax.org/uome/list.owl
python ./load_graph.py   http://localhost:8890 http://ontologies.biosignalml.org/units  \
  http://www.biosignalml.org/ontologies/examples/unit
