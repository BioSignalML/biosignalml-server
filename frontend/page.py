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
import types
import logging, traceback

from utils import cp1252, num, xmlescape, nbspescape
from menu import MAINMENU
##from comet import MESSAGE
from field import Field

import database
from database import  Database, PagedTable  #########

#### from webdb import Database


FORMWIDTH  = 40 ## 54   # It works...!
FORMBTNCOL = 48 ## 64


def MESSAGE():       ########### Temp...
#=============
  return ''


def log(p, n, d):
#================
  l = ['%s:\nDictionary %s:\n' % (p, n)]
  for k, v in d.iteritems(): l.append("  %s = '%s'\n" % (k, v))
  return ''.join(l)


def _editbuttons(editbtns, btnactions, readonly, delete):
#========================================================
  def btnhtml(btn, row):
    action = btnactions.get(btn, None) if btnactions else None
    return ''.join(['<button name="action" prompt="%s" row="%d" col="%d"' % (btn, row, FORMBTNCOL),
                    (' onclick="confirm(\'%s\')"' % xmlescape(action[0])) if action and action[0] else '',
                   '/>'])
  btns = []
  if not readonly:
    btns.append(btnhtml('Update', 1))
##    btns.append(btnhtml('Reset',  2))
    if delete: btns.append(btnhtml('Delete', 2))
    btns.append(btnhtml('Cancel', 3))
    btnrow = 5
    if editbtns:
      for btn in editbtns:
        btns.append(btnhtml(btn, btnrow))
        btnrow += 1
      btnrow += 1
    for btn in btnactions:
      if not (btn in ['Add', 'Update', 'Delete'] or btn in editbtns):
        btns.append(btnhtml(btn, btnrow))
        btnrow += 1
  else:
    btns.append(btnhtml('Return', 1))
  return ''.join(btns)


# search, order, next/prev

class DataPage(object):
#======================
  '''Show a SQL table as a sorted list allowing editing.'''

  def __init__(self, table, key, order, title, singular=None,
  #----------------------------------------------------------
               fields=[], tabs=[],
               editbtns={}, btnactions={}, submitacts={},
               pagesize=50, height=0,
               readonly=False, editonly=False, addonly=False,
               updatefields=None, preedit=None,
               validation=None, numerickey=True,
               filter='', refresh=None):
    '''Initialisation.
    table     string  SQL table name
    key       string  Name of key column
    order     string/list   Column name or list of ('col', 'order') tuples; default display order  
    title     string  Heading to display
    singular  string  Singular form of title. If None the drop last character of title string.
    fields    list    Field objects specifying what to display/edit
    tabs      list    List of ('Tab name', [fields]) tuples
    editbtns  dict    Additional editing functions
    btnactions dict   Additional functions for buttons, including standard buttons
    submitacts dict   Additional functions to call upon submission
    pagesize  int     Number of rows of data records on a page
    height    int     Height of form. If 0 use field layout to determine height.
    readonly  bool
    editonly  bool    If True, then no Add nor Delete
    addonly   bool    If True, then Add but no Delete
    updatefields function(post_data) returning dict {name: value} for SQL update and insert
    filter    string  Filter all rows with this condition
    refresh   funct   Call to get seconds between refreshs of list
    preedit    funt   Call after getting database data before building form
    validation funct  Call to validate POST variables
    numerickey boolean Key column is sorted numerically
    '''
    self._table = table
    self._key = key
    if isinstance(order, list):
      self._defsort, self._deforder = self._setorder(order)
    elif order == None:
      self._defsort  = [ key ]
      self._deforder = [ 'asc' ]
    else:
      self._defsort  = [ order ]
      self._deforder = [ 'asc' ]
    self._sort, self._order = ([ key ], [ 'asc' ])
    if title == None: self._title = table.title()
    else:             self._title = title
    self._singular = singular
    self._tabs   = tabs
    if tabs: self._fields = tabs[0][1]
    else:    self._fields = fields
    self._editbtns = { }
    self._btnactions = { }
    for b, a in editbtns.iteritems():
      if   isinstance(a, tuple):
        self._editbtns[b] = a[1]
        self._btnactions[b] = (a[0], None)
      else:
        self._editbtns[b] = a
    if 'Delete' in btnactions:
      if isinstance(btnactions['Delete'], types.FunctionType):
        btnactions['Delete'] = ('Are you sure you want to delete this?', btnactions['Delete'])
    else:
      btnactions['Delete'] = ('Are you sure you want to delete this?', None)
    for b, a in btnactions.iteritems():
      if   isinstance(a, tuple):              self._btnactions[b] =    a
      elif isinstance(a, types.FunctionType): self._btnactions[b] = ('', a)
      else:                                   self._btnactions[b] = (a, None)
    self._submitacts = submitacts
    self._height = height
    self._calcheight()
    self._pagesize = pagesize
    self._readonly = readonly
    if readonly: self._editonly = True
    else:        self._editonly = editonly
    self._delbutton = not (self._editonly or addonly)
    self._updatefldfn = updatefields
    self._preedit = preedit
    self._validation = validation
    self._numerickey = numerickey
    self._filter = filter
    self._refresh = refresh

  def _calcheight(self):
  #---------------------
    self._formheight = self._height if self._height else Field.calcheight(self._fields)

  @staticmethod
  def _setorder(order):
  #--------------------
    s = []
    o = []
    for k in order:
      if isinstance(k, tuple):
        s.append(k[0])
        o.append(k[1])
      else:
        s.append(k)
        o.append('asc')
    return ((s, o))


  def _list(self, session, searchdata=None, order=None, paging=None, rowkey=-1):
  #-----------------------------------------------------------------------------
#    logging.debug('LIST: %s', rowid)

    if order:
      self._sort, self._order = self._setorder(order)

    rownumber = 0
    objname = self._table.title()
    table = [ ]
    if self._refresh and self._refresh(): table.append('<page keypress="pageitems" refresh="%d">' % self._refresh())
    else:                                 table.append('<page keypress="pageitems">')
    table.append(MAINMENU())
    table.append(MESSAGE())
    table.append('<title>Display/Configure ' + self._title + '</title>')
    table.append('<form class="list" action="%s" key="%d">' % (web.ctx.path, rownumber))
    table.append('<table>')
    
    search = False
    searchkey = []
    searchorder = []
    searchfilter = []
    searching = False
    findflds = ['<tr class="search">']

    if self._tabs: self._fields = self._tabs[0][1]
    listfields = [f for f in self._fields
                   if f and f._datacol and f._listview and not f._hidden]

    db = Database()    ###################
    if not searchdata: searchdata = session.get('savedsearch')
    savedsearch = dict()
    for f in listfields:
      if f._findable:
        search = True
        if searchdata: matchdata = searchdata.get(f._colname, '')
        else:          matchdata = ''
        if matchdata and not paging:
          searching = True
          if isinstance(f._choices, tuple):
            searchfilter.append("t.%s='%s'" % (f._colname, matchdata))
          else:
            searchkey.append(matchdata)
            searchorder.append((f._colname, 'asc'))

        findflds.append('<td class="search">')
        if isinstance(f._choices, tuple):
          findflds.append('<select name="%s" size="%d">' % (f._colname, f._headwidth))
          findflds.append(Field.option(('', ''), None))
          sql = 'select ' + f._choices[1] + ', ' + f._choices[2]
          sql += ' from ' + f._choices[0]
          if f._filter:
            if isinstance(f._filter, types.FunctionType): filter = f._filter(None)
            else:                                         filter = f._filter
            sql += ' where ' + filter
          sql += ' order by ' + f._choices[2]
          for row in db.execute(sql): findflds.append(Field.option(tuple(row), matchdata))
          findflds.append('</select>')
          if matchdata: savedsearch[f._colname] = matchdata
        else:
          findflds.append('<field name="%s" size="%d" value="%s"'
                          % (f._colname, f._layout._width, xmlescape(matchdata)))
          if f._validation: findflds.append(" valid='%s'" % f._validation)
          findflds.append('/>')
        findflds.append('</td>')
    if search:
      findflds.append('<td><button name="action" prompt="Find"/></td></tr>')
      table.append(''.join(findflds))
      if len(searchorder):
        self._sort, self._order = self._setorder(searchorder)
    session['savedsearch'] = savedsearch
    
    cols = ['rowid']
    joins = []
    jfields = []
    resultfields = []
    for f in listfields:
      if isinstance(f._choices, tuple):
        joins.append((f._choices[0], f._colname, f._choices[1], f._choices[2]))
        jfields.append(f)
      else:
        cols.append(f._colname)
        resultfields.append(f)
    resultfields.extend(jfields)

    if paging: datapage = session.get('datapage')
    else:      datapage = None

    #logging.debug('DP: %s', str(datapage))
    if not datapage:
      datapage = PagedTable(self._table, cols, primary=self._key,
                            sort=(self._sort, self._order),
                            defsort=(self._defsort, self._deforder),
                            pagesize=self._pagesize, joins=joins,
                            restriction=self._filter,
                            numerickey=self._numerickey)
    self._sort, self._order = datapage.keycols()

    table.append('<tr>')
    for f in listfields:
      dirn = ''
      table.append('<th')
      if f._layout:
        if   f._layout._align == 'R': table.append(' align="right"')
        elif f._layout._align == 'C': table.append(' align="center"')
      if f._colname in self._sort:
        table.append(' class="order"')
        dirn = self._order[self._sort.index(f._colname)]
        if dirn == 'asc': dirn = '&amp;dirn=desc'
        else:             dirn = ''
      else: dirn = ''
      table.append('><btnlink href="?sort=%s%s">%s</btnlink></th>'
                              % (f._colname, dirn, nbspescape(f._prompt)))
    if self._editonly: table.append('<td></td>')
    else:              table.append('<td><btnlink href="?add">Add</btnlink></td>')
    table.append('</tr>')

    if searching: rows = datapage.findpage(db, searchkey, ' and '.join(searchfilter))
    elif paging=='P':  rows = datapage.prevpage(db)
    elif paging=='N':  rows = datapage.nextpage(db)
    else:              rows = datapage.thispage(db)
    if paging and len(rows) == 0: rows = datapage.thispage(db)
    db.close()
    session['datapage'] = datapage

    logging.debug('Result fields: %s', repr(resultfields))    ##

    odd = True
    rowcount = len(rows)
    for row in rows:
      if rowcount > 1 and str(rowkey) == str(row[0]): table.append('<tr class="key">')
      elif odd:                                       table.append('<tr class="odd">')
      else:                                           table.append('<tr>')
      for f in listfields:
        n = resultfields.index(f) + 1
        if row[n] == None: v = ''
        else:              v = cp1252(row[n])
        if f._mapping and f._mapping[0]: v = f._mapping[0](v)
        table.append('<td')
        if f._layout and f._layout._align == 'R': table.append(' align="right"')
        table.append('>' + xmlescape(v) + '</td>')
      if self._readonly: edit = 'Show'
      else:              edit = 'Edit'
      table.append('<td><btnlink href="?edit=%d">%s</btnlink></td></tr>' % (row[0], edit))
      odd = not odd
    table.append('</table></form></page>')
    return ''.join(table)


  def _add(self, post, error=None):
  #--------------------------------
#    logging.debug('%s', log('ADD', 'POST', post))
    form = []
    if error: form.append('<page alert="%s">' % xmlescape(error))
    else:     form.append('<page>')
    form.append(MAINMENU())
    form.append(MESSAGE())
    singular = self._singular if self._singular else self._title[:-1]
    form.append('<title>Add ' + singular + '</title>')

    if self._tabs:
      self._fields = self._tabs[0][1]
      self._calcheight()

    form.append('<form action="%s" width="%d" height="%d">'
                                           % (web.ctx.path, FORMWIDTH, self._formheight))
    form.append('<button name="action" prompt="Add"    row="1" col="%d"/>' % FORMBTNCOL)
    form.append('<button name="action" prompt="Clear"  row="2" col="%d" type="reset"/>' % FORMBTNCOL)
    form.append('<button name="action" prompt="Cancel" row="3" col="%d"/>' % FORMBTNCOL)
    form.append(Field.fieldhtml(self._fields, post, adding=True))
    form.append('</form></page>')
    return ''.join(form)


  def _edit(self, rowid, data=None, error=None, tab=0):
  #----------------------------------------------------
#    logging.debug('EDIT: %s', rowid)
    form = []
    if error: form.append('<page alert="%s">' % xmlescape(error))
    else:     form.append('<page>')
    form.append(MAINMENU())
    form.append(MESSAGE())
    singular = self._singular if self._singular else self._title[:-1]
    form.append('<title>Display/Edit ' + singular + '</title>')

    tab = num(tab)
    if self._tabs:
      form.append('<tabs selected="%d">' % tab)
      for n, t in enumerate(self._tabs):
        form.append('<tab name="%d" prompt="%s" action="?edit=%s"/>' % (n, t[0], rowid))
      form.append('</tabs>')
      self._fields = self._tabs[tab][1]
      self._calcheight()

    form.append('<form action="%s" width="%d" height="%d" key="%s" tab="%d">'
                        % (web.ctx.path, FORMWIDTH, self._formheight, rowid, tab))
    form.append(_editbuttons(self._editbtns if tab==0 else {},
                             self._btnactions if tab==0 else {},
                             self._readonly, self._delbutton and tab == 0))
    if not data: data = Field.fielddata(self._table, self._fields, 'rowid', rowid)
    if self._preedit: self._preedit(data)
    form.append(Field.fieldhtml(self._fields, data, self._key, readonly=self._readonly))
    form.append('</form></page>')
    return ''.join(form)

  @staticmethod
  def _getdata(post, field):
  #-------------------------
    v = cp1252(post.get(field._colname))
    if field._mapping and len(field._mapping) > 1 and field._mapping[1]:
      v = field._mapping[1](v)
    return v

  def _tableinsert(self, db, post):
  #--------------------------------
    sql = 'insert into %s (' % self._table
    updatable = [f for f in self._fields if f and f._datacol and f._layout]
    updateflds = self._updatefldfn(post) if self._updatefldfn else { }
    for f in updatable:
      if not f._colname in updateflds: sql += f._colname + ','
    for n in updateflds.iterkeys(): sql += n + ','
    sql = sql[:-1] + ') values ('
    for f in updatable:
      if not f._colname in updateflds:
        v = self._getdata(post, f)
        if f._colname == self._key and (not v or v == '0'): return ''
        sql += "'%s'," % database.escape(v)
    for v in updateflds.itervalues(): sql += v + ','
    sql = sql[:-1] + ')'
    try:
      db.execute(sql)                          #########
    except IntegrityError:                     #########
      return self._add(post, 'Code already exists')
    except DatabaseError, msg:                 ##########
      return self._add(post, str(msg))
    return ''

  def _tableupdate(self, db, post):
  #--------------------------------
    updateflds = self._updatefldfn(post) if self._updatefldfn else { }
    sql = 'update ' + self._table + ' set'
    for f in self._fields:
      if f and f._colname and f._datacol and f._layout and not f._table and not f.readonly(post):
        if not f._colname in updateflds:
          sql += ' ' + f._colname + "='" + database.escape(self._getdata(post, f)) + "',"
    for n, v in updateflds.iteritems(): sql += ' ' + n + '=' + v + ','
    sql = sql[:-1] + ' where rowid = ?'
###    logging.error("SQL: (%d) %s", int(post['form_key']), sql)
    try:
      db.execute(sql, (post['form_key'],))
      for f in self._fields:
        if f and f._table:
          tdata = { f._table[1]: str(post['%s_%s' % (f._colname, f._table[0])]) }
          for c in f._table[2]:
            if c._colname and c._layout:
              v = str(post[c._colname])
              if c._mapping and c._mapping[1]: v = c._mapping[1](v)
              tdata[c._colname] = v
          db.assign(f._table[0], f._table[1], tdata)

    except IntegrityError:
      return self._edit(post['form_key'], post, 'Code already exists', post['form_tab'])
    except DatabaseError, msg:
      return self._edit(post['form_key'], post, str(msg), post['form_tab'])
    return ''


  def _checkfields(self, post):
  #----------------------------
    for f in self._fields:
      if (f and not f._optional and f._colname and f._datacol
            and f._layout and not f._table and not f.readonly(post)
            and post[f._colname] == ''):
        return 'Please ' + ('select' if f._choices else 'enter') + ' a ' + f._prompt
    return ''


  def _doupdate(self, db, post):
  #-----------------------------
#    logging.debug('%s', log('UPDATE', 'POST', post))
    action = post['action']
    if action == 'Cancel': return ''
    result = ''
    if self._tabs: self._fields = self._tabs[num(post['form_tab'])][1]
    ##if action in ['Add', 'Update', 'Delete']:
    error = self._checkfields(post)
    if not error and self._validation:
      error = self._validation(db, self, post)
      action = post['action']          # Validation code may change action
    if error != '': return (self._add(post, error) if action == 'Add'
                       else self._edit(post['form_key'], post, error, post['form_tab']))
    if   action in self._editbtns:
      if post['form_key']: result = self._tableupdate(db, post)
      if not result: self._editbtns[action](db, self, post)
    elif action == 'Add':
      result = self._tableinsert(db, post)
    elif action == 'Update':
      result = self._tableupdate(db, post)
    elif action == 'Delete':
      sql = 'delete from ' + self._table + ' where rowid = ?'
      db.execute(sql, (post['form_key'],))
    if result == '' and action in self._btnactions:
      action = self._btnactions[action]
      if action[1]: result = action[1](db, self, post)
    if result == '' and action in self._submitacts:
      action = self._submitacts[action]
      if action: result = action(db, self, post)
    return result

  def _update(self, post):
  #-----------------------
    xml = ''
    db = Database()                   #################
    try:
      db.begin()
      xml = self._doupdate(db, post)
    except Exception:
      logging.error('Error updating: %s', traceback.format_exc())
      db.rollback()
      db.close()
      raise
    if xml: db.rollback()     # Had an error
    else:   db.commit()
    db.close()
    return xml


  def show(self, get, post, session):
  #----------------------------------
    logging.debug('GET: %s', repr(get))
    logging.debug('PST: %s', repr(post))
    ##logging.debug('SES: %s', repr(session))
    
    if post.get('action') == 'Find':
      xml = self._list(session, searchdata = post )
    elif post.get('form_op'):
      xml = self._list(session, searchdata = post, paging = post['form_op'] )
    elif 'action' in post:
      xml = self._update(post)
      if xml == '': xml = self._list(session, paging = 'C', rowkey = post['form_key'])
    elif 'add'    in get and not self._editonly:
      xml = self._add(post)
    elif 'edit'   in get:
      xml = self._edit(str(get['edit']), tab=get.get('tab', ''))
    elif 'sort'   in get:
      if get.get('dirn'): dirn = get['dirn']
      else:               dirn = 'asc'
      xml = self._list(session, order = [ (str(get['sort']), dirn) ])
    else:
      xml = self._list(session)

    ##logging.debug('XML: %s', xml)
    return xml



class FormPage(object):
#======================
  '''Edit a data form'''

  def __init__(self, title, fields, data={}, editbtns={}, readonly=False, height=0, message=''):
  #---------------------------------------------------------------------------------------------
    '''Initialisation.
    title     string  Heading to display
    fields    list    Field objects specifying what to display/edit
    data      dict    Initial values for the fields
    editbtns  dict    Additional editing functions
    height    int     Height of form. If 0 use field layout to determine height.
    message   string  Show as alert when page first displayed
    '''
    self._title = title
    self._fields = fields
    self._data = data
    self._editbtns = editbtns
    self._formheight = height if height else Field.calcheight(fields)
    self._readonly = readonly
    self._message = message


  def show(self, get, post, session):
  #----------------------------------
    form = []
    if self._message:
      form.append('<page alert="%s">' % xmlescape(self._message))
      self._message = ''
    else:
      form.append('<page>')
    form.append(MAINMENU())
    form.append(MESSAGE())
    form.append('<title>' + self._title + '</title>')
    form.append('<form action="%s" width="%d" height="%d">'
                        % (web.ctx.path, FORMWIDTH, self._formheight))
    btns = []
    btnrow = 1
    for btn in self._editbtns:
      form.append('<button name="action" prompt="%s" row="%d" col="%d"/>'
                 % (btn, btnrow, FORMBTNCOL))
      btnrow += 1
    form.append(Field.fieldhtml(self._fields, self._data, 0, readonly=self._readonly))
    form.append('</form></page>')
    xml = ''.join(form)
##    logging.debug('XML: %s', xml)
    return xml



class BlankPage(object):
#======================

  def __init__(self, title, content, message=''):
  #----------------------------------------------
    self._title = title
    self._content = content
    self._message = message

  def show(self, get, post, session):
  #----------------------------------
    page = []
    if self._message:
      page.append('<page alert="%s">' % xmlescape(self._message))
      self._message = ''
    else:
      page.append('<page>')
    page.append(MAINMENU())
    page.append(MESSAGE())
    page.append('<title>' + self._title + '</title>')
    page.append(self._content)
    page.append('</page>')
    return ''.join(page)


"""
# edit an item

     <page alert="$error">
      $MENU
      <title>Display/Edit Departments:</title>
      <form action="depts.php" width="46" height="4" key="$rowid">
       <button name="action" prompt="Update" row="1" col="42"/>
       <button name="action" prompt="Delete" row="2" col="42"/>
       <button name="action" prompt="Cancel" row="3" col="42"/>
       $displayfields
      </form>
     </page>

# code to run upon Save(Add)/Update/Delete

"""
