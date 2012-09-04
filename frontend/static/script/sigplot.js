var ZOOMCOLOUR   = '#ccf' ;
var SELECTCOLOUR = '#fcf' ;
var BORDERCOLOUR = '#ccf' ;
var SCREENCOLOUR = '#eee' ;


function Point(x, y)
//==================
{
  this.x = x ;
  this.y = y ;
  }


function Selection()
//==================
{
  this.reset() ;
  }

Selection.prototype =
/*=================*/
{
  reset: function() {
    this.start = -1 ;
    this.end = -1 ;
    },

  selected: function() {
    return (this.start >= 0 && this.end >= 0 && this.start != this.end) ;
    },

  setStart: function(start) {
    this.start = start ;
    },

  setEnd: function(end) {
    this.end = end ;
    }
  }


function TimePlot(canvas, start, end, signals)
//============================================
{
  canvas.width = canvas.width ;    // Clear canvas
  this.canvas = canvas ;
  this.width = canvas.width ;
  this.height = canvas.height ;
  this.context = canvas.getContext('2d') ;

  this.timeStart = start ;
  this.timeEnd = end ;
  this.timeScale = (this.timeEnd - this.timeStart)/this.width ;

  this.signalplot = new SignalPlot(this.context, this.width, 0, 0.85*this.height, signals)
  this.timeline = new SignalPlot(this.context, this.width, 0.9*this.height, 0.1*this.height, signals)

  this.reset() ;
  this.clear() ;
  this.plot() ;
  }

TimePlot.prototype =
/*================*/
{
  reset: function() {
    this.timePxStart = 0 ;
    this.timePxEnd = this.width ;
    this.timePxMove = -1 ;
    this.signalStart = this.timeStart ;
    this.signalEnd = this.timeEnd ;
    this.signalScale = this.timeScale ;
    this.selection = new Selection() ;
    },

  clear: function() {
    this.canvas.width = this.width ;
    this.canvas.height = this.height ;
    this.signalplot.clear() ;
    this.timeline.clear() ;
    },

  resize: function(width, height) {
    this.width = width ;
    this.height = height ;
    this.signalplot.resize(width, 0, 0.85*height) ;
    this.timeline.resize(width, 0.9*height, 0.1*height) ;
    this.clear() ;
    this.plot() ;
    },

  zoom: function() {
    if (this.selection.selected()) {
      this.clear() ;

      var selstart = this.selection.start ;
      var selend = this.selection.end ;
      if (selend < selstart) {
        selstart = this.selection.end ;
        selend = this.selection.start ;
        }
      var newstart = this.signalStart + selstart*this.signalScale ;
      var newend   = newstart + (selend - selstart)*this.signalScale ;
      if (newstart != newend) {
        this.timePxStart = (newstart - this.timeStart)/this.timeScale ;
        this.timePxEnd   = (newend - this.timeStart)/this.timeScale ;
        this.signalStart = newstart ;
        this.signalEnd   = newend ;
        this.signalScale = (this.signalEnd - this.signalStart)/this.width ;
        this.showZoom(this.signalStart, this.signalEnd, ZOOMCOLOUR, true) ;
        this.plot() ;
        }
      }
    },

  showZoom: function(start, end, fill, showTimeline) {   // Show selected/zoomed time on timeline...
    this.context.fillStyle = fill ;
    if (this.signalScale != this.timeScale) {
      this.context.beginPath() ;
      this.context.moveTo((start-this.signalStart)/this.signalScale, this.signalplot.bottom) ;
      this.context.lineTo((end-this.signalStart)/this.signalScale, this.signalplot.bottom) ;
      this.context.lineTo((end-this.timeStart)/this.timeScale, this.timeline.top) ;
      this.context.lineTo((start-this.timeStart)/this.timeScale, this.timeline.top) ;
      this.context.lineTo((start-this.signalStart)/this.signalScale, this.signalplot.bottom) ;
      this.context.fill() ;
      this.context.closePath() ;

      this.context.beginPath() ;
      this.context.rect((start-this.timeStart)/this.timeScale,
                        this.timeline.top,
                        (end - start)/this.timeScale,
                        this.timeline.height) ;
      this.context.fill() ;
      this.context.closePath() ;
      }
    else if (showTimeline) {
      this.context.beginPath() ;
      this.context.rect(start/this.timeScale, this.timeline.top,
                        (end - start)/this.timeScale,
                        this.timeline.height) ;
      this.context.fill() ;
      this.context.closePath() ;
      }
    },

  select: function() {
    if (this.selection.selected()) {
      this.context.fillStyle   = SELECTCOLOUR ;

      var selwidth = this.selection.end - this.selection.start ;
      this.context.beginPath() ;
      this.context.rect(this.selection.start, this.signalplot.top,
                        selwidth,             this.signalplot.height) ;
      this.context.fill() ;
      this.context.closePath() ;

      this.showZoom(this.signalStart, this.signalEnd, ZOOMCOLOUR, false) ;
      this.showZoom(this.signalStart + this.selection.start*this.signalScale,
                    this.signalStart + this.selection.end*this.signalScale, SELECTCOLOUR, true) ;
      }
    },

   plotZoom: function() {
     this.clear() ;
     this.showZoom(this.signalStart, this.signalEnd, ZOOMCOLOUR, true) ;
     this.plot() ;
     },

  mouseDown: function(point) {
//    log("Mouse down: (" + point.x ", " + point.y + ")") ;
    if (point.y <= this.signalplot.bottom) {
      this.selection.setStart(point.x) ;
      }
    else if (point.y >= this.timeline.top) {
      if (point.x >= 0 && point.x < this.width) {
// Either move or expand/change selection
// Is x inside, outside, or on boundary?
// And change cursor shape if on boundary??
// also to Hand if inside???
        if (point.x < this.timePxStart) {
          this.signalStart += (point.x - this.timePxStart)*this.timeScale ;
          this.timePxStart = point.x ;
          this.plotZoom() ;
          }
        else if (point.x > this.timePxEnd) {
          this.signalEnd += (point.x - this.timePxEnd)*this.timeScale ;
          this.timePxEnd = point.x ;
          this.plotZoom() ;
          }
        else {
          this.timePxMove = point.x ;
          }
        }
/* *** But we never see a click outside canvas...
      else if (point.x < 0) {
        this.signalStart = this.timeStart ;
        this.timePxStart = 0 ;
        this.plotZoom() ;
        }
      else if (point.x < this.width) {
        this.signalEnd = this.timeEnd ;
        this.timePxEnd = this.width ;
        this.plotZoom() ;
        }
**/
      }
    else {     // In band between plot and timeline
// Have a Reset button...
      this.reset() ;
      this.clear() ;
      this.plot() ;
      } ;
    },

  mouseMove: function(point) {
    if (this.selection.start > -1) {
      this.selection.setEnd(point.x) ;
      this.clear() ;
      this.select() ;
      this.plot() ;
      }
    else if (point.y >= this.timeline.top && this.timePxMove >= 0) {
// Limit delta s.th. signalStart >= timeStart and signalEnd <= timeEnd ????
      delta = point.x - this.timePxMove ;
      this.timePxMove = point.x ;
      if      ((this.timePxStart + delta) < 0)          delta = -this.timePxStart ;
      else if ((this.timePxEnd   + delta) > this.width) delta = this.width - this.timePxEnd ;
      if (delta != 0) {
        this.timePxStart += delta ;
        this.timePxEnd   += delta ;
        this.signalStart += delta*this.timeScale ;
        this.signalEnd   += delta*this.timeScale ;
        this.plotZoom() ;
        }

      }
    },

  mouseUp: function(point) {
    this.zoom() ;
    this.selection.reset() ;
    },

  plot: function() {
    this.signalplot.plot(this.signalStart, this.signalEnd) ;
    this.timeline.plot(this.timeStart, this.timeEnd) ;
    }

  }


function SignalPlot(context, width, offset, height, signals)
//==========================================================
{
  this.context = context ;
  this.width = width ;
  this.top = offset ;
  this.bottom = offset + height ;
  this.height = height ;
  this.signals = signals ;
  this.nsignals = signals.length ;
  }

SignalPlot.prototype =
/*==================*/
{
  clear: function() {
    this.context.beginPath() ;
    this.context.rect(0, this.top, this.width, this.height) ;
    this.context.fillStyle = SCREENCOLOUR ;
    this.context.fill() ;
    this.context.strokeStyle = BORDERCOLOUR ;
    this.context.lineWidth = 1 ;
    this.context.stroke() ;
    this.context.closePath() ;
    },

  resize: function(width, offset, height) {
    this.width = width ;
    this.height = height ;
    this.top = offset ;
    this.bottom = offset + height ;
    },

  plot: function(start, end) {
    this.context.save() ;
    this.context.translate(0.0, this.top) ;
    this.context.scale(this.width/(end - start), -this.height/2.0) ;
    this.context.translate(-start, -1.0) ;
    for (var signum = 0 ;  signum < this.nsignals ;  ++ signum) {
      this.context.save() ;
      this.context.translate(0.0, 1.0 - (1.0 + 2.0*signum)/this.nsignals) ;
      this.context.scale(1.0, 1.0/this.nsignals) ;
      this.signals[signum].plot(this.context, start, end) ;
      this.context.restore() ;
      }
    this.context.restore() ;
    }

  }


function Signal(name, units, scale, offset, colour, segments)
//===========================================================
{
  this.label = name ;
  this.units = units ;
  this.scale = scale ;
  this.top = offset ;
  this.colour = colour ;
  this.segments = segments ;
  }

Signal.prototype =
/*==============*/
{
  plot: function(context, start, end) {
//log("Plot: " + this.label) ;
    for (var segnum = 0 ;  segnum < this.segments.length ;  ++segnum) {
// Safari doesn't like 'for each'
      this.segments[segnum].plot(context, start, end, this.colour) ;
      }
    }
  }

/**
 * Creates a segment of a signal.
 *
 * @constructor
 * @this {SignalSegment}
 * @param {number} start The start time of the segment.
 * @param {number} period The segment's duration.
 * @param {array} data The data points the segment.
 */
function SignalSegment(start, period, data)
//=========================================
{
  this.start = start ;
  this.period = period ;
  this.data = data ;
  }

SignalSegment.prototype =
/*=====================*/
{
  plot: function(context, start, end, colour) {
    var segend = this.start + this.period * this.data.length
    if (start <= segend && this.start <= end) {
      if (start < this.start) start = this.start ;
      if (end > segend) end = segend ;
      var firstpoint = Math.floor((start - this.start)/this.period) - 1 ;
      if (firstpoint < 0) firstpoint = 0 ;
      var lastpoint = Math.ceil((end - this.start)/this.period) + 1 ;
      if (lastpoint > this.data.length) lastpoint = this.data.length ;
      var t = start ;

      context.beginPath()
      context.moveTo(t, this.data[firstpoint]) ;
      for (var i = firstpoint + 1 ;  i < lastpoint ;  ++i) {
        t += this.period ;
        context.lineTo(t, this.data[i]) ;
        }
      context.save() ;
      context.setTransform(1, 0, 0, 1, 0, 0) ;
      context.strokeStyle = colour ;
      context.lineWidth = 1 ;
      context.stroke() ;
      context.restore() ;

      context.closePath() ;
      }
    }
  }
