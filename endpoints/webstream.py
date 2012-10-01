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

from tornado.options import options
from tornado.websocket import WebSocketHandler

import biosignalml.transports.stream as stream

from biosignalml      import BSML
from biosignalml.rdf  import Uri
from biosignalml.data import TimeSeries, UniformTimeSeries
import biosignalml.formats as formats


class StreamServer(WebSocketHandler):
#====================================

  protocol = 'biosignalml-ssf'

  def __init__(self, *args, **kwds):
  #---------------------------------
    WebSocketHandler.__init__(self, *args, **kwds)
    self._parser = stream.BlockParser(self.got_block, check=stream.Checksum.CHECK)
    self._repo = options.repository

  def select_subprotocol(self, protocols):
  #---------------------------------------
    if StreamServer.protocol in protocols:
      return StreamServer.protocol
    else:
      self.close()

  def got_block(self, block):
  #--------------------------
    pass

  def on_message(self, msg):
  #-------------------------
    # self.request.headers ### will get headers sent with request, incl. cookies...
    try:
      bytes = bytearray(msg)
    except TypeError:
      bytes = bytearray(str(msg))
    logging.debug('RAW: %s', bytes)
    self._parser.process(bytes)

  def send_block(self, block, check=stream.Checksum.STRICT):
  #---------------------------------------------------------
    '''
    Send a :class:`~biosignalml.transports.stream.StreamBlock` over a web socket.

    :param block: The block to send.
    :param check: Set to :attr:`~biosignalml.transports.stream.Checksum.STRICT`
      to append a MD5 checksum to the block.
    '''
    self.write_message(str(block.bytes(check)), True)


class StreamEchoSocket(StreamServer):
#====================================

  def got_block(self, block):
  #--------------------------
    self.send_block(block)


class StreamDataSocket(StreamServer):
#====================================

  MAXPOINTS = 4096 ### ?????

  def _add_signal(self, uri):
  #--------------------------
    if self._repo.has_signal(uri):
      rec = self._repo.get_recording(uri)
      recclass = formats.CLASSES.get(str(rec.format))
      if recclass:
        sig = self._repo.get_signal(uri)
        rec.add_signal(sig)
        #print sig.graph.serialise()
        recclass.initialise_class(rec, str(rec.source))
        self._sigs.append(sig)

  def got_block(self, block):
  #--------------------------
    logging.debug('GOT: %s', block)
    if   block.type == stream.BlockType.DATA_REQ:
      try:
        uri = block.header.get('uri')
        self._sigs = [ ]
        if isinstance(uri, list):
          for s in uri: self._add_signal(s)
        elif self._repo.has_recording(uri):
          rec = self._repo.get_recording_with_signals(uri)
          recclass = formats.CLASSES.get(str(rec.format))
          if recclass:
            recclass.initialise_class(rec, str(rec.source))
            self._sigs = rec.signals()
        else:
          self._add_signal(uri)
        start = block.header.get('start')
        duration = block.header.get('duration')
        if start is None and duration is None: interval = None
        else:                                  interval = (start, duration)
        offset = block.header.get('offset')
        count = block.header.get('count')
        if offset is None and count is None: segment = None
        else:                                segment = (offset, count)
        dtypes = { 'dtype': block.header.get('dtype'), 'ctype': block.header.get('ctype') }
        for sig in self._sigs:
          for d in sig.read(interval=sig.recording.interval(*interval) if interval else None,
                            segment=segment,
                            points=block.header.get('maxsize', 0)):
            keywords = dtypes.copy()
            if isinstance(d.dataseries, UniformTimeSeries):
              keywords['rate'] = d.dataseries.rate
            else:
              keywords['clock'] = d.dataseries.times
            self.send_block(stream.SignalData(str(sig.uri), d.starttime, d.dataseries.data, **keywords).streamblock())
      except Exception, msg:
        if str(msg) != "Stream is closed":
          self.send_block(stream.ErrorBlock(0, block, str(msg)))
          if options.debug: raise
      finally:
        self.close()     ## All done with data request

    elif block.type == stream.BlockType.DATA:
      # Got 'D' segment(s), uri is that of signal, that should have a recording link
      # look signal's uri up to get its Recording and hence format/source
      try:
        sd = block.signaldata()
        rec_uri = self._repo.get_recording_graph_uri(sd.uri)
        if rec_uri is None or not self._repo.has_signal_in_recording(sd.uri, rec_uri):
          raise stream.StreamException("Unknown signal '%s'" % sd.uri)
        rec = self._repo.get_recording_with_signals(rec_uri)
        if str(rec.format) != str(BSML.BSML_HDF5):
          raise stream.StreamException("Signal can not be appended to -- wrong format")
        recclass = formats.CLASSES.get(str(rec.format))
        recclass.initialise_class(rec, str(rec.source))
        if sd.rate: ts = UniformTimeSeries(sd.data, rate=sd.rate)
        else:       ts = TimeSeries(sd.clock, sd.data)
        rec.get_signal(sd.uri).append(ts)
      except Exception, msg:
        self.send_block(stream.ErrorBlock(0, block, str(msg)))
        if options.debug: raise





if __name__ == '__main__':
#=========================

  import sys

  from triplestore import repository

  def print_object(obj):
  #=====================
    attrs = [ '', repr(obj) ]
    for k in sorted(obj.__dict__):
      attrs.append('  %s: %s' % (k, obj.__dict__[k]))
    print '\n'.join(attrs)


  def test(uri):
  #-------------

    repo = repository.BSMLRepository('http://devel.biosignalml.org', 'http://localhost:8083')



  if len(sys.argv) < 2:
    print "Usage: %s uri..." % sys.argv[0]
    sys.exit(1)

  uri = sys.argv[1:]
  if len(uri) == 1: uri = uri[0]


  test(uri)

