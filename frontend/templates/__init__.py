import page, tree, form, sparql, search

class Page(page.page):
#=====================
  pass

class Tree(tree.tree):
#=====================
  pass

class Form(form.form):
#=====================
  pass

class SparqlForm(sparql.sparql):
#===============================
  pass

class SearchForm(search.search):
#===============================
  pass


class Button(object):
#====================
  def __init__(self, prompt, row, col):
  #------------------------------------
    self.prompt = prompt
    self.row = row
    self.col = col

class Field(object):
#===================
  def __init__(self, prompt, promptpos, id, fieldpos, length, data='', type='input'):
  #----------------------------------------------------------------------------------
    self.prompt = prompt
    self.promptpos = promptpos
    self.id = id
    self.fieldpos = fieldpos
    self.length = length
    self.data = data
    self.type = type

