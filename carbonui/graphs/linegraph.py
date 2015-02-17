#Embedded file name: carbonui/graphs\linegraph.py
from carbonui.primitives.vectorlinetrace import VectorLineTrace
import carbonui.const as uiconst

class LineGraph(VectorLineTrace):
    default_name = 'linegraph'
    default_align = uiconst.TOALL

    def ApplyAttributes(self, attributes):
        VectorLineTrace.ApplyAttributes(self, attributes)
        self.data = attributes.get('data', [])
        self.maxValue = attributes.get('maxValue', 0)
        self.Build()

    def Build(self):

        def set(i, pos):
            self.AddPoint(pos)

        self._BuildHelper(set)

    def Rebuild(self):
        renderObject = self.GetRenderObject()

        def set(i, pos):
            renderObject.vertices[i].position = pos

        self._BuildHelper(set)

    def _BuildHelper(self, op):
        maxValue = self.maxValue
        if maxValue == 0:
            maxValue = max(self.data)
        width, height = self.GetAbsoluteSize()
        verticalScale = height / maxValue
        n = len(self.data)
        step = float(width) / (n - 1)
        x = 0
        for i in xrange(len(self.data)):
            value = self.data[i]
            y = height - value * verticalScale
            op(i, (x, y))
            x += step
