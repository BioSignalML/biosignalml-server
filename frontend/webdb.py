######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id: biosignalml.py,v eeabfc934961 2011/02/14 17:47:59 dave $
#
######################################################

import sqlite3
import logging
import types

class Database(object):
#======================

  def __init__(self, name):
  #------------------------
    self._db = sqlite3.connect(name)

  def execute(self, sql, bindings:tuple=()):
  #-----------------------------------------
    logging.debug("SQL: %s (%s)", sql, bindings)
    return self._db.execute(sql, bindings)

  def findrow(self, table, cond):
  #------------------------------
    sql = [ 'select rowid from %s where ' % table]
    sql.append(' and '.join([ '(%s = :%s)' % (n, n) for n in cond ]))
    sql.append(' limit 1')
    for r in self.execute(''.join(sql), cond): return r[0]
    return 0

  def readrow(self, table, cols, where, order=None, bindings=None):
  #----------------------------------------------------------------
    if isinstance(cols, str):
      cols = [ cols ]
    else:
      try:
        cols.__iter__
      except AttributeError:
        cols = [ str(cols) ]
    sql = [ 'select %s from %s' % (', '.join(list(cols)), table) ]
    if where: sql.append(' where %s' % where)
    if order: sql.append(' order %s' % order)
    sql.append(' limit 1')
    for r in self.execute(''.join(sql), bindings):
      return { n: r[i] for i, n in enumerate(cols) }
    return { }
