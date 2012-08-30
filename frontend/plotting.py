import math
from collections import OrderedDict

import numpy as np
import matplotlib.pyplot as plt


from biosignalml import data



def hideticklines(axis):
#=======================
  for tl in axis.get_ticklines(): tl.set_visible(False)
  for tl in axis.get_ticklines(minor=True): tl.set_visible(False)


def testplot():
#==============

  f  = plt.figure()
  a = f.add_axes([0.05, 0.05, 0.9, 0.9])
  a.xaxis.set_visible(False)
  a.yaxis.set_visible(False)
  #a.set_axis_off()

  a1 = f.add_axes([0.05, 0.05, 0.9, 0.3], frame_on=False)
  a2 = f.add_axes([0.05, 0.35, 0.9, 0.3], sharex=a1, frame_on=False)
  a3 = f.add_axes([0.05, 0.65, 0.9, 0.3], sharex=a1, frame_on=False)

  t = np.arange(0, 2.01, 0.01)
  s = np.cos(6*np.pi*t)
  a1.plot(t, s)

  ts = data.UniformTimeSeries(np.random.rand(1000), rate=500)

  a2.plot(ts.times, ts.data)
  a3.plot(ts.times, ts.data)

#  a1.set_xlim(0, 10)
#  a1.set_ylim(-1, 1)

  a1.set_xticks(np.arange(0, 2.1, 0.1), minor=True)

  hideticklines(a1.xaxis)
  hideticklines(a1.yaxis)
  a1.get_yticklabels()[-1].set_visible(False)
  a1.grid(True, which='both', color='r')

  for tl in a2.get_xticklabels(): tl.set_visible(False)
  hideticklines(a2.xaxis)
  hideticklines(a2.yaxis)
  a2.grid(True, which='both', color='r')

  a2.get_yticklabels()[0].set_visible(False)
  a2.get_yticklabels()[-1].set_visible(False)

  for tl in a3.get_xticklabels(): tl.set_visible(False)
  hideticklines(a3.xaxis)
  hideticklines(a3.yaxis)
  for tl in a3.get_yticklines(): tl.set_visible(False)
  a3.get_yticklabels()[0].set_visible(False)
  a3.grid(True, which='both', color='r')

  plt.show()



def gridspacing(w):
#==================
  """
  Calculate spacing of major and minor grid points.
  
  Major spacing is selected to be either 1, 2, or 5, multipled by
  a power of ten; minor spacing is respectively 0.2, 0.5 or 1.0.

  Spacing is chosen so that around 10 major grid points span the
  interval.

  :param w: The width of the interval.
  :return: A tuple with (major, minor) spacing.
  """
  l = math.log10(w)
  f = math.floor(l)
  x = l - f     # Normalised between 0.0 and 1.0
  scale = math.pow(10.0, f)
  if   x < 0.15: return ( 1*scale/10, 0.02*scale)  # The '/10' appears to
  elif x < 0.50: return ( 2*scale/10, 0.05*scale)  # minimise rounding errors
  elif x < 0.85: return ( 5*scale/10, 0.10*scale)
  else:          return (10*scale/10, 0.20*scale)


class Chart(object):
#===================

  leftmargin   = 0.05   # In figure units [0, 1]
  bottommargin = 0.10
  plotwidth  = 250/25.4      # millimetres
  plotheight =  50/25.4      # Of a single plot

  width  = 1.0 - 2.0*leftmargin
  height = 1.0 - 2.0*bottommargin

  def __init__(self, **kwds):
  #--------------------------
    self._figure = plt.figure(**kwds)
    self._axes = self._figure.add_axes([Chart.leftmargin, Chart.bottommargin,
                                        Chart.width,      Chart.height],
                                        zorder=-99)
    self._axes.tick_params(axis='x', labelsize='xx-small')
    self._axes.set_ylim(0.0, 1.0)
    self._axes.yaxis.set_visible(False)
    self._plots = OrderedDict()

  def plot(self, label, segment):
  #------------------------------
    n = len(self._plots) + 1
    if label in self._plots:
      ax = self._plots[label]
      x0, xN = ax.get_xlim()
      if x0 > segment.times[0]:  x0 = segment.times[0]
      if xN < segment.times[-1]: xN = segment.times[-1]
    else:
      ax = self._figure.add_axes([Chart.leftmargin, Chart.bottommargin,
                                  Chart.width,      Chart.height/n],
                                  label=label, frame_on=False,
                                  visible=False, sharex=self._axes)

      ax.text(-0.05, 0.5, label, transform = ax.transAxes)
      self._plots[label] = ax
      x0 = segment.times[0]
      xN = segment.times[-1]
    ax.xaxis.set_visible(False)
    ax.tick_params(axis='y', labelsize='xx-small')
    ax.set_xlim(x0, xN)
    ax.plot(segment.times, segment.data, zorder=99, color='b')
    ax.yaxis.grid(color='r', lw=0.5, ls='-', zorder=-99)
    hideticklines(ax.yaxis)


  def mark(self, time, symbol='', position=0.5):
  #---------------------------------------------
    self._axes.axvline(time, ymax=0.48, color='g')  # ymax/ymin depend on symbol height
    self._axes.axvline(time, ymin=0.56, color='g')
    self._axes.text(time, position, symbol, color='g')


  def draw(self):
  #--------------
    if self._plots:
      nplots = len(self._plots)
      self._figure.set_size_inches(Chart.plotwidth/Chart.width,
                                   nplots*Chart.plotheight/Chart.height,
                                   forward=True)
      t0 = None
      tN = None
      plotheight = Chart.height/nplots
      for n, ax in enumerate(self._plots.values()):
        m = nplots - n - 1
        ax.set_position([Chart.leftmargin, Chart.bottommargin + m*plotheight,
                         Chart.width,      plotheight])
        ax.set_visible(True)
        if m > 0: ax.get_yticklabels()[0].set_visible(False)
        if m < len(self._plots) - 1: ax.get_yticklabels()[-1].set_visible(False)
        x0, xN = ax.get_xlim()
        if t0 is None or t0 > x0: t0 = x0
        if tN is None or tN < xN: tN = xN

      if t0 is not None:
        grid = gridspacing(tN - t0)
        g0 = grid[0]*math.floor(t0/grid[0])
        gN = grid[0]*math.ceil(tN/grid[0])
        self._axes.set_xlim(g0, gN)
        self._axes.set_xticks(np.arange(g0, gN+grid[0], grid[0]))
        self._axes.set_xticks(np.arange(g0, gN+grid[1], grid[1]), minor=True)
        hideticklines(self._axes.xaxis)
        self._axes.xaxis.grid(which='minor', color='r')
        self._axes.xaxis.grid(which='major', color='r', ls='-')


#========================================================

import sys

import wfdb  # To get annotation texts

import biosignalml.formats.hdf5 as hdf5


def plotchart(record, start, duration):
#======================================
  rec = hdf5.HDF5Recording.open('/physiobank/database/%s.h5' % record)
  ## NB. This doesn't load metadata... Should it??
  chart = Chart(dpi=150)
  for n, s in enumerate(rec.signals()):
    for d in s.read(rec.interval(start, duration)):
      if s.rate: chart.plot('S%d' % n, d)
      else:   ### This assumes a WFDB anotation signal....
        for pt in d.dataseries.points:
          if pt[0] > start:
            mark = wfdb.annstr(int(pt[1]))
            if mark in "NLRBAaJSVrFejnE/fQ?":
              chart.mark(pt[0], mark)
  rec.close()
  chart.draw()

#========================================================


if __name__ == '__main__':
#=========================

  #testplot()

  plotchart('mitdb/102', 90, 20)

  """
  ts = data.UniformTimeSeries(np.random.rand(1000), rate=500)

  c = Chart(dpi=150)
  c.plot('TS1', ts)
  c.plot('TS2', ts)
  c.draw()
  """

  #plt.show()
  plt.savefig('test.png', dpi=300)

"""
## Intractive options:
  Beat markers on/off
  Beat annotations on/off
  Pan/zoom/move window/resize window duration
  Select region and export
  Select region (or instant) and annotate
  Select signal and annotate
  Select event and annotate
  Select annotation and annotate
  Annotate recording
  Edit annotations --> new version of the annotation...
"""
