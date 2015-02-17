#Embedded file name: carbonui/graphs\lowhighvaluegraph.py
import trinity
from carbonui.primitives.container import Container
from carbonui.primitives.vectorline import VectorLine
import carbonui.const as uiconst

class LowHighValueGraph(Container):
    default_name = 'lowhighvaluegraph'
    default_align = uiconst.TOALL

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.data = attributes.get('data', [])
        self.maxValue = attributes.get('maxValue', 0)
        self.markerSize = attributes.get('markerSize', 4)
        self.Build()

    def Build(self):
        maxValue = self.maxValue
        if maxValue == 0:
            maxValue = max(self.data)
        width, height = self.GetAbsoluteSize()
        verticalScale = height / maxValue
        n = len(self.data[0])
        step = float(width) / (n - 1)
        markerHalfSize = self.markerSize / 2
        x = 0
        for i in xrange(len(self.data[0])):
            close = self.data[2][i]
            y = height - close * verticalScale
            VectorLine(parent=self, translationFrom=(x - markerHalfSize, y), translationTo=(x + markerHalfSize, y), spriteEffect=trinity.TR2_SFX_FILL)
            x += step

        x = 0
        for i in xrange(len(self.data[0])):
            low = self.data[0][i]
            high = self.data[1][i]
            y0 = height - low * verticalScale
            y1 = height - high * verticalScale
            VectorLine(parent=self, translationFrom=(x, y0), translationTo=(x, y1), spriteEffect=trinity.TR2_SFX_FILL)
            x += step

    def Rebuild(self):
        maxValue = self.maxValue
        if maxValue == 0:
            maxValue = max(self.data)
        width, height = self.GetAbsoluteSize()
        verticalScale = height / maxValue
        n = len(self.data[0])
        step = float(width) / (n - 1)
        markerHalfSize = self.markerSize / 2
        x = 0
        ix = 0
        for i in xrange(len(self.data[0])):
            close = self.data[2][i]
            y = height - close * verticalScale
            line = self.children[ix]
            line.translationFrom = (x - markerHalfSize, y)
            line.translationTo = (x + markerHalfSize, y)
            x += step
            ix += 1

        x = 0
        for i in xrange(len(self.data[0])):
            low = self.data[0][i]
            high = self.data[1][i]
            y0 = height - low * verticalScale
            y1 = height - high * verticalScale
            line = self.children[ix]
            line.translationFrom = (x, y0)
            line.translationTo = (x, y1)
            x += step
            ix += 1
