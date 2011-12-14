"""
Provide RESTful services.

BioSignalML Management in Python
 
:Author: David Brooks

:Copyright: David Brooks, 2011

:Licence: BSD
 
:Version: $Id$

:Requires: Tornado 2.1.1
 
"""


import tornado.web
import logging


class Resource(tornado.web.RequestHandler):
#==========================================
  """
  Base class for REST handlers.
  """

  allow = ''

  def unsupported(self, *args, **kwds):
  #------------------------------------
    '''
    Returns a 405 HTTP error with the Allow header listing supported methods.
    '''
    self.set_header('Allow', self.allow)
    self.set_status(405)
    self.finish()

  get     = unsupported
  post    = unsupported
  put     = unsupported
  delete  = unsupported
  head    = unsupported
  options = unsupported


  def parse_accept_header(self):
  #-----------------------------
    '''
    Parse an Accept header.

    :rtype: dictionary { mime-type: qvalue }
    '''
    l = [((float(k[1][2:]) if (len(k) > 1 and k[1][0:2] == 'q=') else 1.0), k[0].strip())
                for k in [ a.split(';')
                  for a in self.request.headers.get('Accept', '*/*').split(',') ] ]
    return { j[1]: j[0] for j in l if j[0] > 0 }



class Recording(Resource):
#=========================

  '''
  REST endpoint for recordings.

  '''


  allow = 'GET,POST'

  def get(self, uri='', *args, **kwds):
  #------------------------------------
    logging.debug('GET: %s -- %s', uri, self.request.headers)

    accept = self.parse_accept_header()
    logging.debug('ACCEPT: %s', accept)
    
    # Of the representations we are able to provide, we choose the one most
    # preferred by the client.


    """

    self.request.arguments()


import rdfstore


    if not uri:

      rdfstore.query('construct { ?r a bsml:Recording } distinct ?r where { graph ?r { ?r a bsml:Recording } } order by ?r')


    else:

      does uri have a scheme?  If NO, uri = REPO_BASE + uri  ???



    source, filename, fragment = self._pathname(name)
    #logging.debug('%s, %s, %s', source, filename, fragment)
    if source.startswith('http:'): rec_uri = source
    else: rec_uri = ReST._repo.base + name.split('/', 1)[0] + '/' + source

    recording = ReST._repo.get_recording(rec_uri)
    if recording is None: raise NotFound("Unknown recording: '%s'" % source)
    logging.debug("Request '%s' --> '%s'", name, recording.source)
    logging.debug('ENV: %s', web.ctx.environ)


    objtype = ReST._repo.get_type(rec_uri)
    ctype = (ReST._mimetype.get(str(recording.format), 'application/x-raw')
               if objtype in [BSML.Recording, BSML.Signal]
             else None)
    logging.debug('OBJ=%s, FMT=%s, CT=%s, AC=%s', objtype, recording.format, ctype, accept)

## Should we set 'Content-Location' header as well?
## (to actual URL of representation returned).

    web.header('Vary', 'Accept')      # Let caches know we've used Accept header
    if ctype in accept: # send file
      # Also we may be GETting a signal, not a recording
      # - check rdf:type. If Signal then find/open bsml:recording

      if recording.source is None:
        raise NotFound("Missing recording source: '%s'" % source)
      logging.debug("Streaming '%s'", recording.source)

      try:
        rfile = urllib.urlopen(str(recording.source)).fp
        web.header('Content-Type', ctype)
        ### web.header('Transfer-Encoding','chunked')
        web.header('Content-Disposition', 'attachment; filename=%s' % filename)
        while True:
          data = rfile.read(32768)
          if not data: break
          yield data
        rfile.close()
      except Exception, msg:
        raise InternalError("Error serving recording: %s" % msg)


    elif ctype not in [None, 'application/x-raw'] and 'application/x-stream' in accept:
      logging.debug('Opening: %s', ctype)

      if recording.source is None:
        raise NotFound("Missing recording source: '%s'" % source)

      RecordingClass = ReST._formats.get(ctype, (None, None))[1]
      try:
        rec = RecordingClass.open(str(recording.source), uri=recording.uri)
      except IOError:
        raise NotFound("Cannot open source: '%s'" % recording.source)

      query = web.ctx.environ['QUERY_STRING']
      if query: times = [ self._get_interval(t) for t in query.split(';') ]
      else:     times = [ (0.0, rec.duration) ]
      logging.debug("Times: %s", times)

##      logging.debug('Session: %s', frontend.session._data) # .get('lastrec', None))
      #session.lastrec = rec  ## Swig objects can't be pickled...
      frontend.session.lastrec = 'test...xxx'
##      logging.debug('Session: %s', frontend.session._data) # .get('lastrec', None))
      frontend.session._save()         ## Shouldn't be needed??
                              ## Or does saving depend on how we return??

      if objtype == BSML.Signal:
        try:
          newrate = None ############### set by query parameter... ###################
          sig = rec.get_signal(rec_uri)
          rs = None if newrate is None else samplerate.RateConvertor(newrate)
          for t in times:
            for d in sig.read(rec.interval(*t)):
              yield stream.DataBlock(d if rs is None else rs.convert(d)).data(stream.CHECKSUM_STRICT)
            if rs is not None:
              logging.debug('finish convert')
              db = stream.DataBlock(rs.finish()).data(stream.CHECKSUM_STRICT)
              logging.debug('DB=%s', db)
              yield db
        except Exception, msg:
          raise InternalError(msg)

    # elif ctype == 'text/html':
    #   yield biosignalml.recording_html(rec_uri)

    else:
      ## Build a new RDF Graph that has { <uri> ?p ?o  } UNION { ?s ?p <uri> }
      ## and serialise this??

      # check rdf+xml, turtle, n3, html ??
      format = 'text/turtle' if ('text/turtle' in accept
                              or 'application/x-turtle' in accept) else 'application/rdf+xml'
      web.header('Content-Type', format)
      if recording is not None:
        yield ReST._repo.construct('?s ?p ?o', 'graph <%s> { ?s ?p ?o' % recording.uri
                                             + ' FILTER (?p != <http://4store.org/fulltext#stem>'
                                             + ' && (?s = <%s> || ?o = <%s>)) }' % (rec_uri, rec_uri),
                                    format=format)
      elif format == 'text/turtle':
        yield (ReST._repo.construct('<%s> ?p ?o' % rec_uri,
                                    '<%s> ?p ?o FILTER(?p != <http://4store.org/fulltext#stem>)'
                                     % rec_uri, format=format)
             + ReST._repo.construct('?s ?p <%s>' % rec_uri,
                                    '?s ?p <%s> FILTER(?p != <http://4store.org/fulltext#stem>)'
                                     % rec_uri, format=format) )
      else:
        yield ReST._repo.construct('<%s> ?p ?o' % rec_uri,
         '<%s> ?p ?o FILTER(?p != <http://4store.org/fulltext#stem>)'
           % rec_uri, format=format)

    """

class Signal(Resource):
#======================

  pass


class Stream(Resource):
#======================

  pass
