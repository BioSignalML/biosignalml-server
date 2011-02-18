/*****************************************************
 *
 *  BioSignalML Management in Python
 *
 *  Copyright (c) 2010-2011  David Brooks
 *
 *  $Id: searchform.js,v 2225129d2f7b 2011/02/04 01:05:15 dave $
 *
 ****************************************************/


function rename() {
 $('form > div.search > div.line').each(function(line) {
  $(this).find('.col1 select').attr({'name': 'L' + line + 'LINE'}) ;
  $(this).find('.col2 .group').each(function(grp) {
   $(this).find('select:not(.fld4), input').each(function(fld) {
    $(this).attr({'name': 'L' + line + 'G' + grp + 'F' + fld})
    }) ;
   $(this).find('select.fld4').attr({'name': 'L' + line + 'G' + grp + 'TERM' }) ;
   });
  }) ;
 }

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
 if (fld_index >= 0) {
  var fld = fields[fld_index] ;
  $(this.nextElementSibling).replaceWith(search_tests(fld).addClass('fld2')) ;
  $(this.nextElementSibling
   .nextElementSibling).replaceWith(search_values(fld).addClass('fld3')) ;
  if ($(this).parent().is('.col2 > .group:last-child')
   && $(this).parent().parent().children('.group').length <= 3)
   $(this.nextElementSibling
         .nextElementSibling
         .nextElementSibling)
    .replaceWith(
        group_relns.clone()
                   .addClass('fld4')
                   .focus(save_value)
                   .change(change_group_reln)) ;
  }
 else {
  $(this.nextElementSibling).replaceWith('<span class="fld2"></span>') ;
  $(this.nextElementSibling
   .nextElementSibling).replaceWith('<span class="fld3"></span>') ;
  $(this.nextElementSibling
   .nextElementSibling
   .nextElementSibling).replaceWith('<span class="fld4"></span>') ;
  }
 rename() ;
 }

function search_tests(fld) {
 if      (fld.tests.length > 1) {
  return select_list('Select test:', fld.tests, true) ;
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
    this.firstElementChild.text = "Remove..." ;
    }
  $(this).parent().find('.fld1').children().first().remove() ;
  }
 else {
  $(this).parent().next().remove() ;
  if (this.parentNode.nextElementSibling) this.value = this.savedValue ;
  else                                    this.firstElementChild.text = "Expand..." ;
  }
 rename() ;
 }


$(document).ready(function() {

 $.ajax({
   url: '/comet/search/setup',
   type: 'POST',
   complete:
     function(response, status) {
       if (status == 'success') {
         var text = response.responseText ;
         if (text != '') {
           var data = JSON.parse(text) ;
           fields = data.fields ;
           group = $('<span class="group"></span>')
             .append(type_list().addClass('fld1').change(got_type))
             .append('<span></span>')
             .append('<span></span>')
             .append('<span></span>') ;
           select_list('', data.relns).appendTo($('div.line > .col1')) ;
           group.clone().prependTo($('div.line > .col2')) ;
           group_relns = select_list('Expand...', data.relns) ;

           // Now go through any data sent with HTML <script> (as JSON) and
           // populate...

           // OR have [Search] button make a Comet request (so page doesnt get refreshed...)
           // (and could then send an expression after first validity checking...)

           }
         }
       }
   }) ;

 $('button.add').click(function() {
  if ($('div.search div.line').length < 5) {
   $('div.search div.line:first-child').clone(true)
    .insertAfter('div.search div.line:last-child') ;
   $('div.search div.line:last-child > .col2 > span.group').replaceWith(group.clone()) ;
   if ($('div.search div.line').length == 5) $(this).hide() ;
   rename() ;
   }
  return false ;
  }) ;

 $('button.del').click(function() {
  $(this).parent().parent().remove() ;
  $('button.add').show() ;
  rename() ;
  }) ;

 }) ;
