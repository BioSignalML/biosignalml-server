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


def name(token):
#===============
  try:
    return options.database.readrow('users', 'username',
                                    where='token=:token', bindings=dict(token=token))['username']
  except KeyError:
    return None

def level(token):
#================
  try:
    return int(options.database.readrow('users', 'level',
                                        where='token=:token', bindings=dict(token=token))['level'])
  except (TypeError, KeyError):
    return 0

def _check(name, passwd):
#========================
  db = options.database
  db.execute('begin transaction')
  row = db.findrow('users', dict(username=name, password=passwd))
  if row:
    try:
      token = str(uuid.uuid1())
      db.execute('update users set token=:token where rowid=:row',
                    dict(token=token, row=row))
      db.execute('commit')
      return token
    except Exception:
      db.execute('rollback')
  return None

class Logout(frontend.BasePage):
#===============================
  def get(self):
    self.set_secure_cookie('usertoken', '0')
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
    token = None
    btn = self.get_argument('action')
    username = self.get_argument('username', '')
    if btn == 'Login' and username:
      token = _check(username, self.get_argument('password', ''))
    if token:
      self.set_secure_cookie('usertoken', token,
                      **{'max-age': str(frontend.SESSION_TIMEOUT)})
      self.redirect(self.get_argument('next', '/'))
    elif btn == 'Login': self.redirect('/login?unauthorised')
    else:                self.redirect('/login')
