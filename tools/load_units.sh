python ./delete_graph.py http://virtuoso:8890 http://ontologies.biosignalml.org/units
python ./load_graph.py   http://virtuoso:8890 http://ontologies.biosignalml.org/units  \
  https://www.biosignalml.org/ontologies/uome/list.n3 turtle
python ./load_graph.py   http://virtuoso:8890 http://ontologies.biosignalml.org/units  \
  https://www.biosignalml.org/ontologies/examples/unit
