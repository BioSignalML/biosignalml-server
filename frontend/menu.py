######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id: menu.py,v eeabfc934961 2011/02/14 17:47:59 dave $
#
######################################################


from lxml import etree

import logging
import user
from webserver import sessionGet, sessionSet

ADMINMENU  = """<menu prompt="System Administration">
                 <item prompt="Manage Users"               action="users"/>
<!--             <item prompt="Display Audit Trail" action="audit"/> -->
<!--             <item prompt="Display/Configure System Options" action="options"/> -->
                </menu>"""

UPDATEMENU = """<menu></menu>"""

def VIEWERMENU(level):
#=====================
  return """<menu prompt="View Repository"   action="repository"></menu>
            <menu prompt="Search Repository" action="searchform"></menu>
            <menu prompt="SPARQL Query"      action="sparqlsearch"></menu>"""

LOGINMENU  = """<menu prompt="Login"  action="login"/>"""
LOGOUTMENU = """<menu prompt="Logout" action="logout"/>"""


def setmenu():
#=============
  level = user.level()
  ##logging.debug('LEVEL: %s', str(level))   ##############
  menu = '<menu>'
  if level >= user.VIEWER:        menu += VIEWERMENU(level)
  if level >= user.UPDATER:       menu += UPDATEMENU
  if level >= user.ADMINISTRATOR: menu += ADMINMENU
  if user.loggedin(): menu += LOGOUTMENU
  else:               menu += LOGINMENU
  menu += '</menu>'
  sessionSet('menu', menu)
  ##logging.debug('SET MENU: %s', menu)  #######


def MAINMENU():
#==============
  menu = sessionGet('menu', None)
  ###logging.debug('GOT MENU: %s', menu)  #######
  if menu == None:
    setmenu()
    menu = sessionGet('menu', None)
  return menu


def _find(element, attrib, value):
#=================================
  if element.get(attrib) == value:
    return True
  else:
    for e in element.getchildren():
      r = _find(e, attrib, value)
      if r: return True
  return False


def hasaction(action):
#=====================
  if action in ['index', 'login', 'logout']: return True
  menu = MAINMENU()
  ##logging.debug("A=%s, M=%s", action, menu)
  tree = etree.fromstring(menu)
  return _find(tree, 'action', action)


if __name__ == "__main__":
#=========================
  menu = MAINMENU()
  print hasaction('repository')
  print hasaction('users')
  print hasaction('login')
