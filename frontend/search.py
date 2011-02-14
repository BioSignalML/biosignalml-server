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

from utils import xmlescape
from page import BlankPage

import repository
from repository.fulltext import BOLD_ON, BOLD_OFF

import sparql


# Following is sent as JSON to web browser.
# Field names have to match that in static/scripts/searchform.js

FIELD_DATA = { 'and': ['AND', 'AND NOT', 'OR', 'OR NOT', ],
               'or':  ['OR',  'OR NOT', ],
 
               'fields': [ { 'prompt': 'text',
                             'property': 'fulltext:search',
                             'relns':  ['matching'],
                             'values': [ '' ],
                             },
                           { 'prompt': 'units',
                             'property': 'bsml:units',
                             'relns':  ['equal', 'not equal'],
                             'values': ['V', 'mV', '...'],  ## prefill with ?units from "?s bsml:units ?units"
                             },
                           { 'prompt': 'clock',
                             'property': 'bsml:clock',
                             'relns':  ['of type'],
                             'values': ['Uniform', 'Irregular'],
                           },
                           { 'prompt': 'rate',
                             'property': 'bsml:rate',
                             'relns':  ['<', '<=', '=', '>=', '>', '!='],
                             'values': ['1000.0', '100.0', '...'], ## prefill with ?rate from "?s bsml:rate ?rate"
                           },
                         ],
             }



## select distinct ?value where { ?s property ?value } order by ?value



def template(data, params):
#==========================
  return FIELD_DATA


def highlight(s):
#===============
  x = xmlescape(s)
  return x.replace(BOLD_ON, '<b>').replace(BOLD_OFF, '</b>')


class SearchGroup(object):
#========================

  def __init__(self, fld):
  #-----------------------
    self._fld = fld
    self._prop = fld['property']
    self._reln = None
    self._value = None
    self._or = None

  def set_reln(self, v):
  #---------------------
    if len(self._fld['relns']) > 1:
      if v != '0': self._reln = self._fld['relns'][int(v)-1]
    else:
      self._reln = ''
      self.set_value(v)

  def set_value(self, v):
  #----------------------
    if len(self._fld['values']) > 1:
      if v != '0': self._value = self._fld['values'][int(v)-1]
    elif v: self._value = v

  def set_or(self, v):
  #-------------------
    if v != '0': self._or = FIELD_DATA['or'][int(v)-1]

  def store_tuple(self, grouplist):
  #-------------------------------
    if self._prop is not None and self._reln is not None and self._value is not None:
      grouplist.append(((self._prop, self._reln, self._value), self._or))


def searchform(data, session, param=''):
#======================================
  logging.debug('DATA: %s', data)

  # check data.get('action', '') == 'Search'

  lines = [ ]
  lastline = -1
  line_and = None
  groups = [ ]
  group = None
  lastgroupno = -1

  fields = [(int(k[1]), k[2:], data[k]) for k in sorted(data) if k[0] == 'L']
  for (l, g, v) in fields:
    if lastline != l:  # Start of a new line
      if group: group.store_tuple(groups)
      if groups: lines.append((line_and, groups))
      lastline = l
      line_and = None
      groups = [ ]
      group = None
      lastgroupno = -1

    if   g == 'AND':
      if len(lines) and v != '0': line_and = FIELD_DATA['and'][int(v)-1]
    elif g[0] == 'G':
      groupno = int(g[1])
      if lastgroupno != groupno:
        if group: group.store_tuple(groups)
        lastgroupno = groupno
        group = None
      if   g[2:] == 'F0' and v != '0': group = SearchGroup(FIELD_DATA['fields'][int(v)-1])
      elif g[2:] == 'F1': group.set_reln(v)
      elif g[2:] == 'F2': group.set_value(v)
      elif g[2:] == 'OR': group.set_or(v)

  if group: group.store_tuple(groups)
  if groups: lines.append((line_and, groups))
  logging.debug('LINES: %s', lines)

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
    table = ''
    p = [ ]
    p.append(sparql.prologue())
    p.append('PREFIX fulltext: <fulltext:>')
    p.append('')
    p.append('select * where {')
    p.append('  ?s ?p ?o')
    p.append('  } limit 20')
    query = '\n'.join(p) # Default namespace prefixes

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
