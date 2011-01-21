######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id$
#
######################################################


import signal
import logging
from time import sleep

import repository
from importers import Importers
from frontend import WebServer


def interrupt(signum, frame):
#============================
  raise KeyboardInterrupt


if __name__ == '__main__':
#=========================

# parse arguments
  logging.basicConfig(format='%(asctime)s %(levelname)8s %(threadName)s: %(message)s')
  logging.getLogger().setLevel(logging.DEBUG)   #####

# start threads:
  file_importers = Importers()
  web_server = WebServer(repository.options.webserver['address'])
#    listen for stream requests and serve data

  signal.signal(signal.SIGHUP, interrupt)
  signal.signal(signal.SIGTERM, interrupt)
  try:
    while True: sleep(0.1)
  except KeyboardInterrupt:
    pass

# notify threads we are shutting down
  file_importers.stop()
  web_server.stop()

  #wait for threads to finish...


"""

We have Recordings of Signals. Signals are stored in Files.
Metadata is held as RDF triples in named graphs.

Graphs:


xmlns:rdfg="http://www.w3.org/2004/03/trix/rdfg-1/"

:Repository
  a rdfg:Graph .


holds information about what is in the repository.




:recording
  a rdfg:Graph .




"""


