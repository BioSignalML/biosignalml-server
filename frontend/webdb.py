import web

import repository


class Database(object):
#======================

  def __init__(self):
  #------------------
    dboptions = repository.options.triplestore.copy()
    if dboptions['store'] == 'postgresql':
      del dboptions['store']
      self._db = web.database(dbn='postgres', **dboptions)
    elif dboptions['store'] == 'sqlite':
      del dboptions['store']
      dboptions['db'] = dboptions['database']
      self._db = web.database(dbn='sqlite', **dboptions)
    else:
      raise Exception("Unsupported database: '%s'" % dboptions['store'])   

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
