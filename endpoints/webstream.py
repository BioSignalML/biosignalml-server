######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id: webstream.py,v a82ffb1e85be 2011/02/03 04:16:28 dave $
#
######################################################

import os
import uuid
import logging
import threading
import functools
import time

import tornado
from tornado.options import options
from tornado.websocket import WebSocketHandler
from tornado.ioloop import IOLoop

import biosignalml.transports.stream as stream

from biosignalml      import BSML
from biosignalml.rdf  import Uri
from biosignalml.data import TimeSeries, UniformTimeSeries
from biosignalml.data.convert import RateConverter
from biosignalml.units.convert import UnitConverter
import biosignalml.formats as formats
import biosignalml.utils as utils

from frontend import user


class StreamServer(WebSocketHandler):
#====================================

  protocol = 'biosignalml-ssf'

  def __init__(self, *args, **kwds):
  #---------------------------------
    WebSocketHandler.__init__(self, *args, **kwds)  ## Can't use super() as class is not
                                                    ## correctly initialised.
    self._parser = stream.BlockParser(self.got_block, check=stream.Checksum.CHECK)
    self._repo = options.repository
    self._capabilities = [ ]

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
    self._capabilities = user.capabilities(self, None)
    bytes = bytearray(msg)
    #logging.debug('RAW: %s', bytes)
    self._parser.process(bytes)

  def send_block(self, block, check=stream.Checksum.STRICT):
  #---------------------------------------------------------
    '''
    Send a :class:`~biosignalml.transports.stream.StreamBlock` over a web socket.

    :param block: The block to send.
    :param check: Set to :attr:`~biosignalml.transports.stream.Checksum.STRICT`
      to append a SHA1 checksum to the block.
    '''
    if self.ws_connection is not None:
      self.write_message(str(block.bytes(check)), True)

  def close(self, *args):
  #----------------------
    if self.ws_connection is not None:
      WebSocketHandler.close(self, *args)

  def writing(self):
  #-----------------
    return self.ws_connection is not None and self.ws_connection.stream.writing()

  def write_count(self):
  #---------------------
    return len(self.ws_connection.stream._write_buffer) if self.ws_connection is not None else 0


class StreamEchoSocket(StreamServer):
#====================================

  def got_block(self, block):
  #--------------------------
    self.send_block(block)


class SignalReadThread(threading.Thread):
#========================================

  def __init__(self, handler, block, signals, rates, unit_map=None):
  #-----------------------------------------------------------------
    threading.Thread.__init__(self)
    self._handler = handler
    self._reqblock = block
    self._signals = signals
    self._rates = rates
    self._unit_map = unit_map

  def run(self):
  #-------------
    try:
      header = self._reqblock.header
      dtypes = { 'dtype': header.get('dtype'), 'ctype': header.get('ctype') }
      start = header.get('start')
      duration = header.get('duration')
      if start is None and duration is None: interval = None
      else:                                  interval = (start, duration)
      offset = header.get('offset')
      count = header.get('count')
      if offset is None and count is None: segment = None
      else:                                segment = (offset, count)
      maxpoints = header.get('maxsize', 0)

      # Interleave signal blocks...
      ### What if signal has multiple channels? What does read() return??
      sources = [ sig.read(interval=sig.recording.interval(*interval) if interval else None,
                   segment=segment, maxpoints=maxpoints) for sig in self._signals ]
      ## data is a list of generators
      starttimes = [ None ] * len(sources)
      converters = [ None ] * len(sources)
      datarate   = [ None ] * len(sources)
      self._active = len(sources)
      while self._active > 0:
        for n, sigdata in enumerate(sources):
          if sigdata is not None:
            try:
              data = sigdata.next()
              starttimes[n] = data.starttime
              siguri = str(self._signals[n].uri)
              keywords = dtypes.copy()
              if self._unit_map is not None: datablock = self._unit_map[n](data.data)
              else:                          datablock = data.data
              if data.is_uniform:
                keywords['rate'] = self._rates[n]
                if self._rates[n] != data.rate and converters[n] is None:
                  converters[n] = RateConverter(self._rates[n], data.data.size/len(data), maxpoints)
              else:
                if self._rates[n] is not None: raise ValueError("Cannot rate convert non-uniform signal")
                keywords['clock'] = data.times
              if converters[n] is not None:
                datarate[n] = data.rate
                for out in converters[n].convert(datablock, rate=data.rate):
                  self._send_block(stream.SignalData(siguri, starttimes[n], out, **keywords).streamblock())
                  starttimes[n] += len(out)/converters[n].rate
              else:
                self._send_block(stream.SignalData(siguri, starttimes[n], datablock, **keywords).streamblock())
            except StopIteration:
              if converters[n] is not None:
                for out in converters[n].convert(None, rate=datarate[n], finished=True):
                  self._send_block(stream.SignalData(siguri, starttimes[n], out, **keywords).streamblock())
                  starttimes[n] += len(out)/converters[n].rate
                converters[n] = None
              sources[n] = None
              self._active -= 1

    except Exception as msg:
      if str(msg) != "Stream is closed":
        logging.error("Stream exception - %s" % msg)
        self._send_block(stream.ErrorBlock(self._reqblock, str(msg)))
        if options.debug: raise

    finally:
      IOLoop.instance().add_callback(self._finished)

  def _send_block(self, block):
  #----------------------------
    IOLoop.instance().add_callback(functools.partial(self._send, block))

  def _send(self, block):
  #----------------------
    self._handler.send_block(block)

  def _finished(self):
  #-------------------
    if self._handler.write_count() > 0:
      stream = self._handler.ws_connection.stream ;
      stream._add_io_state(stream.io_loop.WRITE)
      IOLoop.instance().add_callback(self._finished)
      return
    self._active = -1
    self._handler.close()     ## All done with data request
    for s in self._signals: s.recording.close()


class StreamDataSocket(StreamServer):
#====================================

  MAXPOINTS = 50000

  def _send_error(self, msg):
  #--------------------------
    logging.error("Stream error: %s" % msg)
    self.send_block(stream.ErrorBlock(self._block, str(msg)))
    self.close()

  def _add_signal(self, uri):
  #--------------------------
    if self._repo.has_signal(uri):
      rec = self._repo.get_recording(uri, with_signals=False, open_dataset=False)
      recclass = formats.CLASSES.get(str(rec.format))
      if recclass:
        sig = self._repo.get_signal(uri,
           signal_class=rec.SignalClass)  ## Hack....!!
        rec.add_signal(sig)
        #print sig.graph.serialise()
        recclass.initialise_class(rec)
        self._sigs.append(sig)
      else:
        return self._send_error('No format for: %s' % uri)
    else:
      self._send_error('Unknown signal: %s' % uri)

  def _check_authorised(self, action):
  #-----------------------------------
    if action in self._capabilities: return True
    else:
      self._send_error("User <%s> not allowed to %s" % (self.user, user.ACTIONS[action]))
      return False

  @tornado.gen.coroutine
  def got_block(self, block):
  #--------------------------
    ##logging.debug('GOT: %s', block)
    self._block = block        ## For error handling
    if   block.type == stream.BlockType.ERROR:
      self.send_block(block)   ## Error blocks from parser v's from client...
    if   block.type == stream.BlockType.DATA_REQ:
      try:
        if not self._check_authorised(user.ACTION_VIEW): return
        uri = block.header.get('uri')
        ## Need to return 404 if unknown URI... (not a Recording or Signal)
        self._sigs = [ ]
        if isinstance(uri, list):
          for s in uri: self._add_signal(s)
        elif self._repo.has_recording(uri):
          rec = self._repo.get_recording(uri, with_signals=False)
          recclass = formats.CLASSES.get(str(rec.format))
          if recclass:
            recclass.initialise_class(rec)
            self._sigs = rec.signals()
        else:
          self._add_signal(uri)
        requested_rate = block.header.get('rate')
        if requested_rate is not None: rates = len(self._sigs)*[requested_rate]
        else:                          rates = [sig.rate for sig in self._sigs]

        unit_converter = UnitConverter(options.sparql_store)
        conversions = []
        requested_units = block.header.get('units')
        if requested_units is not None:
          units = len(self._sigs)*[requested_units]
          unit_map = [ unit_converter.mapping(sig.units, requested_units) for sig in self._sigs ]
        else:
          units = [str(sig.units) for sig in self._sigs],
          unit_map = None
#        self.send_block(stream.InfoBlock(channels = len(self._sigs),
#                                         signals = [str(sig.uri) for sig in self._sigs],
#                                         rates = rates,
#                                         units = units ))
        sender = SignalReadThread(self, block, self._sigs, rates, unit_map)
        sender.start()

      except Exception as msg:
        if str(msg) != "Stream is closed":
          self._send_error(msg)
          ##if options.debug: raise

#    elif block.type == stream.BlockType.INFO:
#      self._last_info = block.header
#      try:
#        uri = self._last_info['recording']
#        fname = self._last_info.get('dataset')
#
#        if fname is None:
#          fname = options.recordings_path + 'streamed/' + str(uuid.uuid1()) + '.h5'
#        ## '/streamed/' should come from configuration
#
#        ## Metaata PUT should have created file...
#
#        ## We support HDF5, user can use resource endpoint to PUT their EDF file...
#        recording = formats.hdf5.HDF5Recording(uri, dataset=fname)
#        # This will create, so must ensure that path is in our recording's area...
#
#        units = self._last_info.get('units')
#        rates = self._last_info.get('rates')
#        if self._last_info.get('signals'):
#          for n, s in enumerate(self._last_info['signals']):
#            recording.new_signal(siguri, units[n] if units else None,
#                                 rate=(rates[n] if rates else None) )
#        else:
#          signals = [ ]
#          for n in xrange(self._last_info['channels']):
#            signals.append(str(recording.new_signal(None, units[n] if units else None,
#                                 id=n, rate=(rates[n] if rates else None)).uri))
#          self._last_info['signals'] = signals
#        options.repository.store_recording(recording)
#        recording.close()
#
#      except Exception, msg:
#        self.send_block(stream.ErrorBlock(block, str(msg)))
#        if options.debug: raise

    elif block.type == stream.BlockType.DATA:
      # Got 'D' segment(s), uri is that of signal, that should have a recording link
      # look signal's uri up to get its Recording and hence format/source
      try:
        if not self._check_authorised(user.ACTION_EXTEND): return
        sd = block.signaldata()

#        if not sd.uri and sd.info is not None:
#          sd.uri = self._last_info['signals'][sd.info]
#        elif sd.uri not in self._last_info['signals']:
#          raise stream.StreamException("Signal '%s' not in Info header" % sd.uri)

        ## Extend to have mutiple signals in a block -- sd.uri etc are then lists

        ## Also get and use graph uri...
        rec_graph, rec_uri = self._repo.get_graph_and_recording_uri(sd.uri)
        if rec_uri is None or not self._repo.has_signal(sd.uri, rec_graph):
          raise stream.StreamException("Unknown signal '%s'" % sd.uri)

        rec = self._repo.get_recording(rec_uri, open_dataset=False, graph_uri=rec_graph)
        if str(rec.format) != formats.MIMETYPES.HDF5:
          raise stream.StreamException("Signal can not be appended to -- not HDF5")

        if rec.dataset is None:
          rec.dataset = os.path.join(options.recordings_path, str(uuid.uuid1()) + '.h5')
          self._repo.insert_triples(rec_graph,
            [ ('<%s>' % rec_uri, '<%s>' % BSML.dataset, '<%s>' % utils.file_uri(rec.dataset)) ])
          rec.initialise(create=True)
        else:
          rec.initialise()  # Open hdf5 file

        if sd.rate: ts = UniformTimeSeries(sd.data, rate=sd.rate)
        else:       ts = TimeSeries(sd.data, sd.clock)

        sig = rec.get_signal(sd.uri)
        sig.initialise(create=True, dtype=sd.dtype)
        # what if sd.units != sig.units ??
        # what if sd.rate != sig.rate ??
        # What if sd.clock ??

        sig.append(ts)

        if rec.duration is None or rec.duration < sig.duration:
          rec.duration = sig.duration
          self._repo.save_subject_property(rec_graph, rec, 'duration')
        rec.close()

      except Exception as msg:
        self.send_block(stream.ErrorBlock(block, str(msg)))
        if options.debug: raise


if __name__ == '__main__':
#=========================

  import sys

  import biosignalml.repository as repository

  def print_object(obj):
  #=====================
    attrs = [ '', repr(obj) ]
    for k in sorted(obj.__dict__):
      attrs.append('  %s: %s' % (k, obj.__dict__[k]))
    print('\n'.join(attrs))


  def test(uri):
  #-------------
    repo = repository.BSMLRepository('http://devel.biosignalml.org', 'http://localhost:8083')

  if len(sys.argv) < 2:
    sys.exit("Usage: %s uri..." % sys.argv[0])

  uri = sys.argv[1:]
  if len(uri) == 1: uri = uri[0]

  test(uri)

