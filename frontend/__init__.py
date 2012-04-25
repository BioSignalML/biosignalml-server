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
    level = self.get_secure_cookie('userlevel')
    if level is not None:
      self.set_secure_cookie('userlevel', level, **{'max-age': str(SESSION_TIMEOUT)})
      try: return int(level)
      except TypeError: pass
    return 0

  def userlevel(self):
    if not hasattr(self, "_user_level"):
      self._user_level = self.get_current_user()
    return self._user_level
