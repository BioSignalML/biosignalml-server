python /Users/dave/biosignalml/server/client/authorise.py http://devel.biosignalml.org admin admin

cd /Users/dave/biosignalml/workspace/physiobank/index
grep mitdb/102 mitdb-index  > t
python extract.py devel t
#
python /Users/dave/biosignalml/server/tools/load_hdf5.py http://devel.biosignalml.org /recordings/physiobank/mitdb/102.h5
#
#
curl -H "Content-Type: application/x-bsml+edf" -T /usr/local/database/nifecgdb/ecgca102.edf http://devel.biosignalml.org/physiobank/nifecgdb/ecgca102
curl -H "Content-Type: application/x-bsml+edf" -T /Users/dave/biosignalml/workspace/testdata/sinewave.edf http://devel.biosignalml.org/testdata/sinewave

## Getting file back...
#curl -H "Accept: application/x-bsml+edf" -o ecgca102.edf http://devel.biosignalml.org/physiobank/nifecgdb/ecgca102


###

cd /Users/dave/biosignalml/workspace/cellml/workspaces/dbrooks/gall_2000
python csv2bsml.py -m bursting.ttl bursting.csv http://devel.biosignalml.org/calcium/bursting/data
python csv2bsml.py -m spiking.ttl  spiking.csv  http://devel.biosignalml.org/calcium/spiking/data
#
python gall_2000_bsml.py http://devel.biosignalml.org/calcium/bursting/data/signal/0 http://devel.biosignalml.org/calcium/bursting/output
python gall_2000_bsml.py http://devel.biosignalml.org/calcium/spiking/data/signal/0  http://devel.biosignalml.org/calcium/spiking/output



###

cd /Users/dave/biosignalml/streams/FlowData
python ~/biosignalml/server/tools/delete_recording.py http://devel.biosignalml.org/flow/NZ_Patients/14DAY_DATA/04122921/FLW0001
python ~/biosignalml/streams/flow2bsml/flow2bsml.py http://devel.biosignalml.org/flow NZ_Patients/14DAY_DATA/04122921/FLW0001.FPH
