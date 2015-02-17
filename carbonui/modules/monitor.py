#Embedded file name: carbonui/modules\monitor.py
import blue
from carbon.common.script.sys.service import Service
import uthread
import carbonui.const as uiconst
from carbonui.control.scrollentries import ScrollEntryNode, SE_GenericCore
from carbonui.primitives.gridcontainer import GridContainer
import trinity
import util
from carbonui.primitives.base import Base
from carbonui.primitives.container import Container
from carbonui.control.window import WindowCoreOverride as Window
from carbonui.control.label import LabelOverride as Label
from carbonui.control.buttons import ButtonCoreOverride as Button
from carbonui.control.scroll import ScrollCoreOverride as Scroll
from carbonui.control.checkbox import CheckboxCoreOverride as Checkbox
from trinity.GraphManager import GraphManager
KB = 1024
import math

def niceNum(num, precision):
    """Returns a string representation for a floating point number
    that is rounded to the given precision and displayed with
    commas and spaces."""
    accpow = math.floor(math.log10(precision))
    if num < 0:
        digits = int(math.fabs(num / pow(10, accpow) - 0.5))
    else:
        digits = int(math.fabs(num / pow(10, accpow) + 0.5))
    result = ''
    if digits > 0:
        for i in range(0, int(accpow)):
            if i % 3 == 0 and i > 0:
                result = '0,' + result
            else:
                result = '0' + result

        curpow = int(accpow)
        while digits > 0:
            adigit = chr(digits % 10 + ord('0'))
            if curpow % 3 == 0 and curpow != 0 and len(result) > 0:
                if curpow < 0:
                    result = adigit + ' ' + result
                else:
                    result = adigit + ',' + result
            elif curpow == 0 and len(result) > 0:
                result = adigit + '.' + result
            else:
                result = adigit + result
            digits = digits / 10
            curpow = curpow + 1

        for i in range(curpow, 0):
            if i % 3 == 0 and i != 0:
                result = '0 ' + result
            else:
                result = '0' + result

        if curpow <= 0:
            result = '0.' + result
        if num < 0:
            result = '-' + result
    else:
        result = '0'
    return result


def FormatMemory(val):
    if val < KB:
        label = 'B'
    elif val > KB and val < KB ** 2:
        label = 'KB'
        val = val / KB
    elif val > KB ** 2 and val < KB ** 3:
        label = 'MB'
        val = val / KB ** 2
    elif val > KB ** 3:
        label = 'GB'
        val = val / KB ** 3
    return str(round(val, 2)) + label


class GraphRenderer(Base):
    __guid__ = 'uicls.GraphRenderer'
    __renderObject__ = trinity.Tr2Sprite2dRenderJob

    def ApplyAttributes(self, attributes):
        Base.ApplyAttributes(self, attributes)
        self.viewport = trinity.TriViewport()
        self.linegraph = trinity.Tr2LineGraph()
        self.linegraphSize = 0
        self.linegraph.name = 'FPS'
        self.linegraph.color = (0.9, 0.9, 0.9, 1)
        blue.statistics.SetAccumulator(self.linegraph.name, self.linegraph)
        self.renderJob = trinity.CreateRenderJob('Graphs')
        self.renderObject.renderJob = self.renderJob
        self.renderJob.PythonCB(self.AdjustViewport)
        self.renderJob.SetViewport(self.viewport)
        self.renderJob.SetStdRndStates(trinity.RM_SPRITE2D)
        self.renderer = self.renderJob.RenderLineGraph()
        self.renderer.showLegend = False
        self.renderer.lineGraphs.append(self.linegraph)

    def Close(self):
        Base.Close(self)
        self.renderer.scaleChangeCallback = None

    def AdjustViewport(self):
        l, t = self.displayX, self.displayY
        parent = self.GetParent()
        while parent:
            l += parent.displayX
            t += parent.displayY
            parent = parent.GetParent()

        self.viewport.x = l
        self.viewport.y = t
        self.viewport.width = self._displayWidth
        self.viewport.height = self._displayHeight
        if self.linegraphSize != self._displayWidth:
            self.linegraph.SetSize(self._displayWidth)
            self.linegraphSize = self._displayWidth


class FpsMonitor(Window):
    __guid__ = 'uicls.FpsMonitor'
    default_caption = 'FPS Monitor'
    default_windowID = 'fpsMonitor'

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.SetTopparentHeight(4)
        self.fpsLabel = Label(parent=self.sr.main, left=4, width=80, fontsize=18)
        self.platformLabel = Label(parent=self.sr.main, left=4, top=24, width=80, fontsize=12, text=trinity.platform)
        self.toggleDisplayResults = False
        self.legendContainer = GridContainer(parent=self.sr.main, align=uiconst.TORIGHT, width=28, columns=1, padRight=4, padBottom=4)
        self.startStatsBtn = Button(parent=self.sr.main, align=uiconst.BOTTOMLEFT, label='Start Collecting Stats', left=5, top=10, func=self.StartCollectingData)
        self.stopStatsBtn = Button(parent=self.sr.main, align=uiconst.BOTTOMLEFT, label='Stop Collecting Stats', left=5, top=10, func=self.StopCollectingData, state=uiconst.UI_HIDDEN)
        self.timeLabel = Label(parent=self.sr.main, align=uiconst.BOTTOMLEFT, left=142, top=11, width=100, fontsize=12)
        self.displayResultsCheckbox = Checkbox(parent=self.sr.main, align=uiconst.BOTTOMRIGHT, left=10, top=10, callback=self.ToggleDisplayResults, width=100)
        self.labels = []
        for i in xrange(4):
            label = Label(parent=self.legendContainer, align=uiconst.TOTOP, width=20, top=-4)
            self.labels.append(label)

        graphContainer = Container(parent=self.sr.main, align=uiconst.TOALL, padLeft=4, padRight=4, padBottom=4)
        gr = GraphRenderer(parent=graphContainer, align=uiconst.TOALL)
        self.renderer = gr.renderer
        self.renderer.scaleChangeCallback = self.ScaleChangeHandler
        uthread.new(self.UpdateFpsLabel)

    def StartCollectingData(self, *args):
        self.startStatsBtn.Hide()
        self.stopStatsBtn.Show()
        sm.GetService('fpsMonitorSvc').StartCollectingData()

    def StopCollectingData(self, *args):
        self.startStatsBtn.Show()
        self.stopStatsBtn.Hide()
        if self.toggleDisplayResults:
            self.DisplayAverageResults()
        fpsStats = sm.GetService('fpsMonitorSvc').StopCollectingData()
        self.CopyResultsToClipboard(fpsStats)

    def CopyResultsToClipboard(self, fpsStats):
        txt = ''
        for t, value in fpsStats:
            txt += '%.1f\t%6.2f\n' % (t / float(const.SEC), value)

        print txt
        blue.pyos.SetClipboardData(txt)
        uicore.Message('CustomNotify', {'notify': 'FPS Stats have been exported to clipboard'})

    def ToggleDisplayResults(self, chkb):
        if chkb._checked:
            self.toggleDisplayResults = True
        else:
            self.toggleDisplayResults = False

    def ScaleChangeHandler(self):
        numLabels = len(self.labels)
        label = 1.0
        labelStep = 1.0 / float(numLabels)
        for i in xrange(numLabels):
            labelValue = int(label / self.renderer.scale * self.renderer.legendScale + 0.5)
            self.labels[i].SetText(str(labelValue))
            label -= labelStep

    def UpdateFpsLabel(self):
        fpsSvc = sm.GetService('fpsMonitorSvc')
        while not self.destroyed:
            self.fpsLabel.text = '%6.2f' % fpsSvc.GetFPS()
            blue.synchro.SleepWallclock(500)
            if fpsSvc.IsCollectingStats():
                self.timeLabel.text = '%s' % util.FmtTime(fpsSvc.GetStatsCollectionTime())

    def DisplayAverageResults(self):
        """
        This function (mean) averages all the gathered metric data gathered
            during collection and displays them in a Message Window.
        """
        avg = lambda x: sum(x) / len(x)
        statsData = sm.GetService('fpsMonitorSvc').GetStatsData()
        avgfps = avg(statsData['fps'])
        avgframetime = avg(statsData['frametime'])
        uicore.Message('CustomInfo', {'info': 'Mean FPS: %6.2f<br />Mean Frametime:%6.2f' % (avgfps, avgframetime * 1000)})


class FpsMonitorSvc(Service):
    __guid__ = 'svc.fpsMonitorSvc'
    __servicename__ = 'Fps Monitor Service'
    __displayname__ = 'Fps Monitor Service'

    def Run(self, *args):
        self.collectingFpsStats = False
        self.fpsStat = blue.statistics.Find('FPS')
        self.frameTimeStat = blue.statistics.Find('Trinity/FrameTime')

    def GetFPS(self):
        return self.fpsStat.value

    def IsCollectingStats(self):
        return self.collectingFpsStats

    def GetStatsCollectionTime(self):
        return blue.os.GetWallclockTime() - self.collectingFpsStats

    def GetStatsData(self):
        return self.statsData

    def StartCollectingData(self, *args):
        self.fpsStats = []
        self.statsData = {'fps': [],
         'frametime': []}
        uthread.new(self.CollectDataThread)

    def CollectDataThread(self):
        MAX_STATS = 36000
        self.collectingFpsStats = blue.os.GetWallclockTime()
        while self.collectingFpsStats:
            deltaTime = blue.os.GetWallclockTime() - self.collectingFpsStats
            self.fpsStats.append((deltaTime, self.fpsStat.value))
            fps = self.fpsStat.value
            frametime = self.frameTimeStat.value
            if fps:
                self.statsData['fps'].append(fps)
            if frametime:
                self.statsData['frametime'].append(frametime)
            if deltaTime > const.HOUR:
                self.StopCollectingData()
                return
            blue.synchro.SleepWallclock(200)

    def StopCollectingData(self, *args):
        self.collectingFpsStats = None
        ret = self.fpsStats[:]
        self.fpsStats = []
        return ret


class GraphsWindow(Window):
    __guid__ = 'form.GraphsWindow'
    default_caption = 'Blue stats graphs'
    default_minSize = (600, 500)

    def ApplyAttributes(self, attributes):
        self._ready = False
        Window.ApplyAttributes(self, attributes)
        self.graphs = GraphManager()
        self.graphs.SetEnabled(True)
        if hasattr(self, 'SetTopparentHeight'):
            self.SetTopparentHeight(0)
            self.container = Container(parent=self.sr.main, align=uiconst.TOALL)
        else:
            self.container = Container(parent=self.sr.content, align=uiconst.TOALL)
        self.settingsContainer = Container(parent=self.container, align=uiconst.TOTOP, height=30)
        self.showTimersChk = Checkbox(parent=self.settingsContainer, align=uiconst.TOLEFT, text='Timers', checked=True, width=120, height=30, callback=self.PopulateScroll)
        self.showMemoryChk = Checkbox(parent=self.settingsContainer, align=uiconst.TOLEFT, text='Memory counters', checked=True, width=120, height=30, callback=self.PopulateScroll)
        self.showLowCountersChk = Checkbox(parent=self.settingsContainer, align=uiconst.TOLEFT, text='Low counters', checked=True, width=120, height=30, callback=self.PopulateScroll)
        self.showHighCountersChk = Checkbox(parent=self.settingsContainer, align=uiconst.TOLEFT, text='High counters', checked=True, width=120, height=30, callback=self.PopulateScroll)
        self.resetBtn = Button(parent=self.settingsContainer, align=uiconst.TORIGHT, label='Reset peaks', width=120, height=30, func=self.PopulateScroll)
        self.refreshBtn = Button(parent=self.settingsContainer, align=uiconst.TORIGHT, label='Refresh', width=120, height=30, func=self.PopulateScroll)
        self.scroll = Scroll(parent=self.container, id='blueGraphsScroll', align=uiconst.TOTOP, height=200)
        self.graphsContainer = Container(parent=self.container, align=uiconst.TOALL)
        self._ready = True
        self.PopulateScroll()

    def Close(self, *args, **kwargs):
        self.graphs.SetEnabled(False)
        Window.Close(self, *args, **kwargs)

    def DelayedRefresh_thread(self):
        blue.synchro.SleepWallclock(600)
        self.PopulateScroll()

    def DelayedRefresh(self):
        uthread.new(self.DelayedRefresh_thread)

    def ResetPeaks(self, *args):
        blue.statistics.ResetPeaks()
        self.DelayedRefresh()

    def PopulateScroll(self, *args):
        typesIncluded = []
        if self.showTimersChk.GetValue():
            typesIncluded.append('time')
        if self.showMemoryChk.GetValue():
            typesIncluded.append('memory')
        if self.showLowCountersChk.GetValue():
            typesIncluded.append('counterLow')
        if self.showHighCountersChk.GetValue():
            typesIncluded.append('counterHigh')
        stats = blue.statistics.GetValues()
        desc = blue.statistics.GetDescriptions()
        contentList = []
        for key, value in desc.iteritems():
            type = value[1]
            if type in typesIncluded:
                peak = stats[key][1]
                if type == 'memory':
                    label = '%s<t>%s<t>%s' % (key, FormatMemory(peak), value[0])
                elif type.startswith('counter'):
                    label = '%s<t>%s<t>%s' % (key, niceNum(peak, 1), value[0])
                elif type == 'time':
                    label = '%s<t>%s<t>%s' % (key, niceNum(peak, 1e-10), value[0])
                listEntry = ScrollEntryNode(decoClass=SE_GenericCore, id=id, name=key, peak=peak, desc=value[0], label=label, GetMenu=self.GetListEntryMenu, OnDblClick=self.OnListEntryDoubleClicked)
                contentList.append(listEntry)

        self.scroll.Load(contentList=contentList, headers=['Name', 'Peak', 'Description'], noContentHint='No Data available')

    def GetListEntryMenu(self, listEntry):
        return (('Right-click action 1', None), ('Right-click action 2', None))

    def OnListEntryDoubleClicked(self, listEntry):
        node = listEntry.sr.node
        if self.graphs.HasGraph(node.name):
            self.graphs.RemoveGraph(node.name)
        else:
            self.graphs.AddGraph(node.name)

    def _OnResize(self):
        if self._ready:
            l, t, w, h = self.graphsContainer.GetAbsolute()
            scaledAbs = (uicore.ScaleDpi(l),
             uicore.ScaleDpi(t),
             uicore.ScaleDpi(w),
             uicore.ScaleDpi(h))
            self.graphs.AdjustViewports(scaledAbs)
