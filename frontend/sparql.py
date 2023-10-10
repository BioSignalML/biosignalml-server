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

import biosignalml.rdf as rdf
from biosignalml.utils import xmlescape
from biosignalml import BSML

from .forms import Button, Field
import frontend


def prologue():
#==============
  p = [ 'BASE <%s>' % options.repository_uri ]
  for prefix, uri in frontend.NAMESPACES.items():
    p.append('PREFIX %s: <%s>' % (prefix, uri))
  return '\n'.join(p)


def search(sparql):
#==================
  if not sparql: return ''
  body = ['<div id="sparqlresult"><table class="results">']
  results = options.repository.query(sparql, header=True)
  for n, r in enumerate(results):
    if n == 0:                      # Header
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
      for c in cols:
        value = r.get(c, '')
        if  isinstance(value, rdf.Uri):
          value = str(value)
          (LT, GT) = ('&lt;', '&gt;')
          if results.base and value.startswith(results.base):
            uri = value[len(results.base):]
          else:
            uri = results.abbreviate_uri(value)
            if uri != value: (LT, GT) = ('', '')
          if not value.startswith(str(options.repository.uri)):
            d = '%s%s%s' % (LT, uri, GT)
          else:
            d = '%s<a href="%s" class="cluetip" target="_blank">%s</a>%s' % (LT, value, uri, GT)
        else:
          d = xmlescape(str(value))
        body.append('<td>%s</td>' % d)
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
      rows = 22,  cols = 0,
      buttons = [ Button('Search', 1, 2) ],
      fields  = [ Field.textarea('SPARQL', 'query', 75, 26, data=query) ],
      content = results
      )

##  @tornado.web.authenticated
  def get(self):
    p = [ ]
    p.append(prologue())
    p.append('')
    p.append('select ?subject ?type where {')
    p.append('  graph <%s> {' % options.repository.provenance_uri)
    p.append('    ?graph a bsml:RecordingGraph MINUS { [] prv:precededBy ?graph }')
    p.append('    }')
    p.append('  graph ?graph {')
    p.append('    ?subject a ?type')
    p.append('    }')
    p.append('  } limit 20')
    self.render('\n'.join(p)) # Default namespace prefixes and query

##  @tornado.web.authenticated
  def post(self):
    query = self.get_argument('query', '')
    self.render(query, search(query))
