/*****************************************************
 *
 *  BioSignalML Management in Python
 *
 *  Copyright (c) 2010  David Brooks
 *
 *  $Id: comet.js,v a82ffb1e85be 2011/02/03 04:16:28 dave $
 *
 ****************************************************/


(function($) {

/*******   $(document).ready(cometInit) ;  DISABLE ***/

  function cometInit() {
    window.setTimeout(cometPoll, 2000) ;
    }

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
        $("#message").html(json.message) ;
        if (json.alert != '') alert(json.alert) ;
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
            $(selectId).html(json.options) ;
            }
          }
        }
    }) ;
  }
