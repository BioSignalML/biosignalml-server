######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id: importers.py,v eeabfc934961 2011/02/14 17:47:59 dave $
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

from model.mapping import bsml_mapping

from rdfmodel import NS, Graph

from fileformats.edf import EDFRecording  ## Dynamically import..
from fileformats.sdf import SDFRecording

import fileformats.edf.minerva

from repository import options, triplestore


class FileImport(threading.Thread):
#==================================

  def __init__(self, cls, path, extension, interval=1, **kwds):
  #------------------------------------------------------------
    threading.Thread.__init__(self, **kwds)
    self._class = cls
    self._searchpath = os.path.abspath(path)
    self._extension = '*.%s' % extension if extension else None
    ##os.path.join(path, '*.%s' % extension))
    logging.debug("Importer loaded for '%s'", cls)
    self._importNS = NS(options.repository['base'])
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

  def _import(self, root, fname):
  #------------------------------
    fullname = os.path.abspath(os.path.join(root, fname))
    filename = os.path.relpath(fullname, self._searchpath)
    uri = self._importNS[os.path.splitext(filename)[0]].uri
    storedname = os.path.abspath(os.path.join(options.repository['signals'], filename))
    try:    os.makedirs(os.path.dirname(storedname))
    except: pass
    try:     ################## CHECK NOT IN STORE
      shutil.move(fullname, storedname)          ## Move first, before importing metadata
      # Also of we are importing a (SDF) directory, better to move
      # into containing level otherwise a sub-directory of the signal
      # directory is created underneath if it already esisted...

      ## Better to try import then move? So if error can reset?
      ## Also need to log to file... NO, better to add provenance triples
      recording = self._class(storedname, uri)
      recording.add_to_RDFmodel(triplestore, bsml_mapping, Graph(uri))
      recording.close()
      logging.debug("Imported '%s'", storedname)
    except Exception, msg:
      logging.error("Error importing '%s': %s", fullname, msg)

  def _checkdir(self):
  #-------------------
    for root, dirs, files in os.walk(self._searchpath):
      if self._extension:
        for fname in fnmatch.filter(files, self._extension): self._import(root, fname)
      else:
        for fname in dirs: self._import(root, fname)


#########################################################


class MinervaEvent(FileImport):
#==============================

  def save_metadata(self, filepath, uri):
  #-------------------------------------
    logging.debug("Events from '%s' for '%s'...", filepath, uri)

    ## Find in triplestore... 
    #### rec = Recording.open(uri)

    ## What if recording not yet in repository...

    m = fileformats.edf.minerva.EventFile(filepath)
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
    for key, path in formats.iteritems():
      if key[-1] != '/': extn = key
      else:
        key = key[:-1]
        extn = None
      if key in loaders:
        self._threads.append(FileImport(classes[loaders[key]], path, extn, interval=interval))
      else:
        logging.error("Unknown file format: '%s'", key)

  def stop(self):
  #--------------
    for t in self._threads: t.stop()


if __name__ == '__main__':
#=========================

  threads = Importers()

  sleep(10)

  threads.stop()
