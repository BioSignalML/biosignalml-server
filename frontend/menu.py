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

def getmenu(level):
#==================
  menu = [ ]
  if level >= user.VIEWER: menu.extend(VIEWERMENU(level))
  menu.append(LOGOUTMENU if (level > 0) else LOGINMENU)
  return menu

def MAINMENU():
#==============
  return getmenu(user.level())

def find(action, menu):
#======================
  for m in menu:
    if action == m[1]: return True
    elif len(m) > 2:   return find(action, m[2])
  return False

def hasaction(action):
#=====================
##  return True  ########################
  if action in ['index', 'login', 'logout']: return True
  return find(action, MAINMENU())
