######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id: biosignalml.py,v eeabfc934961 2011/02/14 17:47:59 dave $
#
######################################################

import apsw
from tornado.options import options


class Database(object):
#======================

  def __init__(self):
  #------------------
    self._db = apsw.Connection(options.database)
    self._cursor = self._db.cursor()

  def execute(self, sql, bindings=None):
  #-------------------------------------
    return self._cursor.execute(sql, bindings)

  def findrow(self, table, cond):
  #------------------------------
    sql = [ 'select rowid from %s where ' % table]
    sql.append(' and '.join([ '(%s = :%s)' % (n, n) for n in cond ]))
    sql.append(' limit 1')
    for r in self.execute(''.join(sql), cond): return r[0]
    return 0

  def readrow(self, table, cols, where, order=None):
  #-------------------------------------------------
    try:                   cols.__iter__
    except AttributeError: cols = [ str(cols) ]
    sql = [ 'select %s from %s' % (', '.join(list(cols)), table) ]
    if where: sql.append(' where %s' % where)
    if order: sql.append(' order %s' % order)
    sql.append(' limit 1')
    for r in self.execute(''.join(sql)):
      return { n: r[i] for i, n in enumerate(cols) }
    return { }
