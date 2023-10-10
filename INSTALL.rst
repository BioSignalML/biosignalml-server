Pre-requisites
==============

hdf5
libwfdb with Python bindings

easy_install/pip
----------------

* biosignalml >= 0.3.8
* tornado >= 2.4.1
* numpy >= 2.1.1
* h5py


Virtuoso
========

* Use develop/7 HEAD:::

    $ git clone -b develop/7 https://github.com/openlink/virtuoso-opensource.git

* Configuring and building:::

    $ cd virtuoso-opensource
    $ ./autogen.sh
    $ export CFLAGS="-O2 -m64"
    $ ./configure --with-readline
    $ make -j $(nproc)
    $ sudo make install

* Ensure /usr/local/virtuoso-opensource/var/lib/virtuoso/db/ and contents are
  owned by user running Virtuoso.

* Set buffer limits in /usr/local/virtuoso-opensource/var/lib/virtuoso/db/virtuoso.ini:::

    [Parameters]
    # Following for approx 1G of free memory
    NumberOfBuffers  = 100000
    MaxDirtyBuffers  =  60000

    [SPARQL]
    ResultSetMaxRows = 50000
    MaxConstructTriples = 50000

* Enable full text search (see
  http://docs.openlinksw.com/virtuoso/sparqlextensions.html#rdfsparqlrulefulltext):::

    $ /usr/local/virtuoso-opensource/bin/isql
    > DB.DBA.RDF_OBJ_FT_RULE_ADD (null, null, 'All');
    > DB.DBA.VT_BATCH_UPDATE ('DB.DBA.RDF_OBJ', 'OFF', null);
    > EXIT;

* Give SPARQL_UPDATE role to the SPARQL user, using Conductor at
  http://localhost:8890 (dba/dba) -- "System Admin"/"User Accounts"/
  "SPARQL Edit"

* Starting::

  $ cd /usr/local/virtuoso-opensource/var/lib/virtuoso/db
  $ /usr/local/virtuoso-opensource/bin/virtuoso-t -f &


Server Install
==============

Configuration
-------------

Starting
---------



Loading Unit-of-Measure Ontologies
----------------------------------

::
  cd tools
  ./load_units.sh


Loading Semantic Tag Ontologies
-------------------------------

::
  cd tools
  ./load_tags.sh


OS/X System
===========

Three separate services are required to be running for the BioSignalML repository to work:

    Virtuoso -- RDF/SPARQL engine.
    haproxy -- web proxy
    BioSignalML server


They are started and stopped via launchctl:

$ sudo launchctl load /Library/LaunchDaemons/virtuoso.plist
$ sudo launchctl load /Library/LaunchDaemons/biosignalml.plist
$ sudo launchctl load /Library/LaunchDaemons/haproxy.plist

and the equivalent 'unload' command.


---

SNORQL
======

* https://github.com/kurtjx/SNORQL and forks
* https://github.com/calipho-sib/nextprot-snorql

---

4-store
=======

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

