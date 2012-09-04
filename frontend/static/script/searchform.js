/*****************************************************
 *
 *  BioSignalML Management in Python
 *
 *  Copyright (c) 2010-2011  David Brooks
 *
 *  $Id: searchform.js,v 2225129d2f7b 2011/02/04 01:05:15 dave $
 *
 ****************************************************/


var fields      = [ ] ;   // Content sent from server
var group       = null ;  // Set when fields received
var group_relns = null ;


function select_list(prompt, options, nbr) {
 sel = [ '<select>' ] ;
 if (prompt != '') sel.push(' <option value="">' + prompt + '</option>') ;
 for (var i in options) {
  if (nbr) sel.push('  <option value="' + String(Number(i)) + '">' + options[i] + '</option>') ;
  else     sel.push('  <option>'                                   + options[i] + '</option>') ;
  }
 sel.push('</select>') ;
 return $(sel.join('\n')) ;
 }

function type_list() {
 sel = [ '<select>' ] ;
 sel.push(' <option value="">Please select:</option>') ;
 for (var i in fields) {
  sel.push('  <option value="' + String(Number(i)) + '">' + fields[i].prompt + '</option>') ;
  }
 sel.push('</select>') ;
 return $(sel.join('\n'))
 }

function got_type() {
 var fld_index = this.value ; 
 if (fld_index != '') {
  var fld = fields[fld_index] ;
  $(this.nextElementSibling).replaceWith(search_tests(fld).addClass('fld2')) ;
  $(this.nextElementSibling
   .nextElementSibling).replaceWith(search_values(fld).addClass('fld3')) ;
  if ($(this).parent().is('.col2 > .group:last-child')
   && $(this).parent().parent().children('.group').length <= 3) {
    $(this.nextElementSibling
          .nextElementSibling
          .nextElementSibling)
      .replaceWith(
        group_relns.clone()
                   .addClass('fld4')
                   .focus(save_value)) ;
    $('.fld4').change(change_group_reln) ;
    }
  }
 else {
  $(this.nextElementSibling).replaceWith('<span class="fld2"></span>') ;
  $(this.nextElementSibling
   .nextElementSibling).replaceWith('<span class="fld3"></span>') ;
  $(this.nextElementSibling
   .nextElementSibling
   .nextElementSibling).replaceWith('<span class="fld4"></span>') ;
  }
 }

function search_tests(fld) {
 if      (fld.tests.length > 1) {
  return select_list('', fld.tests, true) ;
  }
 else if (fld.tests.length == 1) {
  return $('<span>' + fld.tests[0] + '</span>') ;
  }
 return '' ;
 }

function search_values(fld) {
 if (fld.values.length > 1) {
  return select_list('Select value:', fld.values, false) ;
  }
 else if (fld.tests.length == 1) {
  return $('<input></input>') ;
  }
 return select_list('', fld.values) ;
 }

function save_value() {
 this.savedValue = this.value ;
 }


function change_group_reln() {
 if (this.selectedIndex > 0) {
  // Only if we are the last group...
  if (this.parentNode.nextElementSibling == null) {
    group.clone().insertAfter($(this).parent()) ;
    $('.fld1').change(got_type) ;
    this.firstElementChild.text = "Remove..." ;
    }
  $(this).parent().find('.fld1').children().first().remove() ;
  }
 else {
  $(this).parent().remove() ;
//  if (this.parentNode.nextElementSibling) this.value = this.savedValue ;
//  else                                    this.firstElementChild.text = "Expand..." ;
  }
 }


function get_data() {   // When form is submitted
 var data = { } ;
 $('form > div.search > div.line').each(function(line) {
  $(this).find('.col1 select').each(function(fld) {
    data['L' + line + 'LINE'] = this.value ;
    }) ;
  $(this).find('.col2 .group').each(function(grp) {
   $(this).find('select:not(.fld4), input').each(function(fld) {
    if (fld > 0 && this.value == '') {
     alert('Missing test or search value') ;
     return '' ;
     }
    data['L' + line + 'G' + grp + 'F' + fld] = this.value ;
    }) ;
   $(this).find('select.fld4').each(function(fld) {
    data['L' + line + 'G' + grp + 'TERM'] = this.value ;
    }) ;
   }) ;
  }) ;
 return data ;
 }


function setup_result_click() {
 $('.result').click(function () {
  $('.result').css('background-color', 'white') ;
  $(this).css('background-color', 'blue') ;
  $("div#spinner").html("<img src='./static/img/ajax-loader.gif'>") ;
  $.ajax({
   url: '/comet/search/related',
   type: 'POST',
   data: { 'id': this.id, '_xsrf': getCookie("_xsrf") },
   complete:
    function(response, status) {
     if (status == 'success') {
      var text = response.responseText ;
      if (text != '') {
       var related = JSON.parse(text) ;
       for (n in related.ids)
         $('#' + related.ids[n]).css('background-color', '#88F') ;
       }
      }
     $("div#spinner").html(" ") ;
     }
   }) ;
  } ) ;

 $(".result").mouseover(function () {
   $(this).css('color', '#C00') ;
   } ) ;

 $(".result").mouseout(function () {
   $(this).css('color', '#000') ;
   } ) ;
 }


function enable_cluetips() {
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
                + '&_xsrf=' + getCookie("_xsrf"),
                        },
      ajaxProcess: function(data) {
        return data.html ;
        },
      width: 600
      });
    });
  }


$(document).ready(function() {

 $("div#spinner").html("<img src='./static/img/ajax-loader.gif'>") ;
 $.ajax({
   url: '/comet/search/setup',
   type: 'POST',
   data: { '_xsrf': getCookie("_xsrf") },
   complete:
     function(response, status) {
       if (status == 'success') {
         var text = response.responseText ;
         if (text != '') {
           var data = JSON.parse(text) ;
           fields = data.fields ;
           group = $('<span class="group"></span>')
             .append(type_list().addClass('fld1'))
             .append('<span></span>')
             .append('<span></span>')
             .append('<span></span>') ;
           select_list('', data.relns).appendTo($('div.line > .col1')) ;
           group.clone().prependTo($('div.line > .col2')) ;
           group_relns = select_list('Expand...', data.relns) ;
           $('.fld1').change(got_type) ;

           // Now go through any data sent with HTML <script> (as JSON) and
           // populate...

           // OR have [Search] button make a Comet request (so page doesnt get refreshed...)
           // (and could then send an expression after first validity checking...)

           }
         }
       $("div#spinner").html(" ") ;
       }
   }) ;

 $('button.add').click(function() {
  if ($('div.search div.line').length < 5) {
   $('div.search div.line:first-child').clone(true)
    .insertAfter('div.search div.line:last-child') ;
   $('div.search div.line:last-child > .col2 > span.group').replaceWith(group.clone()) ;
   $('.fld1').change(got_type) ;
   if ($('div.search div.line').length == 5) $(this).hide() ;
   }
  return false ;
  }) ;

 $('button.del').click(function() {
  $(this).parent().parent().remove() ;
  $('button.add').show() ;
  }) ;

 $('form#searchform').submit(function() {
  var searchdata = get_data() ;
  if (searchdata != '') {
   $("div#spinner").html("<img src='./static/img/ajax-loader.gif'>") ;
   searchdata['_xsrf'] = getCookie("_xsrf") ;
   $.ajax({
    url: '/comet/search/query',
    type: 'POST',
    data: searchdata,
    complete:
     function(response, status) {
      if (status == 'success') {
       var text = response.responseText ;
       $('div#searchresults').empty() ;
       if (text != '') {
        var results = JSON.parse(text) ;
        if (results.alert) alert(results.alert) ;
        $('div#searchresults').append(results.html) ;
        enable_cluetips() ;
        }
       }
      setup_result_click() ;
      $("div#spinner").html(" ") ;
      }
    }) ;
   }
  return false ;
  }) ;

 }) ;
