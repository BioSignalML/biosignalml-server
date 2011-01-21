######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id$
#
######################################################


import sys, logging
import types

from utils import cp1252, num, xmlescape
from database import Database


class Layout(object):
  '''Size and position of a data field.'''
  def __init__(self, width, row, cols, height=1, align='L'):
    self._row    = row
    self._cols   = cols             # (prompt, field, helptext)
    self._width  = width
    self._height = height
    self._align  = align


class Field(object):
  '''Specify data to display and edit.'''
  def __init__(self, name, prompt=None, updname=None, helptext=None,
                layout=None, mapping=None, choices=None, filter=None, find=False,
                listview=True, valid=None, control=None, params=None, readonly=False,
                table=None, password=False, hidden=False, datacol=True, headwidth=0,
                optional=False, script=None):
    """Initialisation.
    name        string   SQL column
    prompt      string   Edit field prompt, if different to SQL name.title()
    updname     string   Name of field in HTML when DataPage's 'updatefields()'
                         is used to return value. If set then SQL value is in
                         a hidden field (with column's name).
    helptext    string   Explanatory text for data entry
    headwidth   int      Width of header selection box. Default to layout._width
    layout      Layout   (width, row, cols, height, tab)
    mapping     tuple    Conversion functions - (data2display(), display2data())
    choices     tuple    Validation table ('table', 'key', 'text')
                list     List of values
    filter      string   Selection condition to apply to choices validation table
    find        boolean  Show search box at top of list column
    listview    boolean  Include data in list view
    valid       string   Javascript validation code/function
    control     string   Name of JQuery widget to use for input
    params      string   Any parameters for widget
    readonly    boolean  The field can not be changed
    table       tuple    Secondary data table ('table', 'key', 'text')
    password    boolean  Typed characters are masked.
    hidden      boolean  Field is hidden
    datacol     boolean  Field data comes from database table
    optional    boolean  Field doesn't require a value
    script      string   Javascript to attach to an input field
    """
    self._colname = name
    if prompt == None: self._prompt = name.title()
    else:              self._prompt = prompt
    self._updname  = updname
    self._helptext = helptext
    self._headwidth = (headwidth if headwidth
                 else layout._width if layout
                 else 0)
    self._layout   = layout
    self._mapping  = mapping        # (data2display, display2data)
    self._listview = listview
    self._choices  = choices
    self._filter   = filter
    self._table    = table
    self._validation = valid
    self._control  = control
    self._params   = params
    self._findable = find
    self._readonly = readonly
    self._password = password
    self._hidden   = hidden
    self._datacol  = datacol
    self._optional = optional
    self._script   = script

  @staticmethod
  def calcheight(fields):
    height = 4                  # Minimum height
    for f in fields:
      if f and f._layout:
        lastrow = f._layout._row + f._layout._height - 1
        if lastrow > height: height = lastrow
      elif f and f._table:
        for g in f._table[2]:
          if g._layout:
            lastrow = g._layout._row + g._layout._height - 1
            if lastrow > height: height = lastrow
    return height


  @staticmethod
  def fielddata(table, fields, keycol, keydata):
    datafields = [f for f in fields
                    if f and f._colname and f._datacol and (f._layout or f._table)]
    sql = 'select rowid'
    for f in datafields: sql += ', ' + f._colname
    sql += " from %s where %s='%s' limit 1" % (table, keycol, str(keydata))
    db = Database()
    data = { }
    for row in db.execute(sql):
      data = { 'rowid': row[0] }
      n = 0
      for f in datafields:
        n += 1
        if row[n] == None: v = ''
        else:              v = cp1252(row[n])
        if f._updname == None: fldname = f._colname
        else:
          data[f._colname] = v
          fldname = f._updname
        if f._mapping and f._mapping[0]: data[fldname] = cp1252(f._mapping[0](v))
        else:                            data[fldname] = v
    db.close()
    return data


  @staticmethod
  def option(codevalue, fieldvalue):  
    code = str(codevalue[0])
    opt = "<option value='%s'" % code
    if fieldvalue == code: opt += " selected='yes'"
    opt += '>%s</option>' % xmlescape(cp1252(codevalue[1]))
    return opt


  @staticmethod
  def getvalue(d, n):
    v = d.get(n, '')
    return v if v else ''

  def readonly(self, data):
    if isinstance(self._readonly, types.FunctionType): return self._readonly(data)
    else:                                              return self._readonly


  @staticmethod
  def fieldhtml(fields, data, keyfield='', readonly=False, adding=False):

    html = []
    script = []

    def rowcols(f):
      if f._layout: return(10000*f._layout._row + f._layout._cols[1])  # (row, fcol) order
      else:         return sys.maxint

    for f in sorted([f for f in fields if f and (f._layout or f._table or f._hidden)], key=rowcols):
      if f._script: script.append('%s' % xmlescape(f._script))
      if f._hidden:
        html.append('<field name="%s" type="hidden" value="%s"/>'
                    % (f._colname, xmlescape(Field.getvalue(data, f._colname))))
        continue
      l = f._layout
      if f._updname == None: fieldname = f._colname
      else:
        html.append('<field name="%s" type="hidden" value="%s"/>'
                    % (f._colname, xmlescape(Field.getvalue(data, f._colname))))
        fieldname = f._updname
      fieldvalue = cp1252(Field.getvalue(data, fieldname))
      if f._choices:
        if not adding and (readonly or f.readonly(data)):
          if fieldvalue != '':
            html.append('<field name="%s" type="hidden" value="%s"/>'
                        % (fieldname, xmlescape(fieldvalue)))
            fieldname = 'ro_select_%s' % fieldname
            if   isinstance(f._choices, tuple):
              sql = "select %s from %s where %s='%s' limit 1" % (f._choices[2], f._choices[0], f._choices[1], fieldvalue)
              db = Database()
              for row in db.execute(sql): fieldvalue = str(row[0])
              db.close()
            elif isinstance(f._choices, list):
              for c in f._choices:
                if isinstance(c, tuple) and len(c) > 1:
                  if str(c[0]) == fieldvalue:
                    fieldvalue = cp1252(c[1])
                    break
                elif str(c) == fieldvalue:
                  break
# Now fall through to standard field with update='no'

        else:
          html.append('<select name="%s" prompt="%s" row="%d" pcol="%d" fcol="%d" size="%d"'
                     % (fieldname, xmlescape(f._prompt),
                                                    l._row, l._cols[0], l._cols[1], l._width))
          if f._helptext:
            html.append(' help="%s"' % xmlescape(f._helptext))
            if len(l._cols) > 2: html.append(' hcol="%d"' % l._cols[2])
          html.append('>' + Field.option(('', ''), fieldvalue))
          if   isinstance(f._choices, tuple):
            sql = 'select ' + f._choices[1] + ', ' + f._choices[2]
            sql += ' from ' + f._choices[0]
            if isinstance(f._filter, types.FunctionType): filter = f._filter(data)
            else:                                         filter = f._filter
            if filter: sql += ' where ' + filter
            sql += ' order by ' + f._choices[2]
            db = Database()
            for row in db.execute(sql): html.append(Field.option(tuple(row), fieldvalue))
            db.close()
          elif isinstance(f._choices, list):
            for c in f._choices:
              if isinstance(c, tuple) and len(c) > 1: html.append(Field.option(c, fieldvalue))
              else:                                   html.append(Field.option((c, c), fieldvalue))
          html.append('</select>')
          continue

      elif f._table and fieldvalue != '':
        sqltable = f._table[0]
        html.append('<field name="%s_%s" type="hidden" value="%s"/>' % (fieldname, sqltable, xmlescape(fieldvalue)))
        tdata = Field.fielddata(sqltable, f._table[2], f._table[1], fieldvalue)
        html.append(Field.fieldhtml(f._table[2], tdata, keyfield=keyfield, readonly=readonly))
        continue

# Fall through to here for readonly choice
      html.append('<field name="%s" prompt="%s" row="%d" pcol="%d" fcol="%d"'
                 % (fieldname, xmlescape(f._prompt), l._row, l._cols[0], l._cols[1]))
      if f._password: html.append(' type="password"')
      if fieldvalue != '': html.append(' value="%s"' % xmlescape(fieldvalue))
      if l._height == 1:
        html.append(' size="%d"' % l._width)
        if f._helptext:
          html.append(' help="%s"' % xmlescape(f._helptext))
          if len(l._cols) > 2: html.append(' hcol="%d"' % l._cols[2])
      else:
        html.append(' type="text" cols="%d" rows="%d"' % (l._width, l._height))
      if (not adding and (readonly or f.readonly(data) or fieldname == keyfield)):
        html.append(" update='no'")
      if f._validation: html.append(" valid='%s'" % f._validation)
      if f._control: html.append(" control='%s'" % f._control)
      if f._params: html.append(" params='%s'" % f._params)
      html.append('/>')

    if script: html.append('<script>%s</script>' % '\n'.join(script))
#    logging.error('HTML: %s', ''.join(html))
    return ''.join(html)

