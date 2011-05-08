$(function () {

  $('a.cluetip').each(function () {  // Enable tooltips on <a> elements

    $(this).attr('rel', '/comet/metadata').cluetip({

      // splitTitle: '|',

      clickThrough: true,

      titleAttribute: 'uri',

      ajaxCache: false,   // ####

      ajaxSettings: {
        dataType: 'json',
        type:     'POST',
        data:     'uri=' + $(this).attr('uri').toString()
        },

      ajaxProcess: function(data) {
        return data.html ;
        },
    
      width: 600
      });
    });
  });
