/*****************************************************
 *
 *  BioSignalML Management in Python
 *
 *  Copyright (c) 2010  David Brooks
 *
 *  $Id: comet.js,v a82ffb1e85be 2011/02/03 04:16:28 dave $
 *
 ****************************************************/


//function StreamData(uri, start, duration)
///*=====================================*/
//{
//
//
//  this.uri = uri ;
//
//
//  this.getData = function(start, duration) {
//
//
//    }
//
//
//  this.got_data = function(hdr, data) { }
//
//
//  }



//plot(sig, window, interval)
// var stream = new StreanData(...) ;
// stream.got_data = function(hdr, data) {
//   // plot data points
//   }


// Rename to stream.js...

function getSignalStream(uri) {

  websocket = 'ws://' + window.document.location.host + '/stream/data/' ;

  protocol = 'biosignalml-ssf';


  if (window.WebSocket) {
    ws = new WebSocket(websocket, protocol);
    }
  else if (window.MozWebSocket) {
    ws = MozWebSocket(websocket, protocol);
    }
  else {
    alert('WebSocket Not Supported');
    return;
    }
  ws.binaryType = "arraybuffer" ;  // or "blob" (default)

  $(window).unload(function() {
    ws.close();
    });

  ws.onerror = function(evt) {
    alert('WebSocket error');
    };

  ws.onmessage = function(evt) {
    var reader = new FileReader();
    reader.onloadend = function(evt) {
      if (evt.target.readyState == FileReader.DONE) { // DONE == 2
        var t = evt.target.result ;
        alert('Read:' + t) ;
        }
      };

    var strdata = new Uint8Array(evt.data);
    var s = toString(strdata) ;
    reader.readAsBinaryString(strdata);
    };

  ws.onopen = function(){
    h = $.toJSON({uri: uri, start: 0.0, duration: 10.0, dtype: 'S1'}) ;  // Float32Array

    s = '#d1M' + h.length.toString() + h + '0\n##\n' ;

    if (window.BlobBuilder) {
      bb = new BlobBuilder() ;
      }
    else if (window.MozBlobBuilder) {
      bb = new MozBlobBuilder() ;     // Replace with Blob in FF 14 ??
      }
    else if (window.WebKitBlobBuilder) {
      bb = new WebKitBlobBuilder() ;
      }
    else if (window.MSBlobBuilder) {
      bb = new MSBlobBuilder() ;
      }
    else {
      alert('BlobBuilder Not Supported');
      return;
      }
    bb.append(s) ;
    b = bb.getBlob() ;
    // var b = Blob(s) ;              // FF 14
    ws.send(b) ;
    //ws.send(s) ;
    } ;
  }


(function($) {

/*******   $(document).ready(cometInit) ;  DISABLE ***/

  $(document).ready(function() {
//var buf = new ArrayBuffer(2);
//var i = new Int16Array(buf);
//i[0] = 1;
//var b = new Int8Array(buf);
//var x = b[0];   // Will be 1 on little end systems <
//var y = b[1];




    getSignalStream('http://example.org/test/xx/sinewave9') ;
    }) ;


  })(jQuery) ;
