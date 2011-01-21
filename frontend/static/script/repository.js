$(function () {

  $('a.cluetip').each(function () {  // Enable tooltips on <a> elements

    $(this).attr('rel', '/comet/metadata').cluetip({

      // splitTitle: '|',

      clickThrough: true,

      titleAttribute: 'id',

      ajaxCache: false,   // ####

      ajaxSettings: {
        dataType: 'json',
        type:     'POST',
        data:     'uri=' + $(this).attr('id').toString()
        },

      ajaxProcess: function(data) {
        return data.html ;
        },
    
      width: 600
      });
    });
  });
