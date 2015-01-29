#Embedded file name: eve/client/script/ui/shared/shipTree\shipTreeContainer.py
from .shipTreeShipGroup import ShipTreeShipGroup
from carbonui.primitives.containerAutoSize import ContainerAutoSize
import shipTreeConst
import geo2
from eve.client.script.ui.shared.shipTree.shipTreeConst import TREE_SCALE, NODETYPE_GROUP, NODETYPE_OTHERFACTIONGROUP, COLOR_BG, NODETYPE_ROOT, BG_BY_FACTIONID, COLOR_MASTERED
import carbonui.const as uiconst
from eve.client.script.ui.control.buttons import ButtonIcon
import trinity
from carbonui.primitives.vectorlinetrace import VectorLineTrace
from localization import GetByMessageID, GetByLabel
from carbonui.primitives.stretchspritehorizontal import StretchSpriteHorizontal
from carbonui.primitives.container import Container
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.control.eveLabel import Label
from inventorycommon.const import typeCapsule
import macho
import const
X_OFFSET = 22
Y_OFFSET = 40
COLOR_FONT = (0.667,
 0.796,
 0.906,
 1.0)
COLOR_LINE_TO = (1.0,
 1.0,
 1.0,
 1.0)

class ShipTreeContainer(ContainerAutoSize):
    default_name = 'ShipTreeContainer'
    __notifyevents__ = ('OnUIScalingChange',)

    def ApplyAttributes(self, attributes):
        ContainerAutoSize.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.factionID = attributes.factionID
        self._offset = None
        self._leftFloat = 0.0
        self._topFloat = 0.0
        self.rootNode = None
        self.lineCont = Container(name='lineCont', parent=self)
        self.ConstructTree()
        self.bgCont = Container(name='bgContainer', align=uiconst.CENTER, state=uiconst.UI_DISABLED, parent=self, padding=-100)
        self.topFrame = TopFrame(parent=self.bgCont, align=uiconst.TOTOP)
        self.bottomFrame = BottomFrame(parent=self.bgCont, align=uiconst.TOBOTTOM)
        Sprite(name='grid', bgParent=self.bgCont, state=uiconst.UI_DISABLED, align=uiconst.CENTER, texturePath='res:/UI/Texture/Classes/ShipTree/grid.png', color=(0.43, 0.727, 1.0, 0.2), idx=0, tileX=True, tileY=True)
        texturePath = BG_BY_FACTIONID.get(self.factionID)
        _, h = self.rootNode.GetDimensions()
        height = 3.2 * h * TREE_SCALE
        width = 1.6 / 1.8 * height
        self.factionBG = Sprite(name='factionBG', parent=self.bgCont, align=uiconst.CENTER, texturePath=texturePath, width=width, height=height, opacity=0.18, idx=0)

    def ConstructTree(self):
        self.rootNode = sm.GetService('shipTree').GetRootNode(self.factionID)
        self._offset, _ = self.rootNode.GetBoundingBox()
        self.ConstructNodes()
        self.ConstructLines()

    def ConstructNodes(self):
        self._ConstructNodes(self.rootNode)

    def _ConstructNodes(self, node, i = 0, line = None):
        nodeType = node.GetNodeType()
        if nodeType == NODETYPE_GROUP:
            self.RenderShipGroup(node, i)
        elif nodeType == NODETYPE_OTHERFACTIONGROUP:
            self.RenderNodeOtherFactionGroup(node)
        elif nodeType == NODETYPE_ROOT:
            self.RenderRootNode(node)
        for childNode in node.children:
            self._ConstructNodes(childNode, i + 1, line)

    def ConstructLines(self, animate = True):
        self.lineCont.Flush()
        self._ConstructLines(self.rootNode, animate=animate)

    def _ConstructLines(self, node, i = 0, line = None, animate = True):
        if node.nodeType == NODETYPE_GROUP:
            line = None
        for childNode in node.children:
            line = self.RenderLine(node, childNode, i, line, animate=animate)
            self._ConstructLines(childNode, i + 1, line, animate)
            line = None

    def RenderShipGroup(self, node, i):
        """ Render standard group of ships """
        if node.parent and node.parent.nodeType == NODETYPE_OTHERFACTIONGROUP:
            return
        x, y = self._GetNodePosition(node)
        ShipTreeShipGroup(parent=self, node=node, alignMode=uiconst.TOPLEFT, left=x, top=y, idx=0, nodeNum=i)

    def RenderNodeOtherFactionGroup(self, node):
        """ 
        Render an icon representing a prerequisit faction, other than the currently selected one 
        (used in pirate faction trees) 
        """
        left, top = self._GetNodePosition(node)
        opacity = 0.2 if node.IsLocked() else 1.0
        texturePath = shipTreeConst.ICON_BY_FACTIONID.get(node.factionID)
        size = 64
        shipGroupData = cfg.fsdInfoBubbleGroups[node.shipGroupID]
        shipGroupName = GetByMessageID(shipGroupData.nameID)
        ButtonIcon(parent=self, texturePath=texturePath, pos=(left - size / 2 + X_OFFSET,
         top - size / 2 + Y_OFFSET,
         size,
         size), iconSize=65, idx=0, func=self.OnOtherFactionClicked, args=(node,), opacity=opacity, hint='<b>%s</b>\n%s' % (cfg.factions.Get(node.factionID).factionName, shipGroupName))

    def RenderRootNode(self, node):
        texturePath = cfg.invtypes.Get(typeCapsule).Graphic().isisIconPath
        size = 32
        left, top = self._GetNodePosition(node)
        if self.IsInGoldenPod():
            color = COLOR_MASTERED
            typeID = const.typeCapsuleGolden
        else:
            color = (1, 1, 1, 1)
            typeID = const.typeCapsule
        btn = ButtonIcon(parent=self, pos=(left - size / 2 + X_OFFSET - 6,
         top - size / 2 - 2 + Y_OFFSET,
         size,
         size), func=sm.GetService('info').ShowInfo, iconSize=size, args=(typeID,), texturePath=texturePath, hint=cfg.invtypes.Get(typeID).name, iconColor=color)
        btn.icon.blendMode = trinity.TR2_SBM_ADD

    def IsInGoldenPod(self):
        implants = sm.GetService('godma').GetItem(session.charid).implants
        if implants is None:
            return False
        for implant in implants:
            if implant.typeID == const.typeGoldenCapsuleImplant:
                return True

        return False

    def RenderLine(self, nodeFrom, nodeTo, i, line, animate = True):
        """ Render line between two nodes """
        if nodeTo.nodeType == NODETYPE_OTHERFACTIONGROUP:
            return None
        texturePath = self.GetLineTexturePath(nodeTo)
        if not line or line.texturePath != texturePath:
            line = VectorLineTraceShipTree(parent=self.lineCont, nodeFrom=nodeFrom, nodeTo=nodeTo, texturePath=texturePath)
            pos = self.GetNewLineStartPos(nodeFrom, nodeTo)
            if i == 0 or nodeFrom.nodeType == NODETYPE_OTHERFACTIONGROUP:
                colorFrom = (1.0, 1.0, 1.0, -0.05)
            else:
                colorFrom = COLOR_LINE_TO
            line.AddPoint(pos, colorFrom)
        line.AddPoint(self._GetLinePosition(nodeTo), COLOR_LINE_TO)
        opacity = 0.7 if nodeTo.IsLocked() else 1.0
        if animate:
            uicore.animations.FadeIn(line, opacity, timeOffset=0.05 * i + 0.2, duration=0.3)
        else:
            line.opacity = opacity
        return line

    def GetLineTexturePath(self, nodeTo):
        if nodeTo.IsPathToElite():
            return 'res:/UI/Texture/classes/shipTree/lines/elite.png'
        elif nodeTo.IsLocked():
            return 'res:/UI/Texture/classes/shipTree/lines/locked.png'
        else:
            return 'res:/UI/Texture/classes/shipTree/lines/unlocked.png'

    def GetNewLineStartPos(self, node, childNode):
        pos = self._GetLinePosition(node)
        childPos = self._GetLinePosition(childNode)
        if node.nodeType == NODETYPE_GROUP:
            if childPos[1] == pos[1]:
                offset = node.GetGroupWidth() + 24
                s = offset / geo2.Vec2Length(geo2.Vec2Subtract(childPos, pos))
                pos = geo2.Vec2Lerp(pos, childPos, s)
        return (int(pos[0]), int(pos[1]))

    def _GetNodePosition(self, node):
        """ Returns node position scaled and offset so that the bottom-left most point is at (0, 0) """
        vec = geo2.Vec2Subtract(node.GetPosition(), self._offset)
        return geo2.Vec2Scale(vec, TREE_SCALE)

    def _GetLinePosition(self, node):
        vec = self._GetNodePosition(node)
        vec = geo2.Vec2Add(vec, (X_OFFSET, Y_OFFSET))
        return (int(vec[0]), int(vec[1]))

    def GetLeftFloat(self):
        return self._leftFloat

    def SetLeftFloat(self, value):
        self._leftFloat = value
        self.left = value

    leftFloat = property(GetLeftFloat, SetLeftFloat)

    def GetTopFloat(self):
        return self._topFloat

    def SetTopFloat(self, value):
        self._topFloat = value
        self.top = value

    topFloat = property(GetTopFloat, SetTopFloat)

    def OnOtherFactionClicked(self, node):
        sm.GetService('shipTreeUI').OpenAndShowShipGroup(node.factionID, node.shipGroupID)

    def UpdateTreeSkills(self):
        self.rootNode.FlushCache()
        self.ConstructLines(animate=False)

    def OnUIScalingChange(self, *args):
        self.ConstructLines(animate=False)


class VectorLineTraceShipTree(VectorLineTrace):
    default_spriteEffect = trinity.TR2_SFX_COPY
    default_lineWidth = 10.0
    default_textureWidth = 10.0
    default_opacity = 0.0
    default_idx = -1
    default_state = uiconst.UI_DISABLED


class TopFrame(Container):
    default_name = 'topFrame'
    default_height = 26

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        Sprite(parent=self, align=uiconst.TOLEFT, width=126, texturePath='res:/UI/Texture/classes/shipTree/frame/topLeft.png')
        cont = ContainerAutoSize(parent=self, align=uiconst.TOLEFT, alignMode=uiconst.TOPLEFT, bgTexturePath='res:/UI/Texture/classes/shipTree/frame/topMiddle.png')
        Label(parent=cont, text=GetByLabel('UI/ShipTree/InterbusShipIdentificationSystem'), color=COLOR_BG, top=3, fontsize=12, uppercase=True, bold=True, padRight=4)
        StretchSpriteHorizontal(parent=Container(parent=self), align=uiconst.TOTOP, texturePath='res:/UI/Texture/classes/ShipTree/frame/topRight.png', leftEdgeSize=40, rightEdgeSize=5, height=26)


class BottomFrame(Container):
    default_name = 'bottomFrame'
    default_height = 59

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        Sprite(parent=self, align=uiconst.TOLEFT, width=259, texturePath='res:/UI/Texture/classes/shipTree/frame/bottomLeft.png')
        cont = ContainerAutoSize(parent=self, align=uiconst.TOLEFT, padLeft=4)
        Label(parent=cont, align=uiconst.TOPLEFT, text=GetByLabel('UI/ShipTree/Showing'), uppercase=True, top=38, fontsize=9, color=COLOR_FONT)
        Label(parent=self, text='V1.%s.%s' % (len(cfg.shiptypes), macho.version), uppercase=True, top=43, left=82, fontsize=10, color=COLOR_FONT)
        Label(parent=cont, align=uiconst.TOPLEFT, text=GetByLabel('UI/ShipTree/MilitaryAndIndustrialVessels'), uppercase=True, top=49, fontsize=9, color=COLOR_FONT)
        self.AddSeperator(uiconst.TOLEFT)
        self.AddSeperator(uiconst.TORIGHT)
        Label(parent=ContainerAutoSize(align=uiconst.TORIGHT, parent=self, padLeft=4), align=uiconst.TOPLEFT, text=GetByLabel('UI/ShipTree/CourtesyLabel'), uppercase=True, top=49, fontsize=9, color=COLOR_FONT)
        self.AddSeperator(uiconst.TORIGHT)
        StretchSpriteHorizontal(parent=Container(parent=self, padding=(4, 0, 4, 0)), align=uiconst.TOBOTTOM, texturePath='res:/UI/Texture/classes/ShipTree/frame/bottomLine.png', leftEdgeSize=20, rightEdgeSize=20, height=2)

    def AddSeperator(self, align):
        Sprite(parent=Container(align=align, parent=self, width=40, padLeft=4), texturePath='res:/UI/Texture/classes/shipTree/frame/bottomSeperator.png', align=uiconst.TOBOTTOM, height=8)
