/*****************************************************
 *
 *  BioSignalML Management in Python
 *
 *  Copyright (c) 2010-2011  David Brooks
 *
 *  $Id: searchform.js,v a21580c27867 2011/02/03 21:53:41 dave $
 *
 ****************************************************/


function rename() {
 $('form > div.search > div.line').each(function(line) {
  $(this).find('.col1 select').attr({'name': 'l' + line + 'AND'}) ;
  $(this).find('.col2 .group').each(function(grp) {
   $(this).find('select:not(.fld4), input').each(function(fld) {
    $(this).attr({'name': 'l' + line + 'g' + grp + 'f' + fld})
    }) ;
   $(this).find('select.fld4').attr({'name': 'l' + line + 'OR' + grp}) ;
   });
  }) ;
 }

var fields     = [ ] ;   // Content sent from server
var group      = null ;  // Set when fields received
var or_values  = null ;


function search_types() {
 sel = [ '<select>' ] ;
 sel.push(' <option value="0">Please select:</option>') ;
 for (var i in fields) {
  sel.push('  <option value="' + String(Number(i)+1) + '">Search ' + fields[i].prompt + '</option>') ;
  }
 sel.push('</select>') ;
 return $(sel.join('\n')).addClass('fld1').change(got_type) ;
 }

function got_type() {
 var fld_index = this.value - 1 ; 
 if (fld_index >= 0) {
  var fld = fields[fld_index] ;
  $(this.nextElementSibling).replaceWith(search_relns(fld).addClass('fld2')) ;
  $(this.nextElementSibling
   .nextElementSibling).replaceWith(search_values(fld).addClass('fld3')) ;
  if ($(this).parent().is('.col2 > .group:last-child')
   && $(this).parent().parent().children('.group').length <= 3)
   $(this.nextElementSibling
         .nextElementSibling
         .nextElementSibling)
    .replaceWith(
        or_values.clone()
                 .addClass('fld4')
                 .focus(save_value)
                 .change(change_or)) ;
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

function select_list(prompt, options) {
 sel = [ '<select>' ] ;
 if (prompt != '') sel.push(' <option value="0">' + prompt + '</option>') ;
 for (var i in options) {
  sel.push('  <option value="' + String(Number(i)+1) + '">' + options[i] + '</option>') ;
  }
 sel.push('</select>') ;
 return $(sel.join('\n')) ;
 }

function search_relns(fld) {
 if      (fld.relns.length > 1) {
  return select_list('Select reln:', fld.relns) ;
  }
 else if (fld.relns.length == 1) {
  return $('<span>' + fld.relns[0] + '</span>') ;
  }
 return '' ;
 }

function search_values(fld) {
 if (fld.values.length > 1) {
  return select_list('Select value:', fld.values) ;
  }
 else if (fld.relns.length == 1) {
  return $('<input></input>') ;
  }
 return '' ;
 }

function save_value() {
 this.savedValue = this.value ;
 }


function change_or() {
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
             .append(search_types())
             .append('<span></span>')
             .append('<span></span>')
             .append('<span></span>') ;
           select_list('', data.and).appendTo($('div.line > .col1')) ;
           group.clone().prependTo($('div.line > .col2')) ;
           or_values = select_list('Expand...', data.or) ;
           }
         }
       }
   }) ;

 $('button.add').click(function() {
  $('div.search div.line:first-child').clone(true)
   .insertAfter('div.search div.line:last-child') ;
  $('div.search div.line:last-child > .col2 > span.group').replaceWith(group.clone()) ;
  rename() ;
  return false ;
  }) ;

 $('button.del').click(function() {
  $(this).parent().parent().remove() ;
  rename() ;
  }) ;

 }) ;
