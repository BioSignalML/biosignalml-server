######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id: webpages.py,v eeabfc934961 2011/02/14 17:47:59 dave $
#
######################################################


import web
import logging
from time import strftime, strptime
from functools import partial

from page import DataPage, FormPage
from field import Field, Layout
from utils import num

import user
import biosignalml


FORMAT_SQLDATE     = '%Y-%m-%d %H:%M:%S'   # Python strftime()/strptime()
FORMAT_DISPLAYDATE = '%I:%M%p %d/%m/%Y'    # Python strftime()/strptime()
FORMAT_PICKERDATE  = 'h:MMtt dd/mm/yyyy'   # jQuery datetimepicker

                  

def setLevel(l):
#===============
  if   l >= '9': return 'Admin'
  elif l >= '5': return 'Update'
  elif l >= '1': return 'View'
  else:          return ''

def getLevel(l):
#===============
  if   l == 'Admin':  return '9'
  elif l == 'Update': return '5'
  elif l == 'View':   return '1'
  else:               return '0'


def setpassword(data):
#=====================
  data['password2'] = data.get('password')


def checkpassword(db, page, data):
#=================================
  if data['password'] != data['password2']: return 'Passwords do not match'
  else:                                     return ''


def users(data, session, params):
#===============================
  return DataPage('users', 'username', None, 'Users',
                  fields = [Field('username',  'User Name',         layout=Layout(20, 1, (1, 14))),
                            Field('password',                       layout=Layout(20, 3, (1, 14)),
                              password=True, listview=False),
                            Field('password2', 'Re-enter Password', layout=Layout(20, 4, (1, 14)),
                              password=True, datacol=False),
                            Field('level',                          layout=Layout( 6, 6, (1, 14)),
                              mapping=(setLevel, getLevel), choices=['View', 'Update', 'Admin']),
                           ],
                  preedit = setpassword,
                  validation = checkpassword,
                  numerickey = False,
                 ).show(data, session)


def login(data, session, params):
#===============================
  btn = data.get('action', '')
  if btn:
    if btn == 'Login': user.login(data)
    if user.level(): raise web.seeother(biosignalml.REPOSITORY)
  return FormPage('Please log in:',
                  [Field('username', 'Username', layout=Layout(20, 1, (1, 11))),
                   Field('password', 'Password', layout=Layout(20, 2, (1, 11)), password=True),
                  ],
                  editbtns = ['Login', 'Cancel'],
                  message = ('Session expired, please login' if 'expired'      in data
                        else 'Unauthorised, please login'    if 'unauthorised' in data
                        else ''),
                 ).show(data, session)


def logout(data, session, params):
#================================
  user.logout()
  raise web.seeother('/login')


def index(data, session, params):
#===============================
  if user.loggedin():
    return biosignalml.repository(data, session, params)
  else:
    return login(data, session, params)
