import web
import logging

from metadata import NAMESPACES
from utils import xmlescape
from bsml import BSML

import repository as repo


namespaces = {
  'bsml': str(BSML.uri),
  }

namespaces.update(NAMESPACES)

querybase = repo.options.repository['base']


def prologue():
#==============
  p = [ 'BASE <%s>' % querybase ]
  for ns, prefix in namespaces.iteritems():
    p.append('PREFIX %s: <%s>' % (ns, prefix))
  return '\n'.join(p)


def abbreviate(s):
#=================
  if s:
    for ns, prefix in namespaces.iteritems():
      if s.startswith(prefix): return xmlescape('%s:%s' % (ns, s[len(prefix):]))
    if s.startswith(querybase): return xmlescape('<%s>' % s[len(querybase):])
    return s
  return ''


def make_link(s):
#===============
  if s.startswith(querybase):
    local = xmlescape(s[len(querybase):])
##    href = biosignalml.REPO_LINK + local
    href = '/repository/' + local
    return '<a href="%s" id="%s" class="cluetip">%s</a>' % (href, s, local)
  else:
    return abbreviate(s)



def search(sparql):
#=================

  results = repo.triplestore.query(sparql,
                                   format='turtle')   # If CONSTRUCT graph
  r = results.next()

  if   isinstance(r, list):
    cols = r
    body = ['<table class="search">']
    body.append('<tr>')
    for c in cols: body.append('<th>%s</th>' % xmlescape(c))
    body.append('</tr>\n')
    odd = True
    for r in results:
      body.append('<tr class="odd">' if odd else '<tr>')
      for d in r: body.append('<td>%s</td>' % make_link(unicode(d)))
      body.append('</tr>\n')
      odd = not odd
    body.append('</table>\n')
    return ''.join(body)

  elif isinstance(r, bool):
    return '<div class="search">%s</div>' % r

  elif isinstance(r, str):
    return '<div class="search">%s</div>' % xmlescape(r).replace('\n', '<br/>')

  ## elif isinstance(r, ???) ## a stream iterator
  ## or do we return a serialiased graph ???

##  logging.debug('QResult: %s', results)
##  logging.debug('--> %s', results)

  return ''


class query(object):
#==================

  def _process(self, method, path):
    data = web.input(_method = method)
#    logging.debug('Request: %s %s %s', method, path, str(data))
    sparql = unicode(data.get('query', ''))
    logging.debug('SPARQL: %s', sparql)
    return '<html><body><h1>%d results:</h1>%s</body></html>' % search(sparql)


  def GET(self, name):
  #==================
    return self._process('GET', name)

  def POST(self, name):
  #===================
    return self._process('POST', name)

