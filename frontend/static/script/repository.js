function getCookie(name) {
  var r = document.cookie.match("\\b" + name + "=([^;]*)\\b") ;
  return r ? r[1] : undefined ;
  }

$(function () {
  $('a.cluetip').each(function () {  // Enable tooltips on <a> elements
    $(this).attr('rel', '/frontend/metadata').cluetip({
      // splitTitle: '|',
      clickThrough: true,
      titleAttribute: 'href',
//    ajaxCache: false,   // ####
      ajaxSettings: {
        dataType: 'json',
        type:     'POST',
        data:     'uri=' + $(this).attr('href').toString()
                + '&_xsrf=' + getCookie("_xsrf"),
        },
      ajaxProcess: function(data) {
        return data.html ;
        },
      width: 600
      });
    });
  });
