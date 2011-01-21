######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id$
#
######################################################


import sys, logging, traceback
import threading, Queue
from StringIO import StringIO
from time import sleep
from lxml import etree

from utils import cp1252, xmlescape


class Engine(threading.Thread):
  def __init__(self, xsl, **kwds):
    threading.Thread.__init__(self, **kwds)
    self._inputQ = Queue.Queue()
    self._outputQ = Queue.Queue()
    f = StringIO(xsl)
    p = etree.parse(f)
    self._transform = etree.XSLT(p)
    self.setName('XSLT engine thread')


  def run(self):
    self._running = True
    while self._running:
      if not self._inputQ.empty():
        xml, params = self._inputQ.get()
        try:
          parameters = dict()
          for (k, v) in params.iteritems():
            if isinstance(v, (str, unicode)): parameters[k] = etree.XSLT.strparam(v)
            else:                             parameters[k] = v
          doc = etree.parse(StringIO(cp1252(xml)))
          ##logging.debug("Params: %s", parameters)
          result = self._transform(doc, **parameters)
        except Exception, msg:
          logging.error('Error loading page: %s\n%s', xml, str(msg))
          logging.error('Error loading page: %s', traceback.format_exc())
          xml = '<page alert="Page can not be loaded... %s"/>' % xmlescape(str(msg))
          doc = etree.parse(StringIO(xml))
          result = self._transform(doc)
        self._outputQ.put(str(result))
      sleep(0.1)


  def stop(self):
    self._running = False
    self.join()


  def transform(self, xml, params= { } ):
    self._inputQ.put((xml, params))
##    logging.debug("Transforming '%s'", xml)
    return self._outputQ.get()
