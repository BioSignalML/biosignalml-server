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


ADMINMENU  = ("System Administration", None,
               [ ("Manage Users",                     "/frontend/users"),
#                ("Display Audit Trail",              "audit"),
#                ("Display/Configure System Options", "options"),
               ] )

UPDATEMENU  = ("Settings", None,
               [ ("Namespaces", "/frontend/namespaces"),
               ] )

def VIEWERMENU(level):
#=====================
  return [ ("View Repository",   "/"),
           ("Search Repository", "/frontend/search"),
           ("SPARQL Query",      "/frontend/sparql"),
         ]

LOGINMENU  = ("Login",  "/frontend/login")
LOGOUTMENU = ("Logout", "/frontend/logout")

def getmenu(level):
#==================
  menu = [ ]
#  if level >= user.VIEWER: menu.extend(VIEWERMENU(level))
  menu.extend(VIEWERMENU(level))
  if level > 0: menu.append(LOGOUTMENU)
#  menu.append(LOGOUTMENU if (level > 0) else LOGINMENU)
  return menu
