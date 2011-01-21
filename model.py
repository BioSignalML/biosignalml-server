######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010  David Brooks
#
#  $Id$
#
######################################################


from bsml import BSML, Recording
from metadata import Uri
from metadata import rdf, rdfs, dct, make_literal
from metadata import model as triplestore


def _recordings(properties):
#==========================
  r = [ (s, [ [ make_literal(t, '') for t in triplestore.get_targets(s, p) ] for p in properties ])
        for s in triplestore.get_sources(rdf.type, BSML.Recording) ]
  r.sort()
  return r

def recordings():
#===============
  return [ Recording.open(r)
             for r in triplestore.get_sources(rdf.type, BSML.Recording) ]


def get_recording(uri):
#=====================
  return Recording.open(Uri(uri))


def signals(recording, properties):
#=================================
  r = [ (s, [ [ make_literal(t, '') for t in triplestore.get_targets(s, p) ]
        for p in properties ])
          for s in triplestore.get_sources(BSML.recording, recording)
            if triplestore.contains((s, rdf.type, BSML.Signal)) ]
  r.sort()
  return r


def signal(sig, properties):
#===========================
  if triplestore.contains((sig, rdf.type, BSML.Signal)):
    r = [ [ make_literal(t, '') for t in triplestore.get_targets(sig, p) ] for p in properties ]
    r.sort()
    return r
  else: return None


if __name__ == '__main__':
#=========================

#   for r, a in recordings((rdfs.label, rdfs.comment, dct.description, BSML.format, dct.source)):
#     print r, [ [ str(n) for n in l ] for l in a ]

##
   for n, rec in enumerate(recordings()):
     print str(rec), rec.get_format()

     if n < 2:
       for sig in rec.signals(): print '  ', str(sig), sig.label

##     for s, l in signals(r, (rdfs.label, )): print s, str(l[0][0])
##     print ''


def sparqltest():
#================
   import RDF

   sparql = """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX bsml: <http://www.biosignalml.org/ontologies/2010/05/biosignalml#>

select ?r, ?s where { ?r ?s bsml:Recording }
order by ?r
limit 2"""

##   q = RDF.SPARQLQuery(sparql)
##   print q.execute(triplestore)

   for r in triplestore.query(sparql):
     for s in r: print r[s]
