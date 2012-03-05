######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id: biosignalml.py,v eeabfc934961 2011/02/14 17:47:59 dave $
#
######################################################


import web


def initialise(options):
#=======================
  web.config._dboptions = options


class Database(object):
#======================

  _database = web.config.biosignalml['database']

  def __init__(self):
  #------------------
    self._db = web.database(dbn='sqlite', db=Database._database)
    self._db.printing = False      ## Otherwise set to web.config.debug

  def close(self):
  #---------------
    del self._db

  def execute(self, sql):
  #----------------------
    return self._db.query(sql)

  def matchrow(self, table, where):
  #-------------------------------
    for row in self._db.where(table, what=web.sqllist('rowid'), limit=1, **where):
      return row['rowid']
    return 0

  def readrow(self, table, cols, where, order=None):
  #-------------------------------------------------
    for row in self._db.select(table, what=web.sqllist(cols), where=where, order=order, limit=1):
      return row
    return { }
