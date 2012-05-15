######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id: biosignalml.py,v eeabfc934961 2011/02/14 17:47:59 dave $
#
######################################################


import logging
import tornado.web
from tornado.options import options

from biosignalml.rdf import NAMESPACES
from biosignalml.utils import xmlescape
from biosignalml.model import BSML

from forms import Button, Field
import frontend

namespaces = {
  'bsml': str(BSML.URI),
  }

namespaces.update(NAMESPACES)

def prologue():
#==============
  p = [ 'BASE <%s>' % options.resource_prefix ]
  for prefix, uri in namespaces.iteritems():
    p.append('PREFIX %s: <%s>' % (prefix, uri))
  return '\n'.join(p)


def search(sparql):
#==================
  if not sparql: return ''
  body = ['<div id="sparqlresult"><table class="results">']
  results = options.repository.query(sparql, header=True, html=True, abbreviate=True)
  for n, r in enumerate(results):
    if n == 0:
      if isinstance(r, list):
        cols = r
        body.append('<tr>')
        for c in cols: body.append('<th>%s</th>' % xmlescape(c))
        body.append('</tr>\n')
        odd = True
      elif isinstance(r, bool):
        return '<div class="search">%s</div>' % r
      else:
        return '<div class="search">%s</div>' % xmlescape(str(r)).replace('\n', '<br/>')
    else:
      body.append('<tr class="odd">' if odd else '<tr>')
      for d in r: body.append('<td>%s</td>' % d['html'])
      body.append('</tr>\n')
      odd = not odd
  body.append('</table></div>\n')
  return ''.join(body)


class Query(frontend.BasePage):
#==============================
##  logging.debug('DATA: %s', data)

  def render(self, query, results=''):
    frontend.BasePage.render(self, 'tform.html',
      title = 'SPARQL search...',
      rows = 16,  cols = 0,
      buttons = [ Button('Search', 1, 13) ],
      fields  = [ Field.textarea('SPARQL', 'query', 75, 20, data=query) ],
      content = results
      )

  @tornado.web.authenticated
  def get(self):
    p = [ ]
    p.append(prologue())
    p.append('PREFIX text: <http://4store.org/fulltext#>')
    p.append('')
    p.append('select * where {')
    p.append('  graph ?graph {')
    p.append('    ?subject ?predicate ?object')
    p.append('    }')
    p.append('  } limit 20')
    self.render('\n'.join(p)) # Default namespace prefixes and query

  @tornado.web.authenticated
  def post(self):
    query = self.get_argument('query', '')
    self.render(query, search(query))
