######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id$
#
######################################################

import logging

yscale          = 2.5  # em per row
form_yscale     = 1.5 
extra_form_line = 1   
col_offset      = 1    # Subtract from 'col'
width_scale     = 0.7 


class Button(object):
#====================
  def __init__(self, prompt, col, row):
  #------------------------------------
    self.prompt = prompt
    self.col = col
    self.row = row

class Field(object):
#===================
  def __init__(self, prompt, promptpos, id, fieldpos, length, data='', type=''):
  #-----------------------------------------------------------------------------
    self.prompt = prompt
    self.promptpos = promptpos
    self.id = id
    self.fieldpos = fieldpos
    self.length = length
    self.data = data
    self.type = type

  @classmethod
  def hidden(cls, id, data):
    return cls('', (0, 0), id, (0, 0), 0, data=data, type='hidden')

  @classmethod
  def textarea(cls, prompt, id, width, height, data=''):
    return cls(prompt, (0, 0), id, (width, height), 0, data=data, type='textarea')


def boxsize(handler, cols, rows):
#================================
  a = []
  if cols: a.append('width:%gem' % cols)
  if rows: a.append('height:%gem' % (form_yscale*(rows + extra_form_line)))
  return ' style="%s"' % ';'.join(a)
  
def position(handler, col, row, cls=''):
#=======================================
  #logging.debug('POS: (%s, %s)', col, row)
  attrs = []
  if row or cls:
    c = []
    if row: c.append('fixed')
    if cls: c.append(cls)
    attrs.append(' class="%s"' % ' '.join(c))
  if row or col:
    a = []
    if col: a.append('left:%gem' % (col-col_offset))
    if row: a.append('top:%gem' % (yscale*(row-1)))
    attrs.append(' style="%s"' % ';'.join(a))
  return ''.join(attrs)

def fieldwidth(handler, length):
#===============================
  return width_scale*length
