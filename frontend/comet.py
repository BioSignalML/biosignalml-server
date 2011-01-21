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

from utils import cp1252, num, xmlescape
from webserver import sessionGet, sessionSet


def stream(get, post, params):
#============================
  msgs = [ ]
  alerts = [ ]
  return {'message': ''.join(msgs),
          'alert':   '\n'.join(alerts),
         }

def MESSAGE():   # This is so we can put message into HTML
#-------------   # for initial display *before* first comet request.
  return '<message>%s</message>' % stream({}, {})['message']
