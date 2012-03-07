######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2011  David Brooks
#
#  $ID: ef480c7 on Wed Mar 7 13:10:14 2012 +1300 by Dave Brooks $
#
######################################################


import logging
import web

from biosignalml.rdf.formats import Format


class metadata(object):
#======================

  _repo = web.config.biosignalml['repository']

  def GET(self, name):
  #-------------------
    #logging.debug('GET: %s', web.ctx.environ)
    rec_uri = metadata._repo.get_recording_uri(name)

    accept = { k[0].strip(): k[1].strip() if len(k) > 1 else ''
                for k in [ a.split(';', 1)
                  for a in web.ctx.environ.get('HTTP_ACCEPT', '*/*').split(',') ] }
    # check rdf+xml, turtle, n3, html ??
    format = Format.TURTLE if ('text/turtle' in accept
                            or 'application/x-turtle' in accept) else Format.RDFXML

    ## Build a new RDF Graph that has { <uri> ?p ?o  } UNION { ?s ?p <uri> }
    ## and serialise this??

    if rec_uri is not None:
      rdf = metadata._repo.construct('?s ?p ?o', 'graph <%s> { ?s ?p ?o' % rec_uri
                                               + ' FILTER (?p != <http://4store.org/fulltext#stem>'
                                               + ' && (?s = <%s> || ?o = <%s>)) }' % (name, name),
                                     format=format)

#    elif format == 'text/turtle':
#      rdf = (metadata._repo.construct('<%s> ?p ?o' % name,
#                                  '<%s> ?p ?o FILTER(?p != <http://4store.org/fulltext#stem>)'
#                                   % name, format=format)
#           + metadata._repo.construct('?s ?p <%s>' % name,
#                                  '?s ?p <%s> FILTER(?p != <http://4store.org/fulltext#stem>)'
#                                   % name, format=format) )
    else:
      rdf = metadata._repo.construct('<%s> ?p ?o' % name,
       'graph <%s> { <%s> ?p ?o FILTER(?p != <http://4store.org/fulltext#stem>) }'
         % (name, name), format=format)

    if rdf:
      web.header('Content-Type', format)
      yield rdf
