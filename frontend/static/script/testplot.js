var canvas = 0 ;
var timeplot = 0 ;
var mdown = false ;
var btn = -1 ;

var selectregion = new Selection() ;

function coords(element, mevent)
//==============================
{
  return new Point(mevent.pageX - element.offsetLeft,
                   mevent.pageY - element.offsetTop) ;
  }

function mousebutton(element, event, down)
//========================================
{
  if (timeplot == 0) return ;
  mdown = down;
  btn = event.button ;
  var pt = coords(element, event) ;
  if (mdown) timeplot.mouseDown(pt) ;
  else       timeplot.mouseUp(pt) ;
  }

function mousemoved(element, event)
//=================================
{
  if (timeplot == 0) return ;
  if (mdown) {    // select
    var pt = coords(element, event) ;
//  $("#msg").text("Btn " + btn + " at (" + pt.x + ", " + pt.y + ")") ;
    timeplot.mouseMove(pt) ;
    }
  }


function plotresize(width, height)
//================================
{
  if (timeplot != 0) timeplot.resize(width, height) ;
  else if (canvas != 0) {
    canvas[0].width = width ;
    canvas[0].height = height ;
    }
  }


jQuery(document).ready(function()
//===============================
{

  canvas = $("#signal") ;
  if (canvas != 0) {
    canvas.mousedown(function(event) { mousebutton(this, event, true) ; } ) ;
    canvas.mousemove(function(event) { mousemoved(this, event) ; } ) ;
    $(document).mouseup(function(event) { mousebutton(this, event, false) ; })
    }



  $("#plotarea").resize(function() { plotresize($(this).width(), $(this).height()) ; } ) ;


//  $('#plotarea').resizable({ resize: function(evwnt, ui) { plotresize(ui.size.width, ui.size.height) ; } }) ;
  $("#plotarea").resize() ;

  } ) ;



  const POINTS = 501 ;
  var turns = 5 ;
  var data1 = [ ] ;
  var data2 = [ ] ;
  data1.length = POINTS ;
  data2.length = POINTS ;

  for (var i = 0; i < POINTS ;  i++) {
    if (i <= POINTS/2) {
      data1[i] = Math.sin(2.0*i*turns*Math.PI/(POINTS-1))
      data2[i] = Math.cos(2.0*i*turns*Math.PI/(POINTS-1))
      }
    else {
      data1[i] = 0.0 ;
      data2[i] = -0.5 ;
      }
    }

  var sig1 = new Signal("Sig1", "mV", 1.0, 0.0, "#f00",
    new Array(new SignalSegment(10, 0.1, data1))) ;

  var sig2 = new Signal("Sig2", "mV", 1.0, 0.0, "#00f",
    new Array(new SignalSegment(5, 0.02, data2), new SignalSegment(20, 0.1, data1))) ;

  var sig3 = new Signal("Sig3", "mV", 1.0, 0.0, "#077",
    new Array(new SignalSegment(25, 0.001, data2),
              new SignalSegment(20, 0.01, data1),
              new SignalSegment(30, 0.1, data2))) ;

  var signals = new Array( sig1, sig2, sig3 ) ;



/* Need to get a stream of a recording (or multiple signals)

   Could either do an AJAX/Coment request, with parameters in a JSON block
     recording URI
     signal list (or signal URIs)
     sampling rate (which we resample to)
     time interval (wrt recording)

   Or pass parameters as GET or PUT parameters

   Or craft a URI that denotes everything... NO!!

*/

var starttime =   10.0 ;
var duration  =   20.0 ;
var sig0 = "http://devel.biosignalml.org/recording/testX/sinewave/signal/0" ;
var sig1 = "http://devel.biosignalml.org/recording/testX/sinewave/signal/1" ;

var sigs = [ sig0, sig1 ] ;

$(document).ready(function() {

  timeplot = new TimePlot(canvas[0], 0, 100, signals) ;  // ***

      $.ajax({url:  "/comet/stream",
              
              type: "POST",

              data: { signals: [ sig0, sig1],
                      start:     starttime,
                      duration:  duration,
                      rate:      1000,
                    },

              success: plotSignal,
              }) ;
      

//  $(".showsignals").live("click",
//    function() {
//    alert("Click chained...") ;
//      var id = $(this).parents().filter("li")[0].id ;
//      }
//    ) ;


  } ) ;



function plotSignal(data, status, xhr) {
  var signals = [ ]
  signals.length = data.signals.length
  for (var signum = 0 ;  signum < data.signals.length ;  ++signum) {
    var sig = data.signals[signum]
    var segments = [ ]
    segments.length = sig.segments.length
    for (var segnum = 0 ;  segnum < sig.segments.length ;  ++segnum) {
      var seg = sig.segments[segnum]
      segments[segnum] = new SignalSegment(seg.start, seg.period, seg.data)
      }
    signals[signum] = new Signal(sig.label, sig.units,
                                 sig.scale, sig.top, sig.colour,
                                 segments)
    }
  if (canvas != 0) timeplot = new TimePlot(canvas[0], starttime, starttime + duration, signals) ;
  }


