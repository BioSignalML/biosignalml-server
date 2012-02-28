/*****************************************************
 *
 *  BioSignalML Management in Python
 *
 *  Copyright (c) 2010  David Brooks
 *
 *  $Id: comet.js,v a82ffb1e85be 2011/02/03 04:16:28 dave $
 *
 ****************************************************/


function getSignalStream(uri) {
  websocket = 'ws://localhost:8088/stream/';
  if (window.WebSocket) {
    ws = new WebSocket(websocket);
    }
  else if (window.MozWebSocket) {
    ws = MozWebSocket(websocket);
    }
  else {
    alert('WebSocket Not Supported');
    return;
    }
  //ws.binaryType = "arraybuffer" ;  // or "blob" (default)

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
    reader.readAsBinaryString(evt.data);
    };
  ws.onopen = function(){
    ws.send($.toJSON({uri: uri,
             start: 0.0,
             end: 10.0
            })) ;
    } ;
  }


(function($) {

/*******   $(document).ready(cometInit) ;  DISABLE ***/

  $(document).ready(function() {
//    getSignalStream('http://ex.org/sig/1') ;
    }) ;

  function cometPoll() {
    $.ajax({ url: '/comet/stream',
             type: 'POST',
//             data: { fieldname: fieldvalue, ... },
             dataType: 'text',
             complete: cometResponse
           }) ;
    }

  function cometResponse(response, status) {
    if (status == 'success') {
      var data = response.responseText ;
      if (data != '') {
        var json = JSON.parse(data) ;
        if (json.alert) alert(json.alert) ;
        $("#message").html(json.message) ;
        }
      }
    else {
      alert('Error ' + String(response.status) + ': ' + response.responseText) ;
      }
    cometInit() ;
    }

  })(jQuery) ;


function setSelection(base, selectId) {
  $.ajax({
    url: '/comet/select',
    type: 'POST',
    data: { 'key': base.name, 'value': base.value },
    dataType: 'text',
    complete:
      function(response, status) {
        if (status == 'success') {
          var data = response.responseText ;
          if (data != '') {
            var json = JSON.parse(data) ;
            if (json.alert) alert(json.alert) ;
            $(selectId).html(json.options) ;
            }
          }
        }
    }) ;
  }
 

