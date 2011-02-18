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

from utils import xmlescape
from page import BlankPage

import repository
from repository.fulltext import BOLD_ON, BOLD_OFF
from repository import model as repo

import sparql

PREFIXES = sparql.prologue()


#### Into repository.model
#
def _values(predicate, rtype):
#=============================
  values = [ ]
  # Redland 'distinct' is buggy, so we get everything and filter and sort ourselves.
  sparql = (PREFIXES
## SLOW in Redland SQLite
##       + "\n\nselect ?v where { { ?s %s ?v } union { graph ?g { ?s %s ?v } } }"
##       % (predicate, predicate) )
         + "\n\nselect ?v where { ?s %s ?v }" % predicate )
  rows = repo.triplestore.query(sparql)
  rows.next()     # Skip header
  for r in rows:
    if r[0]:
      if rtype == str: values.append(xmlescape(unicode(r[0])))
      else:
        try:
          values.append(rtype(str(r[0])))
        except ValueError:
          values.append('')
  values = list(set(values))
  values.sort()
  return values


SEARCH_RELNS  = ['AND', 'AND NOT', 'OR', ]

SEARCH_FIELDS = [ { 'prompt': 'having text',
                    'property': 'fulltext:match',
                    'tests':  ['matching'],
                    'sparql': '"%(value)s" %(property)s ?o . ?s ?p ?o .',
                    'values': [ '' ],
                    },
                  { 'prompt': 'with units',
                    'property': 'bsml:units',
                    'tests':  ['equal', 'not equal'],
                    'sparql': [ '?s %(property)s "%(value)s" .',                   # equal
                                '?s %(property)s ?o . FILTER (?o != "%(value)s)',  # not equal
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
                    'property': 'bsml:sampleRate',
                    'tests':  ['<', '<=', '=', '>=', '>', '!='],
                    'values': [ ],
                    'type':   float,
                    'sparql': '?s %(property)s ?o . FILTER (?o %(test)s %(value)s)',
                  },
                ]

# Build search template that is sent as JSON to web browser.
# Field names have to match that in static/scripts/searchform.js

def template(data, params):
#==========================
  fields = [ ]
  for f in SEARCH_FIELDS:
    values = f['values'] if f['values'] != [ ] else _values(f['property'], f.get('type', str))
    if values: fields.append( { 'prompt': f['prompt'],
                                'tests':  f['tests'],
                                'values': values,
                              } )
  return { 'relns': SEARCH_RELNS, 'fields': fields }


def highlight(s):
#===============
  x = xmlescape(s)
  return x.replace(BOLD_ON, '<b>').replace(BOLD_OFF, '</b>')


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


def searchform(data, session, param=''):
#======================================
  #logging.debug('DATA: %s', data)

  # check data.get('action', '') == 'Search'

  lines = [ ]
  lastline = -1
  line_reln = None
  groups = [ ]
  group = None
  lastgroupno = -1

  fields = [(int(k[1]), k[2:], data[k]) for k in sorted(data) if k[0] == 'L']
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
    sparql = [ ]
    sparql.append(PREFIXES)
    sparql.append('PREFIX fulltext: <fulltext:>')
    sparql.append('')
    # Redland 'distinct' is buggy..
    sparql.append('select ?s where {')
    sparql.append(query)
    sparql.append('?s rdf:type %s .' % stype)
    sparql.append('}')
    subjects = set()
    rows = repo.triplestore.query('\n'.join(sparql))
    rows.next()     # Skip header
    for r in rows:
      if r[0]: subjects.add(unicode(r[0]))
    return subjects


##############################################


  def join(s1, op, s2):
    if   op == 'OR':      return s1.union(s2)
    elif op == 'AND':     return s1.intersection(s2)
    elif op == 'AND NOT': return s1.difference(s2)
    else:                 return s1

  def termsearch(term):
    field = SEARCH_FIELDS[term[0]]
    sparql = field['sparql']
    if term[1] >= 0:
      test = field['tests'][term[1]]
      if isinstance(sparql, list): sparql = sparql[term[1]]
    else:
      test = ''
    return sparql_find('bsml:Signal',
                       sparql % { 'property': field['property'], 'test': test, 'value': term[2] })


  def linesearch(line):
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


  print sigs

  ## We need a SignalSet, created from the list of signal uris



  """
  def expr(line):
    ex = [ ]
    for term, op in line:
      ex.append('( %s )' % str(term))
      if op: ex.append(' %s ' % op)
    return ''.join(ex)

  for op, line in lines:
    if op: print '%s ' % op
    print '( %s )' % expr(line)
  """

  searchtext = data.get('text', '')
  if searchtext:
    xml = [ '<table class="search">' ]
    odd = True
    for r in repository.fulltext.search(data['text']):
      logging.debug("ROW: %s", r)
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


   ## Lookup up text
  # Advanced will have other data fields...
  ## Also check action = Search v's Advanced..
  # else:
  return BlankPage('Text search...',

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

                  """<searchform action="/searchform">Search signals...</searchform>
                     <script type="text/javascript" src="/static/script/searchform.js"/>
                     <stylesheet src="/static/css/searchform.css"/>
                  """).show(data, session)



def sparqlsearch(data, session, param=''):
#========================================
#  logging.debug('DATA: %s', data)

  query = data.get('query', '')
  if query:
    result = sparql.search(query)
  else:
    result = ''
    p = [ ]
    p.append(PREFIXES)
    p.append('PREFIX fulltext: <fulltext:>')
    p.append('')
    p.append('select * where {')
    p.append('  ?s ?p ?o')
    p.append('  } limit 20')
    query = '\n'.join(p) # Default namespace prefixes and query

  return BlankPage('SPARQL search...',
    ## Add search box here.... (as a form, action=/search?, and advanced button/link??)
                   """<form action="/sparqlsearch" height="15">
                       <button name="action" prompt="Search" row="1" col="80"/>
                       <field name="query" prompt="SPARQL"
                         type="text"
                         rows="20" cols="75">%s</field>
                      </form>
                      %s
                    """ % (xmlescape(query), result)
                     ).show(data, session)
