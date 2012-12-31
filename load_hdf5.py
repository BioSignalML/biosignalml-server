######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2012  David Brooks
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

from biosignalml.formats.hdf5.h5recording import H5Recording
from biosignalml.rdf.sparqlstore import Virtuoso
from biosignalml.repository import BSMLStore


if __name__ == '__main__':
#=========================

  logging.basicConfig(format='%(asctime)s: %(message)s')
  logging.getLogger().setLevel('DEBUG')

  system = 'devel'

  store = BSMLStore('http://%s.biosignalml.org' % system,
#                     FourStore('http://localhost:8083'))
                     Virtuoso('http://localhost:8890'))

  rec = H5Recording.open(sys.argv[1])
# set dataset attribute... (or is this something repository manages??)

  rdf, format = rec.get_metadata()
  if rdf:
    graph = store.add_recording_graph(rec.uri, rdf, 'file://' + os.path.abspath(__file__), format)
    print '<%s> stored in <%s>' % (rec.uri, graph)

