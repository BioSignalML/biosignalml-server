import Cheetah.Template


class Page(Cheetah.Template.Template):
#=====================================

  def __init__(self):
  #------------------
    super(Page, self).__init__(file='templates/page.html')



class Tree(Cheetah.Template.Template):
#=====================================

  def __init__(self):
  #------------------
    super(Tree, self).__init__(file='templates/tree.html')
