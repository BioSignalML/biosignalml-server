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

from webdb import Database
from webserver import sessionGet, sessionSet
import menu


VIEWER        = 1
UPDATER       = 5
ADMINISTRATOR = 9


def loggedin():
#==============
  return sessionGet('loggedin', False)

def level():
#===========
  return 0 if not loggedin() else sessionGet('userlevel', 0)

def login(data):
#===============
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
    

def logout():
#============
  logging.debug("Logging out...")
  sessionSet('userlevel', 0)
  sessionSet('loggedin', False)
  menu.setmenu()
