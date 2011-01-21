######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id$
#
######################################################


import logging

from utils import xmlescape, maketime, trimdecimal, chop
from page import BlankPage

import repository
from repository import options
import mktree
from sparql import search as sparql_search

#########
import metadata as meta
import bsml.signal
from bsml import BSML, Recording
from metadata import model as triplestore
#########


class TreeBuilder(object):
#=========================

  def __init__(self, tree, prefix, selected=''):
  #--------------------------------------------
    self._tree = tree
    self._prefix = prefix
    self._selected = selected.split('/')


  def _element(self, tree, depth):
  #-------------------------------
    l = [ '<subtree>' ] if depth else [ ]
    last = len(tree) - 1
    for n, t in enumerate(tree):
      if t[1] == [ ]:
        details = t[0]
        l.append('<leaf action="%s%s" id="%s" %s>%s</leaf>'
                % (self._prefix, details[1], details[2].uri,
                   'class="selected"' if depth < len(self._selected) and details[0] == self._selected[depth] else '',
                   details[0]) )
      else:
        l.append('<node %s>%s'
                % ('class="jstree-open"' if depth < len(self._selected) and t[0] == self._selected[depth] else '',
                   xmlescape(t[0])) )
        l.extend(self._element(t[1], depth+1))
        l.append('</node>')
    if depth: l.append('</subtree>')
    return l

  def xml(self):
  #-------------
    l = [ '<tree>' ]
    l.extend(self._element(self._tree, 0))
    l.append('</tree>')
    return '\n'.join(l)


def xmltree(nodes, base, prefix, selected=''):
#============================================
  return TreeBuilder(mktree.maketree(nodes, base), prefix, selected).xml()


def table_header(properties):
#===========================
  return '<th>' + '</th><th>'.join([ p[0] for p in properties ]) + '</th>'
  

def property_details(obj, properties, table, **args):
#===================================================
  opn = '<td>'  if table else '<p>'
  cls = '</td>' if table else '</p>'
  r = [ ]
  for prm, prop, fn in properties:
    v = getattr(obj, prop)
    if fn:                    t = fn[0](v, *[ args[a] for a in fn[1] ] if fn[1] else [ ])
    elif isinstance(v, list): t = '<br/>'.join([ xmlescape(str(s)) for s in v ])
    else:                     t = xmlescape(str(v))
    if table: r.append(t)
    elif v:   r.append(prm + ': ' + t) if prm else r.append(t)
  return opn + (cls + opn).join(r) + cls



############## Above should be in separate module ###############


namespaces = {
  'bsml': str(BSML.uri),
  'repo': options.repository['import_base'],
  }

namespaces.update(meta.NAMESPACES)


def ns_prefix(s):
#===============
  if s:
    for ns, prefix in namespaces.iteritems():
      if s.startswith(prefix): return xmlescape('%s:%s' % (ns, s[len(prefix):]))
    return s
  return ''



# Generate list of signals in a recording (as a <table>)

signal_metadata = [ ('Id',    'uri',   (chop, ['n'])),
                    ('Name',  'label', None),
                    ('Units', 'units', None),
                    ('Rate',  'rate',  (trimdecimal, None)),
                  ]

def signal_details(recuri, signal=None):
#======================================
  lenhdr = len(recuri) + 1
  recording = repository.model.get_recording(recuri)
  xml = [ '<table>' ]
  odd = True
  xml.append('<tr>%s</tr>' % table_header(signal_metadata))
  for sig in recording.signals():
    xml.append('<tr class="selected">' if str(sig.uri) == signal
          else '<tr class="odd">'      if odd
          else '<tr>')
    xml.append(property_details(sig, signal_metadata, True, n=lenhdr))
    xml.append('</tr>')
    odd = not odd
  xml.append('</table>')
  return ''.join(xml)


recording_metadata = [ ('Desc',     'description',    None),
                       ('Created',  'start_datetime', None),
                       ('Duration', 'duration',       (maketime, None)),
                       ('Format',   'format',         None),
                       ('Study',    'investigation',  None),
                       ('Comments', 'comments',       None),
                       ('Source',   'source',         None),
                     ]


def build_metadata(uri):
#======================
  logging.debug('Get metadata for: %s', uri)
  html = [ '<div class="metadata">' ]
  if uri:
    source = meta.Uri(uri)
    objtype = triplestore.get_target(source, meta.rdf.type)
    if   objtype == BSML.Recording:
      rec = repository.model.get_recording(source)
      ## What about a local cache of opened recordings?? (keyed by uri)
      ## in bsml.recordings module ?? in repository.model ??
      html.append(property_details(rec, recording_metadata, False))
    elif objtype == BSML.Signal:
      pass
    elif objtype == BSML.Annotation:
      html.append('annotation comment, time, etc')
  html.append('</div>')
  return ''.join(html)


# Tooltip pop-up:

def metadata(get, post, params):
#==============================
  return { 'html': build_metadata(post.get('uri', '')) }


# Generate tree of recordings along with details of signals when recording clicked on.

REPO_LINK = '/recordings/'       #  Prefix to repository objects 

def recordings(get, post, session, record=''):
#============================================
  prefix = namespaces['repo'][:-1]
  if record:
    recuri = '%s/%s' % (prefix, record)
    baserec = bsml.signal.recording(recuri)
    if baserec:
      sig = recuri
      recuri = str(baserec)
    else:
      sig = None
    return BlankPage(recuri,
                      xmltree(repository.model.recordings(), prefix, REPO_LINK, record)
                    + build_metadata(recuri)
                    + signal_details(recuri, sig)
                     ).show(get, post, session)
  else:
    return BlankPage('Recordings in "repo:" (%s)' % prefix,
                      xmltree(repository.model.recordings(), prefix, REPO_LINK)
                     ).show(get, post, session)


############

from repository.fulltext import BOLD_ON, BOLD_OFF


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


def search(get, post, session, param=''):
#========================================
  logging.debug('POST: %s', post)

  searchtext = post.get('text', '')
  if searchtext:
    xml = [ '<table class="search">' ]
    odd = True
    for r in repository.fulltext.search(post['text']):
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
  # Advanced will have other post fields...
  ## Also check action = Search v's Advanced..
  # else:
  return BlankPage('Text search...',
    ## Add search box here.... (as a form, action=/search?, and advanced button/link??)
                   """<form action="/search" height="1">
                       <button name="action" prompt="Search" row="1" col="42"/>
                       <field name="text" prompt="Find Text" row="1" pcol="1"
                         fcol="10" size="20" value="%s"/>
                      </form>
                    %s
                    """ % (xmlescape(searchtext), ''.join(xml))
                     ).show(get, post, session)



def sparql(get, post, session, param=''):
#========================================
  logging.debug('POST: %s', post)

  query = post.get('query', '')
  if query:
    results = sparql_search(query) ## , namespaces)
    table = results[1] if results[0] else ''
  else:
    table = ''
    p = [ ]
    for ns, prefix in namespaces.iteritems():
      p.append('PREFIX %s: <%s>' % (ns, prefix))
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
                     ).show(get, post, session)

