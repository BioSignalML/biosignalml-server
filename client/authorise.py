######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2013  David Brooks
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
######################################################

import sys
import logging

import biosignalml.client.repository as bsmlrepo


if __name__ == '__main__':
#=========================

  logging.getLogger().setLevel('DEBUG')

  if len(sys.argv) < 4:
    print "Usage: %s REPOSITORY_URI USERNAME PASSWORD" % sys.argv[0]
    sys.exit(1)

  try:
    repo = bsmlrepo.RemoteRepository(sys.argv[1], sys.argv[2], sys.argv[3])
    repo.close()
  except Exception, msg:
    sys.exit(str(msg))

  if repo.access_token is None:
    sys.exit('Cannot authenticate with %s' % sys.argv[1])

  print "%s %s %s" % (sys.argv[1], repo.access_token, repo.access_expiry)
