######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id: biosignalml.py,v eeabfc934961 2011/02/14 17:47:59 dave $
#
######################################################


import web

import logging

from biosignalml.rdf import NAMESPACES
from biosignalml.utils import xmlescape
from biosignalml.model import BSML

import templates


namespaces = {
  'bsml': str(BSML.uri),
  }

namespaces.update(NAMESPACES)

def prologue():
#==============
  p = [ 'BASE <%s>' % web.config.biosignalml['repository'].base ]
  for prefix, uri in namespaces.iteritems():
    p.append('PREFIX %s: <%s>' % (prefix, uri))
  return '\n'.join(p)


def search(sparql):
#==================
  body = ['<table class="search">']
  results = web.config.biosignalml['repository'].query(sparql, header=True, html=True, abbreviate=True)
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
  body.append('</table>\n')
  return ''.join(body)


_page_template   = templates.Page()

_sparql_template = templates.SparqlForm()

def sparqlform(data, session, param=''):
#=======================================
##  logging.debug('DATA: %s', data)

  query = data.get('query', '')
  if query:
    result = search(query)
  else:
    result = ''
    p = [ ]
    p.append(prologue())
    p.append('PREFIX text: <http://4store.org/fulltext#>')
    p.append('')
    p.append('select * where {')
    p.append('  graph ?graph {')
    p.append('    ?subject ?predicate ?object')
    p.append('    }')
    p.append('  } limit 20')
    query = '\n'.join(p) # Default namespace prefixes and query
  return _page_template.page(title   = 'SPARQL search...',
                             content = _sparql_template.sparqlquery('SPARQL', '/sparqlquery', query)
                                     + result,
                             session = session,
                            )
