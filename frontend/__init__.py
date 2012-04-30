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

import tornado.web

REPOSITORY = '/repository/'       #  Prefix to repository objects 
SESSION_TIMEOUT = 1800 # seconds  ## num(config.config['idletime'])


class SubTree(tornado.web.UIModule):
#===================================
  @staticmethod
  def treeaction(text, action='', uri=''):
    return(('<a href="%s" class="cluetip" uri="%s">%s</a>'
                 % (action,                   uri, text)) if action
      else ('<span>%s</span>' % text))

  @staticmethod
  def subtree(tree, prefix, depth, selected):
    html = [ '<ul>\n' ]
    last = len(tree) - 1
    for t in tree:
      html.append('<li')
      if isinstance(t[0], tuple):
        details = t[0]
        if depth < len(selected) and details[0] == selected[depth]:
          html.append(' class="selected"')
        html.append(' id="%s"' % details[1])
        html.append('>')
        html.append(SubTree.treeaction(details[0],
          prefix + details[1].replace(':', '%3A'), details[2].uri))
      else:
        if depth < len(selected) and t[0] == selected[depth]:
          html.append(' class="jstree-open"')
        html.append('>')
        html.append(SubTree.treeaction(t[0]))
        html.append(SubTree.subtree(t[1], prefix, depth+1, selected))
      html.append('</li>\n')
    html.append('</ul>')
    return ''.join(html)

  def render(self, tree=[], prefix='', depth=0, selected=[]):
    return self.subtree(tree, prefix, depth, selected)


class MenuModule(tornado.web.UIModule):
#======================================
  def render(self, level=0):
    out = [ '<div id="menubar"><ul class="jd_menu">' ]
    for item in menu.getmenu(level): out.append(self.menu_entry(item))
    out.append('</ul></div>')
    return ''.join(out)

  def menu_entry(self, item):
    out = [ '<li>' ]
    if item[1]:
      out.append('<a href="%s" title="%s" onClick="return oktoexit(this)">%s</a>' % (item[1], item[0], item[0]))
    elif item[0]:
      out.append('<span class="menu">%s</span>' % item[0])
    if len(item) > 2: out.append(sub_menu(item[2]))
    out.append('</li>')
    return ''.join(out)

  def sub_menu(self, menu):
    out = [ '<ul class="sub_menu">' ]
    for item in menu: out.append(self.menu_entry(item))
    out.append('</ul>')
    return ''.join(out)


class BasePage(tornado.web.RequestHandler):
#==========================================
  def render(self, template, **kwds):
    kwargs = { 'title': '', 'content': '',
               'stylesheets': [ ], 'scripts': [ ],
               'refresh': 0, 'alert': '', 'message': '',
               'keypress': None, 'level': self.userlevel(),
             }
    kwargs.update(kwds)
    return tornado.web.RequestHandler.render(self, template, **kwargs)

  def get_current_user(self):
    name = self.get_secure_cookie('username')
    if name is not None:
      self.set_secure_cookie('username', name, **{'max-age': str(SESSION_TIMEOUT)})
    return name

  def userlevel(self):
    import user
    if not hasattr(self, "_user_level"):
      self._user_level = user.level(self.current_user)
    return self._user_level
