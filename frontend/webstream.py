######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id$
#
######################################################


import os, sys
import threading, Queue
import logging
import web

from edf import EDFSource
from streaming import StreamSink
from metadata import Uri, rdf
from metadata import model as triplestore
from bsml import Recording, Signal, BSML
from repository import options


class Sender(threading.Thread):
#=============================

  def __init__(self, queue, uri, **kwds):
  #-------------------------------------
    if uri:
      source = Uri(uri)

      """
      Allow specification of time segments (use fragment # with list like for -t option)

      Allow metadata only request (don't stream any data)

      Allow specification of signals to stream...

      """
      objtype = triplestore.get_target(source, rdf.type)
      if   objtype == BSML.Recording:
        rec = Recording.open(source)
        signals = rec.signals()
      elif objtype == BSML.Signal:
        sig = Signal.open(source)    #### Need open() to find recording...
                                     #### either from URI structure
                                     #### or global statement...
        rec = sig.recording
        signals = [ sig ]

      self._sendQ = queue
      if rec.format in [ BSML.EDF, BSML.EDFplus ]:
        logging.debug("Opening EDF '%s' with signals: %s", rec.source, signals)
        self._datasource = EDFSource(rec.source, signals)
      else:
        raise Exception('Unsupported data format...')

      self._sink = StreamSink(self, rec.uri, [ s.uri for s in signals ] )

      self._sink.send_metadata(rec, options.repository['import_base'])
      threading.Thread.__init__(self, **kwds)
      self.start()

  def write(self, data):
  #--------------------
    self._sendQ.put(data)

  def run(self):
  #------------  
    for data in self._datasource.frames():
      logging.debug("Signal: '%s'", str(data))
      self._sink.send_signal(data)
    self._sink.flush_signals()
