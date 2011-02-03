import web
import logging

from metadata import NAMESPACES
from metadata import model as triplestore
from utils import xmlescape
from repository import options
from bsml import BSML


namespaces = {
  'bsml': str(BSML.uri),
  'repo': options.repository['import_base'],
  }

namespaces.update(NAMESPACES)


def ns_prefix(s):
#===============
  if s:
    for ns, prefix in namespaces.iteritems():
      if s.startswith(prefix): return xmlescape('%s:%s' % (ns, s[len(prefix):]))
    return s
  return ''



def search(sparql):
#=================
  cols = [ 'error' ]
  words = sparql.split()
  for w in words:
    if w[0] == '?' and w[1:] not in cols: cols.append(w[1:])

  results = triplestore.query(sparql)
  ### Return XML or whatever.
  ### Can we request format??
  ### What about CONSTRUCT, ASK, DESCRIBE ??
  ### XML will have column headings, so give them even if no data rows.

##  logging.debug('--> %s', results)
  hdr = False
  body = ['<table class="search">']
  odd = True
  for r in results:
    if r:
      if not hdr:
        body.append('<tr>')
        for c in cols:
          if c in r: body.append('<th>%s</th>' % xmlescape(c))
        body.append('</tr>\n')
        hdr = True
      body.append('<tr class="odd">' if odd else '<tr>')
      for c in cols:
        if c in r: body.append('<td>%s</td>' % xmlescape(ns_prefix(str(r[c]))))
      body.append('</tr>\n')
      odd = not odd
  body.append('</table>\n')
  return (len(results), ''.join(body))


class query(object):
#==================

  def _process(self, method, path):
    data = web.input(_method = method)
#    logging.debug('Request: %s %s %s', method, path, str(data))
    sparql = str(data.get('query', ''))
    logging.debug('SPARQL: %s', sparql)
    return '<html><body><h1>%d results:</h1>%s</body></html>' % search(sparql)


  def GET(self, name):
  #==================
    return self._process('GET', name)

  def POST(self, name):
  #===================
    return self._process('POST', name)

