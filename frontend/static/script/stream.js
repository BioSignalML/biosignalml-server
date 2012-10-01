/*****************************************************
 *
 *  BioSignalML Implementation
 *
 *  Copyright (c) 2010 - 2012  David Brooks
 *
 ****************************************************/


var STREAM_ENDPOINT = '/stream/data/' ;


function StreamBlock(blockno, type, header, data)
/*=============================================*/
{
  this.blockno = blockno ;
  this.type = type ;
  this.header = header ;
  this.data = data ;
  }


var STREAM = {
  VERSION:   1
  }

var CHAR = {
  LFEED:  0x0A,   // '\n'
  HASH:   0x23,   // '#'
  ZERO:   0x30,   // '0'
  NINE:   0x39,   // '9'
  V:      0x56    // 'V'
  }

var ERROR = {
  NONE:                0,
  UNEXPECTED_TRAILER:  1,
  MISSING_HEADER_LF:   2,
  MISSING_TRAILER:     3,
  INVALID_CHECKSUM:    4,
  MISSING_TRAILER_LF:  5,
  HASH_RESERVED:       6,
  WRITE_EOF:           7,
  VERSION_MISMATCH:    8,
  BAD_JSON_HEADER:     9,
  BAD_FORMAT:         10
  }

var PARSE = {
  RESET:      0,
  TYPE:       1,
  VERSION:    2,
  HDRLEN:     4,
  HEADER:     5,
  DATALEN:    6,
  HDREND:     7,
  CONTENT:    8,
  TRAILER:    9,
  CHECKSUM:  10,
  CHECKDATA: 11,
  BLOCKEND:  12
  }


function makestring(data)
/*=====================*/
{
  s = [ ] ;
  for (var i=0 ; i < data.length ; i++) s.push(String.fromCharCode(data[i])) ;
//print(s.join('')) ;
  return s.join('') ;
  }


function StreamParser()
/*===================*/
{
  this.blockno = -1 ;
  this.version = -1 ;
  this.state = PARSE.RESET ;
  this.error = ERROR.NONE ;
  }

StreamParser.prototype =
/*=====================*/
{
  receiver: function(block) { },

  process: function(data) {
    /**
    Parse data and put stream blocks into the receive queue.

    :param data: A chunk of data.
    :type data: Uint8Array
    */
    var pos = 0 ;
    var datalen = data.byteLength ;

    while (datalen > 0) {
      if      (this.state == PARSE.RESET) {                 // Looking for a block
        while (datalen > 0 && data[pos] != CHAR.HASH) {
          ++pos ;
          --datalen ;
          }
        if (datalen > 0) {
          pos += 1 ;
          datalen -= 1 ;
          this.state = PARSE.TYPE
          }
        }

      else if (this.state == PARSE.TYPE) {                  // Getting block type
        this.type = data[pos] ;
        pos += 1 ;
        datalen -= 1 ;
        if (this.type != CHAR.HASH) {
          this.blockno += 1 ;
          this.version = 0 ;
          this.state = PARSE.VERSION ;
          }
        else
          this.error = ERROR.UNEXPECTED_TRAILER ;
        }

      else if (this.state == PARSE.VERSION) {               // Version number
        while (datalen > 0 && CHAR.ZERO <= data[pos] && data[pos] <= CHAR.NINE) {
          this.version = 10*this.version + (data[pos] - CHAR.ZERO) ;
          pos += 1 ;
          datalen -= 1 ;
          }
        if (datalen > 0) {
          if (data[pos] != CHAR.V)
            this.error = ERROR.BAD_FORMAT ;
          else if (this.version != STREAM.VERSION)
            this.error = ERROR.VERSION_MISMATCH ;
          else {
            pos += 1 ;
            datalen -= 1 ;
            this.length = 0 ;
            this.state = PARSE.HDRLEN ;
            }
          }
        }

      else if (this.state == PARSE.HDRLEN) {                // Getting header length
        while (datalen > 0 && CHAR.ZERO <= data[pos] && data[pos] <= CHAR.NINE) {
          this.length = 10*this.length + (data[pos] - CHAR.ZERO) ;
          pos += 1 ;
          datalen -= 1 ;
          }
        if (datalen > 0) {
          this.jsonhdr = new Uint8Array(this.length) ;
          this.chunkpos = 0 ;
          this.state = PARSE.HEADER ;
          }
        }

      else if (this.state == PARSE.HEADER) {                // Getting header JSON
        while (datalen > 0 && this.length > 0) {
          delta = Math.min(this.length, datalen) ;
          this.jsonhdr.set(data.subarray(pos, pos+delta), this.chunkpos) ;
          pos += delta ;
          datalen -= delta ;
          this.length -= delta ;
          }
        if (this.length == 0) {
          try {
            this.header = JSON.parse(makestring(this.jsonhdr)) ;
            this.length = 0 ;
            this.state = PARSE.DATALEN ;
            }
          catch (e) {
            this.error = ERROR.BAD_JSON_HEADER ;
            }
          }
        }

      else if (this.state == PARSE.DATALEN) {               // Getting content length
        while (datalen > 0 && CHAR.ZERO <= data[pos] && data[pos] <= CHAR.NINE) {
          this.length = 10*this.length + (data[pos] - CHAR.ZERO) ;
          pos += 1 ;
          datalen -= 1 ;
          }
        if (datalen > 0) this.state = PARSE.HDREND ;
        }

      else if (this.state == PARSE.HDREND) {                // Checking header LF
        if (data[pos] == CHAR.LFEED) {
          pos += 1 ;
          datalen -= 1 ;
          this.buffer = new ArrayBuffer(this.length) ;
          this.content = new Uint8Array(this.buffer) ;
          this.chunkpos = 0 ;
          this.state = PARSE.CONTENT ;
          }
        else
          this.error = ERROR.MISSING_HEADER_LF ;
        }

      else if (this.state == PARSE.CONTENT) {               // Getting content
        while (datalen > 0 && this.length > 0) {
          delta = Math.min(this.length, datalen) ;
          this.content.set(data.subarray(pos, pos+delta), this.chunkpos) ;
          this.chunkpos += delta ;
          pos += delta ;
          datalen -= delta ;
          this.length -= delta ;
          }
        if (this.length == 0) {
          this.length = 2 ;     // Two '#' after content
          this.state = PARSE.TRAILER ;
          }
        }

      else if (this.state == PARSE.TRAILER) {               // Getting trailer
        if (data[pos] == CHAR.HASH) {
          pos += 1 ;
          datalen -= 1 ;
          this.length -= 1 ;
          if (this.length == 0) this.state = PARSE.CHECKSUM ;
          }
        else
          this.error = ERROR.MISSING_TRAILER
        }

      else if (this.state == PARSE.CHECKSUM) {              // Checking for checksum
        if (data[pos] != CHAR.LFEED) {
          this.length = 32 ;    // 32 checksum characters (hex digest)
          this.state = PARSE.CHECKDATA ;
          }
        else
          this.state = PARSE.BLOCKEND ;
        //this.checks = [ ] ;
        }

      else if (this.state == PARSE.CHECKDATA) {             // Getting checksum
        while (datalen > 0 && this.length > 0) {
          //this.checks.append(str(data[pos:pos+this.length])) ;
          delta = Math.min(this.length, datalen) ;
          pos += delta ;
          datalen -= delta ;
          this.length -= delta ;
          }
        if (this.length == 0) this.state = PARSE.BLOCKEND ;
        }

      else if (this.state == PARSE.BLOCKEND) {              // Checking for final LF
        if (data[pos] == CHAR.LFEED) {
          pos += 1 ;
          datalen -= 1 ;
          this.state = PARSE.RESET ;

          this.receiver(new StreamBlock(this.blockno, String.fromCharCode(this.type),
                                        this.header, this.buffer)) ;

          }
        else
          this.error = ERROR.MISSING_TRAILER_LF ;
        }

      else {                                                // Unknown state...
        this.state = PARSE.RESET ;
        }

      if (this.error != ERROR.NONE) {
        console.error('Stream parsing error: %d, state=%d', this.error, this.state) ;
        this.error = ERROR.NONE ;
        this.state = PARSE.RESET ;
        }

      }

    }

  }


function hasFullWebSockets()
/*========================*/
{
  if (window.WebSocket) {
    browser = navigator.userAgent || "Unknown" ;
    if (browser.indexOf("Firefox") > -1) {
      i = browser.indexOf("Firefox") ;
      return (parseFloat(browser.substr(i + 8)) >= 11.0) ;
      }
    else if (browser.indexOf("Chrome") > -1) {
      i = browser.indexOf("Chrome") ;
      return (parseFloat(browser.substr(i + 7)) >= 16.0) ;
      }
    else if (browser.indexOf("Safari") > -1) {
      i = browser.indexOf("Version") ;
      return (parseFloat(browser.substr(i + 8)) >= 6.0) ;
      }
    else
      return (browser != "Unknown") ;
    }
  return false ;
  }

function getSignal(uri, processor, start, duration, datatype)
/*=========================================================*/
{
  websocket = 'ws://' + window.document.location.host + STREAM_ENDPOINT ;
  protocol = 'biosignalml-ssf';
  sp = new StreamParser() ;
  sp.receiver = processor ;

  if (hasFullWebSockets()) {
    ws = new WebSocket(websocket, protocol);
    }
  else {
    alert('WebSocket Standard not supported in browser');
    return;
    }
  ws.binaryType = "arraybuffer" ;

  window.onunload = function() {
    ws.close();
    } ;

  ws.onerror = function(evt) {
    alert('WebSocket error');
    } ;

  ws.onmessage = function(evt) {
    var data = new Uint8Array(evt.data);
    sp.process(data) ;
    } ;

  ws.onopen = function() {
    var hdr = {uri: uri } ;
    if (typeof start != 'undefined') {
      hdr.start = start ;
      if (typeof duration != 'undefined') {
        hdr.duration = duration ;
        if (typeof datatype != 'undefined') hdr.dtype = datatype ;
        }
      }
    h = JSON.stringify(hdr) ;
//    s = '#d' + STREAM.VERSION.toString() + 'V'
    var s = '#d1V'
             + h.length.toString() + h
             + '0\n##\n' ;
    ws.send(new Blob([ s ])) ;
//    ws.send(makeblob(s)) ;
    } ;
  }
