######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $ID: e3e37fb on Thu Feb 9 14:13:46 2012 +1300 by Dave Brooks $
#
######################################################

import logging
import urllib.parse as urlparse

import tornado.web

from biosignalml import BSML
import biosignalml.rdf as rdf

import frontend.menu as menu


RDF_ENDPOINT    = '/frontend/rdf/'
SNORQL_ENDPOINT = '/frontend/snorql/'

SESSION_TIMEOUT = 86400 ### 1800 # seconds  ## num(config.config['idletime'])


NAMESPACES = {
  'bsml':  str(BSML.BASE),
  'unit':  "http://www.biosignalml.org/ontologies/examples/unit#",
  'sleep': "http://www.biosignalml.org/ontologies/examples/sleep#",
  'pbank': "http://www.biosignalml.org/ontologies/examples/physiobank#",
  }

NAMESPACES.update(rdf.NAMESPACES)


# Provide useful utility functions
def rdf_link(uri):
#=================
  return '<a href="%s%s">RDF</a>' % (RDF_ENDPOINT, uri)

def snorql_link(uri, graph=None):
#================================
  if uri in ['', None]: return ''
  if graph is not None: g = '&graph=' + urlparse.quote_plus(str(graph))
  else:                 g = ''
  return ('<a href="%s?describe=%s%s" target="_blank">SNORQL</a>'
         % (SNORQL_ENDPOINT, urlparse.quote_plus(str(uri)), g) )

def make_link(uri, graph=None):
#==============================
  if uri in ['', None]: return ''
  if graph is not None: g = '&graph=' + urlparse.quote_plus(str(graph))
  else:                 g = ''
  return rdf_link(uri) + ' ' + snorql_link(uri, graph)


class SubTree(tornado.web.UIModule):
#===================================

  @staticmethod
  def treeaction(text, uri=''):
  #----------------------------
    return(('<a href="%s" class="cluetip">%s</a>'
                 % (uri,                 text)) if uri
      else ('<span>%s</span>' % text))

  @staticmethod
  def subtree(tree, depth, selected):
  #----------------------------------
    html = [ '<ul>\n' ]
    last = len(tree) - 1
    for t in tree:
      html.append('<li')
      if isinstance(t[0], tuple):
        details = t[0]
        if depth < len(selected) and details[0] == selected[depth]:
          html.append(' class="selected"')
        html.append('>')
        html.append(SubTree.treeaction(details[0], details[1]))
      else:
        if depth < len(selected) and t[0] == selected[depth]:
          html.append(' class="jstree-open"')
        html.append('>')
        html.append(SubTree.treeaction(t[0]))
        html.append(SubTree.subtree(t[1], depth+1, selected))
      html.append('</li>\n')
    html.append('</ul>')
    return ''.join(html)

  def render(self, tree=[], depth=0, selected=[]):
  #-----------------------------------------------
    return self.subtree(tree, depth, selected)


class MenuModule(tornado.web.UIModule):
#======================================

  def render(self, level=0):
  #-------------------------
    out = [ '<div id="menubar"><ul class="jd_menu">' ]
    for item in menu.getmenu(level): out.append(self.menu_entry(item))
    out.append('</ul></div>')
    return ''.join(out)

  def menu_entry(self, item):
  #--------------------------
    out = [ '<li>' ]
    if item[1]:
      out.append('<a href="%s" title="%s" onClick="return oktoexit(this)">%s</a>' % (item[1], item[0], item[0]))
    elif item[0]:
      out.append('<span class="menu">%s</span>' % item[0])
    if len(item) > 2: out.append(sub_menu(item[2]))
    out.append('</li>')
    return ''.join(out)

  def sub_menu(self, menu):
  #------------------------
    out = [ '<ul class="sub_menu">' ]
    for item in menu: out.append(self.menu_entry(item))
    out.append('</ul>')
    return ''.join(out)


class BasePage(tornado.web.RequestHandler):
#==========================================

  def render(self, template, **kwds):
  #----------------------------------
    kwargs = { 'title': '', 'bodytitle': '', 'content': '',
               'stylesheets': [ ], 'scripts': [ ],
               'refresh': 0, 'alert': '', 'message': '',
               'keypress': None, 'level': self.userlevel(),
             }
    kwargs.update(kwds)
    return tornado.web.RequestHandler.render(self, template, **kwargs)

  def get_current_user(self):
  #--------------------------
    name = self.get_secure_cookie('username')
    if name is not None:
      self.set_secure_cookie('username', name, **{'max-age': str(SESSION_TIMEOUT)})
    return name

  def userlevel(self):
  #-------------------
    import frontend.user as user
    if not hasattr(self, "_user_level"):
      self._user_level = user.level(self.current_user)
    return self._user_level


class Snorql(tornado.web.StaticFileHandler):
#===========================================

  def check_xsrf_cookie(self):
  #---------------------------
    """Don't check XSRF token for POSTs."""
    pass

  def parse_url_path(self, url_path):
  #----------------------------------
    return url_path if url_path else 'index.html'
