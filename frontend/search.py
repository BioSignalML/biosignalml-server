######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id: search.py,v eeabfc934961 2011/02/14 17:47:59 dave $
#
######################################################


import logging
import copy

import Stemmer
import tornado.web
import tornado.escape
from tornado.options import options

import sparql
import frontend


PREFIXES = sparql.prologue()


#### Into repository.model
#
def _values(predicate, rtype):
#=============================
  values = [ ]
  # Redland 'distinct' is buggy, so we get everything and filter and sort ourselves.
  sparql = PREFIXES + "\n\nselect distinct ?v where { ?s %s ?v }" % predicate
  #logging.debug('SP: %s', sparql)
  results = options.repository.query(sparql)
  for r in results:
    v = r[0].get('value')
    if v:
      if r[0]['type'] == 'uri':
        values.append(tornado.escape.xhtml_escape(results.abbreviate_uri(v)))
      elif rtype == str:
        values.append(tornado.escape.xhtml_escape(unicode(v)))
      else:
        try:               values.append(rtype(str(v)))
        except ValueError: values.append('')
  values = list(set(values))
  values.sort()
  return values


SEARCH_RELNS  = ['AND', 'AND NOT', 'OR', ]

SEARCH_FIELDS = [ { 'prompt': 'having text',
                    'property': 'text:stem',
                    'tests':  ['matching'],
                    'sparql': '?s %(property)s "%(value)s" ; ?p ?o .',
                    'values': [ '' ],
                    'stemtext': True,
                    },
                  { 'prompt': 'with units',
                    'property': 'bsml:units',
                    'tests':  ['equal', 'not equal'],
                    'sparql': [ '?s %(property)s %(value)s .',                   # equal
                                '?s %(property)s ?o . FILTER (?o != %(value)s)', # not equal
                              ],
                    'values': [ ]
                    },
### To come from ontology....
##                  { 'prompt': 'clock',
##                    'property': 'bsml:clock',
##                    'tests':  ['of type'],
##                    'values': ['Uniform', 'Irregular'],
##                  },
                  { 'prompt': 'having rate',
                    'property': 'bsml:rate',
                    'tests':  ['=', '!=', '<', '<=', '>', '>='],
                    'values': [ ],
                    'type':   float,
                    'sparql': '?s %(property)s ?o . FILTER (?o %(test)s %(value)s)',
                  },
                ]

# Build search template that is sent as JSON to web browser.
# Field names have to match that in static/scripts/searchform.js

class Template(tornado.web.RequestHandler):
#==========================================
  def post(self):
    fields = [ ]
    for f in SEARCH_FIELDS:
      values = f['values'] if f['values'] != [ ] else _values(f['property'], f.get('type', str))
      if values: fields.append( { 'prompt': f['prompt'],
                                  'tests':  f['tests'],
                                  'values': values } )
    self.write({ 'relns': SEARCH_RELNS, 'fields': fields })


#def highlight(s):
##===============
#  x = xmlescape(s)
#  return x.replace(BOLD_ON, '<b>').replace(BOLD_OFF, '</b>')


class SearchGroup(object):
#========================

  def __init__(self, nbr):
  #-----------------------
    self._index = int(nbr)
    self._test = None
    self._value = None
    self._termreln = None

  def set_test(self, v):
  #---------------------
    if len(SEARCH_FIELDS[self._index]['tests']) > 1:
      self._test = int(v)
    else:
      self._test = -1
      self.set_value(v)

  def set_value(self, v):
  #----------------------
    if v: self._value = v

  def term_reln(self, v):
  #---------------------
    if v: self._termreln = v

  def store_tuple(self, grouplist):
  #-------------------------------
    if self._test is not None and self._value is not None:
      grouplist.append(((self._index, self._test, self._value), self._termreln))



  """
  def expr(line):
  #--------------
    ex = [ ]
    for term, op in line:
      ex.append('( %s )' % str(term))
      if op: ex.append(' %s ' % op)
    return ''.join(ex)

  for op, line in lines:
    if op: print '%s ' % op
    print '( %s )' % expr(line)

  searchtext = data.get('text', '')
  if searchtext:
    xml = [ '<table class="search">' ]
    odd = True
    for r in repository.fulltext.search(data['text']):
      #logging.debug("ROW: %s", r)
      xml.append('<tr class="odd">' if odd else '<tr>')
      xml.append('<td>%s</td><td>%s</td><td>%s</td><td>%s</td>' % (sparql.abbreviate(r[0]),
                                                                   sparql.make_link(r[1]),
                                                                   sparql.abbreviate(r[2]),
                                                                   highlight(r[3])))
      xml.append('</tr>')
      odd = not odd
    xml.append('</table>')
  else:
    xml = [ ]

  """

  ## Lookup up text
  # Advanced will have other data fields...
  ## Also check action = Search v's Advanced..
  # else:


class Related(tornado.web.RequestHandler):
#=========================================
  @tornado.web.authenticated
  def post(self):
    related = [ ]
    clicked = self.get_argument('id', '')
    related.append('id...')
    self.write( { 'ids': related } )


class Search(frontend.BasePage):
#===============================

  @tornado.web.authenticated
  def get(self):
    self.render('search.html', title = 'Query repository')

## Simple text search v's advanced...
    ## Add search box here.... (as a form, action=/search?, and advanced button/link??)
#                  """<form action="/search" height="1">
#                      <button name="action" prompt="Search" row="1" col="42"/>
#                      <field name="text" prompt="Find Text" row="1" pcol="1"
#                        fcol="10" size="20" value="%s"/>
#                     </form>
#                     <script type="text/javascript" src="/static/script/searchform.js"/>
#                     <stylesheet src="/static/css/searchform.css"/>
#                   %s
#                   """ % (xmlescape(searchtext), ''.join(xml))


  @tornado.web.authenticated
  def post(self):
    data = self.request.arguments
    #logging.debug('DATA: %s', data)
    # check data.get('action', '') == 'Search'

    lines = [ ]
    lastline = -1
    line_reln = None
    groups = [ ]
    group = None
    lastgroupno = -1
    fields = [(int(k[1]), k[2:], data[k][0]) for k in sorted(data) if k[0] == 'L']
    for (l, g, v) in fields:
      ##print l, g, v
      if lastline != l:  # Start of a new line
        if group: group.store_tuple(groups)
        if groups: lines.append((line_reln, groups))
        lastline = l
        line_reln = None
        groups = [ ]
        group = None
        lastgroupno = -1
      if   g == 'LINE':
        if len(lines) and v: line_reln = v
      elif g[0] == 'G':
        groupno = int(g[1])
        if lastgroupno != groupno:
          if group: group.store_tuple(groups)
          lastgroupno = groupno
          group = None
        if   g[2:] == 'F0' and v: group = SearchGroup(v)
        elif g[2:] == 'F1':   group.set_test(v)
        elif g[2:] == 'F2':   group.set_value(v)
        elif g[2:] == 'TERM': group.term_reln(v)
    if group: group.store_tuple(groups)
    if groups: lines.append((line_reln, groups))
    #logging.debug('LINES: %s', lines)

##############################################
#
# This goes into repository.model....

    def sparql_find(stype, query):
    #-----------------------------
      sparql = [ ]
      sparql.append(PREFIXES)
      sparql.append('PREFIX text: <http://4store.org/fulltext#>')
      sparql.append('')
      # Redland 'distinct' is buggy..
      sparql.append('select ?s ?t where {')
      sparql.append(query)
      sparql.append('?s rdf:type ?t .')   ##  % stype)
      sparql.append('}')
      subjects = set()
      for r in options.repository.query('\n'.join(sparql), html=True, abbreviate=True):
        #logging.debug('R: %s', r)
        if r[0].get('value'):
          subjects.add((r[0]['value'], r[0]['html'], r[1]['html'] if r[1]['html'] else ''))
      return subjects

##############################################

    def join(s1, op, s2):
    #--------------------
      #logging.debug('S2: %s', s2)
      if   op == 'OR':      return s1.union(s2)
      elif op == 'AND':     return s1.intersection(s2)
      elif op == 'AND NOT': return s1.difference(s2)
      else:                 return s1

    stemmer = Stemmer.Stemmer('en', 0)

    def termsearch(term):
    #--------------------
      field = SEARCH_FIELDS[term[0]]
      sparql = field['sparql']
      if term[1] >= 0:
        test = field['tests'][term[1]]
        if isinstance(sparql, list): sparql = sparql[term[1]]
      else:
        test = ''
      v = stemmer.stemWord(term[2]).lower() if field.get('stemtext') else term[2]
      return sparql_find('bsml:Signal',
                         sparql % { 'property': field['property'], 'test': test, 'value': v })

    def linesearch(line):
    #--------------------
      sigs = set()
      nextop = 'OR'
      for term, op in line:
        sigs = join(sigs, nextop, termsearch(term))
        nextop = op
      return sigs

    sigs = set()
    for op, line in lines:
      if not op: op = 'OR'
      sigs = join(sigs, op, linesearch(line))
    sigs = list(sigs)
    sigs.sort()
    html = [ '<div>' ]
    for n, s in enumerate(sigs):
      html.append('<div class="result%s" id="%s">%s %s</div>'
                             % (' odd' if n%2 else '', s[0], s[1], s[2]))
    html.append('</div>')
    self.write( { 'html': '\n'.join(html) } )

  ## We need a SignalSet, created from the list of signal uris



  """
  def expr(line):
  #--------------
    ex = [ ]
    for term, op in line:
      ex.append('( %s )' % str(term))
      if op: ex.append(' %s ' % op)
    return ''.join(ex)

  for op, line in lines:
    if op: print '%s ' % op
    print '( %s )' % expr(line)

  searchtext = data.get('text', '')
  if searchtext:
    xml = [ '<table class="search">' ]
    odd = True
    for r in repository.fulltext.search(data['text']):
      #logging.debug("ROW: %s", r)
      xml.append('<tr class="odd">' if odd else '<tr>')
      xml.append('<td>%s</td><td>%s</td><td>%s</td><td>%s</td>' % (sparql.abbreviate(r[0]),
                                                                   sparql.make_link(r[1]),
                                                                   sparql.abbreviate(r[2]),
                                                                   highlight(r[3])))
      xml.append('</tr>')
      odd = not odd
    xml.append('</table>')
  else:
    xml = [ ]

  """


"""
select ?graph ?rec ?tl ?evt ?desc ?at where {
  graph ?graph {
    ?rec a bsml:Recording ;
         tl:timeline ?tl .
    ?evt a evt:Event ;
         dcterms:description ?desc ;
         tl:time ?tim .
    ?tim a tl:RelativeInstant ;
         tl:timeline ?tl ;
         tl:atDuration ?at .
    }
  }


"""
