######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id$
#
######################################################

import uuid
import logging

import tornado.web
from tornado.options import options

from forms import Button, Field
import frontend

VIEWER        = 1
UPDATER       = 5
ADMINISTRATOR = 9


def level(name):
#===============
  try:
    return int(options.database.readrow('users', 'level',
                                        where='username=:name', bindings=dict(name=name))['level'])
  except (TypeError, KeyError):
    return 0

def _check(name, passwd):
#========================
  return options.database.findrow('users', dict(username=name, password=passwd))

class Logout(frontend.BasePage):
#===============================
  def get(self):
    self.set_secure_cookie('username', '')
    self.redirect('/login')

class Login(frontend.BasePage):
#==============================
  def get(self):
    self.render('tform.html',
                title = 'Please log in:',
                rows = 4,  cols = 0,
                buttons = [ Button('Login', 35, 1), Button('Cancel', 42, 1) ],
                fields  = [ Field('Username', (1, 1), 'username', (11, 1), 20),
                            Field('Password', (1, 2), 'password', (11, 2), 20, type='password'),
                            Field.hidden('next', self.get_argument('next', '')) ],
                alert = ('Session expired, please login' if self.get_argument('next', '')
                    else 'Unauthorised, please login'    if self.request.query.find('unauthorised') >= 0
                    else ''),
                )

  def post(self):
    import frontend
    btn = self.get_argument('action')
    username = self.get_argument('username', '')
    if btn == 'Login' and username and _check(username, self.get_argument('password', '')):
      self.set_secure_cookie('username', username, **{'max-age': str(frontend.SESSION_TIMEOUT)})
      self.redirect(self.get_argument('next', '/'))
    elif btn == 'Login': self.redirect('/login?unauthorised')
    else:                self.redirect('/login')
