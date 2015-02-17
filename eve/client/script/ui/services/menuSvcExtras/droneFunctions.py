#Embedded file name: eve/client/script/ui/services/menuSvcExtras\droneFunctions.py
import uthread
import blue
import moniker
import carbonui.const as uiconst
import localization
import const
from eveexceptions import UserError

def HandleMultipleCallError(droneID, ret, messageName):
    if not len(ret):
        return
    if len(droneID) == 1:
        pick = droneID[0]
        raise UserError(ret[pick][0], ret[pick][1])
    elif len(droneID) >= len(ret):
        lastError = ''
        for error in ret.itervalues():
            if error[0] != lastError and lastError != '':
                raise UserError(messageName, {'succeeded': len(droneID) - len(ret),
                 'failed': len(ret),
                 'total': len(droneID)})
            lastError = error[0]
        else:
            pick = ret.items()[0][1]
            raise UserError(pick[0], pick[1])


def EngageTarget(droneIDs):
    michelle = sm.StartService('michelle')
    dronesRemoved = []
    for droneID in droneIDs:
        item = michelle.GetItem(droneID)
        if not item:
            dronesRemoved.append(droneID)

    for droneID in dronesRemoved:
        droneIDs.remove(droneID)

    targetID = sm.GetService('target').GetActiveTargetID()
    if targetID is None:
        raise UserError('DroneCommandRequiresActiveTarget')
    crimewatchSvc = sm.GetService('crimewatchSvc')
    requiredSafetyLevel = crimewatchSvc.GetRequiredSafetyLevelForEngagingDrones(droneIDs, targetID)
    if crimewatchSvc.CheckUnsafe(requiredSafetyLevel):
        crimewatchSvc.SafetyActivated(requiredSafetyLevel)
        return
    entity = moniker.GetEntityAccess()
    if entity:
        ret = entity.CmdEngage(droneIDs, targetID)
        HandleMultipleCallError(droneIDs, ret, 'MultiDroneCmdResult')
        if droneIDs:
            name = sm.GetService('space').GetWarpDestinationName(targetID)
            eve.Message('CustomNotify', {'notify': localization.GetByLabel('UI/Inflight/DronesEngaging', name=name)})


def ReturnControl(droneIDs):
    michelle = sm.StartService('michelle')
    dronesByOwner = {}
    for droneID in droneIDs:
        ownerID = michelle.GetDroneState(droneID).ownerID
        if ownerID in dronesByOwner:
            dronesByOwner[ownerID].append(droneID)
        else:
            dronesByOwner[ownerID] = [droneID]

    entity = moniker.GetEntityAccess()
    if entity:
        for ownerID, IDs in dronesByOwner.iteritems():
            ret = entity.CmdRelinquishControl(IDs)
            HandleMultipleCallError(droneIDs, ret, 'MultiDroneCmdResult')


def DelegateControl(charID, droneIDs):
    if charID is None:
        targetID = sm.StartService('target').GetActiveTargetID()
        if targetID is None:
            raise UserError('DroneCommandRequiresActiveTarget')
        michelle = sm.StartService('michelle')
        targetItem = michelle.GetItem(targetID)
        if targetItem.categoryID != const.categoryShip or targetItem.groupID == const.groupCapsule:
            raise UserError('DroneCommandRequiresShipButNotCapsule')
        targetBall = michelle.GetBall(targetID)
        if not targetBall.isInteractive or not sm.GetService('fleet').IsMember(targetItem.ownerID):
            raise UserError('DroneCommandRequiresShipPilotedFleetMember')
        controllerID = targetItem.ownerID
    else:
        controllerID = charID
    entity = moniker.GetEntityAccess()
    if entity:
        ret = entity.CmdDelegateControl(droneIDs, controllerID)
        HandleMultipleCallError(droneIDs, ret, 'MultiDroneCmdResult')


def Assist(charID, droneIDs):
    if charID is None:
        targetID = sm.StartService('target').GetActiveTargetID()
        if targetID is None:
            raise UserError('DroneCommandRequiresActiveTarget')
        michelle = sm.StartService('michelle')
        targetItem = michelle.GetItem(targetID)
        if targetItem.categoryID != const.categoryShip or targetItem.groupID == const.groupCapsule:
            raise UserError('DroneCommandRequiresShipButNotCapsule')
        targetBall = michelle.GetBall(targetID)
        if not targetBall.isInteractive or not sm.GetService('fleet').IsMember(targetItem.ownerID):
            raise UserError('DroneCommandRequiresShipPilotedFleetMember')
        assistID = targetItem.ownerID
    else:
        assistID = charID
    entity = moniker.GetEntityAccess()
    if entity:
        ret = entity.CmdAssist(assistID, droneIDs)
        HandleMultipleCallError(droneIDs, ret, 'MultiDroneCmdResult')


def Guard(charID, droneIDs):
    if charID is None:
        targetID = sm.StartService('target').GetActiveTargetID()
        if targetID is None:
            raise UserError('DroneCommandRequiresActiveTarget')
        michelle = sm.StartService('michelle')
        targetItem = michelle.GetItem(targetID)
        if targetItem.categoryID != const.categoryShip or targetItem.groupID == const.groupCapsule:
            raise UserError('DroneCommandRequiresShipButNotCapsule')
        targetBall = michelle.GetBall(targetID)
        if not targetBall.isInteractive or not sm.GetService('fleet').IsMember(targetItem.ownerID):
            raise UserError('DroneCommandRequiresShipPilotedFleetMember')
        guardID = targetItem.ownerID
    else:
        guardID = charID
    entity = moniker.GetEntityAccess()
    if entity:
        ret = entity.CmdGuard(guardID, droneIDs)
        HandleMultipleCallError(droneIDs, ret, 'MultiDroneCmdResult')


def Mine(droneIDs):
    targetID = sm.StartService('target').GetActiveTargetID()
    if targetID is None:
        raise UserError('DroneCommandRequiresActiveTarget')
    entity = moniker.GetEntityAccess()
    if entity:
        ret = entity.CmdMine(droneIDs, targetID)
        HandleMultipleCallError(droneIDs, ret, 'MultiDroneCmdResult')


def MineRepeatedly(droneIDs):
    targetID = sm.StartService('target').GetActiveTargetID()
    if targetID is None:
        raise UserError('DroneCommandRequiresActiveTarget')
    entity = moniker.GetEntityAccess()
    if entity:
        ret = entity.CmdMineRepeatedly(droneIDs, targetID)
        HandleMultipleCallError(droneIDs, ret, 'MultiDroneCmdResult')


def Salvage(droneIDs):
    targetID = sm.GetService('target').GetActiveTargetID()
    entity = moniker.GetEntityAccess()
    if entity:
        ret = entity.CmdSalvage(droneIDs, targetID)
        HandleMultipleCallError(droneIDs, ret, 'MultiDroneCmdResult')


def DroneUnanchor(droneIDs):
    targetID = sm.StartService('target').GetActiveTargetID()
    if targetID is None:
        raise UserError('DroneCommandRequiresActiveTarget')
    entity = moniker.GetEntityAccess()
    if entity:
        ret = entity.CmdUnanchor(droneIDs, targetID)
        HandleMultipleCallError(droneIDs, ret, 'MultiDroneCmdResult')


def ReturnAndOrbit(droneIDs):
    entity = moniker.GetEntityAccess()
    if entity:
        ret = entity.CmdReturnHome(droneIDs)
        HandleMultipleCallError(droneIDs, ret, 'MultiDroneCmdResult')


def ReturnToDroneBay(droneIDs):
    entity = moniker.GetEntityAccess()
    if entity:
        ret = entity.CmdReturnBay(droneIDs)
        HandleMultipleCallError(droneIDs, ret, 'MultiDroneCmdResult')


def RealScoopToDroneBay(objectIDs):
    ship = sm.StartService('gameui').GetShipAccess()
    if ship:
        ret = ship.ScoopDrone(objectIDs)
        HandleMultipleCallError(objectIDs, ret, 'MultiDroneCmdResult')


def AbandonDrone(droneIDs):
    if eve.Message('ConfirmAbandonDrone', {}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
        return
    entity = moniker.GetEntityAccess()
    if entity:
        ret = entity.CmdAbandonDrone(droneIDs)
        HandleMultipleCallError(droneIDs, ret, 'MultDroneCmdResult')


def ReconnectToDrones():
    ret = {}
    bp = sm.GetService('michelle').GetBallpark()
    if not bp:
        return ret
    shipBall = bp.GetBall(session.shipid)
    if not shipBall:
        return ret
    drones = sm.GetService('michelle').GetDrones()
    droneCandidates = []
    for ball, slimItem in bp.GetBallsAndItems():
        if slimItem and slimItem.categoryID == const.categoryDrone:
            if slimItem.ownerID == session.charid and ball.id not in drones:
                droneCandidates.append(ball.id)
                if len(droneCandidates) >= const.MAX_DRONE_RECONNECTS:
                    break

    if droneCandidates:
        eve.Message('CustomNotify', {'notify': localization.GetByLabel('UI/Messages/ReconnectFoundDrones')})
        _ReconnectToDroneCandidates(droneCandidates)
    else:
        eve.Message('CustomNotify', {'notify': localization.GetByLabel('UI/Messages/ReconnectFoundNoDrones')})
    return ret


def _ReconnectToDroneCandidates(droneCandidates):
    if not droneCandidates:
        return
    entity = moniker.GetEntityAccess()
    if entity:

        def SpewError(*args):
            raise UserError(*args)

        ret = entity.CmdReconnectToDrones(droneCandidates)
        for errStr, dicty in ret.iteritems():
            uthread.new(SpewError, errStr, dicty)
            blue.pyos.synchro.Sleep(5000)


def FitDrone(invItems, invCacheSvc):
    if type(invItems) is not list:
        invItems = [invItems]
    itemIDs = [ node.itemID for node in invItems ]
    if session.shipid:
        for itemID in itemIDs:
            invCacheSvc.UnlockItem(itemID)

        invCacheSvc.GetInventoryFromId(session.shipid).MultiAdd(itemIDs, invItems[0].locationID, flag=const.flagDroneBay)
