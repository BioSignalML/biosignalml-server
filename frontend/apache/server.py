import os, sys
import logging

print 'PATH=%s' % sys.path

import web


APIDIR = '/Users/dave/biosignalml/python/api'
APPDIR = '/Users/dave/biosignalml/python/apps'

sys.path.append(APIDIR)
sys.path.append(APPDIR)

import repository.frontend.recording as recording
import repository.frontend.webserver as webserver
import repository.frontend.xslt      as xslt
import repository.frontend.xsl       as xsl


webserver.pagexsl = xslt.Engine(xsl.PAGEXSL)
if web.config.debug: web.webapi.internalerror = web.debugerror
recording.initialise()

webserver.pagexsl.start()
application = webserver.webapp.wsgifunc()
