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
import tornado.web

from webdb import Database
from forms import Button, Field
import htmlview

VIEWER        = 1
UPDATER       = 5
ADMINISTRATOR = 9

def level():
#===========
  return int(web.cookies().get('userlevel', 0))

def loggedin():
#==============
  return level() > 0

def _check(name, passwd):
#========================
  level = 0
  db = Database()
  row = db.findrow('users', {'username': name, 'password': passwd })
  if row:
    try:
      level = int(db.readrow('users', 'level', where='rowid=%d' % row)['level'])
      ## logging.debug("User level: %d", level)
    except Exception:
      raise
      pass
  return level

class Logout(htmlview.BasePage):
#===============================
  def get(self):
    self.clear_cookie('userlevel')
    self.redirect('/login')

class Login(htmlview.BasePage):
#==============================
  def get(self):
    self.render('tform.html',
                title = 'Please log in:',
                rows = 4,  cols = 0,
                buttons = [ Button('Login', 35, 1), Button('Cancel', 42, 1) ],
                fields  = [ Field('Username', (1, 1), 'username', (11, 1), 20),
                            Field('Password', (1, 2), 'password', (11, 2), 20, type='password'),
                            Field.hidden('next', self.get_argument('next', '')) ],
                alert = ('Session expired, please login' if self.request.query.find('expired') >= 0
                    else 'Unauthorised, please login'    if self.request.query.find('unauthorised') >= 0
                    else ''),
                )

  def post(self):
    import frontend
    btn = self.get_argument('action', '')
    if btn == 'Login': level = _check(self.get_argument('username', ''),
                                      self.get_argument('password', ''))
    else:              level = 0
    if level:
      self.set_cookie('userlevel', str(level),
                      **{'max-age': str(frontend.SESSION_TIMEOUT)})
      self.redirect(self.get_argument('next', '/'))
    elif btn == 'Login': self.redirect('/login?unauthorised')
    else:                self.redirect('/login')
