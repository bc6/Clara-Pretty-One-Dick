#Embedded file name: carbonui/graphs\donchianchannel.py
import trinity
from carbonui.primitives.polygon import Polygon
import carbonui.const as uiconst

class DonchianChannel(Polygon):
    default_name = 'donchianchannel'
    default_align = uiconst.TOALL

    def ApplyAttributes(self, attributes):
        Polygon.ApplyAttributes(self, attributes)
        self.data = attributes.get('data', [])
        self.maxValue = attributes.get('maxValue', 0)
        self.Build()

    def Build(self):
        donchianLowData, donchianHighData = self.data
        maxValue = self.maxValue
        if maxValue == 0:
            maxValue = max(donchianHighData)
        width, height = self.GetAbsoluteSize()
        verticalScale = height / maxValue
        n = len(donchianHighData)
        step = float(width) / (n - 1)
        renderObject = self.GetRenderObject()
        x0 = 0
        n = len(donchianLowData)
        for i in xrange(n - 1):
            highLeft = donchianHighData[i]
            lowLeft = donchianLowData[i]
            highRight = donchianHighData[i + 1]
            lowRight = donchianLowData[i + 1]
            x1 = x0 + step
            topLeft = trinity.Tr2Sprite2dVertex()
            topLeft.position = (x0, height - highLeft * verticalScale)
            renderObject.vertices.append(topLeft)
            topRight = trinity.Tr2Sprite2dVertex()
            topRight.position = (x1, height - highRight * verticalScale)
            renderObject.vertices.append(topRight)
            bottomRight = trinity.Tr2Sprite2dVertex()
            bottomRight.position = (x1, height - lowRight * verticalScale)
            renderObject.vertices.append(bottomRight)
            bottomLeft = trinity.Tr2Sprite2dVertex()
            bottomLeft.position = (x0, height - lowLeft * verticalScale)
            renderObject.vertices.append(bottomLeft)
            x0 = x1

        for i in xrange(n - 1):
            t1 = trinity.Tr2Sprite2dTriangle()
            t1.index0 = i * 4
            t1.index1 = i * 4 + 1
            t1.index2 = i * 4 + 2
            t2 = trinity.Tr2Sprite2dTriangle()
            t2.index0 = i * 4
            t2.index1 = i * 4 + 2
            t2.index2 = i * 4 + 3
            renderObject.triangles.append(t1)
            renderObject.triangles.append(t2)

    def Rebuild(self):
        donchianLowData, donchianHighData = self.data
        maxValue = self.maxValue
        if maxValue == 0:
            maxValue = max(donchianHighData)
        width, height = self.GetAbsoluteSize()
        verticalScale = height / maxValue
        n = len(donchianHighData)
        step = float(width) / (n - 1)
        renderObject = self.GetRenderObject()
        x0 = 0
        n = len(donchianLowData)
        ix = 0
        for i in xrange(n - 1):
            highLeft = donchianHighData[i]
            lowLeft = donchianLowData[i]
            highRight = donchianHighData[i + 1]
            lowRight = donchianLowData[i + 1]
            x1 = x0 + step
            topLeft = renderObject.vertices[ix]
            topLeft.position = (x0, height - highLeft * verticalScale)
            ix += 1
            topRight = renderObject.vertices[ix]
            topRight.position = (x1, height - highRight * verticalScale)
            ix += 1
            bottomRight = renderObject.vertices[ix]
            bottomRight.position = (x1, height - lowRight * verticalScale)
            ix += 1
            bottomLeft = renderObject.vertices[ix]
            bottomLeft.position = (x0, height - lowLeft * verticalScale)
            ix += 1
            x0 = x1
