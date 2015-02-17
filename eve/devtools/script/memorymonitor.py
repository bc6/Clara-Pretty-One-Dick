#Embedded file name: eve/devtools/script\memorymonitor.py
from carbonui.graphs.grid import Grid
import trinity
import blue
import uicontrols
import uthread2
import carbonui.const as uiconst
from eve.client.script.ui.control.eveLabel import Label
from carbonui.graphs import graphsutil
from carbonui.graphs.linegraph import LineGraph
from carbonui.graphs.axislabels import VerticalAxisLabels
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
from carbonui.util.color import Color

class MemoryMonitor(uicontrols.Window):
    __guid__ = 'form.MemoryMonitor'
    default_caption = 'Memory Monitor'
    default_minSize = (400, 200)
    default_windowID = 'MemoryMonitor'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.SetTopparentHeight(0)
        self.graph = Container(parent=self.sr.main, align=uiconst.TOALL)
        self.data = None
        self.graphs = []
        self.isBuilding = False
        self.isResizing = False
        uthread2.StartTasklet(self.UpdateGraph)

    def UpdateGraph(self):
        while not self.destroyed:
            if not self.isResizing:
                self.Build()
            uthread2.Sleep(0.5)

    def Build(self):
        self.minGridLineHeight = 32
        self.graph.Flush()
        self.isBuilding = True
        minutes = 60
        self.data = blue.pyos.cpuUsage[-minutes * 60 / 10:]
        memData = []
        pymemData = []
        bluememData = []
        othermemData = []
        workingsetData = []
        for t, cpu, mem, sched in self.data:
            mem, pymem, workingset, pagefaults, bluemem = mem
            memData.append(mem)
            pymemData.append(pymem)
            bluememData.append(bluemem)
            othermem = mem - bluemem
            othermemData.append(othermem)
            workingsetData.append(workingset)

        maxValues = []
        for each in [memData,
         pymemData,
         bluememData,
         othermemData,
         workingsetData]:
            maxValues.append(max(each))

        self.overallMaxValue = max(maxValues)
        width, height = self.graph.GetAbsoluteSize()
        height = float(height)
        adjustedMaxValue, numGridLines = graphsutil.AdjustMaxValue(height, self.overallMaxValue, self.minGridLineHeight)
        gridLineStep = height / numGridLines
        labelsAndGrid = Container(parent=self.graph, align=uiconst.TOALL)
        self.axisLabels = VerticalAxisLabels(parent=labelsAndGrid, align=uiconst.TOLEFT, width=80, padRight=8, labelClass=Label, fontsize=16, maxValue=adjustedMaxValue, step=gridLineStep, count=numGridLines)
        self.grid = Grid(parent=labelsAndGrid, maxValue=adjustedMaxValue, step=gridLineStep, count=numGridLines)
        self.graphContainer = Container(parent=labelsAndGrid, align=uiconst.TOALL)
        Fill(parent=labelsAndGrid, color=(0, 0, 0, 0.25))
        self.graphs = []
        graphSources = [(memData, Color.RED),
         (pymemData, Color.GREEN),
         (bluememData, Color.BLUE),
         (othermemData, Color.YELLOW),
         (workingsetData, Color.AQUA)]
        for source, color in graphSources:
            graph = LineGraph(parent=self.graphContainer, color=color, lineWidth=1, data=source, maxValue=adjustedMaxValue, spriteEffect=trinity.TR2_SFX_FILL)
            self.graphs.append(graph)

        self.isBuilding = False

    def ResizeGraphs(self):
        if self.isBuilding:
            return
        if not self.data:
            return
        self.isResizing = True
        width, height = self.graphContainer.GetAbsoluteSize()
        adjustedMaxValue, numGridLines = graphsutil.AdjustMaxValue(height, self.overallMaxValue, self.minGridLineHeight)
        for graph in self.graphs:
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
        self.isResizing = False

    def _OnSizeChange_NoBlock(self, width, height):
        self.ResizeGraphs()
