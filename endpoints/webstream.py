######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id: webstream.py,v a82ffb1e85be 2011/02/03 04:16:28 dave $
#
######################################################

import uuid
import logging

from tornado.options import options
from tornado.websocket import WebSocketHandler

import biosignalml.transports.stream as stream

from biosignalml      import BSML
from biosignalml.rdf  import Uri
from biosignalml.data import TimeSeries, UniformTimeSeries
from biosignalml.units.convert import UnitConvertor
import biosignalml.formats as formats
import biosignalml.utils as utils



class StreamServer(WebSocketHandler):
#====================================

  protocol = 'biosignalml-ssf'

  def __init__(self, *args, **kwds):
  #---------------------------------
    WebSocketHandler.__init__(self, *args, **kwds)
    self._parser = stream.BlockParser(self.got_block, check=stream.Checksum.CHECK)
    self._repo = options.repository
#    self._last_info = None

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
    self.write_message(str(block.bytes(check)), True)


class StreamEchoSocket(StreamServer):
#====================================

  def got_block(self, block):
  #--------------------------
    self.send_block(block)


class StreamDataSocket(StreamServer):
#====================================

  MAXPOINTS = 50000

  def _add_signal(self, uri):
  #--------------------------
    if self._repo.has_signal(uri):
      rec = self._repo.get_recording(uri)
      recclass = formats.CLASSES.get(str(rec.format))
      if recclass:
        sig = self._repo.get_signal(uri)
        rec.add_signal(sig)
        #print sig.graph.serialise()
        recclass.initialise_class(rec)
        self._sigs.append(sig)
      else:
        raise IOError('No format for: %s' % uri)
    else:
      raise IOError('Unknown signal: %s' % uri)

  def got_block(self, block):
  #--------------------------
    logging.debug('GOT: %s', block)
    if   block.type == stream.BlockType.DATA_REQ:
      try:
        uri = block.header.get('uri')
        ## Need to return 404 if unknown URI... (not a Recording or Signal)
        self._sigs = [ ]
        if isinstance(uri, list):
          for s in uri: self._add_signal(s)
        elif self._repo.has_recording(uri):
          rec = self._repo.get_recording_with_signals(uri)
          recclass = formats.CLASSES.get(str(rec.format))
          if recclass:
            recclass.initialise_class(rec)
##########
            self._sigs = [ s for s in rec.signals() if s.rate ]   #### Only uniformly sampled, no annotation signals....
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

        unit_convertor = UnitConvertor(options.sparql_store)
        conversions = []
        requested_units = block.header.get('units')
        if requested_units is not None:
          units = len(self._sigs)*[requested_units]
          unit_conversion = [ unit_convertor.mapping(sig.units, requested_units) for sig in self._sigs ]
        else:
          units = [str(sig.units) for sig in self._sigs],

        self.send_block(stream.InfoBlock(channels = len(self._sigs),
                                         signals = [str(sig.uri) for sig in self._sigs],
                                         rates = [sig.rate for sig in self._sigs],
                                         units = units ))
        # Interleave signal blocks...
        ### What if signal has multiple channels? What does read() return??
        ###
        data = [ sig.read(interval=sig.recording.interval(*interval) if interval else None,
                          segment=segment, maxpoints=block.header.get('maxsize', 0))
                   for sig in self._sigs ]

        active = len(data)
        while active > 0:
          for n, sigdata in enumerate(data):
            if sigdata is not None:
              try:
                d = sigdata.next()
                siguri = str(self._sigs[n].uri)
                keywords = dtypes.copy()
                keywords['info'] = n
                if isinstance(d.dataseries, UniformTimeSeries):
                  keywords['rate'] = d.dataseries.rate
                else:
                  keywords['clock'] = d.dataseries.times
                if requested_units is not None: datablock = unit_conversion[n](d.dataseries.data)
                else:                           datablock = d.dataseries.data
                logging.debug("Send block for %s", siguri)
                self.send_block(stream.SignalData(siguri, d.starttime, datablock, **keywords).streamblock())
              except StopIteration:
                data[n] = None
                active -= 1
      except Exception, msg:
        if str(msg) != "Stream is closed":
          self.send_block(stream.ErrorBlock(block, str(msg)))
          if options.debug: raise
      finally:
        self.close()     ## All done with data request

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

#    elif block.type == stream.BlockType.RDF:
#      ## Or do we just use REST services? Or SPARQL??
#      uri = self._last_info['recording']
#      graph_uri = self._repo.get_graph_and_recording_uri(uri)[0]
#      mimetype = block.header.get('mimetype')
#      options.repository.extend_graph(graph_uri, unicode(block.content), format=mimetype)

    elif block.type == stream.BlockType.DATA:
      # Got 'D' segment(s), uri is that of signal, that should have a recording link
      # look signal's uri up to get its Recording and hence format/source
      try:
        sd = block.signaldata()

#        if not sd.uri and sd.info is not None:
#          sd.uri = self._last_info['signals'][sd.info]
#        elif sd.uri not in self._last_info['signals']:
#          raise stream.StreamException("Signal '%s' not in Info header" % sd.uri)

        ## Also get and use graph uri...
        rec_graph, rec_uri = self._repo.get_graph_and_recording_uri(sd.uri)
        if rec_uri is None or not self._repo.has_signal(sd.uri, rec_graph):
          raise stream.StreamException("Unknown signal '%s'" % sd.uri)

        rec = self._repo.get_recording_with_signals(rec_uri, False, rec_graph)
        if str(rec.format) != formats.hdf5.HDF5Recording.MIMETYPE:
          raise stream.StreamException("Signal can not be appended to -- not HDF5")

        if rec.dataset is None:
          rec.dataset = options.recordings_path + 'streamed/' + str(uuid.uuid1()) + '.h5'

          self._repo.insert_triples(rec_graph,
            [ ('<%s>' % rec_uri, '<%s>' % BSML.dataset, '<%s>' % utils.file_uri(rec.dataset)) ])
#          self._repo.insert_triples(rec.graph_uri, # or rec.graph.uri ???
#            [ '<%s> <%s> <%s>' % (rec_uri, BSML.dataset, file_uri(rec.dataset)) ])

          rec.initialise(create=True)
        else:
          rec.initialise(create_signals=True)  # Open hdf5 file

        sig = rec.get_signal(sd.uri)

        # what if sd.units != sig.units ??
        # what if sd.rate != sig.rate ??
        # What if sd.clock ??

        if sd.rate: ts = UniformTimeSeries(sd.data, rate=sd.rate)
        else:       ts = TimeSeries(sd.data, sd.clock)


        sig.append(ts)
        rec.close()

      except Exception, msg:
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

