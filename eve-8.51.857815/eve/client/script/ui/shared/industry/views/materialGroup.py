#Embedded file name: eve/client/script/ui/shared/industry/views\materialGroup.py
from collections import defaultdict
from math import ceil, cos, asin
import carbonui.const as uiconst
from carbonui.primitives.container import Container
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.shared.industry import industryUIConst
from eve.client.script.ui.shared.industry.industryUIConst import RADIUS_CONNECTOR_SMALL, RADIUS_CENTERCIRCLE_OUTER
import geo2
from eve.client.script.ui.shared.industry.views.industryLine import IndustryLineTrace
from eve.client.script.ui.shared.industry.views.material import Material, OptionalMaterial
from eve.client.script.ui.shared.industry.views.materialGroupDashedCircle import MaterialGroupDashedCircle
import localization
OFFSET_CONNECTIONPOINT = 8
ICONCOLUMN_WIDTH = 38

class MaterialGroup(Container):
    default_name = 'MaterialGroup'
    default_height = 60
    default_alignMode = uiconst.TOPLEFT
    default_align = uiconst.TOPLEFT

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.jobData = attributes.jobData
        self.materialsData = attributes.materialsData
        self.numRows = attributes.numRows
        self.industryGroupID = attributes.industryGroupID
        self.perRow = self.GetNumPerRow()
        self.materials = []
        self.lines = []
        self.connectorCircle = None
        self.pCircleIntersect = None
        self.materialsCont = ContainerAutoSize(name='materialsCont', parent=self, align=uiconst.TOPLEFT, alignMode=uiconst.TOPLEFT)
        self.icon = GroupIconSprite(name='icon', parent=self, align=uiconst.CENTERLEFT, pos=(7, 0, 22, 22), industryGroupID=self.industryGroupID)
        self.ConstructMaterials()
        self.ConstructLines()

    def AnimEntry(self, timeOffset, animate = True):
        for i, material in enumerate(self.materials):
            if animate:
                uicore.animations.FadeTo(material, 0.0, 1.0, duration=0.3, timeOffset=timeOffset + i * 0.02)
            else:
                material.opacity = 1.0

        for i, line in enumerate(self.lines):
            line.AnimEntry(timeOffset, i, animate)

        if animate:
            uicore.animations.FadeTo(self.connectorCircle, 0.0, 1.0, duration=0.3, timeOffset=timeOffset)
        else:
            self.connectorCircle.opacity = 1.0

    def ConstructLines(self):
        for line in self.lines:
            line.Close()

        self.lines = []
        usedRows = int(ceil(len(self.materialsData) / float(self.perRow)))
        pointsStart = self.GetLineStartingPoints()
        pConnect = self.GetLineConnectionPoint(pointsStart)
        y = self.top + self.materialsCont.top + self.materialsCont.height / 2
        x = self.GetLineCirceOffset(y)
        width, height = self.parent.GetCurrentAbsoluteSize()
        self.pCircleIntersect = (width / 2 - x, pConnect[1])
        pEnd = geo2.Vec2Subtract(self.pCircleIntersect, (1 * RADIUS_CONNECTOR_SMALL, 0))
        if len(pointsStart) == 1:
            self.DrawLine((pointsStart[0], pEnd))
        else:
            for point in pointsStart:
                if point[1] == pEnd[1]:
                    self.DrawLine((point, geo2.Vec2Subtract(pConnect, (3, 0))))
                else:
                    self.DrawLine((point, (pConnect[0], point[1]), pConnect))

            self.DrawLine((geo2.Vec2Add(pConnect, (3, 0)), pEnd))
        if not self.connectorCircle:
            self.connectorCircle = MaterialGroupDashedCircle(parent=self.materialsCont, numSegments=len(self.materialsData), radius=RADIUS_CONNECTOR_SMALL, materialsByGroupID=((self.industryGroupID, self.materialsData),), jobData=self.jobData)
        self.connectorCircle.left = pEnd[0]
        self.connectorCircle.top = pEnd[1] - RADIUS_CONNECTOR_SMALL
        self.UpdateState(animate=False)

    def DrawLine(self, points):
        line = IndustryLineTrace(parent=self.materialsCont)
        line.AddPoints(points)
        self.lines.append(line)

    def GetEndPoint(self):
        return self.pCircleIntersect

    def ConstructMaterials(self):
        for i, materialData in enumerate(self.materialsData):
            top = 66 * (i / self.perRow)
            cls = self.GetMaterialClass()
            material = cls(parent=self.materialsCont, jobData=self.jobData, materialData=materialData, align=uiconst.TOPLEFT, left=ICONCOLUMN_WIDTH + i % self.perRow * 48, top=top)
            self.materials.append(material)

        self.materialsCont.SetSizeAutomatically()
        self.materialsCont.top = (self.height - self.materialsCont.height) / 2

    def GetMaterialClass(self):
        if self.IsOptional():
            return OptionalMaterial
        else:
            return Material

    def IsOptional(self):
        for materialData in self.materialsData:
            if not materialData.IsOptional():
                return False

        return True

    def IsOptionSelected(self):
        """
        Returns True unless all items are optional and none of them have an item selected
        """
        for materialData in self.materialsData:
            if materialData.IsOptionSelected():
                return True

        return False

    def GetLineStartingPoints(self):
        ret = defaultdict(int)
        for material in self.materials:
            x = material.left + Material.default_width
            y = material.top + Material.default_height / 2
            ret[y] = max(ret[y], x)

        ret = zip(ret.values(), ret.keys())
        return ret

    def OnRunsChanged(self):
        self.UpdateState()

    def UpdateState(self, animate = True):
        for line in self.lines:
            line.UpdateColor(self.IsReady(), self.IsOptional(), self.IsOptionSelected(), animate)

        numReadySegments = sum([ materialData.valid for materialData in self.materialsData ])
        self.connectorCircle.UpdateState(numReadySegments, self.IsReady(), self.IsOptionSelected(), animate=animate)

    def GetNumPerRow(self):
        numMaterials = len(self.materialsData)
        if self.numRows >= 2:
            if numMaterials > 3:
                return min(5, int(ceil(numMaterials / 2.0)))
        return numMaterials

    def GetLineConnectionPoint(self, points):
        """
        Returs coordinates of point where all lines coming from the groups connect
        """
        x = max((x for x, _ in points))
        x += OFFSET_CONNECTIONPOINT
        y = sum((y for _, y in points)) / len(points)
        return (x, y)

    def GetLineCirceOffset(self, y):
        """
        Returns x-part of intersection line with outer circle
        """
        r = RADIUS_CENTERCIRCLE_OUTER
        y = float(y)
        return r * cos(asin((r - y) / r))

    def IsReady(self):
        """
        Are all materials in group owned in full quantity
        """
        for materialData in self.materialsData:
            if not materialData.valid:
                return False

        return True


class GroupIconSprite(Sprite):
    default_opacity = 0.25

    def ApplyAttributes(self, attributes):
        Sprite.ApplyAttributes(self, attributes)
        self.industryGroupID = attributes.industryGroupID
        self.texturePath = industryUIConst.ICON_BY_INDUSTRYGROUP[self.industryGroupID]

    def LoadTooltipPanel(self, tooltipPanel, *args):
        tooltipPanel.LoadGeneric1ColumnTemplate()
        groupName = industryUIConst.LABEL_BY_INDUSTRYGROUP[self.industryGroupID]
        groupHint = industryUIConst.HINT_BY_INDUSTRYGROUP[self.industryGroupID]
        tooltipPanel.AddLabelMedium(text=localization.GetByLabel(groupName), bold=True)
        tooltipPanel.AddLabelMedium(text=localization.GetByLabel(groupHint), wrapWidth=200)
