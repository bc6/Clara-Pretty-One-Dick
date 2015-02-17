#Embedded file name: eve/client/script/ui/shared/shipTree\shipTreeSvc.py
import service
import shipTreeConst
import geo2
import const
import log
from collections import defaultdict
from eve.client.script.ui.shared.shipTree.shipTreeConst import NODETYPE_CONNECTOR, NODETYPE_GROUP, NODETYPE_OTHERFACTIONGROUP, NODETYPE_ROOT
import uthread
from eve.client.script.ui.control.treeData import TreeData
from eve.client.script.ui.shared.monetization.trialPopup import ORIGIN_ISIS
K2 = 1.0 / 2
K3 = 1.0 / 3
K4 = 1.0 / 4
K8 = 1.0 / 8
K12 = 1.0 / 12
K24 = 1.0 / 24

class ShipTree(service.Service):
    """
    Provides data for the ship tree
    """
    __guid__ = 'svc.shipTree'
    __servicename__ = 'Ship tree service'
    __displayname__ = 'Ship tree service'

    def Run(self, *args):
        self.shipTypeIDsByFactionIDAndGroupID = None
        self._recentlyChangedSkills = None

    def GetGroupMaxRadius(self, factionID, shipGroupID):
        maxHeight = 0
        for typeID in self.GetShipTypeIDs(factionID, shipGroupID):
            try:
                diameter = self.GetShipDiameter(typeID)
                if diameter > maxHeight:
                    maxHeight = diameter
            except:
                log.LogException('FAILED to get bounding box for %s (%s)' % (cfg.invtypes.Get(typeID).name, typeID))

        return maxHeight / 2.0

    def GetGroupMaxHeight(self, factionID, shipGroupID):
        maxHeight = 0
        for typeID in self.GetShipTypeIDs(factionID, shipGroupID):
            try:
                p0, = self.GetShipBoundingBox(typeID)
                height = -p0[1]
                if height > maxHeight:
                    maxHeight = height
            except:
                log.LogException('FAILED to get bounding box for %s (%s)' % (cfg.invtypes.Get(typeID).name, typeID))

        return maxHeight

    def GetShipBoundingBox(self, typeID):
        g = cfg.invtypes.Get(typeID).Graphic()
        p0 = [g.graphicMinX, g.graphicMinY, g.graphicMinZ]
        p1 = [g.graphicMaxX, g.graphicMaxY, g.graphicMaxZ]
        return (p0, p1)

    def GetShipDiameter(self, typeID):
        p0, p1 = self.GetShipBoundingBox(typeID)
        return geo2.Vec3Distance(p0, p1)

    def GetShipTypeIDs(self, factionID, isisGroupID):
        if self.shipTypeIDsByFactionIDAndGroupID:
            if (factionID, isisGroupID) in self.shipTypeIDsByFactionIDAndGroupID:
                return self.shipTypeIDsByFactionIDAndGroupID[factionID, isisGroupID]
            return []
        self.shipTypeIDsByFactionIDAndGroupID = defaultdict(list)
        for groupObj in cfg.groupsByCategories[const.categoryShip]:
            if not groupObj.published:
                continue
            for typeObj in cfg.typesByGroups[groupObj.groupID]:
                typeID = typeObj.typeID
                try:
                    shipType = cfg.fsdTypeOverrides.Get(typeID)
                    key = (shipType.factionID, shipType.isisGroupID)
                    self.shipTypeIDsByFactionIDAndGroupID[key].append(typeID)
                except (KeyError, AttributeError):
                    pass

        if (factionID, isisGroupID) in self.shipTypeIDsByFactionIDAndGroupID:
            return self.shipTypeIDsByFactionIDAndGroupID[factionID, isisGroupID]
        return []

    def GetRootNode(self, factionID):
        """ Returns root node of ship tree representing the given factionID """
        if factionID == const.factionORE:
            return self._GetOREData(factionID)
        if factionID in (const.factionGuristasPirates,
         const.factionSanshasNation,
         const.factionTheBloodRaiderCovenant,
         const.factionAngelCartel,
         const.factionSerpentis,
         const.factionSistersOfEVE,
         const.factionMordusLegion):
            return self._GetPirateFactionData(factionID)
        return self._GetFactionData(factionID)

    def _GetFactionData(self, factionID):

        def Grp(parent, position, shipGroupID, iconsPerRow = 3):
            return GroupNode(parent=parent, position=position, shipGroupID=shipGroupID, iconsPerRow=iconsPerRow, factionID=factionID, treeID=factionID)

        def Con(parent, position):
            return ConnectorNode(parent=parent, position=position, treeID=factionID)

        root = RootNode(parent=None, position=(0, 0))
        c = Grp(root, (K2, 0), shipTreeConst.groupRookie)
        cIndustr = Con(c, (0, 3 * K4))
        c = Con(c, (3 * K4, 0))
        c = Con(c, (K12, -K12))
        c = Grp(c, (0, -K2), shipTreeConst.groupFrigate)
        c2 = Grp(c, (0, -K2), shipTreeConst.groupNavyFrigate, 4)
        c2 = Con(c2, (0, -K8))
        Grp(c2, (K3, -K3), shipTreeConst.groupInterceptor, 6)
        c2 = Con(c2, (0, -K2))
        Grp(c2, (K3, -K3), shipTreeConst.groupAssault, 6)
        c2 = Con(c2, (0, -K2))
        Grp(c2, (K3, -K3), shipTreeConst.groupCovertOps, 6)
        c2 = Con(c2, (0, -K2))
        Grp(c2, (K3, -K3), shipTreeConst.groupElectronicAttack, 6)
        c = Grp(c, (5 * K4, 0), shipTreeConst.groupDestroyer)
        c2 = Con(c, (0, -K3))
        Grp(c2, (K3, -K3), shipTreeConst.groupInterdictor)
        if factionID in (const.factionAmarrEmpire, const.factionMinmatarRepublic):
            c2 = Con(c2, (0, -K2))
            Grp(c2, (K3, -K3), shipTreeConst.groupTacticalDestroyer)
        c = Grp(c, (5 * K4, 0), shipTreeConst.groupCruiser)
        c2 = Grp(c, (0, -K2), shipTreeConst.groupNavyCruiser, 4)
        c2 = Con(c2, (0, -K4))
        Grp(c2, (K3, -K3), shipTreeConst.groupRecon, 6)
        c2 = Con(c2, (0, -K2))
        Grp(c2, (K3, -K3), shipTreeConst.groupHeavyAssault, 6)
        c2 = Con(c2, (0, -K2))
        Grp(c2, (K3, -K3), shipTreeConst.groupHeavyInterdictor, 6)
        c2 = Con(c2, (0, -K2))
        Grp(c2, (K3, -K3), shipTreeConst.groupLogistics, 6)
        c2 = Con(c2, (0, -K2))
        Grp(c2, (K2, -K2), shipTreeConst.groupStrategicCruiser, 6)
        c = Grp(c, (3 * K2, 0), shipTreeConst.groupBattlecruiser)
        c2 = Grp(c, (0, -K2), shipTreeConst.groupNavyBattlecruiser)
        c2 = Con(c2, (0, -K4))
        Grp(c2, (K3, -K3), shipTreeConst.groupCommandship)
        c = Grp(c, (6 * K4, 0), shipTreeConst.groupBattleship)
        c2 = Grp(c, (0, -K2), shipTreeConst.groupNavyBattleship)
        c2 = Con(c2, (0, -3 * K8))
        Grp(c2, (K3, -K3), shipTreeConst.groupBlackOps)
        c2 = Con(c2, (0, -K2))
        Grp(c2, (K3, -K3), shipTreeConst.groupMarauder)
        c = Con(c, (7 * K4, 0))
        Grp(c, (K4, 0), shipTreeConst.groupDreadnought)
        c = Con(c, (0, -2 * K2 + K12))
        Grp(c, (K3, -K3), shipTreeConst.groupCarrier)
        c = Con(c, (0, -2 * K2 - 3 * K24))
        Grp(c, (K3, -K3), shipTreeConst.groupTitan)
        c = Con(cIndustr, (K12, K12))
        c = Grp(c, (K2, 0), shipTreeConst.groupShuttle)
        c = Grp(c, (17 * K4, 0), shipTreeConst.groupIndustrial)
        c2 = Con(c, (0, -K8))
        Grp(c2, (K3, -K3), shipTreeConst.groupTransport)
        c = Grp(c, (3.0, 0), shipTreeConst.groupFreighter)
        c2 = Con(c, (0, -K8))
        Grp(c2, (K2, -K2), shipTreeConst.groupJumpFreighter)
        return root

    def _GetOREData(self, factionID):

        def Grp(parent, position, shipGroupID, iconsPerRow = 3):
            return GroupNode(parent=parent, position=position, shipGroupID=shipGroupID, iconsPerRow=iconsPerRow, factionID=factionID, treeID=factionID)

        def Con(parent, position):
            return ConnectorNode(parent=parent, position=position, treeID=factionID)

        root = RootNode(parent=None, position=(0, 0))
        c = Con(root, (K2, 0))
        cLeft = Con(c, (0, 0))
        cRight = Con(c, (0, 1.0))
        c = Grp(cLeft, (K2, 0), shipTreeConst.groupMiningFrigate)
        c1 = Con(c, (0, -K2))
        Grp(c1, (K2, -K2), shipTreeConst.groupExpeditionFrigate)
        c = Grp(c, (1.0, 0), shipTreeConst.groupMiningBarge)
        c2 = Con(c, (0, -K2))
        Grp(c2, (K2, -K2), shipTreeConst.groupExhumers)
        c = Grp(cRight, (3 * K2, 0), shipTreeConst.groupOreIndustrial)
        cDown = Con(c, (0, 1.0))
        c3 = Grp(cDown, (4 * K2, 0), shipTreeConst.groupFreighter)
        c = Grp(c, (1.0, 0), shipTreeConst.groupIndustrialCommand)
        c = Grp(c, (1.0, 0), shipTreeConst.groupCapitalIndustrial)
        return root

    def _GetPirateFactionData(self, factionID):

        def Grp(parent, position, shipGroupID, facID, showLinksTo, iconsPerRow = 3):
            return GroupNode(parent=parent, position=position, shipGroupID=shipGroupID, factionID=facID, showLinksTo=showLinksTo, treeID=factionID, iconsPerRow=iconsPerRow)

        def OtherGrp(parent, position, shipGroupID, facID, showLinksTo, iconsPerRow = 3):
            return OtherFactionGroupNode(parent=parent, position=position, shipGroupID=shipGroupID, factionID=facID, showLinksTo=showLinksTo, treeID=factionID, iconsPerRow=iconsPerRow)

        def Con(parent, position):
            return ConnectorNode(parent=parent, position=position, treeID=factionID)

        factionID1, factionID2 = shipTreeConst.PARENT_FACTIONIDS_BY_FACTIONID[factionID]
        root = c = RootNode(parent=None, position=(0, 0))
        for i, shipGroupID in enumerate((shipTreeConst.groupFrigate,
         shipTreeConst.groupCruiser,
         shipTreeConst.groupBattleship,
         shipTreeConst.groupCarrier)):
            if sm.GetService('shipTree').GetShipTypeIDs(factionID, shipGroupID):
                x = K2 if i == 0 else 3 * K4
                c = Grp(c, (x, 0), shipGroupID, factionID, False)
                top = OtherGrp(root, (K2 + i * x, -3 * K4), shipGroupID, factionID1, True)
                Grp(top, (0, 3 * K4), shipGroupID, factionID, False)
                bottom = OtherGrp(root, (K2 + i * x, 3 * K4), shipGroupID, factionID2, True)
                Grp(bottom, (0, -3 * K4), shipGroupID, factionID, False)

        return root

    def IsInShipTree(self, typeID):
        """ Is the ship to be found somewhere in the ship tree ? """
        return hasattr(cfg.fsdTypeOverrides.Get(typeID), 'isisGroupID')

    def GetRecentlyChangedSkills(self):
        if self._recentlyChangedSkills is not None:
            return self._recentlyChangedSkills
        uthread.Lock(self, 'GetRecentlyChangedSkills')
        try:
            if self._recentlyChangedSkills is None:
                self._recentlyChangedSkills = sm.GetService('skills').GetRecentlyTrainedSkills()
        finally:
            uthread.UnLock(self, 'GetRecentlyChangedSkills')

        return self._recentlyChangedSkills

    def IsShipMasteryRecentlyIncreased(self, typeID):
        masteryLevel = sm.GetService('certificates').GetCurrCharMasteryLevel(typeID)
        certs = sm.GetService('certificates').GetCertificatesForShipByMasteryLevel(typeID, masteryLevel)
        changed = self.GetRecentlyChangedSkills()
        for cert in certs:
            for skillTypeID, level in changed.iteritems():
                if skillTypeID in cert.skills:
                    currCertSkillLevel = cert.skills[skillTypeID][cert.currentLevel]
                    if currCertSkillLevel > level:
                        return True

        return False

    def IsGroupsRecentlyUnlocked(self, factionID):
        """ 
        Returns true if this faction has recently unlocked ship groups or recently improved masteries on ships
        """
        factionData = self.GetRootNode(factionID)
        shipGroups = [ node for node in factionData.GetDescendants().values() if isinstance(node, GroupNode) ]
        for shipGroup in shipGroups:
            if shipGroup.IsRecentlyUnlocked():
                return True

        return False

    def EmptyRecentlyChangedSkillsCache(self):
        self._recentlyChangedSkills = {}

    def FlushRecentlyChangedSkillsCache(self):
        self._recentlyChangedSkills = None

    def LogIGS(self, loggingType):
        int_1 = int_2 = int_3 = float_1 = 0
        if loggingType == 'FactionSwitch':
            int_1 = 1
        elif loggingType == 'HoverType':
            int_2 = 1
        elif loggingType == 'HoverGroup':
            int_3 = 1
        elif loggingType == 'OpenInISIS':
            float_1 = 1
        else:
            return
        sm.GetService('infoGatheringSvc').LogInfoEvent(eventTypeID=const.infoEventISISCounters, itemID=session.charid, int_1=int_1, int_2=int_2, int_3=int_3, float_1=float_1)

    def OpenSubscriptionPage(self, reason):
        uicore.cmd.OpenSubscriptionPage(origin=ORIGIN_ISIS, reason=':'.join(map(str, reason)))


class ShipTreeNodeBase(TreeData):
    __guid__ = 'shipTree.NodeBase'
    nodeType = None

    def __init__(self, treeID = None, showLinksTo = True, iconsPerRow = 3, *args, **kw):
        TreeData.__init__(self, *args, **kw)
        self._isLocked = None
        self._isRestricted = None
        self._isPathToElite = None
        self.showLinksTo = showLinksTo
        self.treeID = treeID
        self._boundingBox = None
        self._position = (0, 0)
        self._iconsPerRow = iconsPerRow

    def GetNodeType(self):
        return self.nodeType

    def GetDimensions(self):
        p0, p1 = self.GetBoundingBox()
        return geo2.Vec2Subtract(p1, p0)

    def GetCenter(self):
        p0, p1 = self.GetBoundingBox()
        return geo2.Vec3Lerp(p0, p1, 0.5)

    def GetPosition(self):
        return self._position

    def GetPositionProportional(self):
        rootNode = self.GetRootNode()
        (minX, minY), (maxX, maxY) = rootNode.GetBoundingBox()
        x, y = self.GetPosition()
        if minX == maxX:
            x = 0.0
        else:
            x = (x - minX) / (maxX - minX)
        if minY == maxY:
            y = 0.0
        else:
            y = (y - minY) / (maxY - minY)
        return (x, y)

    def SetPosition(self, position):
        self._position = position

    def GetBoundingBox(self):
        if self._boundingBox:
            return self._boundingBox
        minX, minY = self.GetPosition()
        maxX, maxY = self.GetPosition()
        children = self.GetChildren()
        if not children:
            return (self.GetPosition(), self.GetPosition())
        for child in self.GetChildren():
            (x1, y1), (x2, y2) = child.GetBoundingBox()
            minX = min(minX, x1, x2)
            minY = min(minY, y1, y2)
            maxX = max(maxX, x1, x2)
            maxY = max(maxY, y1, y2)

        self._boundingBox = ((minX, minY), (maxX, maxY))
        return self._boundingBox

    def GetGroupNodesByLevel(self):
        nodes = []
        self._GetGroupNodesByLevel(nodes, 0)
        return nodes

    def GetIconsPerRow(self):
        return self._iconsPerRow

    def IsAllChildrenElite(self):
        if not self.children:
            return self.IsElite()
        for child in self.children:
            if child.nodeType == NODETYPE_OTHERFACTIONGROUP:
                continue
            if not child._IsAllChildrenElite(child):
                return False

        return True

    def _IsAllChildrenElite(self, node):
        if not node.IsElite():
            return False
        for child in node.children:
            if not child._IsAllChildrenElite(child):
                return False

        return True

    def IsElite(self):
        return True

    def FlushCache(self):
        self._isLocked = None
        self._isRestricted = None
        self._isPathToElite = None
        for child in self.children:
            child.FlushCache()

    def IsPathToElite(self):
        """ Should the path to this node be drawn with elite visual effect ? """
        if self._isPathToElite is not None:
            return self._isPathToElite
        parNode = self
        while True:
            childNode = parNode
            parNode = parNode.parent
            if parNode is None or parNode.nodeType != NODETYPE_CONNECTOR:
                if childNode.nodeType == NODETYPE_CONNECTOR:
                    self._isPathToElite = childNode.IsAllChildrenElite()
                else:
                    self._isPathToElite = childNode.IsElite() and childNode.IsAllChildrenElite()
                return self._isPathToElite


class GroupNode(ShipTreeNodeBase):
    nodeType = NODETYPE_GROUP

    def __init__(self, shipGroupID, factionID, position, *args, **kw):
        ShipTreeNodeBase.__init__(self, *args, **kw)
        self.shipGroupID = shipGroupID
        self.factionID = factionID
        if self.parent:
            self.SetPosition(geo2.Add(self.parent.GetPosition(), position))
        else:
            self.SetPosition(position)

    def GetID(self):
        return self.shipGroupID

    def IsLocked(self):
        if self._isLocked is not None:
            return self._isLocked
        mySkills = sm.GetService('skills').MySkills(byTypeID=True)
        for skillTypeID, data in self._LoopInfoBubbleGroupsPreReqSkills():
            mySkill = mySkills.get(skillTypeID, None)
            if mySkill is None or mySkill.skillLevel < data['level']:
                self._isLocked = True
                return self._isLocked

        self._isLocked = False
        return self._isLocked

    def IsRestricted(self):
        if self._isRestricted is not None:
            return self._isRestricted
        for skillTypeID, _ in self._LoopInfoBubbleGroupsPreReqSkills():
            if sm.GetService('skills').IsTrialRestricted(skillTypeID):
                self._isRestricted = True
                break
        else:
            self._isRestricted = False

        return self._isRestricted

    def IsRecentlyUnlocked(self):
        if self.IsLocked():
            return False
        oldSkills = sm.GetService('shipTree').GetRecentlyChangedSkills()
        for skillTypeID, data in self._LoopInfoBubbleGroupsPreReqSkills():
            myOldLevel = oldSkills.get(skillTypeID, None)
            if myOldLevel is not None and myOldLevel < data['level']:
                return True

        return False

    def IsBeingTrained(self):
        skillQueue = sm.GetService('skillqueue').GetQueue()
        requiredSkills = self.GetRequiredSkills()
        for typeID, _ in skillQueue:
            if typeID in requiredSkills:
                return True

        return False

    def GetSkillLevel(self):
        """ Returns the level of the lowest required skill for this group """
        lowest = 5
        mySkills = sm.GetService('skills').MySkills(byTypeID=True)
        for skillTypeID, _ in self._LoopInfoBubbleGroupsPreReqSkills():
            mySkill = mySkills.get(skillTypeID, None)
            if not mySkill:
                return 0
            if mySkill.skillLevel < lowest:
                lowest = mySkill.skillLevel

        return lowest

    def GetRequiredSkills(self, onlyVisible = False):
        """ Returns a dict of skill levels by typeID """
        skillsWithLevel = {}
        for skillTypeID, data in self._LoopInfoBubbleGroupsPreReqSkills():
            if onlyVisible and not data['display']:
                continue
            skillsWithLevel[skillTypeID] = data['level']

        return skillsWithLevel

    def GetRequiredSkillsSorted(self, onlyVisible = False):
        """ Returns a sorted list of (typeID, skillLevel) tuples """

        def Compare(x, y):
            typeID1, level1 = x
            typeID2, level2 = y
            if level1 != level2:
                return level2 - level1
            typeName1 = cfg.invtypes.Get(typeID1).typeName
            typeName2 = cfg.invtypes.Get(typeID2).typeName
            if typeName1 > typeName2:
                return 1
            else:
                return -1

        skills = self.GetRequiredSkills(onlyVisible)
        skills = [ (typeID, level) for typeID, level in skills.iteritems() ]
        return sorted(skills, cmp=Compare)

    def _LoopInfoBubbleGroupsPreReqSkills(self):
        infoBubbleGroupPreReqSkills = cfg.fsdInfoBubbleGroups[self.shipGroupID].preReqSkills
        if self.factionID in infoBubbleGroupPreReqSkills:
            skillData = infoBubbleGroupPreReqSkills[self.factionID]['skills']
            for skillTypeID, data in skillData.iteritems():
                yield (skillTypeID, data)

    def GetBonusSkills(self):
        """ Returns a dict of skill levels by typeID """
        return self.GetRequiredSkills(onlyVisible=True)

    def GetBonusSkillsSorted(self):
        """ Returns a sorted list of (typeID, skillLevel) tuples """
        return self.GetRequiredSkillsSorted(onlyVisible=True)

    def _GetGroupNodesByLevel(self, nodes, level):
        if len(nodes) <= level:
            nodes.append([])
        nodes[level].append(self)
        for child in self.GetChildren():
            child._GetGroupNodesByLevel(nodes, level + 1)

    def GetIconSize(self):
        if self.shipGroupID in (shipTreeConst.groupJumpFreighter, shipTreeConst.groupFreighter):
            rigSize = 4
        else:
            typeIDs = self.GetShipTypeIDs()
            if typeIDs:
                rigSize = sm.GetService('godma').GetType(typeIDs[0]).rigSize
            else:
                rigSize = 0
        return 82 + 16 * rigSize

    def IsElite(self):
        if self.IsLocked():
            return False
        for typeID in self.GetShipTypeIDs():
            masteryLevel = sm.GetService('certificates').GetCurrCharMasteryLevel(typeID)
            if masteryLevel != 5:
                return False

        return True

    def GetShipTypeIDs(self):
        return sm.GetService('shipTree').GetShipTypeIDs(self.factionID, self.shipGroupID)

    def GetTimeToUnlock(self):
        """ Returns amount of skill training time required to unlock group """
        typeIDs = self.GetShipTypeIDs()
        if typeIDs:
            return sm.GetService('skills').GetSkillTrainingTimeLeftToUseType(typeIDs[0])
        return 0

    def GetGroupWidth(self):
        """ Returns group width in pixels """
        numIcons = min(len(self.GetShipTypeIDs()), self.GetIconsPerRow())
        return (self.GetIconSize() + 1) * numIcons


class OtherFactionGroupNode(GroupNode):
    nodeType = NODETYPE_OTHERFACTIONGROUP


class ConnectorNode(ShipTreeNodeBase):
    nodeType = NODETYPE_CONNECTOR

    def __init__(self, position, *args, **kw):
        ShipTreeNodeBase.__init__(self, *args, **kw)
        self._skillLevel = None
        if self.parent:
            self.SetPosition(geo2.Add(self.parent.GetPosition(), position))
        else:
            self.SetPosition(position)

    def GetID(self):
        return '%s_%s' % self.GetPosition()

    def IsLocked(self):
        if self._isLocked is not None:
            return self._isLocked
        for child in self.GetChildren():
            if not child.IsLocked():
                self._isLocked = False
                return self._isLocked

        self._isLocked = True
        return self._isLocked

    def GetSkillLevel(self):
        if self._skillLevel is not None:
            return self._skillLevel
        self._skillLevel = max([ child.GetSkillLevel() for child in self.GetChildren() ])
        return self._skillLevel

    def _GetGroupNodesByLevel(self, nodes, level):
        for child in self.GetChildren():
            child._GetGroupNodesByLevel(nodes, level)


class RootNode(ConnectorNode):
    nodeType = NODETYPE_ROOT
