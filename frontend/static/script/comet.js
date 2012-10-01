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


function makeblob(s)      // Make a Blob from a string
/*================*/      // FF 14 will implement Blob(s)
{
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
  return bb.getBlob() ;
  }


function getSignalStream(uri, blockprocess)
/*========================================*/
{
  stream = 'ws://' + window.document.location.host + '/stream/data/' ;
  protocol = 'biosignalml-ssf';
  streamparser = new StreamParser() ;
  streamparser.receiver = blockprocess ;

  if (window.WebSocket) {
    ws = new WebSocket(stream, protocol);
    }
  else if (window.MozWebSocket) {
    ws = MozWebSocket(stream, protocol);
    }
  else {
    alert('WebSocket Not Supported');
    return;
    }
  ws.binaryType = "arraybuffer" ;

  $(window).unload(function() {
    ws.close();
    }) ;

  ws.onerror = function(evt) {
    alert('WebSocket error');
    } ;

  ws.onmessage = function(evt) {
    var data = new Uint8Array(evt.data);
    streamparser.process(data) ;
    } ;

  ws.onopen = function() {
    h = JSON.stringify({uri: uri, start: 0.0, duration: 10.0, dtype: '<f4'}) ;  // Float32Array
    s = '#d1M' + h.length.toString() + h + '0\n##\n' ;
    ws.send(makeblob(s)) ;
    } ;
  }
