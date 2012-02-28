######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id: menu.py,v eeabfc934961 2011/02/14 17:47:59 dave $
#
######################################################



import logging
import user

ADMINMENU  = ("System Administration", None,
               [ ("Manage Users",                     "users"),
#                ("Display Audit Trail",              "audit"),
#                ("Display/Configure System Options", "options"),
               ] )

UPDATEMENU  = ("Settings", None,
               [ ("Namespaces", "namespaces"),
               ] )


def VIEWERMENU(level):
#=====================
  return [ ("View Repository",   "repository"),
           ("Search Repository", "searchform"),
           ("SPARQL Query",      "sparqlquery"),
         ]

LOGINMENU  = ("Login",  "login")
LOGOUTMENU = ("Logout", "logout")


def setmenu(session):
#====================
  level = user.level(session)
  logging.debug('Menu SES:: %s', session)
  ##level = 1   ##############################
  logging.debug('LEVEL: %s', str(level))   ##############
  menu = [ ]
  if level >= user.VIEWER:        menu.extend(VIEWERMENU(level))
  if level >= user.UPDATER:       menu.append(UPDATEMENU)
  if level >= user.ADMINISTRATOR: menu.append(ADMINMENU)
  menu.append(LOGOUTMENU if user.loggedin(session) else LOGINMENU)
  session.menu = menu
  ##logging.debug('SET MENU: %s', menu)  #######


def MAINMENU(session):
#=====================
  menu = session.get('menu', None)
  ###logging.debug('GOT MENU: %s', menu)  #######
  if menu == None:
    setmenu(session)
    menu = session.get('menu', None)
  return menu


def find(action, menu):
#======================
  for m in menu:
    if action == m[1]: return True
    elif len(m) > 2:   return find(action, m[2])
  return False

def hasaction(action, session):
#==============================
##  return True  ########################
  if action in ['index', 'login', 'logout']: return True
  return find(action, MAINMENU(session))
