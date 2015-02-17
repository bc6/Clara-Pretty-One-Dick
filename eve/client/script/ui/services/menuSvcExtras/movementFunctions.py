#Embedded file name: eve/client/script/ui/services/menuSvcExtras\movementFunctions.py
import sys
import uix
import uiutil
import util
import service
import destiny
import carbonui.const as uiconst
import localization
import eve.client.script.ui.util.defaultRangeUtils as defaultRangeUtils
import const
import log
from eveexceptions import UserError

def SetDefaultDist(key):
    if not key:
        return
    minDist, maxDist = {'Orbit': (500, 1000000),
     'KeepAtRange': (50, 1000000),
     'WarpTo': (const.minWarpEndDistance, const.maxWarpEndDistance)}.get(key, (500, 1000000))
    current = sm.GetService('menu').GetDefaultActionDistance(key)
    current = current or ''
    fromDist = util.FmtAmt(minDist)
    toDist = util.FmtAmt(maxDist)
    if key == 'KeepAtRange':
        hint = localization.GetByLabel('UI/Inflight/SetDefaultKeepAtRangeDistanceHint', fromDist=fromDist, toDist=toDist)
        caption = localization.GetByLabel('UI/Inflight/SetDefaultKeepAtRangeDistance')
    elif key == 'Orbit':
        hint = localization.GetByLabel('UI/Inflight/SetDefaultOrbitDistanceHint', fromDist=fromDist, toDist=toDist)
        caption = localization.GetByLabel('UI/Inflight/SetDefaultOrbitDistance')
    elif key == 'WarpTo':
        hint = localization.GetByLabel('UI/Inflight/SetDefaultWarpWithinDistanceHint', fromDist=fromDist, toDist=toDist)
        caption = localization.GetByLabel('UI/Inflight/SetDefaultWarpWithinDistance')
    else:
        hint = ''
        caption = ''
    r = uix.QtyPopup(maxvalue=maxDist, minvalue=minDist, setvalue=current, hint=hint, caption=caption, label=None, digits=0)
    if r:
        newRange = max(minDist, min(maxDist, r['qty']))
        defaultRangeUtils.UpdateRangeSetting(key, newRange)


def GetKeepAtRangeRanges():
    keepRangeRanges = [500,
     1000,
     2500,
     5000,
     7500,
     10000,
     15000,
     20000,
     25000,
     30000]
    return keepRangeRanges


def GetDefaultDist(key, itemID = None, minDist = 500, maxDist = 1000000):
    drange = sm.GetService('menu').GetDefaultActionDistance(key)
    if drange is None:
        dist = ''
        if itemID:
            bp = sm.StartService('michelle').GetBallpark()
            if not bp:
                return
            ball = bp.GetBall(itemID)
            if not ball:
                return
            dist = long(max(minDist, min(maxDist, ball.surfaceDist)))
        fromDist = util.FmtAmt(minDist)
        toDist = util.FmtAmt(maxDist)
        if key == 'KeepAtRange':
            hint = localization.GetByLabel('UI/Inflight/SetDefaultKeepAtRangeDistanceHint', fromDist=fromDist, toDist=toDist)
            caption = localization.GetByLabel('UI/Inflight/SetDefaultKeepAtRangeDistance')
        elif key == 'Orbit':
            hint = localization.GetByLabel('UI/Inflight/SetDefaultOrbitDistanceHint', fromDist=fromDist, toDist=toDist)
            caption = localization.GetByLabel('UI/Inflight/SetDefaultOrbitDistance')
        elif key == 'WarpTo':
            hint = localization.GetByLabel('UI/Inflight/SetDefaultWarpWithinDistanceHint', fromDist=fromDist, toDist=toDist)
            caption = localization.GetByLabel('UI/Inflight/SetDefaultWarpWithinDistance')
        else:
            hint = ''
            caption = ''
        r = uix.QtyPopup(maxvalue=maxDist, minvalue=minDist, setvalue=dist, hint=hint, caption=caption, label=None, digits=0)
        if r:
            newRange = max(minDist, min(maxDist, r['qty']))
            defaultRangeUtils.UpdateRangeSetting(key, newRange)
        else:
            return
    return drange


def KeepAtRange(itemID, followRange = None):
    if itemID == session.shipid:
        return
    if followRange is None:
        followRange = GetDefaultDist('KeepAtRange', itemID, minDist=const.approachRange)
    bp = sm.StartService('michelle').GetRemotePark()
    if bp is not None and followRange is not None:
        sm.GetService('space').SetIndicationTextForcefully(ballMode=destiny.DSTBALL_FOLLOW, followId=itemID, followRange=int(followRange))
        bp.CmdFollowBall(itemID, followRange)
        if not sm.GetService('machoNet').GetGlobalConfig().get('newAutoNavigationKillSwitch', False):
            sm.GetService('autoPilot').CancelSystemNavigation()
        sm.GetService('flightPredictionSvc').OptionActivated('KeepAtRange', itemID, followRange)


def Orbit(itemID, followRange = None):
    if itemID == session.shipid:
        return
    if followRange is None:
        followRange = GetDefaultDist('Orbit')
    bp = sm.StartService('michelle').GetRemotePark()
    if bp is not None and followRange is not None:
        followRange = float(followRange) if followRange < 10.0 else int(followRange)
        sm.GetService('space').SetIndicationTextForcefully(ballMode=destiny.DSTBALL_ORBIT, followId=itemID, followRange=followRange)
        bp.CmdOrbit(itemID, followRange)
        if not sm.GetService('machoNet').GetGlobalConfig().get('newAutoNavigationKillSwitch', False):
            sm.GetService('autoPilot').CancelSystemNavigation()
        sm.GetService('flightPredictionSvc').OptionActivated('Orbit', itemID, followRange)
        try:
            slimItem = sm.GetService('michelle').GetItem(itemID)
            sm.ScatterEvent('OnClientEvent_Orbit', slimItem)
        except Exception as e:
            log.LogTraceback('Failed at scattering orbit event')


def GetWarpToRanges():
    ranges = [const.minWarpEndDistance,
     (const.minWarpEndDistance / 10000 + 1) * 10000,
     (const.minWarpEndDistance / 10000 + 2) * 10000,
     (const.minWarpEndDistance / 10000 + 3) * 10000,
     (const.minWarpEndDistance / 10000 + 5) * 10000,
     (const.minWarpEndDistance / 10000 + 7) * 10000,
     const.maxWarpEndDistance]
    return ranges


def DockOrJumpOrActivateGate(itemID):
    bp = sm.StartService('michelle').GetBallpark()
    menuSvc = sm.GetService('menu')
    if bp:
        groupID = bp.GetInvItem(itemID).groupID
        if groupID == const.groupStation:
            menuSvc.Dock(itemID)
        if groupID == const.groupStargate:
            bp = sm.StartService('michelle').GetBallpark()
            slimItem = bp.slimItems.get(itemID)
            if slimItem:
                jump = slimItem.jumps[0]
                if not jump:
                    return
                menuSvc.StargateJump(itemID, jump.toCelestialID, jump.locationID)
        elif groupID == const.groupWarpGate:
            menuSvc.ActivateAccelerationGate(itemID)


def ApproachLocation(bookmark):
    bp = sm.StartService('michelle').GetRemotePark()
    if bp:
        if getattr(bookmark, 'agentID', 0) and hasattr(bookmark, 'locationNumber'):
            referringAgentID = getattr(bookmark, 'referringAgentID', None)
            sm.StartService('agents').GetAgentMoniker(bookmark.agentID).GotoLocation(bookmark.locationType, bookmark.locationNumber, referringAgentID)
        else:
            bp.CmdGotoBookmark(bookmark.bookmarkID)
            sm.ScatterEvent('OnClientEvent_Approach')


def WarpToBookmark(bookmark, warpRange = 20000.0, fleet = False):
    bp = sm.StartService('michelle').GetRemotePark()
    if bp:
        if getattr(bookmark, 'agentID', 0) and hasattr(bookmark, 'locationNumber'):
            referringAgentID = getattr(bookmark, 'referringAgentID', None)
            sm.StartService('agents').GetAgentMoniker(bookmark.agentID).WarpToLocation(bookmark.locationType, bookmark.locationNumber, warpRange, fleet, referringAgentID)
        else:
            if not sm.GetService('machoNet').GetGlobalConfig().get('newAutoNavigationKillSwitch', False):
                sm.GetService('autoPilot').CancelSystemNavigation()
            bp.CmdWarpToStuff('bookmark', bookmark.bookmarkID, minRange=warpRange, fleet=fleet)
            sm.StartService('space').WarpDestination(bookmarkID=bookmark.bookmarkID)


def WarpFleetToBookmark(bookmark, warpRange = 20000.0, fleet = True):
    bp = sm.StartService('michelle').GetRemotePark()
    if bp:
        if getattr(bookmark, 'agentID', 0) and hasattr(bookmark, 'locationNumber'):
            referringAgentID = getattr(bookmark, 'referringAgentID', None)
            sm.StartService('agents').GetAgentMoniker(bookmark.agentID).WarpToLocation(bookmark.locationType, bookmark.locationNumber, warpRange, fleet, referringAgentID)
        else:
            if not sm.GetService('machoNet').GetGlobalConfig().get('newAutoNavigationKillSwitch', False):
                sm.GetService('autoPilot').CancelSystemNavigation()
            bp.CmdWarpToStuff('bookmark', bookmark.bookmarkID, minRange=warpRange, fleet=fleet)


def WarpToItem(itemID, warpRange = None, cancelAutoNavigation = True):
    if itemID == session.shipid:
        return
    if warpRange is None:
        warprange = sm.GetService('menu').GetDefaultActionDistance('WarpTo')
    else:
        warprange = warpRange
    bp = sm.StartService('michelle').GetRemotePark()
    if bp is not None and sm.StartService('space').CanWarp(itemID):
        if not sm.GetService('machoNet').GetGlobalConfig().get('newAutoNavigationKillSwitch', False):
            if cancelAutoNavigation:
                sm.GetService('autoPilot').CancelSystemNavigation()
        else:
            sm.GetService('autoPilot').AbortWarpAndTryCommand(itemID)
            sm.GetService('autoPilot').AbortApproachAndTryCommand()
        bp.CmdWarpToStuff('item', itemID, minRange=warprange)
        sm.StartService('space').WarpDestination(celestialID=itemID)
        sm.GetService('flightPredictionSvc').OptionActivated('AlignTo', itemID)


def WarpToDistrict(districtID, warpRange = None, cancelAutoNavigation = True):
    if warpRange is None:
        warprange = sm.GetService('menu').GetDefaultActionDistance('WarpTo')
    else:
        warprange = warpRange
    bp = sm.StartService('michelle').GetRemotePark()
    if bp is not None and sm.StartService('space').CanWarp(districtID):
        if not sm.GetService('machoNet').GetGlobalConfig().get('newAutoNavigationKillSwitch', False):
            if cancelAutoNavigation:
                sm.GetService('autoPilot').CancelSystemNavigation()
        else:
            sm.GetService('autoPilot').AbortWarpAndTryCommand(districtID)
            sm.GetService('autoPilot').AbortApproachAndTryCommand()
        bp.CmdWarpToStuff('district', districtID, minRange=warprange)


def RealDock(itemID):
    bp = sm.StartService('michelle').GetBallpark()
    if not bp:
        return
    if sm.GetService('viewState').HasActiveTransition():
        return
    eve.Message('OnDockingRequest')
    eve.Message('CustomNotify', {'notify': localization.GetByLabel('UI/Inflight/RequestToDockAt', station=itemID)})
    paymentRequired = 0
    try:
        bp = sm.GetService('michelle').GetRemotePark()
        if bp is not None:
            log.LogNotice('Docking', itemID)
            if uicore.uilib.Key(uiconst.VK_CONTROL) and uicore.uilib.Key(uiconst.VK_SHIFT) and uicore.uilib.Key(uiconst.VK_MENU) and session.role & service.ROLE_GML:
                success = sm.GetService('sessionMgr').PerformSessionChange('dock', bp.CmdTurboDock, itemID)
            else:
                success = sm.GetService('sessionMgr').PerformSessionChange('dock', bp.CmdDock, itemID, session.shipid)
    except UserError as e:
        if e.msg == 'DockingRequestDeniedPaymentRequired':
            sys.exc_clear()
            paymentRequired = e.args[1]['amount']
        else:
            raise
    except Exception as e:
        raise

    if paymentRequired:
        if eve.Message('AskPayDockingFee', {'cost': paymentRequired}, uiconst.YESNO) == uiconst.ID_YES:
            bp = sm.GetService('michelle').GetRemotePark()
            if bp is not None:
                session.ResetSessionChangeTimer('Retrying with docking payment')
                if uicore.uilib.Key(uiconst.VK_CONTROL) and session.role & service.ROLE_GML:
                    sm.GetService('sessionMgr').PerformSessionChange('dock', bp.CmdTurboDock, itemID, paymentRequired)
                else:
                    sm.GetService('sessionMgr').PerformSessionChange('dock', bp.CmdDock, itemID, session.shipid, paymentRequired)


def RealActivateAccelerationGate(itemID):
    if eve.rookieState and not sm.StartService('tutorial').CheckAccelerationGateActivation():
        return
    sm.StartService('sessionMgr').PerformSessionChange(localization.GetByLabel('UI/Inflight/ActivateGate'), sm.RemoteSvc('keeper').ActivateAccelerationGate, itemID, violateSafetyTimer=1)
    log.LogNotice('Acceleration Gate activated to ', itemID)


def RealEnterWormhole(itemID):
    fromSecClass = sm.StartService('map').GetSecurityClass(session.solarsystemid)
    if fromSecClass == const.securityClassHighSec and eve.Message('WormholeJumpingFromHiSec', {}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
        return
    log.LogNotice('Wormhole Jump from', session.solarsystemid2, 'to', itemID)
    sm.StartService('sessionMgr').PerformSessionChange(localization.GetByLabel('UI/Inflight/EnterWormhole'), sm.RemoteSvc('wormholeMgr').WormholeJump, itemID)


def GetGlobalActiveItemKeyName(forWhat):
    key = None
    actions = ['UI/Inflight/OrbitObject', 'UI/Inflight/Submenus/KeepAtRange', DefaultWarpToLabel()[0]]
    if forWhat in actions:
        idx = actions.index(forWhat)
        key = ['Orbit', 'KeepAtRange', 'WarpTo'][idx]
    return key


def DefaultWarpToLabel():
    defaultWarpDist = sm.GetService('menu').GetDefaultActionDistance('WarpTo')
    label = uiutil.MenuLabel('UI/Inflight/WarpToWithinDistance', {'distance': util.FmtDist(float(defaultWarpDist))})
    return label
