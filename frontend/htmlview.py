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
import biosignalml.model as model
from biosignalml import BSML, Annotation, Event
from biosignalml.utils import trimdecimal, chop, xmlescape
from biosignalml.utils import maketime, datetime_to_isoformat

from forms import Button, Field
import frontend
import mktree
import menu
import user


PREFIXES = { 'bsml':     BSML.URI,
             'pbterms': 'http://www.biosignalml.org/ontologies/examples/physiobank#',
           }
PREFIXES.update(rdf.NAMESPACES)



def abbreviate(u):
#-----------------
  s = str(u) if u else ''
  for p, n in PREFIXES.iteritems():
    if s.startswith(n): return ''.join([p, ':', s[len(n):]])
  return s


class Properties(object):
#========================

  def __init__(self, properties):
  #------------------------------
    self._properties = properties

  def header(self, all=False):
  #---------------------------
    if all:
      return [ (p[0] if p[0][0] != '*' else p[0][1:]) for p in self._properties ]
    else:
      return [ p[0] for p in self._properties if p[0][0] != '*']

  def details(self, object, all=False, **kwds):
  #--------------------------------------------
    r = [ ]
    for p in [ p for p in self._properties if (all or p[0][0] != '*')]:
      prop = p[1]
      v = getattr(object, prop, None)
      if v is None:
        meta = getattr(object, 'metadata', None)
        if meta: v = meta.get(prop)
      args = p[3] if (len(p) > 3) else []
      r.append('' if v is None
          else (p[2](v, **{ k: v for k, v in kwds.iteritems() if k in args })) if (len(p) > 2)
          else [ str(s) for s in v ] if hasattr(v, '__iter__')
          else unicode(v)
          )
    return r


provenance_properties = Properties([
                         ('Imported', 'completed', datetime_to_isoformat),
                         ('Importer', 'performedby'),
                       ])


def property_details(object, properties, graph, provenance=False, **args):
#-------------------------------------------------------------------------
  r = [ ]
  def _append_details(prompts, details):
    for n, d in enumerate(details):
      if d:
        t = ', '.join(d) if isinstance(d, list) else str(d)
        r.append('<span class="emphasised">%s: </span><span class="details">%s</span>'
                                   % (prompts[n], xmlescape(t).replace('\n', '<br/>')))
  _append_details(properties.header(), properties.details(object, **args))
  if provenance:
    prov = options.repository.get_provenance(graph)
    if prov is not None:
      _append_details(provenance_properties.header(), provenance_properties.details(prov.createdby))
#  logging.debug('PROV: %s by %s, prec %s, next %s', provenance.createdby.completed,
#    provenance.createdby.performedby, provenance.precededby, provenance.followedby)
  return '<p>' + '</p><p>'.join(r) + '</p>'


def annotatelink(uri):
#---------------------
  return '<a href="%s?annotations">Add Annotation</a>' % uri


def link(uri, trimlen=0, makelink=True):
#---------------------------------------
  text = chop(uri, trimlen)
  if makelink:
    return '<a href="%s">%s</a>' % (uri, text)
  else:
    return text


def time_display(t):
#-------------------
  d = ['%gs' % t.start]
  if t.duration: d.append('to %gs' % t.end)
  return ' '.join(d)


signal_properties = Properties([
                      ('Id',    'uri',   link, ['trimlen', 'makelink']),
                      ('Name',  'label'),
                      ('Units', 'units', abbreviate),
                      ('Rate',  'rate',  trimdecimal),
##                      ('*Annotations', 'uri', annotatelink),
                      ('*RDF',  'uri',   frontend.make_link, ['graph']),
                    ])

recording_properties = Properties([
                         ('Description', 'description'),
                         ('Created',     'starttime'),
                         ('Creator',     'creator'),
                         ('Duration',    'duration', maketime),
                         ('Format',      'format', abbreviate),
                         ('Study',       'investigation'),
                         ('Comments',    'comment'),
                         ('Source',      'source'),
                         ('Submitted',   'dateSubmitted', datetime_to_isoformat),
                       ])

event_properties = Properties([
                          ('Recording', 'recording'),
                          ('Type',      'eventtype'),
                          ('Time',      'time', time_display),
                        ])

annotation_properties = Properties([
                          ('About',      'about'),
                          ('Time',       'time', time_display),
                          ('Annotation', 'comment'),
                          ('Author',     'creator'),
                          ('Created',    'created', datetime_to_isoformat),
                        ])


def recording_info(rec):
#-----------------------
  html = [ '<div id="recording" class="treespace">' ]
  html.append('<div class="block">')
  html.append(frontend.make_link(rec.uri, rec.graph.uri))
##  html.append(annotatelink(rec.uri))
  html.append('</div>')
  html.append(property_details(rec, recording_properties, rec.graph.uri, provenance=True))
  html.append('</div>')
  return ''.join(html)


def event_info(evt):
#------------------
  props = Properties([('Time:',  'time', time_display),
                      ('Event:', 'tags', lambda t: abbreviate(t[0]) if t else ''),
                      ('Event:', 'comment')])
  h = [ ]
  prompts = props.header()
  h.append('<div>')
  for n, d in enumerate(props.details(evt)):
    if d:
      t = '<br/>'.join(list(d)) if hasattr(d, '__iter__') else str(d)
      p = '<span class="prompt">%s </span>%s' % (prompts[n], xmlescape(t).replace('\n', '<br/>'))
      if n == 0: h.append('<div class="rside">%s</div>' % p)
      else: h.append('<div>%s</div>' % p)
  h.append('</div>')
  return ''.join(h)


def annotation_info(ann):
#------------------------
  if getattr(ann, 'time') is not None: return event_info(ann)

  props = Properties([('Annotation', 'comment'),
                      ('Author',     'creator'),
                      ('Created',    'created', datetime_to_isoformat)])
  h = [ ]
  prompts = props.header()
  for n, d in enumerate(props.details(ann)):
    if d is None: d = ''
    t = '<br/>'.join(list(d)) if hasattr(d, '__iter__') else str(d)
    p = '<span class="prompt">%s: </span><pre>%s</pre>' % (prompts[n], xmlescape(t))
    if   n == 0: h.append('<p>%s</p>' % p)
    elif n == 1 and d: h.append('<div><div class="half">%s</div>' % p)
    elif n == 2 and (len(h) > 1 or d):
      if len(h) == 1: h.append('<div><div class="half"></div>')
      h.append('<span>%s</span></div>' % p)
  return ''.join(h)


def signal_table(handler, recording, selected=None):
#---------------------------------------------------
  lenhdr = len(str(recording.uri)) + 1
  # Above is for abbreviating signal id;
  # should we check str(sig.uri).startswith(str(rec.uri)) ??
  rows = [ ]
  selectedrow = -1
  for n, sig in enumerate(recording.signals()):
    if str(sig.uri) == selected: selectedrow = n
    rows.append(signal_properties.details(sig, True, trimlen=lenhdr, graph=recording.graph.uri))
  return handler.render_string('table.html',
    header = signal_properties.header(True),
    rows = rows,
    selected = selectedrow,
    treespace = True,
    tableclass = 'signal')


def build_metadata(uri):
#-----------------------
  #logging.debug('Get metadata for: %s', uri)
  html = [ '<div class="metadata">' ]
  if uri:
    uri = uri.rsplit('#')[0]
    repo = options.repository
    graph_uri = repo.get_graph_and_recording_uri(uri)[0]
    objtypes = repo.get_types(uri, graph_uri)
    if   BSML.Recording in objtypes:    # repo.has_recording(uri)
      rec = repo.get_recording(uri, with_signals=False, open_dataset=False, graph_uri=graph_uri)
      ## What about a local cache of opened recordings?? (keyed by uri)
      ## in bsml.recordings module ?? in repo ??
      html.append(property_details(rec, recording_properties, graph_uri, provenance=True))
      # And append info from repo.provenance graph...
    elif BSML.Signal in objtypes:       # repo.has_signal(uri)
      sig = repo.get_signal(uri, graph_uri)
      html.append(property_details(sig, signal_properties, graph_uri, makelink=False))
#    elif BSML.Event in objtypes:
#      html.append('event type, time, etc')
    elif (rdf.TL.RelativeInstant in objtypes
       or rdf.TL.RelativeInterval in objtypes):
      html.append('time, etc')
    elif BSML.Annotation in objtypes:
      ann = repo.get_annotation(uri, graph_uri)
      #html.append(annotation_info(ann))
      html.append(property_details(ann, annotation_properties, graph_uri))
    elif BSML.Event in objtypes:
      evt = repo.get_event(uri, graph_uri)
      html.append(property_details(evt, event_properties, graph_uri, makelink=False))
    else:
      html.append('<br/>'.join([str(o) for o in objtypes]))
  html.append('</div>')
  return ''.join(html)


class Metadata(tornado.web.RequestHandler):  # Tool-tip popup
#==========================================

  def post(self):
  #--------------
    self.write({ 'html': build_metadata(self.get_argument('uri', '')) })


class Repository(frontend.BasePage):
#===================================

  def _xmltree(self, uris, select=''):
  #-----------------------------------
    tree = mktree.maketree(uris)
    #logging.debug('tree: %s', tree)
    selectpath = select.rsplit('/', select.count('/') - 2)
    #logging.debug('SP: %s, %s', select, selectpath)
    return self.render_string('ttree.html',
                               tree=tree,
                               selectpath=selectpath)

  def _show_contents(self, name, annotate):
  #----------------------------------------
    repo = options.repository
    if name:
      uri = name
      recording = repo.get_recording(uri, open_dataset=False)
      if recording is None:        ## Not part of a recording, so return RDF
        self.set_header('Content-Type', rdf.Format.RDFXML)
        self.write(repo.describe(uri, format=rdf.Format.RDFXML))
        return
      selectedsig = None
      if str(recording.uri) != uri:
        if repo.has_signal(uri): selectedsig = uri
        uri = str(recording.uri)

      # By now we should have all of recording's RDF as a Graph so we
      # can use this to get events, annotations, etc, etc

 ## Is sending tree each time, that then has JScript setting up tooltips
 ## a cause of connection closed problems...???

####      print recording.graph.serialise(format=rdf.Format.TURTLE, base=recording.uri, prefixes=PREFIXES)

      kwds = dict(bodytitle = uri, style = 'signal',
                  tree = self._xmltree(repo.recording_uris(), name),
                  content = recording_info(recording)
                          + signal_table(self, recording, selectedsig) )
      target = selectedsig if selectedsig else uri

      annotations = [ annotation_info(repo.get_annotation(ann, recording.graph.uri))
                       for ann in repo.annotations(target, recording.graph.uri) ]
      if not annotate: annotations.append(annotatelink(target))
      kwds['content'] += self.render_string('annotate.html', uri=target, annotations=annotations)
      if annotate:
        self.render('tform.html',
          bottom = True,    # Form below other content
          treespace = True,
          formclass = 'annotform',
          rows = 6,  cols = 0,
          buttons = [ Button('Annotate', 1, 4), Button('Cancel', 1, 5) ],
          fields = [ Field.textarea('Add Annotation', 'annotation', 60, 8),
                     Field.hidden('target', target ) ],
          **kwds)
      else: self.render('tpage.html', **kwds)
    else:
      self.render('tpage.html',
        title = 'Recordings in repository:',
        tree = self._xmltree(repo.recording_uris()))

##  @tornado.web.authenticated
  def get(self):
  #-------------
    name = self.full_uri
    #logging.debug('HTML GET: %s from %s', name, self.request.path)
    self._show_contents(name, 'annotations' in self.request.query)

##  @tornado.web.authenticated
  def post(self):
  #--------------
    name = self.full_uri
    text = self.get_argument('annotation', '').strip()
    if self.get_argument('action') == 'Annotate' and text:
      repo = options.repository
      target = self.get_argument('target')
      recording = repo.get_recording(target, with_signals=False, open_dataset=False)
      ann = Annotation.Note(recording.make_uri(prefix='annotation'), target, text,
                            creator='%s/user/%s' % (repo.uri, self.current_user)
                              if self.current_user is not None else None)
      repo.extend_graph(recording.graph.uri, ann.metadata_as_string())
    self._show_contents(name, False)
