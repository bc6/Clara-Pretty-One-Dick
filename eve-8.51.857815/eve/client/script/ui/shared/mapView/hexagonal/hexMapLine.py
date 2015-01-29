#Embedded file name: eve/client/script/ui/shared/mapView/hexagonal\hexMapLine.py
from eve.client.script.ui.shared.mapView.hexagonal import hexUtil
import geo2
__author__ = 'fridrik'
from carbonui.primitives.vectorlinetrace import VectorLineTrace

class HexMapLine(VectorLineTrace):
    positionsUnscaled = None
    margin = 6
    lineColor = (1, 1, 1, 0)

    def ApplyAttributes(self, attributes):
        VectorLineTrace.ApplyAttributes(self, attributes)

    def AddPoints(self, posList, color = None, scaling = 1.0):
        posList = list(posList)
        totalPoints = len(posList)
        if totalPoints > 2:
            p1, p2 = self.ApplyLineMargin(posList[0], posList[1], self.margin, 0)
            posList[0] = p1
            p1, p2 = self.ApplyLineMargin(posList[-2], posList[-1], 0, self.margin)
            posList[-1] = p2
        elif totalPoints == 2:
            p1, p2 = self.ApplyLineMargin(posList[0], posList[1], self.margin, self.margin)
            posList[0] = p1
            posList[1] = p2
        for pos in posList:
            x, y = pos
            self.AddPoint((x * scaling, y * scaling), color or self.lineColor)

    def ApplyLineMargin(self, p1, p2, radius1, radius2):
        v = geo2.Vec2Subtract(p1, p2)
        vn = geo2.Vec2Normalize(v)
        l = geo2.Vec2Length(v)
        if not l:
            return (None, None)
        s = (radius1 + radius2) / l
        mp1 = geo2.Vec2Subtract(p1, geo2.Vec2Scale(vn, radius1))
        mp2 = geo2.Vec2Add(p2, geo2.Vec2Scale(vn, radius2))
        return (mp1, mp2)

    def GetCrossPointsWithLine(self, hexLine, stopOnFirstCross = True):
        crossPoints = []
        myVertexCount = len(self.renderObject.vertices)
        otherVertexCount = len(hexLine.renderObject.vertices)
        if myVertexCount < 2 or otherVertexCount < 2:
            return crossPoints
        for m_i in xrange(myVertexCount - 1):
            m_p1 = self.renderObject.vertices[m_i].position
            m_p2 = self.renderObject.vertices[m_i + 1].position
            for o_i in xrange(otherVertexCount - 1):
                o_p1 = hexLine.renderObject.vertices[o_i].position
                o_p2 = hexLine.renderObject.vertices[o_i + 1].position
                if m_p1 == o_p1 or m_p1 == o_p2:
                    crossPoint = m_p1
                elif m_p2 == o_p1 or m_p2 == o_p2:
                    crossPoint = m_p2
                else:
                    try:
                        crossPoint = hexUtil.intersect_line_segments((m_p1, m_p2), (o_p1, o_p2))
                    except ValueError:
                        continue

                if crossPoint:
                    crossPoints.append(crossPoint)
                    if stopOnFirstCross:
                        break

            if crossPoints and stopOnFirstCross:
                break

        return crossPoints
