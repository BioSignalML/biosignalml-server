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

import biosignalml.rdf
from biosignalml.model import BSML
from biosignalml.utils import maketime, trimdecimal, chop

import frontend
import mktree
import menu


PREFIXES = { 'bsml':  BSML.URI }
PREFIXES.update(biosignalml.rdf.NAMESPACES)

def abbreviate(u):
  s = str(u) if u else ''
  for p, n in PREFIXES.iteritems():
    if s.startswith(n): return ''.join([p, ':', s[len(n):]])
  return s


class Properties(object):
#========================
  def __init__(self, properties):
    self._properties = properties

  def header(self):
    return [ p[0] for p in self._properties ]

  def details(self, object, **args):
    r = [ ]
    for p in self._properties:
      prop = p[1]
      v = getattr(object, prop, None)
      if v is None:
        meta = getattr(object, 'metadata', None)
        if meta: v = meta.get(prop)
      r.append('' if v is None
          else (p[2](v, *[ args[a] for a in p[3] ] if (len(p) > 3) else [ ]))
            if (len(p) > 2)
          else [ str(s) for s in v ]
            if isinstance(v, list)
          else unicode(v)
          )
    return r

def property_details(object, properties, **args):
  r = [ ]
  prompts = properties.header()
  for n, d in enumerate(properties.details(object, **args)):
    if d:
      t = '<br/>'.join(d) if isinstance(d, list) else d
      r.append((prompts[n] + ': ' + t) if prompts[n] else t)
  return '<p>' + '</P><p>'.join(r) + '</p>'


signal_properties = Properties([
                      ('Id',    'uri',   chop, ['n']),
                      ('Name',  'label'),
                      ('Units', 'units', abbreviate),
                      ('Rate',  'rate',  trimdecimal),
                    ])

def signal_table(handler, recording, selected=None):
  lenhdr = len(str(recording.uri)) + 1
  # Above is for abbreviating signal id;
  # should we check str(sig.uri).startswith(str(rec.uri)) ??
  rows = [ ]
  selectedrow = -1
  for n, sig in enumerate(recording.signals()):
    if str(sig.uri) == selected: selectedrow = n
    rows.append(signal_properties.details(sig, n=lenhdr))
  return handler.render_string('table.html',
    header = signal_properties.header(),
    rows = rows,
    selected = selectedrow,
    tableclass = 'signal')


recording_properties = Properties([
                         ('Desc',      'description'),
                         ('Created',   'starttime'),
                         ('Duration',  'duration', maketime),
                         ('Format',    'format', abbreviate),
                         ('Study',     'investigation'),
                         ('Comments',  'comment'),
                         ('Source',    'source'),
                         ('Submitted', 'dateSubmitted', lambda d: str(d) + ' UTC'),
                       ])

def build_metadata(uri):
  #logging.debug('Get metadata for: %s', uri)
  html = [ '<div class="metadata">' ]
  if uri:
    repo = options.repository
    objtype = repo.get_type(uri)
    if   objtype == BSML.Recording:    # repo.has_recording(uri)
      rec = repo.get_recording(uri)
      ## What about a local cache of opened recordings?? (keyed by uri)
      ## in bsml.recordings module ?? in repo ??
      html.append(property_details(rec, recording_properties))
      # And append info from repo.provenance graph...
    elif objtype == BSML.Signal:       # repo.has_signal(uri)
      sig = repo.get_signal(uri)
      html.append(property_details(sig, signal_properties, n=0))
    elif objtype == BSML.Event:
      html.append('event comment, time, etc')
    elif objtype == BSML.Annotation:
      html.append('annotation comment, time, etc')
  html.append('</div>')
  return ''.join(html)


class Metadata(tornado.web.RequestHandler):  # Tool-tip popup
#==========================================
  def post(self):
    self.write({ 'html': build_metadata(self.get_argument('uri', '')) })


class Repository(frontend.BasePage):
#===================================

  def xmltree(self, nodes, base, prefix, select=''):
    tree = mktree.maketree(nodes, base)
    #logging.debug('tree: %s', tree)
    if select.startswith('http://') or select.startswith('file://'):
      selectpath = select.rsplit('/', select.count('/') - 2)
    else:
      selectpath = select.split('/')
    return self.render_string('ttree.html',
                               tree=tree, prefix=prefix,
                               selectpath=selectpath)

  @tornado.web.authenticated
  def get(self, name=''):
    #logging.debug('GET: %s (%s)', name, self.get_current_user())
    repo = options.repository
    prefix = repo.uri + '/recording'  ## MUST match path of ReST recording server ####
    if name:
      recuri = (name if name.startswith('http://') or name.startswith('file://')
               else '%s/%s' % (prefix, name))
      logging.debug('RECORDING: %s', recuri)
      recording = repo.get_recording_with_signals(recuri)
      if recording is None:
        self.send_error(404) # 'Unknown recording...')
        return
      if str(recording.uri) != recuri:
        selectedsig = recuri
        recuri = str(recording.uri)
      else:
        selectedsig = None
      self.render('tpage.html',
        title = recuri,
        tree = self.xmltree(repo.recordings(), prefix, frontend.REPOSITORY, name),
        style = 'signal',
        content = build_metadata(recuri) + signal_table(self, recording, selectedsig)
        )
    else:
      self.render('tpage.html',
        title = 'Recordings in repository:',
        tree = self.xmltree(repo.recordings(), prefix, frontend.REPOSITORY))
