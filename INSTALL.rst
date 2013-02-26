Pre-requisites
==============

hdf5
libwfdb with Python bindings

easy_install/pip
----------------

* biosignalml >= 0.3.7
* tornado >= 2.4.1
* numpy >= 2.1.1



Server Install
==============

Configuration
-------------

Starting
---------

Loading Unit-of-Measure Ontologies
----------------------------------

::

  tools/load_units.sh http://www.sbpax.org/uome/list.owl
  tools/load_units.sh http://www.biosignalml.org/ontologies/examples/unit.rdf



---

# Setting up repository configuration with a 4store backend:
#

# Create an empty 4store database.
4s-backend-setup biosignal

# Start 4store and its httpd frontend (on port 8083).
4s-backend biosignal

# Load configuration graphs
4s-import biosignal --model system:config --format turtle ~/biosignalml/python/apps/repository/fulltext.ttl

## Configuration is all in Python code...
##4s-import biosignal --model http://biosignalml/configuration --format turtle ~/biosignalml/python/apps/repository/config.ttl

# Load PhysioBank database...
4s-import biosignal --format trig ~/biosignalml/physiobank/index/demo.trig


# Start httpd frontend on port 8083
4s-httpd -p 8083 biosignal

### Use 4s-import above...
### Replace the graph system:config with the contents of fulltext.ttl
##curl -T fulltext.ttl -H 'Content-Type: application/x-turtle' http://localhost:8083/data/system:config
###
### Replace the graph <http://biosignalml/configuration> with the contents of config.ttl
##curl -T config.ttl -H 'Content-Type: application/x-turtle' http://localhost:8083/data/http://biosignalml/configuration





curl -T ~/biosignalml/testdata/sinewave.edf -H "Content-type: application/x-edf" \
  http://devel.biosignalml.org/recording/test/sinewave

curl -H 'Accept: application/x-stream'						 \
  http://devel.biosignalml.org/recording/test/sinewave



curl -H "Transfer-Encoding: chunked" -T file5M \
  http://devel.biosignalml.org/recording/test/sinewave

