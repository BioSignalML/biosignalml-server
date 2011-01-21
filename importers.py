######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id$
#
######################################################


"""

Watch specified directories and import signal files:

  read headers and event blocks and save as RDF triples in store

  move file into repository storage area

  add curation and provenance triples for file


  generic FileImport class and then sub-class for specific file formats.


"""

import threading
import os, sys, glob, shutil, fnmatch
import logging

from time import sleep

from repository import options
from metadata import NS
from bsml import Recording

from edf import EDFRecording
import edf.minerva


class FileImport(threading.Thread):
#==================================

  def __init__(self, path, extension, interval=1, **kwds):
  #-------------------------------------------------------
    threading.Thread.__init__(self, **kwds)
    self._searchpath = os.path.normpath(path)
    self._extension = '*.%s' % extension
    ##os.path.join(path, '*.%s' % extension))
    logging.debug("Importer loaded for '%s'", self._extension)
    self._importNS = NS(options.repository['import_base'])
    self._interval = interval
    self._running = False
    self.start()

  def run(self):
  #-------------
    self._running = True
    while self._running:
      self._checkdir()
      sleep(self._interval)

  def stop(self):
  #--------------
    self._running = False
    self.join()

  def _checkdir(self):
  #-------------------
    for root, dirs, files in os.walk(self._searchpath):
      for fname in fnmatch.filter(files, self._extension):
        fullname = os.path.join(root, fname)
        filename = os.path.relpath(fullname, self._searchpath)
        uri = self._importNS[os.path.splitext(filename)[0]].uri
        storename = os.path.normpath(os.path.join(options.repository['signal_store'], filename))
        try:    os.makedirs(os.path.dirname(storename))
        except: pass
        try:     ################## CHECK NOT IN STORE
          shutil.move(fullname, storename)          ## Move first, before importing metadata
          ## Better to try import then move? So if error can reset?
          ## Also need to log to file... NO, better to add provenance triples
          self.save_metadata(storename, uri)
        except Exception, msg:
          logging.error("Error importing '%s': %s", fullname, msg)
          raise  ##################


  def save_metadata(self, filepath, uri):    # Override in format specific subclass
  #-------------------------------------
    pass


#########################################################


class EDFImport(FileImport):
#===========================

  def save_metadata(self, filepath, uri):
  #-------------------------------------
    logging.debug("Importing '%s'", filepath)
    edf = EDFRecording.open(filepath, uri)
    edf.close()


class MinervaEvent(FileImport):
#==============================

  def save_metadata(self, filepath, uri):
  #-------------------------------------
    logging.debug("Events from '%s' for '%s'...", filepath, uri)

    rec = Recording.open(uri)

    ## What if recording not yet in repository...

    m = edf.minerva.EventFile(filepath)
    m.read_header()
    events = m.read_events()
    for n, e  in enumerate(events):
      id = 'minerva_%d' % (n + 1)
      sig = rec.get_signal(id=str(e[1]))
      if sig: sig.event(id, e[2], rec.interval(*e[0]))
      else:   logging.error("Signal with id '%s' not in '%s'", e[1], str(rec))
    m.close()


#########################################################

class Importers(object):
#=======================

  def __init__(self, interval=1):  
  #------------------------------
    classes = globals()
    loaders = options.loaders
    formats = options.imports
    self._threads = [ ]
    for extn, path in formats.iteritems():
      if extn in loaders: self._threads.append(classes[loaders[extn]](path, extn, interval=interval))
      else:               logging.error("Unknown file format: '%s'", extn)

  def stop(self):
  #--------------
    for t in self._threads: t.stop()


if __name__ == '__main__':
#=========================

  threads = Importers()

  sleep(10)

  threads.stop()
