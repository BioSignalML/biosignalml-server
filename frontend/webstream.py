######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id: webstream.py,v a82ffb1e85be 2011/02/03 04:16:28 dave $
#
######################################################

import logging

import web
from ws4py.websocket import WebSocket

import biosignalml.transports.stream as stream
from biosignalml.rdf import Uri


class StreamServer(WebSocket):
#=============================

  protocol = 'biosignalml-ssf'

  def __init__(self, *args, **kwds):
  #---------------------------------
    WebSocket.__init__(self, *args, **kwds)
    self._parser = stream.BlockParser(self._gotblock, check=stream.Checksum.CHECK)

  def _gotblock(self, block):
  #--------------------------
    pass

  def received_message(self, msg):
  #-------------------------------
    self._parser.process(msg.data)
    self.close()



class StreamEchoSocket(StreamServer):
#====================================

  def _gotblock(self, block):
  #--------------------------
    self.send(block.bytes(), True)



class StreamDataSocket(StreamServer):
#====================================

  MAXPOINTS = 4096 ### ?????

  def _gotblock(self, block):
  #--------------------------
    if block.type == stream.BlockType.DATA_REQ:
      repo = web.config.biosignalml['repository']
      uri = block.header.uri
      if isinstance(uri, list):
        recsigs = [ (repo.get_recording(s), s)
                      for s in [ repo.get_signal(u) for u in uri ] if s is not None ]
      elif repo.is_recording(uri):
        rec = repo.get_recording(uri)
        recsigs = [ (rec, s) for s in repo.get_recording_signals(uri) ]
      elif repo.is_signal(uri):
        signals = [ (repo.get_recording(uri), repo.get_signal(uri)) ]

      for (r, s) in signals:
        pass
        '''
        rec = formats.open(rec.uri)  ## Want to extend...?? Attach source...


        s.recording.source
        s.recording.type

        sigdata(s)

        source


   get ts data
    --> sd = stream.SignalData(uri, start, data, rate, clock)


    --> self.send(sd.streamblock().bytes(), True)

    repo = web.config.biosignalml['repository']
'''

'''
from biosignalml.formats.edf import EDFSource
from biosignalml.formats.streaming import StreamSink
from biosignalml.rdf import Uri, EDF
from biosignalml.model import Recording, Signal, BSML
from biosignalml.repository import triplestore
from biosignalml.repository import options


class Sender(threading.Thread):
#=============================

  def __init__(self, queue, uri, **kwds):
  #-------------------------------------
    if uri:
      source = Uri(uri)

      """
      Allow specification of time segments
        (use fragment # with list like for -t option) NO, since frag id is client side only.
        Instead use query variable ?start=123.233?duration=10.34
        Or in URI .../segment/123.233-10.34

      Allow metadata only request (don't stream any data)

      Allow specification of signals to stream...

      """
      objtype = triplestore.get_target(source, RDF.type)
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
'''
