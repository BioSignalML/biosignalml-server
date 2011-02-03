######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id: search.py,v a82ffb1e85be 2011/02/03 04:16:28 dave $
#
######################################################


import logging

from utils import xmlescape
from page import BlankPage

import repository
from repository.fulltext import BOLD_ON, BOLD_OFF

from sparql import search as sparql_search
from sparql import namespaces, ns_prefix


def template(data, params):
#==========================
  return { 'and': ['AND', 'AND NOT', 'OR', 'OR NOT', ],
           'or':  ['OR',  'OR NOT', ],
 
           'fields': [ { 'prompt': 'text',
                         'relns':  ['matching'],
                         'values': [ '' ],
                         },
                       { 'prompt': 'units',
                         'relns':  ['equal'],
                         'values': ['V', 'mV', '...'],  ## prefill with ?units from "?s bsml:units ?units"
                         },
                       { 'prompt': 'clock',
                         'relns':  [ 'of type' ],
                         'values': ['Uniform', 'Irregular'],
                       },
                       { 'prompt': 'rate',
                         'relns':  ['<', '<=', '=', '>=', '>', '!='],
                         'values': ['1000.0', '100.0', '...'], ## prefill with ?rate from "?s bsml:rate ?rate"
                       },
                     ],
         }


def highlight(s):
#===============
  x = xmlescape(s)
  return x.replace(BOLD_ON, '<b>').replace(BOLD_OFF, '</b>')


def make_link(s):
#===============
  if s:
    for ns, prefix in namespaces.iteritems():
      if s.startswith(prefix):
        local = s[len(prefix):]
        link = xmlescape('%s:%s' % (ns, local))
        if ns != 'repo': return link
        else:
           href = REPO_LINK + local
           return '<a href="%s" id="%s" class="cluetip">%s</a>' % (href, s, link)
  return ''


def searchform(data, session, param=''):
#======================================
  logging.debug('DATA: %s', data)

  searchtext = data.get('text', '')
  if searchtext:
    xml = [ '<table class="search">' ]
    odd = True
    for r in repository.fulltext.search(data['text']):
      logging.debug("ROW: %s", r)
      xml.append('<tr class="odd">' if odd else '<tr>')
      xml.append('<td>%s</td><td>%s</td><td>%s</td><td>%s</td>' % (ns_prefix(r[0]),
                                                                   make_link(r[1]),
                                                                   ns_prefix(r[2]),
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



def sparql(data, session, param=''):
#==================================
  logging.debug('DATA: %s', data)

  query = data.get('query', '')
  if query:
    results = sparql_search(query) ## , namespaces)
    table = results[1] if results[0] else ''
  else:
    table = ''
    p = [ ]
    for ns, prefix in namespaces.iteritems():
      p.append('PREFIX %s: <%s>' % (ns, prefix))
    p.append('PREFIX fulltext: <fulltext:>')
    p.append('')
    p.append('')
    query = '\n'.join(p) # Default namespace prefixes

  return BlankPage('SPARQL search...',
    ## Add search box here.... (as a form, action=/search?, and advanced button/link??)
                   """<form action="/sparql" height="15">
                       <button name="action" prompt="Search" row="1" col="80"/>
                       <field name="query" prompt="SPARQL"
                         type="text"
                         rows="20" cols="75">%s</field>
                      </form>
                      %s
                    """ % (xmlescape(query), table)
                     ).show(data, session)
