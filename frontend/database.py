######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id$
#
######################################################


import sqlite3

import logging
import threading
from time import sleep


def escape(s):
#=============
  if isinstance(s, (str, unicode)): return s.replace("'", "''")
  else:                             return s

# For controlling access to SQL transactions:
transaction_lock = None

def initDB():
#============
  global transaction_lock
  transaction_lock = threading.Lock()


class Database(object):
#======================

  def __init__(self):
  #------------------
    if transaction_lock is None: initDB()
    self._connection = sqlite3.connect('database.db', 10.0, check_same_thread = False)
    self._connection.isolation_level = None   ## We use SQL to control transactions

  def __del__(self):
  #-----------------
    self.close()

  def close(self):
  #---------------
    self._connection.close()

  def execute(self, sql, *args):
  #-----------------------------
    ##logging.debug('Execute: %s', sql)
    return self._connection.execute(sql, *args)

  def readlist(self, table, col, where=None, order=None, limit=None):
  #------------------------------------------------------------------
    if isinstance(col, tuple):
      sql = ['select ']
      sql += [c + ', ' for c in col]
      sql = ''.join(sql)[:-2]
    else:
      sql = 'select ' + col  
    sql += ' from ' + table ;
    if where: sql += ' where ' + where
    if order: sql += ' order by ' + order
    if limit: sql += ' limit ' + str(limit)
    ##logging.debug('readlist: %s', sql)
    rows = []
    if isinstance(col, tuple):
      for row in self.execute(sql):
        if row == None: rows.append('')
        else:           rows.append(row)
    else:
      for row in self.execute(sql):
        if row[0] == None: rows.append('')
        else:              rows.append(row[0])
    return rows 

  def readrow(self, table, col, where=None, order=None):
  #-----------------------------------------------------
    if isinstance(col, tuple):
      sql = ['select ']
      sql += [c + ', ' for c in col]
      sql = ''.join(sql)[:-2]
    else:
      sql = 'select ' + col  
    sql += ' from ' + table ;
    if where: sql += ' where ' + where
    if order: sql += ' order by ' + order
    sql += ' limit 1'
    ##logging.debug('readrow: %s', sql)
    rows = dict()
    for row in self.execute(sql):
      if isinstance(col, tuple):
        for n, c in enumerate(col):
          key = c[c.find('.')+1:]
          if row[n] == None: rows[key] = ''
          else:              rows[key] = row[n]
      else:
        key = col[col.find('.')+1:]
        if row[0] == None: rows[key] = ''
        else:              rows[key] = row[0]
    return rows  

  def matchrow(self, table, match, where=None):
  #--------------------------------------------
    sql = 'select rowid from ' + table
    cond = list()
    for k, v in match.iteritems():
      cond.append(' and ' + k + "='" + escape(str(v)) + "'")
    if len(cond) or where:
      sql += ' where ' ;
      if len(cond):
        sql += ''.join(cond)[5:]
        if where: sql += ' and '
      if where: sql += '(%s)' % where
    sql += ' limit 1'
    rowid = 0
    for row in self.execute(sql):
      rowid = int(row[0])
    ##logging.debug('matchrow=%d: %s', rowid, sql)
    return rowid

  def copyrow(self, table, keycol, oldkey, newkey):
  #------------------------------------------------
    self.execute("create temporary table temptable as select * from %s where %s='%s'"
                 % (table, keycol, oldkey))
    self.execute("update temptable set %s='%s'" % (keycol, newkey))
    self.execute("insert or replace into %s select * from temptable" % table)
    self.execute("drop table temptable")

  def update(self, table, keycols, data):
  #--------------------------------------
    if not isinstance(keycols, tuple): keycols = (keycols, )
    sql = ['update ' + table + ' set ']
    sql += [k + "='" + escape(str(data[k])) + "', " for k in data if k not in keycols]
    sql = ''.join(sql)[:-2] + ' where '
    for k in keycols:
      sql += k + "='" + escape(str(data[k])) + "' and "
    sql = sql[:-5]
    ##logging.debug('Update: %s', sql)
    return self.execute(sql)

  def assign(self, table, keycols, data):
  #--------------------------------------
    try:
      sql = ['insert into ' + table + ' (']
      sql += [k + ', ' for k in data]
      val = ["'" + escape(str(data[k])) + "', " for k in data]
      sql = ''.join(sql)[:-2] + ') values (' + ''.join(val)[:-2] + ')'
      r = self.execute(sql)
    except Exception:
      return self.update(table, keycols, data)
    ##logging.debug('Assign: %s', sql)
    return r

  def delete(self, table, keycol, key):
  #------------------------------------
    sql = 'delete from ' + table + ' where ' + keycol + "='" + escape(str(key)) + "'"
    ##logging.debug('Delete: %s', sql)
    return self.execute(sql)

  def begin(self):
  #---------------
    ##logging.debug('Start transaction')
    transaction_lock.acquire()
    return self.execute('begin immediate')

  def commit(self):
  #----------------
    result = self.execute('commit')
    transaction_lock.release()
    return result

  def rollback(self):
  #------------------
    result = self.execute('rollback')
    transaction_lock.release()
    return result

  def transaction(self, sql, *args):
  #---------------------------------
    ##logging.debug('Begin transaction')
    transaction_lock.acquire()
    self._connection.execute('begin immediate')
    ##logging.debug('Execute: %s', sql)
    r = self._connection.execute(sql, *args)
    self._connection.execute('commit')
    transaction_lock.release()
    ##logging.debug('End transaction')
    return r

  def get_status(self, key):
  #-------------------------
    sql = "select value from status where name='%s' limit 1" % key
    ##logging.debug("SQL: %s", sql)
    for row in self.execute(sql):
      if row[0] == None: return ''
      else:              return row[0]
    return ''  

  def put_status(self, key, val):
  #------------------------------
    sql = "select value from status where name='%s' limit 1" % key
    for row in self.execute(sql):
      if   row[0] != val:
        sql = "update status set value='%s' where name='%s'" % (val, key)
        ##logging.debug("SQL: %s", sql)
        self.execute(sql)
      return
    sql = "insert into status (name, value) values ('%s', '%s')" % (key, val)
    ##logging.debug("SQL: %s", sql)
    self.execute(sql)


class PagedTable(object):
#========================

  def __init__(self, table, columns, primary=None,
  #-----------------------------------------------
               sort=None, defsort=None,
               pagesize=0, joins=None,
               restriction=None, numerickey=True):
    """
      table       string    Name of table
      columns     list      Column names to return from table
      primary     string    Primary key column
      sort        tuple(list, list)
        keycols             Column names to order result by
        keyorder            Parallel list giving sort direction
      defsort     tuple(list, list)
        keycols             Default column names to order result by
        keyorder            Parallel list giving sort direction
      pagesize    integer
      joins       list      tuple(jtable, column, matchcol, resultcol)
        jtable    string    Table to left join to
        column    string    Column in main table used for join
        matchcol  string    Column in join table to match (equal)
        resultcol string    Data to return from join table
      restriction string    Restriction filter to apply
      numerickey  boolean   Key column has numeric values
    """
    self._table = table
    self._joins = joins
    self._columns = columns
    if primary == None: primary = 'rowid'
    self._primary = primary
    if sort:
      self._keycols  = sort[0]
      self._keyorder = sort[1]
    else:
      self._keycols  = list()
      self._keyorder = list()
    if primary not in self._keycols:
      self._keycols.append(primary)
      self._keyorder.append('asc')
    ##logging.debug('keycols: %s', self._keycols)
    self._defsort = defsort
    self._pagesize = pagesize
    self._toprow = self._botrow = None
    self._filter = None
    self._restriction = restriction
    self._numerickey = numerickey

  def _keydata(self, db, rowid):
  #-----------------------------
    if rowid == None: return None
    if len(self._keycols) == 1 and self._keycols[0] == 'rowid': return [ rowid ]
    sql = 'select '
    for k in self._keycols: sql += k + ','
    sql = sql[:-1] + ' from %s where rowid=%d' % (self._table, rowid)
    ##logging.debug('KEYS: %s', sql)
    for r in db.execute(sql): return list(r)
    return None

  def _where(self, keydata, next, equals):
  #---------------------------------------
    if keydata == None: return ''
    ##logging.debug("keys: %s %s %s", repr(self._keycols), repr(self._keyorder), repr(keydata))
    sql = ['(']
    for i in xrange(0, len(keydata)):
      if self._keyorder[i] == 'desc':
        if next: reln = '<'
        else:    reln = '>'
      else:
        if next: reln = '>'
        else:    reln = '<'
      if self._keyorder[i] == 'eq' or keydata[i] is not None or reln == '>':
        for j in xrange(0, i):
          if keydata[j] is None:
            sql.append("t.%s is NULL" % self._keycols[j])
          elif self._numerickey and self._keycols[j] == self._primary:
            sql.append("t.%s = %d" % (self._keycols[j], int(keydata[j])))
          else:
            sql.append("upper(t.%s) = '%s'" % (self._keycols[j], escape(str(keydata[j])).upper()))
          sql.append(' and ')
        if self._keyorder[i] != 'eq' and keydata[i] is not None:
          if self._numerickey and self._keycols[i] == self._primary:
            sql.append("t.%s %c %d" % (self._keycols[i], reln, int(keydata[i])))
          else:
            sql.append("upper(t.%s) %c '%s'" % (self._keycols[i], reln, escape(str(keydata[i])).upper()))
          sql.append(' or ')
    if equals:
      for i in xrange(0, len(keydata)):
        if keydata[i] is None:
          sql.append("t.%s is NULL" % self._keycols[i])
        elif self._numerickey and self._keycols[i] == self._primary:
          sql.append("t.%s = %d" % (self._keycols[i], int(keydata[i])))
        else:
          sql.append("upper(t.%s) = '%s'" % (self._keycols[i], escape(str(keydata[i])).upper()))
        sql.append(') and (')
    sql.pop()
    sql.append(')')
    return ''.join(sql)

  def _order(self, cols, order, quote, reverse):
  #---------------------------------------------
    sql = [ ]
    for n, k in enumerate(cols):
      if k == self._primary: sql.append('%st.%s%s' % (quote, k, quote))
      else:                  sql.append('upper(%st.%s%s)' % (quote, k, quote))
      dirn = order[n]
      if reverse:
        if dirn == 'asc': sql.append(' desc')
      else:
        if dirn == 'desc': sql.append(' desc')
      sql.append(', ')
    sql.pop()
    return ''.join(sql)

  @staticmethod
  def _colprefix(prefix, cols):
  #----------------------------
    result = [] 
    for p in cols.split(' '):
      if p and p[0].isalpha(): result.append(prefix + p)
      else:                    result.append(p)
    return ' '.join(result)

  def _getpage(self, db, keydata, next, match):
  #--------------------------------------------
    sql = []
    if not next: sql.append('select * from (')
    sql.append('select t.rowid')
    for c in self._columns: sql.append(', t.' + c)
    if self._joins:
      for n, j in enumerate(self._joins): sql.append(', %s' % self._colprefix('j%d.' % n, j[3]))
    sql.append(' from %s as t' % self._table)
    if self._joins:
      for n, j in enumerate(self._joins):
        sql.append(' left join %s as j%d on t.%s = j%d.%s' % (j[0], n, j[1], n, j[2]))
    if keydata or self._filter or self._restriction:
      sql.append(' where (')
      if keydata:
        sql.append(self._where(keydata, next, match))
        if self._filter or self._restriction: sql.append(') and (')
      if self._filter:
        sql.append(self._filter)
        if self._restriction: sql.append(') and (')
      if self._restriction: sql.append(self._restriction)
      sql.append(')')
    sql.append(' order by ')
    sql.append(self._order(self._keycols, self._keyorder, '', not next))
    if not next:
      if self._pagesize: sql.append(' limit %d' % self._pagesize)
      sql.append(') order by ')
      sql.append(self._order(self._keycols, self._keyorder, '"', False))
      if self._defsort and self._defsort[0]:
        sql.append(', ')
        sql.append(self._order(self._defsort[0], self._defsort[1], '"', False))
    elif self._defsort and self._defsort[0]:
      sql.append(', ')
      sql.append(self._order(self._defsort[0], self._defsort[1], '', False))
      if self._pagesize: sql.append(' limit %d' % self._pagesize)
    ##logging.debug('SQL: %s', ''.join(sql))
    rows = db.execute(''.join(sql))
    data = []
    for n,d in enumerate(rows):
      if n == 0: self._toprow = int(d[0])
      data.append(d[1:])
    if len(data): self._botrow = int(d[0])
###    for d in data: logging.debug('DATA: %s', str(d))
    ##logging.debug('Got %d rows', len(data))
    return data

  def nextpage(self, db):
  #----------------------
#    logging.debug('Next page...')
    return self._getpage(db, self._keydata(db, self._botrow), True, False)

  def thispage(self, db):
  #----------------------
#    logging.debug('This page...')
    return self._getpage(db, self._keydata(db, self._toprow), True, True)

  def prevpage(self, db):
  #----------------------
#    logging.debug('Prev page...')
    return self._getpage(db, self._keydata(db, self._toprow), False, False)

  def findpage(self, db, keydata, filter):
  #---------------------------------------
#    logging.debug('Find page...')
    self._filter = filter
    return self._getpage(db, keydata, True, True)

  def keycols(self):
  #-----------------
    kc = self._keycols[:]    # Make a copy...
    ko = self._keyorder[:]   # Make a copy...
    if self._primary in kc:
      n = kc.index(self._primary)
      if n > 0:
        kc.pop(n)
        ko.pop(n)
    return ((kc, ko))
