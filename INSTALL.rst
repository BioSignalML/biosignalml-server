===================
Server Installation
===================

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

::

  $ poetry install


Configuration
-------------


Starting
---------

::

  $ poetry shell
  $ python tornadoserver.py --config=production.ini


Loading Unit-of-Measure Ontologies
----------------------------------

::

  $ poetry shell
  $ cd tools
  $ ./load_units.sh


Loading Semantic Tag Ontologies
-------------------------------

::

  $ poetry shell
  $ cd tools
  $ ./load_tags.sh



---

SNORQL
======

* https://github.com/kurtjx/SNORQL and forks
* https://github.com/calipho-sib/nextprot-snorql

---


Testing
=======

::

  $ curl -T ~/biosignalml/testdata/sinewave.edf -H "Content-type: application/x-edf" \
    http://devel.biosignalml.org/recording/test/sinewave

  $ curl -H 'Accept: application/x-stream'						 \
    http://devel.biosignalml.org/recording/test/sinewave

  $ curl -H "Transfer-Encoding: chunked" -T file5M \
    http://devel.biosignalml.org/recording/test/sinewave

