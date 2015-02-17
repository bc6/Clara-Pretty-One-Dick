#Embedded file name: eve/client/script/ui/inflight\drone.py
from carbon.common.script.util.timerstuff import AutoTimer
from eve.client.script.ui.inflight.actions import ActionPanel
import uiprimitives
import uicontrols
from eve.client.script.ui.inflight.baseTacticalEntry import BaseTacticalEntry
import uix
import uiutil
import blue
from eveDrones.droneConst import DAMAGESTATE_NOT_READY
from eveInflight.damageStateValue import CalculateCurrentDamageStateValues
import uthread
import util
from eve.client.script.ui.control import entries as listentry
import state
import carbonui.const as uiconst
import localization
import itertoolsext
import log
import eve.common.script.mgt.entityConst as entities
from eve.client.script.ui.control.listgroup import ListGroup as Group
from eve.client.script.ui.services.menuSvcExtras.droneFunctions import ReturnToDroneBay

class DroneEntry(BaseTacticalEntry):
    """
    Display drones inspace in DroneView.
    
    (For drones in bay we use standard inventory entry.)    
    """
    __guid__ = 'listentry.DroneEntry'
    isDragObject = True
    __notifyevents__ = ['OnStateChange', 'OnDroneStateChange2', 'OnDroneActivityChange']

    def UpdateDamage(self):
        if self.destroyed:
            self.sr.dmgTimer = None
            return
        if self.sr.node.droneState == 'inbay':
            return self.UpdateDamageInBay()
        return BaseTacticalEntry.UpdateDamage(self)

    def UpdateDamageInBay(self):
        droneID = self.GetShipID()
        dmg = self.GetDamageInBay(droneID)
        ret = False
        if dmg is not None:
            if self.sr.dmgTimer is None:
                self.sr.dmgTimer = AutoTimer(1000, self.UpdateDamage)
            if dmg == DAMAGESTATE_NOT_READY:
                return
            ret = self.SetDamageState(dmg)
            self.ShowDamageDisplay()
        else:
            self.HideDamageDisplay()
        return ret

    def GetDamageInBay(self, itemID):
        if self.sr.node.damageState == DAMAGESTATE_NOT_READY:
            if not getattr(self, 'fetchingDamageValue', False):
                self.fetchingDamageValue = True
                uthread.new(self.SetDamageValue_thread, itemID)
            return DAMAGESTATE_NOT_READY
        if self.sr.node.damageState:
            damageInMichelleFormat = self.sr.node.damageState.GetInfoInMichelleFormat()
            time = self.sr.node.damageState.timestamp
            ret = CalculateCurrentDamageStateValues(damageInMichelleFormat, time)
            return ret

    def SetDamageValue_thread(self, droneID):
        self.sr.node.damageState = sm.GetService('tactical').GetInBayDroneDamageTracker().GetDamageStateForDrone(droneID)
        self.fetchingDamageValue = False

    def OnMouseDown(self, *args):
        uthread.new(self.OnMouseDown_thread)

    def OnMouseDown_thread(self):
        selelectedDrones = self.sr.node.scroll.GetSelectedNodes(self.sr.node)
        droneState = self.sr.node.droneState
        displayLabel = self.sr.node.label
        if len(selelectedDrones) > 1:
            displayLabel += '<fontsize=14> + %s' % (len(selelectedDrones) - 1)
        if droneState == 'inbay':
            nodesData = [ (drone.invItem, 0, None) for drone in selelectedDrones if drone.invItem is not None ]
            manyItemsData = uiutil.Bunch(menuFunction=sm.GetService('menu').InvItemMenu, itemData=nodesData, displayName='<b>%s</b>' % displayLabel)
        elif droneState in ('inlocalspace', 'inDistantSpace'):
            if len(selelectedDrones) > 1:
                nodesData = [ (drone.itemID, cfg.invtypes.Get(drone.typeID).groupID, drone.ownerID) for drone in selelectedDrones if drone.typeID ]
                manyItemsData = uiutil.Bunch(menuFunction=sm.GetService('menu').GetDroneMenu, itemData=nodesData, displayName='<b>%s</b>' % displayLabel)
            else:
                manyItemsData = None
        else:
            return
        sm.GetService('menu').TryExpandActionMenu(itemID=self.sr.node.itemID, typeID=self.sr.node.typeID, clickedObject=self, manyItemsData=manyItemsData)

    def Startup(self, *args):
        BaseTacticalEntry.Startup(self, *args)
        self.activityID = None
        self.activity = None
        text_gaugeContainer = uiprimitives.Container(name='text_gaugeContainer', parent=self, idx=0, pos=(0, 0, 0, 0))
        self.sr.gaugesContainer = uiprimitives.Container(name='gaugesContainer', parent=text_gaugeContainer, width=85, align=uiconst.TORIGHT, state=uiconst.UI_HIDDEN)
        tClip = uiprimitives.Container(name='textClipper', parent=text_gaugeContainer, state=uiconst.UI_PICKCHILDREN, clipChildren=1)
        uiutil.Transplant(self.sr.label, tClip)

    def Load(self, node):
        BaseTacticalEntry.Load(self, node)
        if self.sr.node.droneState in ('inlocalspace', 'indistantspace'):
            self.UpdateState()
        self.sr.gaugesContainer.state = uiconst.UI_PICKCHILDREN

    def UpdateState(self, droneState = None):
        michelle = sm.GetService('michelle')
        droneRow = michelle.GetDroneState(self.sr.node.itemID)
        droneActivity = michelle.GetDroneActivity(self.sr.node.itemID)
        if droneActivity:
            self.activity, self.activityID = droneActivity
        if droneState is None and droneRow is not None:
            droneState = droneRow.activityState
        droneStates = {entities.STATE_IDLE: 'UI/Inflight/Drone/Idle',
         entities.STATE_COMBAT: 'UI/Inflight/Drone/Fighting',
         entities.STATE_MINING: 'UI/Inflight/Drone/Mining',
         entities.STATE_APPROACHING: 'UI/Inflight/Drone/Approaching',
         entities.STATE_DEPARTING: 'UI/Inflight/Drone/ReturningToShip',
         entities.STATE_DEPARTING_2: 'UI/Inflight/Drone/ReturningToShip',
         entities.STATE_OPERATING: 'UI/Inflight/Drone/Operating',
         entities.STATE_PURSUIT: 'UI/Inflight/Drone/Following',
         entities.STATE_FLEEING: 'UI/Inflight/Drone/Fleeing',
         entities.STATE_ENGAGE: 'UI/Inflight/Drone/Repairing',
         entities.STATE_SALVAGING: 'UI/Inflight/Drone/Salvaging',
         None: 'UI/Inflight/Drone/NoState'}
        droneStateLabel = droneStates.get(droneState, 'UI/Inflight/Drone/Incapacitated')
        stateText = localization.GetByLabel(droneStateLabel)
        label = localization.GetByLabel('UI/Inflight/Drone/Label', droneType=self.sr.node.label, state=stateText)
        target = ''
        if droneState in [const.entityCombat, const.entityEngage, const.entityMining]:
            targetID = droneRow.targetID
            targetTypeName = None
            pilotName = None
            if targetID:
                targetSlim = michelle.GetItem(targetID)
                if targetSlim:
                    if targetSlim.groupID == const.categoryShip:
                        pilotID = michelle.GetCharIDFromShipID(targetSlim.itemID)
                        if pilotID:
                            pilotName = cfg.eveowners.Get(pilotID).name
                    targetTypeName = uix.GetSlimItemName(targetSlim)
            if pilotName:
                target = pilotName
            elif targetTypeName:
                target = targetTypeName
            else:
                target = localization.GetByLabel('UI/Generic/Unknown')
        tooltipExtra = ''
        if self.sr.node.ownerID != eve.session.charid:
            tooltipExtra = localization.GetByLabel('UI/Inflight/Drone/OwnershipText', owner=self.sr.node.ownerID)
        elif self.sr.node.controllerID != eve.session.shipid:
            tooltipExtra = localization.GetByLabel('UI/Inflight/Drone/ControllerText', controller=self.sr.node.controllerOwnerID)
        elif self.activityID and self.activity:
            activity = ''
            if self.activity == 'guard':
                activity = localization.GetByLabel('UI/Inflight/Drone/Guarding')
            elif self.activity == 'assist':
                activity = localization.GetByLabel('UI/Inflight/Drone/Assisting')
            tooltipExtra = localization.GetByLabel('UI/Inflight/Drone/Activity', activity=activity, idInfo=cfg.eveowners.Get(self.activityID).name)
        tooltip = localization.GetByLabel('UI/Inflight/Drone/Tooltip', droneType=self.sr.node.label, state=stateText, target=target, tooltipExtra=tooltipExtra)
        self.sr.label.text = label
        self.hint = tooltip

    def GetHeight(self, *args):
        node, width = args
        node.height = uix.GetTextHeight('Xg', maxLines=1) + 4
        return node.height

    def OnDroneStateChange2(self, droneID, oldActivityState, newActivityState):
        if not self or getattr(self, 'sr', None) is None:
            return
        if self.sr.node and self.sr.node.droneState in ('inlocalspace', 'indistantspace') and droneID == self.sr.node.itemID:
            droneRow = sm.GetService('michelle').GetDroneState(self.sr.node.itemID)
            if droneRow:
                self.sr.node.controllerID = droneRow.controllerID
                self.sr.node.controllerOwnerID = droneRow.controllerOwnerID
                self.UpdateState(newActivityState)

    def OnDroneActivityChange(self, droneID, activityID, activity):
        if not self or getattr(self, 'sr', None) is None:
            return
        if self.sr.node and self.sr.node.droneState in ('inlocalspace', 'indistantspace') and droneID == self.sr.node.itemID:
            self.activity = activity
            self.activityID = activityID
            self.UpdateState()

    def OnClick(self, *args):
        if self.sr.node:
            self.sr.node.scroll.SelectNode(self.sr.node)
            eve.Message('ListEntryClick')
            if not uicore.uilib.Key(uiconst.VK_CONTROL):
                if not uicore.uilib.Key(uiconst.VK_SHIFT):
                    sm.GetService('state').SetState(self.sr.node.itemID, state.selected, 1)
            else:
                sm.GetService('target').TryLockTarget(self.sr.node.itemID)

    def GetSelected(self):
        ids = []
        sel = self.sr.node.scroll.GetSelectedNodes(self.sr.node)
        for node in sel:
            if node.Get('typeID', None) is None:
                continue
            if cfg.invtypes.Get(node.typeID).groupID == cfg.invtypes.Get(self.sr.node.typeID).groupID:
                ids.append(node.itemID)

        return ids

    def GetSelectedItems(self):
        items = []
        sel = self.sr.node.scroll.GetSelectedNodes(self.sr.node)
        for node in sel:
            items.append(node.invItem)

        return items

    def GetMenu(self):
        m = []
        if self.sr.node.customMenu:
            m += self.sr.node.customMenu(self.sr.node)
        if self.sr.node.droneState != 'inbay':
            args = []
            droneData = []
            selected = self.sr.node.scroll.GetSelectedNodes(self.sr.node)
            for node in selected:
                if node.Get('typeID', None) is None:
                    continue
                args.append((self.sr.node.itemID,
                 None,
                 None,
                 0,
                 self.sr.node.typeID,
                 None,
                 None))
                droneData.append((node.itemID, cfg.invtypes.Get(node.typeID).groupID, eve.session.charid))

            if droneData:
                m += self.DroneMenu(droneData)
            m += sm.GetService('menu').CelestialMenu(args, ignoreDroneMenu=1)
        else:
            selected = self.GetSelectedItems()
            args = []
            for rec in selected:
                if rec is None:
                    continue
                args.append((rec, 0, 0))

            filterFunc = [uiutil.MenuLabel('UI/Inventory/ItemActions/BuyThisType'),
             uiutil.MenuLabel('UI/Inventory/ItemActions/AddTypeToMarketQuickbar'),
             uiutil.MenuLabel('UI/Inventory/ItemActions/ViewTypesMarketDetails'),
             uiutil.MenuLabel('UI/Inventory/ItemActions/FindInContracts')]
            m += sm.GetService('menu').InvItemMenu(args, filterFunc=filterFunc)
        return m

    def DroneMenu(self, droneData):
        menuSvc = sm.GetService('menu')
        specialDroneData = []
        for droneID, groupID, ownerID in droneData:
            if cfg.invtypes.Get(self.sr.node.typeID).groupID == groupID:
                specialDroneData.append([droneID, groupID, ownerID])

        menu = menuSvc.GetGroupSpecificDroneMenu(specialDroneData)
        menu += menuSvc.GetCommonDroneMenu(droneData)
        return menu

    def SelectAll(self):
        self.sr.node.scroll.SelectAll()
        sel = self.GetSelected()
        if len(sel) > 1:
            sm.ScatterEvent('OnMultiSelect', sel)

    def InitGauges(self):
        if getattr(self, 'gaugesInited', False):
            self.sr.gaugeParent.state = uiconst.UI_DISABLED
            return
        parent = self.sr.gaugesContainer
        uiprimitives.Line(parent=parent, align=uiconst.TOLEFT)
        barw, barh = (24, 6)
        borderw = 2
        barsw = (barw + borderw) * 3 + borderw
        par = uiprimitives.Container(name='gauges', parent=parent, align=uiconst.TORIGHT, width=barsw + 2, height=0, left=0, top=0, idx=10)
        self.sr.gauges = []
        l = 2
        for each in ('SHIELD', 'ARMOR', 'STRUCT'):
            g = uiprimitives.Container(parent=par, name='gauge_%s' % each.lower(), align=uiconst.CENTERLEFT, width=barw, height=barh, left=l)
            uicontrols.Frame(parent=g)
            g.sr.bar = uiprimitives.Fill(parent=g, name='droneGaugeBar', align=uiconst.TOLEFT)
            uiprimitives.Fill(parent=g, name='droneGaugeBarDmg', color=(158 / 256.0,
             11 / 256.0,
             14 / 256.0,
             1.0))
            self.sr.gauges.append(g)
            setattr(self.sr, 'gauge_%s' % each.lower(), g)
            l += barw + borderw

        self.sr.gaugeParent = par
        self.gaugesInited = True

    def GetDragData(self, *args):
        return [ node for node in self.sr.node.scroll.GetSelectedNodes(self.sr.node) if node.__guid__ == 'listentry.DroneEntry' ]


class DroneView(ActionPanel):
    """
    Represent drones in space and in drone bay.
    
    Part of the tactical overview.
    """
    __guid__ = 'form.DroneView'
    __notifyevents__ = ['OnItemLaunch',
     'OnDroneControlLost',
     'ProcessSessionChange',
     'OnAttribute',
     'OnAttributes',
     'OnItemChange']
    default_windowID = 'droneview'
    default_pinned = True

    @staticmethod
    def default_top(*args):
        topRight_TopOffset = uicontrols.Window.GetTopRight_TopOffset()
        if topRight_TopOffset is not None:
            return topRight_TopOffset
        return 16

    @staticmethod
    def default_left(*args):
        return uicore.desktop.width - DroneView.default_width - 16

    def ApplyAttributes(self, attributes):
        self.fafDefVal = cfg.dgmattribs.Get(const.attributeFighterAttackAndFollow).defaultValue
        self.droneAggressionDefVal = cfg.dgmattribs.Get(const.attributeDroneIsAggressive).defaultValue
        self.droneFFDefVal = cfg.dgmattribs.Get(const.attributeDroneFocusFire).defaultValue
        ActionPanel.ApplyAttributes(self, attributes)

    def OnItemLaunch(self, ids):
        reload = False
        for oldID, newIDs in ids.iteritems():
            group = self.GetDroneGroup(oldID)
            if group is not None:
                for newID in newIDs:
                    if newID != oldID:
                        group['droneIDs'].add(newID)
                        reload = True

        if reload:
            self.UpdateGroupSettings()
            self.CheckDrones(True)

    def ProcessSessionChange(self, *etc):
        self.CheckDrones(True)

    ProcessSessionChange = util.Uthreaded(ProcessSessionChange)

    def OnDroneControlLost(self, droneID):
        self.CheckDrones(True)

    def OnAttributes(self, l):
        for attributeName, item, newValue in l:
            self.OnAttribute(attributeName, item, newValue)

    def OnAttribute(self, attributeName, item, newValue):
        if not self or self.destroyed:
            return
        if item.itemID == session.charid and attributeName == 'maxActiveDrones':
            t = self.sr.lastUpdate
            if t is None:
                self.CheckDrones()
            else:
                self.UpdateHeader(t[0], t[1] + t[2])

    def OnItemChange(self, item, change):
        if item.locationID == session.shipid:
            if item.flagID == const.flagDroneBay or change.get(const.ixFlag, None) == const.flagDroneBay:
                ignoreClose = session.solarsystemid == change.get(const.ixLocationID, None)
                self.CheckDrones(ignoreClose=ignoreClose)
        elif change.get(const.ixLocationID, None) == session.shipid and change.get(const.ixFlag, None) == const.flagDroneBay:
            self.CheckDrones()

    def PostStartup(self):
        if not self or self.destroyed:
            return
        self.SetTopparentHeight(0)
        self.SetMinSize((240, 80))
        self.SetUtilMenu(utilMenuFunc=self.DroneSettings)
        self.sr.scroll = uicontrols.Scroll(name='dronescroll', align=uiconst.TOALL, parent=self.sr.main)
        self.sr.scroll.multiSelect = 1
        self.sr.scroll.OnChar = self.OnDronesScrollChar
        self.sr.inSpace = None
        self.sr.lastUpdate = None
        self.settingsName = 'droneBlah2'
        self.reloading = 0
        self.pending = None
        openState = uicore.registry.GetListGroupOpenState(('dronegroups', 'inbay'), default=False)
        uicore.registry.GetLockedGroup('dronegroups', 'inbay', localization.GetByLabel('UI/Inflight/Drone/DronesInBay'), openState=openState)
        openState = uicore.registry.GetListGroupOpenState(('dronegroups', 'inlocalspace'), default=False)
        uicore.registry.GetLockedGroup('dronegroups', 'inlocalspace', localization.GetByLabel('UI/Inflight/Drone/DronesInLocalSpace'), openState=openState)
        uicore.registry.GetLockedGroup('dronegroups', 'indistantspace', localization.GetByLabel('UI/Inflight/Drone/DronesInDistantSpace'))
        self.groups = self.SettifyGroups(settings.user.ui.Get(self.settingsName, {}))
        droneSettingChanges = {}
        droneSettingChanges[const.attributeDroneIsAggressive] = settings.char.ui.Get('droneAggression', self.droneAggressionDefVal)
        droneSettingChanges[const.attributeFighterAttackAndFollow] = settings.char.ui.Get('fighterAttackAndFollow', self.fafDefVal)
        droneSettingChanges[const.attributeDroneFocusFire] = settings.char.ui.Get('droneFocusFire', self.droneFFDefVal)
        sm.GetService('godma').GetStateManager().ChangeDroneSettings(droneSettingChanges)
        if self and not self.destroyed:
            uthread.new(self.CheckDrones)

    def OnDronesScrollChar(self, *args):
        """
        Needed for combat shortcuts to work while focus is on the scroll
        """
        return False

    def GroupXfier(fn):

        def XfyGroup(group):
            """
            Return a copy of a group with some transformation applied to its
            droneIDs. 
            """
            ret = group.copy()
            ret['droneIDs'] = fn(group['droneIDs'])
            return ret

        return lambda self, groups: dict([ (name, XfyGroup(group)) for name, group in groups.iteritems() ])

    ListifyGroups = GroupXfier(list)
    SettifyGroups = GroupXfier(set)
    del GroupXfier

    def GetSelected(self, fromNode):
        nodes = []
        sel = self.sr.scroll.GetSelectedNodes(fromNode)
        for node in sel:
            if node.Get('typeID', None) is None:
                continue
            if cfg.invtypes.Get(node.typeID).groupID == cfg.invtypes.Get(fromNode.typeID).groupID:
                if node.droneState == fromNode.droneState:
                    nodes.append(node)

        return nodes

    def UpdateHeader(self, inBay, inSpace):
        self.SetCaption(localization.GetByLabel('UI/Inflight/Drone/PanelHeader', panelName=self.panelname, inSpace=len(inSpace), maxTotal=int(sm.GetService('godma').GetItem(session.charid).maxActiveDrones) or 0))

    def UpdateAll(self):
        if self.sr.main.state != uiconst.UI_PICKCHILDREN:
            self.sr.actionsTimer = None
            return
        self.CheckDrones()

    def GetSubGroups(self, what):
        return []

    def CheckDrones(self, force = False, ignoreClose = False, *args):
        if session.stationid:
            return
        if not self.pending:
            self.pending = ('updating',)
        else:
            if 'updating' in self.pending:
                self.pending = ('pending', force, ignoreClose)
                return
            if 'pending' in self.pending:
                return
        if self.destroyed:
            return
        inBay = self.GetDronesInBay()
        inBayIDs = [ drone.itemID for drone in inBay ]
        inBayIDs.sort()
        uthread.new(sm.GetService('tactical').GetInBayDroneDamageTracker().FetchInBayDroneDamageToServer, inBayIDs)
        inLocalSpace = [ drone for drone in self.GetDronesInLocalSpace() if drone.droneID not in inBayIDs ]
        inLocalSpaceIDs = [ drone.droneID for drone in inLocalSpace ]
        inLocalSpaceIDs.sort()
        inDistantSpace = [ drone for drone in self.GetDronesInDistantSpace() if drone.droneID not in inBayIDs ]
        inDistantSpaceIDs = [ drone.droneID for drone in inDistantSpace ]
        inDistantSpaceIDs.sort()
        t = (inBayIDs, inLocalSpaceIDs, inDistantSpaceIDs)
        if self.sr.lastUpdate != t or force or inDistantSpace:
            self.sr.lastUpdate = t
            groupInfo = uicore.registry.GetListGroup(('dronegroups', 'inbay'))
            scrolllist = self.GetGroupListEntry(groupInfo, 'inbay', inBayIDs)
            groupInfo = uicore.registry.GetListGroup(('dronegroups', 'inlocalspace'))
            scrolllist += self.GetGroupListEntry(groupInfo, 'inlocalspace', inLocalSpaceIDs)
            if inDistantSpaceIDs:
                groupInfo = uicore.registry.GetListGroup(('dronegroups', 'indistantspace'))
                scrolllist += self.GetGroupListEntry(groupInfo, 'indistantspace', inDistantSpaceIDs)
            self.sr.scroll.Load(contentList=scrolllist)
        self.UpdateHeader(inBayIDs, inLocalSpaceIDs + inDistantSpaceIDs)
        self.CheckHint()
        blue.pyos.synchro.SleepWallclock(500)
        if not self or self.destroyed:
            return
        if 'pending' in self.pending:
            p, force, ignoreClose = self.pending
            self.pending = None
            self.CheckDrones(force, ignoreClose)
            return
        self.pending = None
        if not ignoreClose and not self.destroyed:
            self.CheckClose()

    def CheckClose(self):
        if not (self.GetDronesInBay() or sm.GetService('michelle').GetDrones()) and hasattr(self, 'Close'):
            self.Close()

    def GetMainFolderMenu(self, node):
        m = [None]
        delMenu = [ (groupName, self.DeleteGroup, (groupName,)) for groupName, groupInfo in self.groups.iteritems() ]
        if delMenu:
            m += [(uiutil.MenuLabel('UI/Commands/DeleteGroup'), delMenu), None]
        data = self.GetDroneDataForMainGroup(node)
        if not data:
            return m
        if node.droneState in ('inlocalspace', 'indistantspace'):
            m += sm.GetService('menu').GetDroneMenu(data)
        else:
            filterFunc = [uiutil.MenuLabel('UI/Inventory/ItemActions/BuyThisType'),
             uiutil.MenuLabel('UI/Inventory/ItemActions/AddTypeToMarketQuickbar'),
             uiutil.MenuLabel('UI/Inventory/ItemActions/ViewTypesMarketDetails'),
             uiutil.MenuLabel('UI/Inventory/ItemActions/FindInContracts')]
            m += sm.GetService('menu').InvItemMenu(data, filterFunc=filterFunc)
        return m

    def GetNodesToMoveAround(self, nodes):
        """
            returns the drones nodes that belong to 'nodes'.
            That is, if we are dragging a group, we get the drones that belong to that group, otherwise just
            the original nodes
        """
        if len(nodes) > 1:
            return nodes
        firstNode = nodes[0]
        if firstNode['__guid__'] == 'listentry.DroneSubGroup':
            nodes = self.GetSubGroupContent(firstNode)
        elif firstNode['__guid__'] == 'listentry.DroneMainGroup':
            nodes = self.GetAllMainGroupContent(firstNode)
        return nodes

    def GroupDropData(self, dragObj, nodes):
        groupState = dragObj[1]
        self.LaunchOrPullDrones(groupState, nodes)

    def GetAllMainGroupContent(self, nodedata):
        nodes = self.GetGroupContent(nodedata)
        myNodes = []
        for eachNode in nodes:
            if eachNode.decoClass == DroneSubGroup:
                myNodes += self.GetSubGroupContent(eachNode)
            else:
                myNodes.append(eachNode)

        return myNodes

    def SubGroupDropData(self, dragObj, nodes):
        groupState = dragObj[0]
        groupNameAndID = dragObj[1]
        groupName = groupNameAndID[0]
        nodes = self.GetNodesToMoveAround(nodes)
        dronesWithChangedState = self.LaunchOrPullDrones(groupState, nodes)
        self.MoveDronesToSubGroup(groupName=groupName, nodes=nodes, excludedDrones=dronesWithChangedState)

    def MoveDronesToSubGroup(self, groupName, nodes, excludedDrones = []):
        subGroupInfo = self.GetSubGroup(groupName)
        movingDrones = []
        for droneNode in nodes:
            if droneNode in excludedDrones:
                continue
            if droneNode.itemID not in subGroupInfo['droneIDs']:
                movingDrones.append(droneNode)

        if movingDrones:
            firstDrone = movingDrones[0]
            self.MoveToGroup(groupName, firstDrone.itemID, cfg.invtypes.Get(firstDrone.typeID).groupID, movingDrones)

    def LaunchOrPullDrones(self, groupState, nodes, *args):
        nodes = self.GetNodesToMoveAround(nodes)
        changingState = []
        for droneNode in nodes:
            if droneNode.droneState in ('inlocalspace', 'inbay') and droneNode.droneState != groupState:
                changingState.append(droneNode)

        if changingState:
            if groupState == 'inlocalspace':
                sm.GetService('menu').LaunchDrones([ droneNode.invItem for droneNode in changingState ])
            elif groupState == 'inbay':
                ReturnToDroneBay([ droneNode.itemID for droneNode in changingState ])
        return changingState

    def DeleteGroup(self, groupName):
        self.EmptyGroup(groupName)
        if groupName in self.groups:
            del self.groups[groupName]
        self.UpdateGroupSettings()
        self.UpdateAll()

    def GetSubFolderMenu(self, node):
        m = [None]
        data = self.GetDroneDataForSubGroup(node)
        if not data:
            return m
        if node.droneState in ('inlocalspace', 'indistantspace'):
            droneMenu = sm.GetService('menu').GetDroneMenu(data)
            m += droneMenu
        elif node.droneState == 'inbay':
            filterFunc = [uiutil.MenuLabel('UI/Inventory/ItemActions/BuyThisType'),
             uiutil.MenuLabel('UI/Inventory/ItemActions/AddTypeToMarketQuickbar'),
             uiutil.MenuLabel('UI/Inventory/ItemActions/ViewTypesMarketDetails'),
             uiutil.MenuLabel('UI/Inventory/ItemActions/FindInContracts')]
            m += sm.GetService('menu').InvItemMenu(data, filterFunc=filterFunc)
        return m

    def GroupMenu(self, droneNode):
        selected = self.GetSelected(droneNode)
        m = []
        move = [(uiutil.MenuLabel('UI/Commands/NewGroup'), self.CreateSubGroup, (droneNode.itemID, cfg.invtypes.Get(droneNode.typeID).groupID, selected))]
        inGroup = []
        for node in selected:
            group = self.GetDroneGroup(node.itemID)
            if group:
                inGroup.append(node)

        if inGroup:
            move += [(uiutil.MenuLabel('UI/Commands/OutOfThisGroup'), self.NoGroup, (inGroup,))]
        groupNames = self.groups.keys()[:]
        groupNames.sort(key=lambda x: x.lower())
        move += [ (groupName, self.MoveToGroup, (groupName,
          droneNode.itemID,
          cfg.invtypes.Get(droneNode.typeID).groupID,
          selected)) for groupName in groupNames ]
        m += [(uiutil.MenuLabel('UI/Commands/MoveDrone'), move)]
        return m

    def GetEmptyGroups(self):
        empty = []
        for groupName, groupInfo in self.groups.iteritems():
            if not groupInfo['droneIDs']:
                empty.append(groupName)

        return empty

    def DeleteEmptyGroups(self, *args):
        for groupName in self.GetEmptyGroups():
            del self.groups[groupName]

    def GetDroneGroup(self, droneID, getall = 0):
        retall = []
        for groupName, group in self.groups.iteritems():
            if droneID in group['droneIDs']:
                if getall:
                    retall.append(group)
                else:
                    return group

        if getall:
            return retall

    def NoGroup(self, nodes):
        for node in nodes:
            for group in self.GetDroneGroup(node.itemID, getall=1):
                group['droneIDs'].remove(node.itemID)

        self.CheckDrones(1)
        self.UpdateGroupSettings()

    def EmptyGroup(self, groupName):
        droneGroup = self.GetSubGroup(groupName)
        for droneID in droneGroup.get('droneIDs', set()).copy():
            for group in self.GetDroneGroup(droneID, getall=1):
                group['droneIDs'].remove(droneID)

        self.CheckDrones(1)

    def MoveToGroup(self, groupName, droneID, droneGroupID, nodes):
        group = self.GetSubGroup(groupName)
        if group['droneIDs'] and group['droneGroupID'] != droneGroupID:
            eve.Message('CannotMixDrones')
            return
        for node in nodes:
            for group in self.GetDroneGroup(node.itemID, getall=1):
                group['droneIDs'].remove(node.itemID)

        group = self.GetSubGroup(groupName)
        if not group['droneIDs']:
            group['droneGroupID'] = droneGroupID
        if group:
            for node in nodes:
                group['droneIDs'].add(node.itemID)

        self.CheckDrones(1)
        self.UpdateGroupSettings()

    def GetSubGroup(self, groupName):
        if groupName in self.groups:
            return self.groups[groupName]

    def CreateSubGroup(self, droneID, droneGroupID, nodes = None):
        ret = uiutil.NamePopup(localization.GetByLabel('UI/Generic/TypeGroupName'), localization.GetByLabel('UI/Generic/TypeNameForGroup'))
        if not ret:
            return
        droneIDs = set()
        for node in nodes:
            for group in self.GetDroneGroup(node.itemID, getall=1):
                group['droneIDs'].remove(node.itemID)

            droneIDs.add(node.itemID)

        origname = groupname = ret
        i = 2
        while groupname in self.groups:
            groupname = '%s_%i' % (origname, i)
            i += 1

        group = {}
        group['label'] = groupname
        group['droneIDs'] = droneIDs
        group['id'] = (groupname, str(blue.os.GetWallclockTime()))
        group['droneGroupID'] = droneGroupID
        self.groups[groupname] = group
        self.CheckDrones(1)
        self.UpdateGroupSettings()

    def OnMainGroupClick(self, group, *args):
        itemIDs = self.GetDroneIDsInMainGroup(group.sr.node)
        if itemIDs:
            sm.ScatterEvent('OnMultiSelect', itemIDs)

    def OnSubGroupClick(self, group, *args):
        itemIDs = self.GetDroneIDsInSubGroup(group.sr.node)
        if itemIDs:
            sm.ScatterEvent('OnMultiSelect', itemIDs)

    def GetDroneIDsInMainGroup(self, groupNode):
        """
            returns the droneIDs of the drones in this main group
        """
        droneDict = self.GetDroneDictFromDroneIDs(None, groupNode.droneState, includeFunction=self.IncludeAllDrones)
        return droneDict.keys()

    def GetDroneDataForMainGroup(self, groupNode):
        """
            returns the drone data (for menu creation) of the drones in this main group
        """
        droneDict = self.GetDroneDictFromDroneIDs(None, groupNode.droneState, includeFunction=self.IncludeAllDrones)
        return droneDict.values()

    def GetDroneIDsInSubGroup(self, groupNode):
        """
            returns the droneIDs of the drones in this subgroup
        """
        droneDict = self.GetDroneDictForSubGroup(groupNode)
        return droneDict.keys()

    def GetDroneDataForSubGroup(self, groupNode):
        """
            returns the drone data (for menu creation) of the drones in this subgroup
        """
        droneDict = self.GetDroneDictForSubGroup(groupNode)
        return droneDict.values()

    def GetDroneDictForSubGroup(self, groupNode):
        """
            returns a dictionary with droneIDs and droneData of the drones in this subgroup
        """
        droneState = groupNode.droneState
        allDronesBelongingToGroup = self.GetSubGroup(groupNode.groupName)['droneIDs']
        droneDict = self.GetDroneDictFromDroneIDs(allDronesBelongingToGroup, droneState)
        return droneDict

    def GetDroneDictFromDroneIDs(self, itemIDs, droneState, includeFunction = None):
        """
            itemIDs is a set of drone itemIDs.
            This function will return a dictionary of corresponding drones if they are
            in the droneState that is passed in.
        """
        if includeFunction is None:
            includeFunction = self.IsDroneIDinItemIDs
        droneDict = {}
        if droneState == 'inbay':
            droneDict = {drone.itemID:(drone, 0, None) for drone in self.GetDronesInBay() if includeFunction(drone.itemID, itemIDs)}
            return droneDict
        if droneState == 'inlocalspace':
            listOfDrones = self.GetDronesInLocalSpace()
        elif droneState == 'indistantspace':
            listOfDrones = self.GetDronesInDistantSpace()
        else:
            return droneDict
        droneDict = {drone.droneID:(drone.droneID, cfg.invtypes.Get(drone.typeID).groupID, drone.ownerID) for drone in listOfDrones if includeFunction(drone.droneID, itemIDs)}
        return droneDict

    def IsDroneIDinItemIDs(self, droneID, itemIDs):
        return droneID in itemIDs

    def IncludeAllDrones(self, droneID, itemIDs):
        return True

    def OnMouseDownOnDroneMainGroup(self, group, *args):
        self.OnMouseDownOnDroneMainGroup_thread(group)

    def OnMouseDownOnDroneMainGroup_thread(self, group):
        groupNode = group.sr.node
        droneData = self.GetDroneDataForMainGroup(groupNode)
        return self.GetRadialMenuOnGroup(group, droneData)

    def OnMouseDownOnDroneSubGroup(self, group, *args):
        uthread.new(self.OnMouseDownOnDroneSubGroup_thread, group)

    def OnMouseDownOnDroneSubGroup_thread(self, group):
        groupNode = group.sr.node
        droneData = self.GetDroneDataForSubGroup(groupNode)
        return self.GetRadialMenuOnGroup(group, droneData)

    def GetRadialMenuOnGroup(self, group, droneData):
        if not droneData:
            return
        groupNode = group.sr.node
        droneState = groupNode.droneState
        if droneState == 'inbay':
            manyItemsData = uiutil.Bunch(menuFunction=sm.GetService('menu').InvItemMenu, itemData=droneData, displayName='<b>%s</b>' % groupNode.cleanLabel)
        elif droneState in ('inlocalspace', 'indistantspace'):
            manyItemsData = uiutil.Bunch(menuFunction=sm.GetService('menu').GetDroneMenu, itemData=droneData, displayName='<b>%s</b>' % groupNode.cleanLabel)
        else:
            return
        typeID = GetTypeIDForManyDrones(droneState, droneData)
        sm.GetService('menu').TryExpandActionMenu(itemID=None, typeID=typeID, clickedObject=group, manyItemsData=manyItemsData)

    def GetDronesInBay(self, *args):
        if eve.session.shipid:
            return sm.GetService('invCache').GetInventoryFromId(eve.session.shipid).ListDroneBay()
        return []

    def GetDronesInLocalSpace(self):
        ballpark = sm.GetService('michelle').GetBallpark()
        if ballpark is None:
            return []
        drones = sm.GetService('michelle').GetDrones()
        return [ drones[droneID] for droneID in drones if droneID in ballpark.slimItems and (drones[droneID].ownerID == eve.session.charid or drones[droneID].controllerID == eve.session.shipid) ]

    def GetDronesInDistantSpace(self):
        ballpark = sm.GetService('michelle').GetBallpark()
        if ballpark is None:
            return []
        drones = sm.GetService('michelle').GetDrones()
        return [ drones[droneID] for droneID in drones if droneID not in ballpark.slimItems and (drones[droneID].ownerID == eve.session.charid or drones[droneID].controllerID == eve.session.shipid) ]

    def GetSpaceDrone(self, droneID):
        return sm.GetService('michelle').GetDroneState(droneID)

    def GetGroupListEntry(self, group, state, items):
        if not group or 'id' not in group:
            return []
        numDrones = self.GetNumberOfDronesInGroup(state, items)
        states = {'INBAY': localization.GetByLabel('UI/Inflight/Drone/DronesInBay'),
         'INLOCALSPACE': localization.GetByLabel('UI/Inflight/Drone/DronesInLocalSpace'),
         'INDISTANTSPACE': localization.GetByLabel('UI/Inflight/Drone/DronesInDistantSpace')}
        data = {'GetSubContent': self.GetGroupContent,
         'DropData': self.GroupDropData,
         'MenuFunction': self.GetMainFolderMenu,
         'label': localization.GetByLabel('UI/Inflight/Drone/DroneGroupWithCount', groupLabel=states[state.upper()], count=numDrones),
         'id': group['id'],
         'groupItems': items,
         'iconMargin': 18,
         'state': 'locked',
         'sublevel': 0,
         'droneState': state,
         'BlockOpenWindow': 1,
         'OnClick': self.OnMainGroupClick,
         'showlen': 0,
         'groupName': group['label'],
         'name': 'droneOverview%s' % group['label'].replace(' ', '').capitalize(),
         'OnMouseDown': self.OnMouseDownOnDroneMainGroup}
        return [listentry.Get(entryType=None, data=data, decoClass=DroneMainGroup)]

    def GetSubGroupListEntry(self, group, state, items):
        numDrones = self.GetNumberOfDronesInGroup(state, items)
        data = {'GetSubContent': self.GetSubGroupContent,
         'DropData': self.SubGroupDropData,
         'MenuFunction': self.GetSubFolderMenu,
         'label': localization.GetByLabel('UI/Inflight/Drone/DroneGroupWithCount', groupLabel=group['label'], count=numDrones),
         'id': (state, group['id']),
         'droneGroupID': group['droneGroupID'],
         'groupItems': None,
         'iconMargin': 18,
         'state': 'locked',
         'sublevel': 1,
         'droneState': state,
         'BlockOpenWindow': 1,
         'OnClick': self.OnSubGroupClick,
         'showlen': 0,
         'groupName': group['label'],
         'OnMouseDown': self.OnMouseDownOnDroneSubGroup}
        return listentry.Get(entryType=None, data=data, decoClass=DroneSubGroup)

    def GetNumberOfDronesInGroup(self, droneState, items):
        t = 0
        if droneState == 'inbay':
            dronebay = {}
            for drone in self.GetDronesInBay():
                dronebay[drone.itemID] = drone

            for droneID in items:
                if droneID not in dronebay:
                    log.LogWarn("Drone we thought was in the dronebay wasn't actually there, droneID = ", droneID)
                    continue
                t += dronebay[droneID].stacksize

        else:
            t = len(items)
        return t

    def GetGroupContent(self, nodedata, newitems = 0):
        scrollList = []
        if nodedata.droneState == 'inbay':
            dronebay = {}
            for drone in self.GetDronesInBay():
                dronebay[drone.itemID] = drone

        subGroups = {}
        for droneID in nodedata.groupItems:
            group = self.GetDroneGroup(droneID)
            if group:
                subGroups.setdefault(group['label'], []).append(droneID)
                continue
            if nodedata.droneState == 'inbay':
                if dronebay.has_key(droneID):
                    entry = self.GetBayDroneEntry(dronebay[droneID], nodedata.sublevel, nodedata.droneState)
                    scrollList.append(((0, entry.label.lower()), entry))
            else:
                entry = self.GetSpaceDroneEntry(self.GetSpaceDrone(droneID), nodedata.sublevel, nodedata.droneState)
                scrollList.append(((0, entry.label.lower()), entry))

        for groupName, droneIDs in subGroups.iteritems():
            group = self.GetSubGroup(groupName)
            if group:
                entry = self.GetSubGroupListEntry(group, nodedata.droneState, droneIDs)
                scrollList.append(((1, entry.label.lower()), entry))

        if not scrollList:
            noItemEntry = self.GetNoItemEntry(sublevel=1, droneState=nodedata.droneState)
            scrollList.append((0, noItemEntry))
        return uiutil.SortListOfTuples(scrollList)

    def GetSubGroupContent(self, nodedata, newitems = 0):
        scrollList = []
        subGroupInfo = self.GetSubGroup(nodedata.groupName)
        if nodedata.droneState == 'inbay':
            drones = self.GetDronesInBay()
            for drone in drones:
                if drone.itemID in subGroupInfo['droneIDs']:
                    entry = self.GetBayDroneEntry(drone, 1, nodedata.droneState)
                    scrollList.append(((entry.subLevel, entry.label), entry))

        elif nodedata.droneState == 'inlocalspace':
            drones = self.GetDronesInLocalSpace()
            for drone in drones:
                if drone.droneID in subGroupInfo['droneIDs']:
                    entry = self.GetSpaceDroneEntry(drone, 1, nodedata.droneState)
                    scrollList.append(((entry.subLevel, entry.label), entry))

        else:
            drones = self.GetDronesInDistantSpace()
            for drone in drones:
                if drone.droneID in subGroupInfo['droneIDs']:
                    entry = self.GetSpaceDroneEntry(drone, 1, nodedata.droneState)
                    scrollList.append(((entry.subLevel, entry.label), entry))

        if not scrollList:
            noItemEntry = self.GetNoItemEntry(sublevel=2, droneState=nodedata.droneState)
            scrollList.append((0, noItemEntry))
        return uiutil.SortListOfTuples(scrollList)

    def GetNoItemEntry(self, sublevel, droneState, *args):
        data = util.KeyVal()
        data.droneState = droneState
        data.label = localization.GetByLabel('/Carbon/UI/Controls/Common/NoItem')
        data.sublevel = sublevel
        data.itemID = None
        data.OnDropData = lambda dragObject, nodes: self.DropDronesOnDroneEntry(data, dragObject, nodes)
        noItemEntry = listentry.Get('Generic', data=data)
        return noItemEntry

    def GetDroneDamageState(self, droneID):
        damageTracker = sm.GetService('tactical').GetInBayDroneDamageTracker()
        if damageTracker.IsDroneDamageReady(droneID):
            damageState = damageTracker.GetDamageStateForDrone(droneID)
        else:
            damageState = -1
        return damageState

    def GetBayDroneEntry(self, drone, level, droneState):
        data = util.KeyVal()
        data.itemID = drone.itemID
        data.typeID = drone.typeID
        data.invItem = drone
        data.damageState = self.GetDroneDamageState(drone.itemID)
        data.displayName = cfg.invtypes.Get(drone.typeID).name
        if drone.stacksize > 1:
            data.label = localization.GetByLabel('UI/Inflight/Drone/DroneBayEntryWithStacksize', drone=drone.typeID, stacksize=drone.stacksize)
        else:
            data.label = cfg.invtypes.Get(drone.typeID).name
        data.sublevel = level
        data.customMenu = self.GroupMenu
        data.droneState = droneState
        data.OnDropData = lambda dragObject, nodes: self.DropDronesOnDroneEntry(data, dragObject, nodes)
        return listentry.Get('DroneEntry', data=data)

    def GetSpaceDroneEntry(self, drone, level, droneState):
        data = util.KeyVal()
        data.itemID = drone.droneID
        data.typeID = drone.typeID
        data.ownerID = drone.ownerID
        data.controllerID = drone.controllerID
        data.controllerOwnerID = drone.controllerOwnerID
        data.displayName = data.label = cfg.invtypes.Get(drone.typeID).name
        data.sublevel = level
        data.customMenu = self.GroupMenu
        data.droneState = droneState
        data.OnDropData = lambda dragObject, nodes: self.DropDronesOnDroneEntry(data, dragObject, nodes)
        return listentry.Get('DroneEntry', data=data)

    def DropDronesOnDroneEntry(self, entryData, dragObject, nodes):
        """
            Called when drones or drone groups are dropped on individual drones.
            In both cases, the drones will be launched or pulled in, depending on the location of the drone they were
            dropped on.
            If individual drones are being dragged around, they are also moved to the group of the drone they were dropped on.
            If groups are being dragged around, the drones in them will however NOT be moved to the other group since
            the player probably only wanted to launch/pull the drones
        """
        if dragObject.sr.node['__guid__'] not in ('listentry.DroneEntry', 'listentry.DroneMainGroup', 'listentry.DroneSubGroup'):
            return
        newGroupState = entryData.droneState
        dronesWithChangedState = self.LaunchOrPullDrones(newGroupState, nodes)
        droneEntries = [ node for node in nodes if node.__guid__ == 'listentry.DroneEntry' ]
        if not droneEntries:
            return
        group = self.GetDroneGroup(entryData.itemID)
        if group:
            self.MoveDronesToSubGroup(groupName=group['label'], nodes=droneEntries, excludedDrones=dronesWithChangedState)
        else:
            self.NoGroup(droneEntries)

    def CheckHint(self):
        if not self.sr.scroll.GetNodes():
            self.sr.scroll.ShowHint(localization.GetByLabel('UI/Inflight/Drone/NoDrones'))
        else:
            self.sr.scroll.ShowHint()

    def UpdateGroupSettings(self):
        settings.user.ui.Set(self.settingsName, self.ListifyGroups(self.groups))
        sm.GetService('settings').SaveSettings()

    def GetUtilMenuFunc(self):
        return self.DroneSettings

    def DroneSettings(self, menuParent):
        self.droneBehaviour = sm.GetService('godma').GetStateManager().GetDroneSettingAttributes()
        self.fafDefVal = cfg.dgmattribs.Get(const.attributeFighterAttackAndFollow).defaultValue
        self.droneAggressionDefVal = cfg.dgmattribs.Get(const.attributeDroneIsAggressive).defaultValue
        self.droneFFDefVal = cfg.dgmattribs.Get(const.attributeDroneFocusFire).defaultValue
        if not self.droneBehaviour.has_key(const.attributeDroneIsAggressive):
            self.droneBehaviour[const.attributeDroneIsAggressive] = settings.char.ui.Get('droneSettingAttributeID ' + str(const.attributeDroneIsAggressive), 0)
        aggressive = settings.char.ui.Get('droneAggression', self.droneAggressionDefVal)
        menuParent.AddRadioButton(text=localization.GetByLabel('UI/Drones/AggressionStatePassive'), checked=not aggressive, callback=(self.AggressiveChange, False))
        menuParent.AddRadioButton(text=localization.GetByLabel('UI/Drones/AggressionStateAggressive'), checked=aggressive, callback=(self.AggressiveChange, True))
        focusFire = settings.char.ui.Get('droneFocusFire', self.droneFFDefVal)
        menuParent.AddCheckBox(text=localization.GetByLabel('UI/Drones/AttackModeFocusFire'), checked=focusFire, callback=(self.FocusFireChange, not focusFire))
        menuParent.AddHeader(text=localization.GetByLabel('UI/Drones/FighterSettings'))
        fightFollow = settings.char.ui.Get('fighterAttackAndFollow', self.fafDefVal)
        menuParent.AddCheckBox(text=localization.GetByLabel('UI/Drones/AttackModeAttackAndFollow'), checked=fightFollow, callback=(self.FightFollowChange, not fightFollow))

    def AggressiveChange(self, aggressive, *args):
        settings.char.ui.Set('droneAggression', aggressive)
        self.OnChange()

    def FocusFireChange(self, focusFire, *args):
        settings.char.ui.Set('droneFocusFire', focusFire)
        self.OnChange()

    def FightFollowChange(self, fightFollow, *args):
        settings.char.ui.Set('fighterAttackAndFollow', fightFollow)
        self.OnChange()

    def OnChange(self):
        droneSettingChanges = {}
        droneSettingChanges[const.attributeDroneIsAggressive] = settings.char.ui.Get('droneAggression', self.droneAggressionDefVal)
        droneSettingChanges[const.attributeFighterAttackAndFollow] = settings.char.ui.Get('fighterAttackAndFollow', self.fafDefVal)
        droneSettingChanges[const.attributeDroneFocusFire] = settings.char.ui.Get('droneFocusFire', self.droneFFDefVal)
        sm.GetService('godma').GetStateManager().ChangeDroneSettings(droneSettingChanges)


class DroneMainGroup(Group):
    __guid__ = 'listentry.DroneMainGroup'
    isDragObject = True

    def GetDragData(self, *args):
        return [self.sr.node]


class DroneSubGroup(Group):
    __guid__ = 'listentry.DroneSubGroup'
    isDragObject = True

    def Startup(self, *args):
        Group.Startup(self, args)
        if self.sr.fill:
            self.sr.fill.opacity = 0.9 * self.sr.fill.color.a

    def GetDragData(self, *args):
        return [self.sr.node]


def GetTypeIDForManyDrones(droneState, droneData):
    """
        find typeID for a group of drones that might be mixed.
        If one of the drones is salvage, mine or unanchor, we want to make sure that's not the drone
        we get the typeID for, because it's more important to get the Engage option for combat drones
    """
    if not droneData:
        return None
    if droneState == 'inbay':
        firstDroneData = droneData[0]
        invItem, viewOnly, voucher = firstDroneData
        return invItem.typeID
    if droneState in ('inlocalspace', 'indistantspace'):
        lowPriorityDrones = [const.groupMiningDrone, const.groupSalvageDrone, const.groupUnanchoringDrone]

        def IsHigherPrioritySpaceDrone(droneData):
            droneID, groupID, ownerID = droneData
            if groupID in lowPriorityDrones:
                return False
            return True

        priorityDrone = itertoolsext.first_or_default(droneData, predicate=IsHigherPrioritySpaceDrone, default=droneData[0])
        droneSlimItem = sm.GetService('michelle').GetItem(priorityDrone[0])
        if droneSlimItem:
            return droneSlimItem.typeID


def DropDronesInSpace(dragObj, nodes):
    """
        only to move drones from bay to space
    """
    if dragObj.sr.node.droneState != 'inbay':
        return
    droneWnd = DroneView.GetIfOpen()
    if droneWnd is None:
        return
    drones = []
    if dragObj.__guid__ in ('listentry.DroneSubGroup', 'listentry.DroneMainGroup'):
        if dragObj.__guid__ == 'listentry.DroneSubGroup':
            nodes = droneWnd.GetSubGroupContent(dragObj.sr.node)
        else:
            nodes = droneWnd.GetAllMainGroupContent(dragObj.sr.node)
    drones = [ node.invItem for node in nodes ]
    sm.GetService('menu').LaunchDrones(drones)
