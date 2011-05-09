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

from utils import xmlescape, maketime, trimdecimal, chop
import templates

import repository as repo
import mktree
import sparql
import user

#########
import metadata as meta
from rdfmodel import Uri
from bsml import BSML
#########

_tree_template = templates.Tree()

def xmltree(nodes, base, prefix, selected=''):
#============================================
  logging.debug('Selected: %s', selected)
  tree = mktree.maketree(nodes, base)
  return _tree_template.htmltree(tree, prefix, selected)


def table_header(properties):
#===========================
  return '<th>' + '</th><th>'.join([ p[0] for p in properties ]) + '</th>'
  

def property_details(obj, properties, table, **args):
#===================================================
  opn = '<td>'  if table else '<p>'
  cls = '</td>' if table else '</p>'
  r = [ ]
  for prm, prop, fn in properties:
    v = getattr(obj, prop, None)
    if v is None:
      meta = getattr(obj, 'metadata', None)
      if meta: v = meta.get(prop)
    if v is None: r.append('')
    else:
      if fn:                    t = fn[0](v, *[ args[a] for a in fn[1] ] if fn[1] else [ ])
      elif isinstance(v, list): t = '<br/>'.join([ xmlescape(str(s)) for s in v ])
      else:                     t = xmlescape(unicode(v))
      if table: r.append(t)
      elif v:   r.append(prm + ': ' + t) if prm else r.append(t)
  return opn + (cls + opn).join(r) + cls



############## Above should be in separate module ###############




# Generate list of signals in a recording (as a <table>)

signal_metadata = [ ('Id',    'uri',   (chop, ['n'])),
                    ('Name',  'label', None),
                    ('Units', 'units', None),
                    ('Rate',  'rate',  (trimdecimal, None)),
                  ]

def signal_details(recuri, signal=None):
#======================================
  lenhdr = len(recuri) + 1
  recording = repo.get_recording_signals(recuri)
  html = [ '<table class="signal">' ]
  odd = True
  html.append('<tr>%s</tr>' % table_header(signal_metadata))
  for sig in recording.signals():
    html.append('<tr class="selected">' if str(sig.uri) == signal
          else '<tr class="odd">'      if odd
          else '<tr>')
    html.append(property_details(sig, signal_metadata, True, n=lenhdr))
    html.append('</tr>')
    odd = not odd
  html.append('</table>')
  return ''.join(html)



def event_details(recuri, signal=None):
#======================================
  lenhdr = len(recuri) + 1
  recording = repo.get_recording(recuri)
  html = [ '<table>' ]
  html.append('</table>')
  return ''.join(html)



recording_metadata = [ ('Desc',      'description',     None),
                       ('Created',   'recording_start', None),
                       ('Duration',  'recording_duration', (maketime, None)),
                       ('Format',    'format',          None),
                       ('Study',     'investigation',   None),
                       ('Comments',  'comment',         None),
                       ('Source',    'source',          None),
                       ('Submitted', 'dateSubmitted',   (lambda d: str(d) + ' UTC', None)),
                     ]


def build_metadata(uri):
#======================
  logging.debug('Get metadata for: %s', uri)
  html = [ '<div class="metadata">' ]
  if uri:
    source = Uri(uri)
    objtype = repo.triplestore.get_target(source, meta.rdf.type)
    if   objtype == BSML.Recording:
      rec = repo.get_recording(source)
      ## What about a local cache of opened recordings?? (keyed by uri)
      ## in bsml.recordings module ?? in repo ??
      html.append(property_details(rec, recording_metadata, False))
    elif objtype == BSML.Signal:
      sig = repo.get_signal(source)
      html.append(property_details(sig, signal_metadata, False, n=0))
    elif objtype == BSML.Annotation:
      html.append('annotation comment, time, etc')
  html.append('</div>')
  return ''.join(html)


# Tooltip pop-up:

def metadata(data, session, params):
#===================================
  return { 'html': build_metadata(data.get('uri', '')) }


# Generate tree of recordings along with details of signals when recording clicked on.

_page_template = templates.Page()

REPOSITORY = '/repository/'       #  Prefix to repository objects 

def repository(data, session, record=''):
#=======================================
  prefix = repo.base[:-1]
  if record:
    recuri = '%s/%s' % (prefix, record)
    baserec = repo.signal_recording(recuri)
    if baserec:
      sig = recuri
      recuri = str(baserec)
    else:
      sig = None

    return _page_template.page(title   = recuri,
                               content = xmltree(repo.recordings(), prefix, REPOSITORY, record)
                                       + build_metadata(recuri)
                                       + signal_details(recuri, sig)
                              )

#    return BlankPage(recuri,
#                      xmltree(repo.recordings(), prefix, REPOSITORY, record)
#                    + build_metadata(recuri)
#                    + signal_details(recuri, sig)
#                     ).show(data, session)
  else:
    return _page_template.page(title   = 'Recordings in repo: %s' % prefix,
                               content = xmltree(repo.recordings(), prefix, REPOSITORY),
                              )

def index(data, session, params):
#===============================
  if user.loggedin():
    return repository(data, session, params)
  else:
    return user.login(data, session, params)
