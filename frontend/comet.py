######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id$
#
######################################################


import web
import logging


def MESSAGE():   # This is so we can put message into HTML
#-------------   # for initial display *before* first comet request.
  return '<message>%s</message>' % stream({}, {})['message']
