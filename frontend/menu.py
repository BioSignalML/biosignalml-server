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

import frontend
import user

ADMINMENU  = ("System Administration", None,
               [ ("Manage Users",                     "/users"),
#                ("Display Audit Trail",              "audit"),
#                ("Display/Configure System Options", "options"),
               ] )

UPDATEMENU  = ("Settings", None,
               [ ("Namespaces", "/namespaces"),
               ] )

def VIEWERMENU(level):
#=====================
  return [ ("View Repository",   frontend.REPOSITORY[:-1]),
           ("Search Repository", "/search"),
           ("SPARQL Query",      "/sparqlquery"),
         ]

LOGINMENU  = ("Login",  "/login")
LOGOUTMENU = ("Logout", "/logout")

def getmenu(level):
#==================
  menu = [ ]
#  if level >= user.VIEWER: menu.extend(VIEWERMENU(level))
  menu.extend(VIEWERMENU(level))
#  menu.append(LOGOUTMENU if (level > 0) else LOGINMENU)
  return menu
