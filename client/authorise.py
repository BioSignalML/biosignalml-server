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
import urllib
import httplib2

import biosignalml.client as client


if __name__ == '__main__':
#=========================

  if len(sys.argv) < 3:
    print "Usage: %s REPOSITORY_URI USERNAME PASSWORD" % sys.argv[0]
    sys.exit(1)

  repository = sys.argv[1]
  remote = httplib2.Http()
  try:
    response, token = remote.request(repository + '/frontend/login', method='POST',
      body=urllib.urlencode({'action': 'Token', 'username': sys.argv[2], 'password': sys.argv[3]}),
      headers={'Content-type': 'application/x-www-form-urlencoded'})
  except Exception, msg:
    sys.exit(str(msg))
  if response.status != 200:
    sys.exit('Cannot obtain token -- unauthorised?')

  client.Repository.save_token(repository, token)
  print "%s %s" % (repository, token)
