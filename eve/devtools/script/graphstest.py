#Embedded file name: eve/devtools/script\graphstest.py
from carbonui.graphs.axislabels import VerticalAxisLabels
from carbonui.graphs.grid import Grid
import trinity
import random
import uicontrols
import carbonui.const as uiconst
from carbonui.primitives.container import Container
from eve.client.script.ui.control.eveLabel import Label
from carbonui.graphs.linegraph import LineGraph
from carbonui.graphs.donchianchannel import DonchianChannel
from carbonui.graphs.lowhighvaluegraph import LowHighValueGraph
import carbonui.graphs.gridlegends as gridlegends
import carbonui.graphs.graphsutil as graphsutil

class GraphsTest(uicontrols.Window):
    __guid__ = 'form.GraphsTest'
    default_caption = 'Graphs Test'
    default_minSize = (400, 200)
    default_windowID = 'GraphsTest'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.SetTopparentHeight(0)
        self.topPanel = Container(parent=self.sr.main, align=uiconst.TOTOP, height=30)
        uicontrols.Button(parent=self.topPanel, align=uiconst.TOLEFT, label='Graph', width=120, height=30, func=self.Graph)
        self.main = Container(parent=self.sr.main, align=uiconst.TOALL)
        self.data = []

    def Graph(self, *args):
        self.data = self.RandomData(60)
        self.LineGraph()

    def RandomData(self, numValues = 30):
        values = []
        prev_low = random.randint(5, 300)
        for i in xrange(numValues):
            volume = random.randint(100, 100000)
            low = random.randint(max(prev_low - 30, 5), prev_low + 30)
            high = random.randint(low, low + 10)
            close = random.randint(low, high)
            timestamp = i
            values.append((timestamp,
             low,
             high,
             close,
             volume))
            prev_low = low

        return values

    def SplitData(self, values):
        timeStamps = []
        volData = []
        closeData = []
        lowData = []
        highData = []
        for x in values:
            timeStamps.append(x[0])
            volData.append(x[4])
            closeData.append(x[3])
            lowData.append(x[1])
            highData.append(x[2])

        return (timeStamps,
         volData,
         closeData,
         lowData,
         highData)

    def LineGraph(self):
        self.main.Flush()
        if not self.data:
            return
        self.minGridLineHeight = 32
        timeStamps, volData, closeData, lowData, highData = self.SplitData(self.data)
        width, height = self.main.GetAbsoluteSize()
        width = float(width)
        height = float(height)
        n = len(self.data)
        self.maxValue = float(max(highData))
        adjustedMaxValue, numGridLines = graphsutil.AdjustMaxValue(height, self.maxValue, self.minGridLineHeight)
        gridLineStep = height / numGridLines
        donchianHighData = graphsutil.MovingHigh(highData)
        donchianLowData = graphsutil.MovingLow(lowData)
        movingAvg = graphsutil.MovingAvg(closeData, n=20)
        labelsAndGrid = Container(parent=self.main, align=uiconst.TOALL)
        self.axisLabels = VerticalAxisLabels(parent=labelsAndGrid, align=uiconst.TORIGHT, width=80, padLeft=8, labelClass=Label, fontsize=16, maxValue=adjustedMaxValue, step=gridLineStep, count=numGridLines)
        gridAndGraphs = Container(parent=labelsAndGrid, align=uiconst.TOALL)
        self.graphContainer = Container(parent=gridAndGraphs, align=uiconst.TOALL)
        self.grid = Grid(parent=gridAndGraphs, maxValue=adjustedMaxValue, step=gridLineStep, count=numGridLines)
        self.lowHighValue = LowHighValueGraph(parent=self.graphContainer, data=(lowData, highData, closeData), maxValue=adjustedMaxValue, markerSize=6)
        self.donchianHigh = LineGraph(parent=self.graphContainer, lineWidth=1.25, data=donchianHighData, maxValue=adjustedMaxValue)
        self.donchianLow = LineGraph(parent=self.graphContainer, lineWidth=1.25, data=donchianLowData, maxValue=adjustedMaxValue)
        self.movingAvg = LineGraph(parent=self.graphContainer, lineWidth=1.25, data=movingAvg, maxValue=adjustedMaxValue)
        self.donchianChannel = DonchianChannel(parent=self.graphContainer, color=(0.25, 0, 0, 0.25), data=(donchianLowData, donchianHighData), maxValue=adjustedMaxValue)
        gridlegends.AddHorizontalGridLines(self.gridContainer, numGridLines, gridLineStep, height, width)

    def ResizeLineGraph(self):
        if not self.data:
            return
        width, height = self.graphContainer.GetAbsoluteSize()
        adjustedMaxValue, numGridLines = graphsutil.AdjustMaxValue(height, self.maxValue, self.minGridLineHeight)
        for graph in [self.donchianHigh,
         self.donchianLow,
         self.movingAvg,
         self.donchianChannel,
         self.lowHighValue]:
            graph.maxValue = adjustedMaxValue
            graph.Rebuild()

        gridLineStep = height / numGridLines
        self.axisLabels.maxValue = adjustedMaxValue
        self.axisLabels.count = numGridLines
        self.axisLabels.step = gridLineStep
        self.axisLabels.Rebuild()
        self.grid.count = numGridLines
        self.grid.step = gridLineStep
        self.grid.Rebuild()

    def _OnSizeChange_NoBlock(self, width, height):
        self.ResizeLineGraph()
