/*****************************************************
 *
 *  BioSignalML Management in Python
 *
 *  Copyright (c) 2010  David Brooks
 *
 *  $Id$
 *
 ****************************************************/


var datachanged = false ;

function changed(f)
/*===============*/
{
 datachanged = true ;
 }

function oktoexit(f)
/*================*/
{
  return(!datachanged || confirm("OK to discard changes?")) ;
  }

function resetform(f)
/*=================*/
{
 datachanged = false ;
 }


function getkey(e)
/*==============*/
{
  if (window.event) return(event.keyCode) ;
  else if (e.which) return(e.which) ;
  else              return(null) ;
  }

function controlkey(k)
/*==================*/
{
  switch (k) {
   case 0:
   case 8:
   case 9:
   case 13:
   case 27:
   case null:
    return(true) ;
   default:
    return(false) ;
    }
  }

function validnumber(f, e)
/*======================*/
{
  var c, k ;
  k = getkey(e) ;
  if (controlkey(k)) return(true) ;
  c = String.fromCharCode(k) ;
  return(("0123456789").indexOf(c) > -1) ;
  }

function validdecimal(f, e)
/*=======================*/
{
  var c, k ;
  k = getkey(e) ;
  if (controlkey(k)) return(true) ;
  c = String.fromCharCode(k) ;
  return((("0123456789").indexOf(c) > -1) || (c == '.' && f.value.indexOf('.') < 0)) ;
  }

function validprice(f, e)
/*=====================*/
{
  return validdecimal(f, e) ;
  }

function validyesno(f, e)
/*=====================*/
{
  var c, k ;
  k = getkey(e) ;
  if (controlkey(k)) return(true) ;
  c = String.fromCharCode(k) ;
  return(("yYnN").indexOf(c) > -1) ;
  }


function validmatch(f, e, s)
/*========================*/
{
  var c, k ;
  k = getkey(e) ;
  if (controlkey(k)) return(true) ;
  c = String.fromCharCode(k) ;
  return(s.indexOf(c) > -1) ;
  }


function showitems(op)
/*==================*/
{
  var myform = document.getElementById("form") ;
  myform.form_op.value = op ;
  myform.submit() ;
  }


function pageitems(e)
/*=================*/
{
  var k ;
  k = getkey(e) ;
  if      (k == 33) showitems('P') ;    // PgUp
  else if (k == 34) showitems('N') ;    // PgDn
  }
