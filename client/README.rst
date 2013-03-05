Client Tools
============

This directory contains utilities and example scripts for using a
BioSignalML repository.



Uploading an EDF file:::

  # Creates recording http://sleep.biosignalml.org/edf/examples/swa49
  # Uses extension to determine file type

  curl -H "Transfer-Encoding: chunked"       \
       -H "Content-Type: application/x-bsml" \
       -T ./swa49.edf
       http://devel.biosignalml.org/edf/examples/
  

  # creates recording http://devel.biosignalml.org/my/path/edf_example
  # 
  curl -H "Transfer-Encoding: chunked"           \
       -H "Content-Type: application/x-bsml+edf" \
       -T /path/of/file.edf
       http://devel.biosignalml.org/my/path/edf_example
  

Downloading an EDF file:::

  curl -H "Accept: application/x-bsml+edf" \
       -o downloaded.edf                   \
       http://devel.biosignalml.org/my/path/edf_example
