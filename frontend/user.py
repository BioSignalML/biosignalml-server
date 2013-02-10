######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id$
#
######################################################

from datetime import timedelta, datetime
import hashlib
import logging
import dateutil.parser

import tornado.web
from tornado.options import options

from forms import Button, Field
import frontend

# Levels of user
GUEST         = 0
USER          = 1
UPDATER       = 5
ADMINISTRATOR = 9

# User actions against repository:
ACTION_VIEW   = 1
ACTION_EXTEND = 3
ACTION_MODIFY = 5
ACTION_DELETE = 7
ACTION_ADMIN  = 9

ACTIONS = {
  ACTION_VIEW:   'VIEW',
  ACTION_EXTEND: 'EXTEND',
  ACTION_MODIFY: 'MODIFY',
  ACTION_DELETE: 'DELETE',
  ACTION_ADMIN:  'ADMIN',
  }


CAPABILITIES = { GUEST:         [ ACTION_VIEW ],
                 USER:          [ ACTION_VIEW, ACTION_EXTEND ],
                 UPDATER:       [ ACTION_VIEW, ACTION_EXTEND, ACTION_MODIFY ],
                 ADMINISTRATOR: [ ACTION_VIEW, ACTION_EXTEND, ACTION_MODIFY, ACTION_DELETE, ACTION_ADMIN ],
               }

TOKEN_TIMEOUT = 86400  # seconds


## FUTURE: Define groups and assign users to them.

## FUTURE: Also use URI to control access.

def capabilities(request, uri):
#==============================
  token = request.get_cookie('access')
  row = options.database.readrow('users', ('email', 'level', 'expiry'),
                                 where='token=:t', bindings=dict(t=token))
  try:
    request.user = row.get('email', 'guest')
    if datetime.utcnow() < dateutil.parser.parse(row['expiry']):
      return CAPABILITIES[int(row['level'])]
  except (TypeError, KeyError):
    pass
  return CAPABILITIES[GUEST]

def capable(action):
#===================
  def decorator(method):
    def wrapper(request, *args, **kwds):
      if action in capabilities(request, getattr(request, 'full_uri', None)):
        logging.info("User <%s> allowed to %s", request.user, ACTIONS[action])
        return method(request, *args, **kwds)
      else:
        logging.error("User <%s> not allowed to %s", request.user, ACTIONS[action])
        request.set_status(401)  ## 531 is a better status, but not in httplib.responses
    return wrapper
  return decorator


def level(name):
#===============
  try:
    return int(options.database.readrow('users', 'level',
                                        where='username=:name', bindings=dict(name=name))['level'])
  except (TypeError, KeyError):
    return 0


def _check(name, passwd):
#========================
  return (options.database.findrow('users', dict(username=name, password=passwd))
       or options.database.findrow('users', dict(email=name, password=passwd)))


def _make_token(user, row, timeout):
#=====================================
  expiry = (datetime.utcnow() + timedelta(seconds=timeout)).isoformat()
  token = hashlib.sha1(user + expiry).hexdigest()
  options.database.execute('update users set token=:t, expiry=:e where rowid=:r and username=:u',
    dict(t=token, e=expiry, r=row, u=user))
  return (token, expiry)


class Logout(frontend.BasePage):
#===============================

  def get(self):
  #-------------
    self.set_secure_cookie('username', '')
    self.redirect('/frontend/login')


class Login(frontend.BasePage):
#==============================

  def get(self):
  #-------------
    self.render('tform.html',
                title = 'Please log in:',
                rows = 4,  cols = 0,
                buttons = [ Button('Login', 35, 1), Button('Cancel', 42, 1) ],
                fields  = [ Field('Username', (1, 1), 'username', (11, 1), 20),
                            Field('Password', (1, 2), 'password', (11, 2), 20, type='password'),
                            Field.hidden('next', self.get_argument('next', '')) ],
                alert = ('Session expired, please login' if self.get_argument('next', '')
                    else 'Unauthorised, please login'    if self.request.query.find('unauthorised') >= 0
                    else ''),
                )

  def check_xsrf_cookie(self):
  #---------------------------
    """Don't check XSRF token for POSTs."""
    pass

  def post(self):
  #--------------
    btn = self.get_argument('action')
    username = self.get_argument('username', '')
    user_row = _check(username, self.get_argument('password', ''))

    if btn == 'Login':
      if user_row > 0:
        kwds = { 'max-age': str(frontend.SESSION_TIMEOUT), 'expires_days': None }
        self.set_secure_cookie('username', username, **kwds)
        self.redirect(self.get_argument('next', '/'))
      else:
        self.redirect('/frontend/login?unauthorised')

    elif btn == 'Token':
      if user_row > 0:
        token, expiry = _make_token(username, user_row, TOKEN_TIMEOUT)
        self.set_cookie('access', token)
        self.set_header('Content-Type', 'text/plain')
        self.set_status(200)
        self.write('%s %s %s' % (token, username, expiry))
      else:
        self.set_status(401)
        # self.set_header('WWW-Authenticate', ???) ####

    else:
      self.redirect('/frontend/login')
