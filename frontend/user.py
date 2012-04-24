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
import web

from webdb import Database
import menu
import templates


VIEWER        = 1
UPDATER       = 5
ADMINISTRATOR = 9


def level():
#===========
  return int(web.cookies().get('userlevel', 0))

def loggedin():
#==============
  return level() > 0

def _check(data):
#================
  level = 0
  db = Database()
  row = db.matchrow('users', {'username': data.get('username'),
                              'password': data.get('password') })
  if row:
    try:
      level = int(db.readrow('users', 'level', where='rowid=%d' % row)['level'])
      ## logging.debug("User level: %d", level)
    except Exception:
      raise
      pass
  db.close()        
  return level

def logout(data={}, params={}):
#==============================
  ## logging.debug("Logging out...")
  web.setcookie('userlevel', 0)
  raise web.seeother('/login')


_page_template = templates.Page()

_form_template = templates.Form()

from templates import Button, Field


def login(data, params):
#=======================
  import frontend
  btn = data.get('action', '')
#  web.setcookie('userlevel', 0)
  level = 0
  if btn:
    if btn == 'Login': level = _check(data)
    if level:
      web.setcookie('userlevel', level, frontend.SESSION_TIMEOUT)
      raise web.seeother('/repository')
  form = _form_template.form('/login', 4, 0,
           [ Button('Login', 1, 35),
             Button('Cancel', 1, 42) ],
           [ Field('Username', (1, 1), 'username', (1, 11), 20),
             Field('Password', (2, 1), 'password', (2, 11), 20, type='password'),
           ] )
  return _page_template.page(title   = 'Please log in:',
                             content = form,
                             alert = ('Session expired, please login' if 'expired'      in data
                                 else 'Unauthorised, please login'    if 'unauthorised' in data
                                 else ''),
                            )
