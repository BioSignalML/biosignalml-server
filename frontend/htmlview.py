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
import web

from biosignalml.utils import xmlescape, maketime, trimdecimal, chop

import templates
import mktree
import user

#########
from biosignalml.rdf import Uri
from biosignalml.model import BSML
#########

_tree_template = templates.Tree()

def xmltree(nodes, base, prefix, select=''):
#===========================================
  #logging.debug('Selected: %s', select)
  tree = mktree.maketree(nodes, base)
  if select.startswith('http://') or select.startswith('file://'):
    selectpath = select.rsplit('/', select.count('/') - 2)
  else:
    selectpath = select.split('/')
  return _tree_template.htmltree(tree, prefix, selectpath)


def table_header(properties):
#===========================
  return '<th>' + '</th><th>'.join([ p[0] for p in properties ]) + '</th>'
  

def property_details(obj, properties, table, **args):
#===================================================
  opn = '<td>'  if table else '<p>'
  cls = '</td>' if table else '</p>'
  r = [ ]
  for p in properties:
    prm, prop = p[0:2]
    v = getattr(obj, prop, None)
    if v is None:
      meta = getattr(obj, 'metadata', None)
      if meta: v = meta.get(prop)
    if v is None: r.append('')
    else:
      if len(p) > 2:            t = p[2](v, *[ args[a] for a in p[3] ] if (len(p) > 3) else [ ])
      elif isinstance(v, list): t = '<br/>'.join([ xmlescape(str(s)) for s in v ])
      else:                     t = xmlescape(unicode(v))
      if table: r.append(t)
      elif v:   r.append(prm + ': ' + t) if prm else r.append(t)
  return opn + (cls + opn).join(r) + cls


BSML_NAMESPACE = 'http://www.biosignalml.org/ontologies/2011/04/biosignalml#'


PREFIXES = { 'rdf':  'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
             'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
             'xsd':  'http://www.w3.org/2001/XMLSchema#',
             'owl':  'http://www.w3.org/2002/07/owl#',
             'dc':   'http://purl.org/dc/elements/1.1/',
             'dcterms': 'http://purl.org/dc/terms/',
             'time': 'http://www.w3.org/2006/time#',
             'bsml':  BSML_NAMESPACE,
           }


def abbreviate(u):
#-----------------
  s = str(u) if u else ''
  for p, n in PREFIXES.iteritems():
    if s.startswith(n): return ''.join([p, ':', s[len(n):]])
  return s


############## Above should be in separate module ###############




# Generate list of signals in a recording (as a <table>)

signal_metadata = [ ('Id',    'uri',   chop, ['n']),
                    ('Name',  'label'),
                    ('Units', 'units', abbreviate),
                    ('Rate',  'rate',  trimdecimal),
                  ]

def signal_details(recording, selected=None):
#============================================
  lenhdr = len(str(recording.uri)) + 1
  # Above is for abbreviating signal id; should we check str(sig.uri).startswith(str(rec.uri)) ??
  html = [ '<table class="signal">' ]
  html.append('<tr>%s</tr>' % table_header(signal_metadata))
  odd = True
  for sig in recording.signals():
    html.append('<tr class="selected">' if str(sig.uri) == selected
          else '<tr class="odd">'       if odd
          else '<tr>')
    html.append(property_details(sig, signal_metadata, True, n=lenhdr))
    html.append('</tr>')
    odd = not odd
  html.append('</table>')
  return ''.join(html)



def event_details(recuri, signal=None):
#======================================
  lenhdr = len(recuri) + 1
  recording = web.config.biosignalml['repository'].get_recording(recuri)
  html = [ '<table>' ]
  html.append('</table>')
  return ''.join(html)



recording_metadata = [ ('Desc',      'description'),
                       ('Created',   'starttime'),
                       ('Duration',  'duration', maketime),
                       ('Format',    'format', abbreviate),
                       ('Study',     'investigation'),
                       ('Comments',  'comment'),
                       ('Source',    'source'),
                       ('Submitted', 'dateSubmitted', lambda d: str(d) + ' UTC'),
                     ]


def build_metadata(uri):
#======================
  #logging.debug('Get metadata for: %s', uri)
  html = [ '<div class="metadata">' ]
  if uri:
    source = Uri(uri)
    repo = web.config.biosignalml['repository']
    objtype = repo.get_type(source)
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
#========================================
  #logging.debug('SES: %s', session)
  repo = web.config.biosignalml['repository']
  prefix = repo.base + 'recording'     ## MUST match path of ReST recording server ####
  if record:
    recuri = (record if record.startswith('http://') or record.startswith('file://')
             else '%s/%s' % (prefix, record))
    ##logging.debug('RECORDING: %s', recuri)
    recording = repo.get_recording_with_signals(recuri)
    if recording is None: raise web.NotFound('Unknown recording...')
    if str(recording.uri) != recuri:
      selectedsig = recuri
      recuri = str(recording.uri)
    else:
      selectedsig = None

    return _page_template.page(title   = recuri,
                               content = "<span>"
                                       + xmltree(repo.recordings(), prefix, REPOSITORY, record)
                                       + "<div class='signal'>"
                                       + build_metadata(recuri)
                                       + signal_details(recording, selectedsig)
                                       + "</div></span>",
                               session = session,
                              )

#    return BlankPage(recuri,
#                      xmltree(repo.recordings(), prefix, REPOSITORY, record)
#                    + build_metadata(recuri)
#                    + signal_details(recuri, sig)
#                     ).show(data, session)
  else:
    return _page_template.page(title   = 'Recordings in repo: %s' % prefix,
                               content = xmltree(repo.recordings(), prefix, REPOSITORY),
                               session = session,
                              )


def recording_html(recuri):
#==========================
  return _page_template.page(title   = recuri,
                             content = build_metadata(recuri)
                                     + signal_details(recuri, None),
                            )


def index(data, session, params):
#===============================
  if user.loggedin(session):
    return repository(data, session, params)
  else:
    return user.login(data, session, params)
