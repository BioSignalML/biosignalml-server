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
import htmlview


VIEWER        = 1
UPDATER       = 5
ADMINISTRATOR = 9


def loggedin(session):
#=====================
  return session.get('loggedin', False)

def level(session):
#==================
  return 0 if not loggedin(session) else session.get('userlevel', 0)

def _check(data, session):
#=========================
  session.userlevel = 0
  session.loggedin = False
  db = Database()
  row = db.matchrow('users', {'username': data.get('username'),
                              'password': data.get('password') })
  if row:
    try:
      level = int(db.readrow('users', 'level', where='rowid=%d' % row)['level'])
##      logging.debug("User level: %d", level)
      session.userlevel = level
      session.loggedin = True
    except Exception:
      raise
      pass
  db.close()        
  menu.setmenu(session)
    

def logout(data={}, session=None, params={}):
#============================================
  logging.debug("Logging out...")
  if session:
    session.userlevel = 0
    session.loggedin = False
    menu.setmenu(session)
  raise web.seeother('/login')


_page_template = templates.Page()

_form_template = templates.Form()

from templates import Button, Field


def login(data, session, params):
#===============================
  btn = data.get('action', '')
  if btn:
    if btn == 'Login': _check(data, session)
    if level(session): raise web.seeother(htmlview.REPOSITORY)
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
                             session = session,
                            )
