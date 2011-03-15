## Partially based on Tools/scripts/dutree.py from Python sources.



def maketree(nodes, prefix):
#===========================
  namestart = len(prefix) + 1
  tree = {}
  for node in nodes:
    path = str(node.uri)[namestart:]
    components = path.split('/')
    if components[0] == '':  components[0] = '/'
    if components[-1] == '': del components[-1]
    else:                    components[-1] = (components[-1], path, node)
    tree = addpath(components, tree)
  return sort(tree)


def addpath(c, t):
#=================
  if c == []:  return t
  if c[0] not in t: t[c[0]] = {}
  t1 = t[c[0]]
  t[c[0]] = addpath(c[1:], t1)
  return t

def _text(k):
#============
  if isinstance(k, tuple): return _text(k[0])
  else:                    return str(k)  

def sort(t):
#===========
  if t == { }: return [ ]
  return sorted([ (k, sort(v)) for k, v in t.iteritems() ],
                cmp=lambda x,y: cmp(_text(x).lower(), _text(y).lower()))



if __name__ == '__main__':
#=========================

  def test(l):
  #-----------
    print l
    print '-->', maketree(l)
    print ''

  test([ "a"])
  test([ "a", "b/c"])
  test([ "a/b", "a", "a/c", "d" ])
  test([ "a/r1",   "a/b/r2",   "a/b/r3",   "d/r4",   "r0", ])

"""
  [ ('a',  [ ('b',  [ ('r2', [ ]),
                      ('r3', [ ])
                    ] ),
             ('r1', [ ])
           ] ),

    ('d',  [ ('r4', [ ]) ]),
    
    ('r0', [ ])
     
  ]



 <li>a
  <li>b
   <li>r2</li>
   <li>r3</li>
  </li>
  <li>r1</li>
 </li>
 <li>d
  <li>r4</li>
 </li>
 <li>r0</li>


<ul>
 <li>a
  <li>b
   <li>r2</li>
   <li>r3</li>
  </li>
  <l1>r1</l1>
 </li>
 <li>d
  <li>r4</li>
 </li>
 <li>r0</li>
</ul>

"""
