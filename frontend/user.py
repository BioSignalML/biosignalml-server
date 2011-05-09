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
from webserver import sessionGet, sessionSet
import menu
import templates
import biosignalml


VIEWER        = 1
UPDATER       = 5
ADMINISTRATOR = 9


def loggedin():
#==============
  return sessionGet('loggedin', False)

def level():
#===========
  return 0 if not loggedin() else sessionGet('userlevel', 0)

def _check(data):
#================
  sessionSet('userlevel', 0)
  sessionSet('loggedin', False)
  db = Database()
  row = db.matchrow('users', {'username': data.get('username'),
                              'password': data.get('password') })
  if row:
    try:
      level = int(db.readrow('users', 'level', where='rowid=%d' % row)['level'])
##      logging.debug("User level: %d", level)
      sessionSet('userlevel', level)
      sessionSet('loggedin', True)
    except Exception:
      raise
      pass
  db.close()        
  menu.setmenu()
    

def logout(data, session, params):
#================================
  logging.debug("Logging out...")
  sessionSet('userlevel', 0)
  sessionSet('loggedin', False)
  menu.setmenu()
  raise web.seeother('/login')


_page_template = templates.Page()

_form_template = templates.Form()

from templates import Button, Field


def login(data, session, params):
#===============================
  btn = data.get('action', '')
  if btn:
    if btn == 'Login': _check(data)
    if level(): raise web.seeother(biosignalml.REPOSITORY)
  form = _form_template.form('/login', 4, 0,
           [ Button('Login', 1, 75),
             Button('Cancel', 3, 75) ],
           [ Field('Username', (1, 1), 'username', (1, 11), 20),
             Field('Password', (2, 1), 'password', (2, 11), 20, type='password'),
           ] )
  return _page_template.page(title   = 'Please log in:',
                             content = form,
                             alert = ('Session expired, please login' if 'expired'      in data
                                 else 'Unauthorised, please login'    if 'unauthorised' in data
                                 else ''),
                            )
