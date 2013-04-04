######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2013  David Brooks
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
######################################################

import os, sys
import logging

from biosignalml import BSML
import biosignalml.rdf as rdf
from biosignalml.formats.hdf5 import H5Recording
from biosignalml.rdf.sparqlstore import Virtuoso
from biosignalml.repository import BSMLUpdateStore


if __name__ == '__main__':
#=========================

  logging.basicConfig(format='%(asctime)s: %(message)s')
  logging.getLogger().setLevel('DEBUG')

  if len(sys.argv) < 3:
    print "Usage: %s REPOSITORY_URI BIOSIGNALML_HDF5_FILE" % sys.argv[0]
    sys.exit(1)

  store = BSMLUpdateStore(sys.argv[1],
#                     FourStore('http://localhost:8083'))
                     Virtuoso('http://localhost:8890'))

  rec = H5Recording.open(sys.argv[2])

  statements, format = rec.get_metadata()
  if statements is None: raise ValueError("No metadata in source file")

  # rec.dataset = ....  From repo? Parameter?? Default to filename's full path??
  #                     Move/rename/copy file ??
  dataset = rdf.Uri('file://' + os.path.abspath(sys.argv[2]))

  graph = rdf.Graph.create_from_string(rec.uri, statements, format)
  graph.set_subject_property(rec.uri, BSML.dataset, dataset)

  graph_uri = store.add_recording_graph(rec.uri, graph.serialise(), 'file://' + os.path.abspath(__file__))
  print '<%s> stored in <%s>' % (rec.uri, graph_uri)

