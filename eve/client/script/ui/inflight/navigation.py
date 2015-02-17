#Embedded file name: eve/client/script/ui/inflight\navigation.py
from itertools import chain
from carbonui.uianimations import animations
from eve.client.script.ui.inflight.bracketsAndTargets.bracketVarious import GetOverlaps
from eve.client.script.ui.shared.infoPanels.infoPanelLocationInfo import ListSurroundingsBtn
from eve.client.script.ui.tooltips.tooltipHandler import TOOLTIP_SETTINGS_BRACKET, TOOLTIP_DELAY_BRACKET
from sensorsuite.overlay.brackets import SensorSuiteBracket
from spacecomponents.client.components import deploy
from spacecomponents.common.helper import HasDeployComponent
import uiprimitives
import uthread
import trinity
import uix
import uiutil
import mathUtil
import blue
import service
import state
import uicls
import carbonui.const as uiconst
import geo2
from eve.client.script.ui.inflight.drone import DropDronesInSpace
from eve.client.script.ui.inflight.bracketsAndTargets.inSpaceBracketTooltip import PersistentInSpaceBracketTooltip
from evecamera import FOV_MAX, FOV_MIN

class InflightLayer(uicls.LayerCore):
    """Navigation layer for space view where mouse interaction and camera control is implemented"""
    __guid__ = 'uicls.InflightLayer'

    def ApplyAttributes(self, attributes):
        uicls.LayerCore.ApplyAttributes(self, attributes)
        self.looking = 1
        self.locked = 0
        self.zoomlooking = 0
        self.fovready = 0
        self.resetfov = 0
        self.prefov = None
        self.align = uiconst.TOALL
        self.notdbl = 0
        self.sr.tcursor = None
        self.sr.clicktime = None
        self.hoverbracket = None
        self.blockDisable = 0
        self.movingCursor = None
        self.isMouseMoving = False
        self.sr.spacemenu = None
        self.downpos = None
        self.locks = {}
        self._isPicked = False
        self.dungeonEditorSelectionEnabled = False
        self.sr.tcursor = uiprimitives.Container(name='targetingcursor', parent=self, align=uiconst.ABSOLUTE, width=1, height=1, state=uiconst.UI_HIDDEN)
        uiprimitives.Line(parent=self.sr.tcursor, align=uiconst.RELATIVE, left=10, width=3000, height=1)
        uiprimitives.Line(parent=self.sr.tcursor, align=uiconst.TOPRIGHT, left=10, width=3000, height=1)
        uiprimitives.Line(parent=self.sr.tcursor, align=uiconst.RELATIVE, top=10, width=1, height=3000)
        uiprimitives.Line(parent=self.sr.tcursor, align=uiconst.BOTTOMLEFT, top=10, width=1, height=3000)

    def GetSpaceMenu(self):
        if self.sr.spacemenu:
            if self.sr.spacemenu.solarsystemid == eve.session.solarsystemid2:
                return self.sr.spacemenu
            m = self.sr.spacemenu
            self.sr.spacemenu = None
            m.Close()
        solarsystemitems = sm.GetService('map').GetSolarsystemItems(session.solarsystemid2)
        listbtn = ListSurroundingsBtn(name='gimp', parent=self, state=uiconst.UI_HIDDEN, pos=(0, 0, 0, 0))
        listbtn.sr.mapitems = solarsystemitems
        listbtn.sr.groupByType = 1
        listbtn.filterCurrent = 1
        listbtn.solarsystemid = eve.session.solarsystemid2
        self.sr.spacemenu = listbtn
        return self.sr.spacemenu

    def GetSelfMenu(self):
        cam = sm.GetService('sceneManager').GetRegisteredCamera('default')
        if cam is not None and eve.session.shipid and cam.parent and getattr(cam.parent, 'translationCurve', None) is not None and cam.parent.translationCurve.id == eve.session.shipid:
            return sm.GetService('menu').CelestialMenu(eve.session.shipid)
        return self.GetMenu()

    def SelfMouseDown(self, *args):
        picktype, pickobject = self.GetPick()
        if not (pickobject and hasattr(pickobject, 'translationCurve') and hasattr(pickobject.translationCurve, 'id')):
            if sm.GetService('menu').TryExpandActionMenu(eve.session.shipid, self):
                return
        self.OnMouseDown()

    def _OnClose(self):
        uiprimitives.Container._OnClose(self)
        if not uicore.cmd.IsUIHidden():
            uicore.layer.main.state = uiconst.UI_PICKCHILDREN

    def OnMouseDown(self, *args):
        self._isPicked = True
        self.downpos = (uicore.uilib.x, uicore.uilib.y)
        if not self.blockDisable and not uicore.cmd.IsUIHidden():
            uicore.layer.main.state = uiconst.UI_DISABLED
        self.notdbl = 0
        camera = sm.GetService('sceneManager').GetRegisteredCamera('default')
        if camera is None:
            return
        if uicore.uilib.rightbtn:
            sm.GetService('target').CancelTargetOrder()
            if getattr(self, 'prefov', None) is None:
                self.prefov = camera.fieldOfView
            self.notdbl = 1
        picktype, pickobject = self.GetPick()
        if pickobject and hasattr(pickobject, 'translationCurve') and hasattr(pickobject.translationCurve, 'id'):
            uthread.pool('navigation::OnMouseDown', sm.GetService('menu').TryExpandActionMenu, pickobject.translationCurve.id, self)
        if uicore.uilib.leftbtn:
            if sm.IsServiceRunning('scenario') and sm.GetService('scenario').IsActive():
                self.movingCursor = sm.GetService('scenario').GetPickAxis()
            if pickobject:
                if sm.GetService('posAnchor').IsActive():
                    if pickobject.name[:6] == 'cursor':
                        self.movingCursor = pickobject
                        sm.GetService('posAnchor').StartMovingCursor()
                        return
                if eve.session.role & service.ROLE_CONTENT and self.dungeonEditorSelectionEnabled and not self.movingCursor:
                    scenario = sm.GetService('scenario')
                    michelle = sm.GetService('michelle')
                    item = michelle.GetItem(pickobject.translationCurve.id)
                    if getattr(item, 'dunObjectID', None) != None and hasattr(pickobject, 'translationCurve') and hasattr(pickobject.translationCurve, 'id'):
                        shift = uicore.uilib.Key(uiconst.VK_SHIFT)
                        if not shift:
                            slimItem = michelle.GetItem(item.itemID)
                            scenario.SetSelectionByID([slimItem.dunObjectID])
                        elif not scenario.IsSelected(item.itemID):
                            scenario.AddSelected(item.itemID)
                        else:
                            scenario.RemoveSelected(item.itemID)
        self.looking = 1
        uicore.uilib.ClipCursor(0, 0, uicore.desktop.width, uicore.desktop.height)
        uicore.uilib.SetCapture(self)

    def OnDblClick(self, *args):
        if eve.rookieState and eve.rookieState < 22:
            return
        self.sr.clicktime = None
        solarsystemID = eve.session.solarsystemid
        uthread.Lock(self)
        try:
            if solarsystemID != eve.session.solarsystemid:
                return
            if self.notdbl:
                return
            if uicore.uilib.Key(uiconst.VK_SHIFT) and eve.session.role & service.ROLE_CONTENT:
                return
            x, y = uicore.uilib.x, uicore.uilib.y
            if uicore.uilib.rightbtn or uicore.uilib.mouseTravel > 6:
                return
            cameraSvc = sm.GetService('camera')
            if cameraSvc.dungeonHack.IsFreeLook():
                picktype, pickobject = self.GetPick()
                if pickobject:
                    cameraSvc.LookAt(pickobject.translationCurve.id)
                return
            scene = sm.GetService('sceneManager').GetRegisteredScene('default')
            camera = sm.GetService('sceneManager').GetRegisteredCamera('default')
            if camera is not None:
                proj = camera.projectionMatrix.transform
                view = camera.viewMatrix.transform
                pickDir = scene.PickInfinity(uicore.ScaleDpi(x), uicore.ScaleDpi(y), proj, view)
                if pickDir:
                    bp = sm.GetService('michelle').GetRemotePark()
                    if bp is not None:
                        if solarsystemID != eve.session.solarsystemid:
                            return
                        try:
                            bp.CmdGotoDirection(pickDir[0], pickDir[1], pickDir[2])
                            sm.ScatterEvent('OnClientEvent_MoveWithDoubleClick')
                            sm.GetService('menu').ClearAlignTargets()
                            sm.GetService('flightPredictionSvc').GotoDirection(pickDir)
                        except RuntimeError as what:
                            if what.args[0] != 'MonikerSessionCheckFailure':
                                raise what

        finally:
            uthread.UnLock(self)

    def OnMouseUp(self, button, *args):
        sm.ScatterEvent('OnCameraDragEnd')
        self.isMouseMoving = False
        if not (uicore.uilib.leftbtn or uicore.uilib.rightbtn):
            self._isPicked = False
        if not self.blockDisable and not uicore.cmd.IsUIHidden():
            uicore.layer.main.state = uiconst.UI_PICKCHILDREN
        camera = sm.GetService('sceneManager').GetRegisteredCamera('default')
        if camera is None:
            return
        if not uicore.uilib.rightbtn:
            if self.zoomlooking and self.resetfov and camera.fieldOfView != self.prefov:
                uthread.new(self.ResetFov)
            if camera.__typename__ == 'EveCamera':
                if not sm.GetService('camera').targetTracker.tracking:
                    camera.rotationOfInterest = geo2.QuaternionIdentity()
            self.zoomlooking = 0
        if not uicore.uilib.leftbtn:
            self.looking = 0
            self.fovready = 0
        if button == 0 and not uicore.uilib.rightbtn:
            mt = self.GetMouseTravel()
            cameraSvc = sm.GetService('camera')
            freeLookMove = cameraSvc.dungeonHack.IsFreeLook() and uicore.uilib.Key(uiconst.VK_MENU)
            if not (mt and mt > 5 or freeLookMove):
                picktype, pickobject = self.GetPick()
                if pickobject and hasattr(pickobject, 'translationCurve') and hasattr(pickobject.translationCurve, 'id'):
                    slimItem = uix.GetBallparkRecord(pickobject.translationCurve.id)
                    if slimItem and slimItem.groupID not in const.nonTargetableGroups:
                        itemID = pickobject.translationCurve.id
                        sm.GetService('state').SetState(itemID, state.selected, 1)
                        sm.GetService('menu').TacticalItemClicked(itemID)
                elif uicore.uilib.Key(uiconst.VK_MENU):
                    sm.GetService('menu').TryLookAt(eve.session.shipid)
        if not uicore.uilib.leftbtn and not uicore.uilib.rightbtn:
            uicore.uilib.UnclipCursor()
            if uicore.uilib.GetCapture() == self:
                uicore.uilib.ReleaseCapture()
        elif uicore.uilib.leftbtn or uicore.uilib.rightbtn:
            uicore.uilib.SetCapture(self)
        if self.movingCursor:
            if sm.GetService('posAnchor').IsActive():
                sm.GetService('posAnchor').StopMovingCursor()
                self.movingCursor = None
                return
        if eve.session.role & service.ROLE_CONTENT:
            if self.movingCursor:
                self.movingCursor = None
        self.downpos = None

    def GetMouseTravel(self):
        if self.downpos:
            x, y = uicore.uilib.x, uicore.uilib.y
            v = trinity.TriVector(float(x - self.downpos[0]), float(y - self.downpos[1]), 0.0)
            return int(v.Length())
        else:
            return None

    def OnMouseWheel(self, *args):
        self.ZoomBy(uicore.uilib.dz)
        return 1

    def ZoomBy(self, amount):
        sm.GetService('camera').PanCameraBy(amount * 0.001, time=0, cache=True)

    def PrepareTooltipLoad(self, bracket):
        if uicore.uilib.leftbtn or uicore.uilib.rightbtn:
            return None
        currentPos = (uicore.uilib.x, uicore.uilib.y)
        lastPos = getattr(self, 'lastLoadPos', (None, None))
        if lastPos == currentPos:
            return None
        self.lastLoadPos = currentPos
        self.tooltipBracket = bracket
        currentTooltip = uicore.uilib.tooltipHandler.GetPersistentTooltipByOwner(self)
        if currentTooltip and not (currentTooltip.destroyed or currentTooltip.beingDestroyed):
            if currentTooltip.IsOverlapBracket(bracket):
                return None
            currentTooltip.Close()
        isFloating = bracket.IsFloating()
        overlaps, boundingBox = GetOverlaps(bracket, useMousePosition=isinstance(bracket, SensorSuiteBracket), customBracketParent=uicore.layer.bracket)
        overlapSites = sm.GetService('sensorSuite').GetOverlappingSites()
        if isFloating and len(overlaps) + len(overlapSites) == 1:
            return None
        overlapSites.sort(key=lambda x: x.data.GetSortKey())
        self.tooltipPositionRect = bracket.GetAbsolute()
        ro = bracket.renderObject
        self.bracketPosition = (ro.displayX,
         ro.displayY,
         ro.displayWidth,
         ro.displayHeight)
        for bracket in chain(overlaps, overlapSites):
            bracket.opacity = 2.0

        for layer in (uicore.layer.inflight, uicore.layer.sensorSuite):
            animations.FadeTo(layer, startVal=layer.opacity, endVal=0.5, duration=0.5)

        uicore.uilib.tooltipHandler.LoadPersistentTooltip(self, loadArguments=(bracket,
         overlaps,
         boundingBox,
         overlapSites), customTooltipClass=PersistentInSpaceBracketTooltip, customPositionRect=boundingBox)

    def GetTooltipDelay(self):
        return settings.user.ui.Get(TOOLTIP_SETTINGS_BRACKET, TOOLTIP_DELAY_BRACKET)

    def GetTooltipPosition(self, *args, **kwds):
        return self.tooltipPositionRect

    def GetTooltipPointer(self):
        tooltipPanel = uicore.uilib.tooltipHandler.GetPersistentTooltipByOwner(self)
        if not tooltipPanel:
            return
        x, y, width, height = self.bracketPosition
        bracketLayerWidth = uicore.layer.bracket.displayWidth
        bracketLayerHeight = uicore.layer.bracket.displayHeight
        width = uicore.ReverseScaleDpi(width)
        height = uicore.ReverseScaleDpi(height)
        overlapAmount = len(tooltipPanel.overlaps)
        isCompact = tooltipPanel.isCompact
        if x <= 0:
            if isCompact and overlapAmount == 1:
                return uiconst.POINT_LEFT_2
            else:
                return uiconst.POINT_LEFT_3
        elif x + width >= bracketLayerWidth:
            if isCompact and overlapAmount == 1:
                return uiconst.POINT_RIGHT_2
            else:
                return uiconst.POINT_RIGHT_3
        elif y <= 0:
            if isCompact:
                return uiconst.POINT_TOP_2
            else:
                return uiconst.POINT_TOP_1
        elif y + height >= bracketLayerHeight:
            if isCompact:
                return uiconst.POINT_BOTTOM_2
            else:
                return uiconst.POINT_BOTTOM_1
        if isCompact:
            return uiconst.POINT_BOTTOM_2
        else:
            return uiconst.POINT_BOTTOM_1

    def GetTooltipPositionFallbacks(self):
        tooltipPanel = uicore.uilib.tooltipHandler.GetPersistentTooltipByOwner(self)
        if tooltipPanel:
            isCompact = tooltipPanel.isCompact
        else:
            isCompact = False
        if isCompact:
            return [uiconst.POINT_TOP_2,
             uiconst.POINT_TOPLEFT,
             uiconst.POINT_TOPRIGHT,
             uiconst.POINT_BOTTOMLEFT,
             uiconst.POINT_BOTTOMRIGHT]
        else:
            return [uiconst.POINT_TOP_1,
             uiconst.POINT_TOPLEFT,
             uiconst.POINT_TOPRIGHT,
             uiconst.POINT_BOTTOMLEFT,
             uiconst.POINT_BOTTOMRIGHT]

    def OnMouseEnter(self, *args):
        if self is None or self.destroyed or self.parent is None or self.parent.destroyed:
            return
        if not self.blockDisable and not uicore.cmd.IsUIHidden():
            uicore.layer.main.state = uiconst.UI_PICKCHILDREN
        if sm.IsServiceRunning('tactical'):
            uthread.pool('InflightNav::MouseEnter --> ResetTargetingRanges', sm.GetService('tactical').ResetTargetingRanges)
        uiutil.SetOrder(self, -1)

    def OnMouseMove(self, *args):
        if uicore.IsDragging():
            return
        if uicore.uilib.leftbtn:
            if not self.isMouseMoving:
                sm.ScatterEvent('OnCameraDragStart')
            self.isMouseMoving = True
        self.sr.hint = ''
        self.sr.tcursor.left = uicore.uilib.x - 1
        self.sr.tcursor.top = uicore.uilib.y
        if not self._isPicked:
            return
        lib = uicore.uilib
        ctrl = lib.Key(uiconst.VK_CONTROL)
        alt = lib.Key(uiconst.VK_MENU)
        camera = sm.GetService('sceneManager').GetRegisteredCamera('default')
        if camera is None:
            return
        if lib.leftbtn and self.movingCursor:
            if sm.GetService('posAnchor').IsActive():
                sm.GetService('posAnchor').MoveCursor(self.movingCursor, lib.dx, lib.dy, camera)
                return
            if eve.session.role & service.ROLE_CONTENT:
                sm.GetService('scenario').MoveCursor(self.movingCursor, lib.dx, lib.dy, camera)
                return
        if (self.looking or self.zoomlooking) and camera.__typename__ == 'EveCamera':
            dx = lib.dx
            dy = lib.dy
            fov = camera.fieldOfView
            cameraSvc = sm.GetService('camera')
            if alt and cameraSvc.dungeonHack.IsFreeLook():
                leftBtn = lib.leftbtn and not lib.rightbtn and not lib.midbtn
                rightBtn = lib.rightbtn and not lib.leftbtn and not lib.midbtn
                midBtn = lib.rightbtn and lib.leftbtn or lib.midbtn
                if leftBtn:
                    camera.OrbitParent(-dx * fov * 0.2, -dy * fov * 0.2)
                if rightBtn:
                    cameraSvc.PanCameraBy(-0.01 * dy, time=0)
                if midBtn:
                    vertMovement = geo2.Vec3Scale(camera.upVec, dy * camera.translationFromParent / uicore.uilib.desktop.height)
                    horizMovement = geo2.Vec3Scale(camera.rightVec, -dx * camera.translationFromParent / uicore.uilib.desktop.height)
                    cameraSvc._ChangeCamPos(geo2.Vec3Add(vertMovement, horizMovement))
                return
            if lib.rightbtn and not lib.leftbtn:
                camera.RotateOnOrbit(-dx * fov * 0.2, dy * fov * 0.2)
                self.fovready = self.zoomlooking = 1
            if lib.leftbtn ^ lib.rightbtn:
                if abs(dx) + abs(dy) > 1:
                    sm.GetService('targetTrackingService').MouseTrackInterrupt()
            if lib.leftbtn and not lib.rightbtn:
                camera.OrbitParent(-dx * fov * 0.2, dy * fov * 0.2)
            if lib.leftbtn and lib.rightbtn:
                if self.fovready and self.zoomlooking:
                    camera.fieldOfView = dy * 0.01 + fov
                    if camera.fieldOfView > FOV_MAX:
                        camera.fieldOfView = FOV_MAX
                    if camera.fieldOfView < FOV_MIN:
                        camera.fieldOfView = FOV_MIN
                    self.resetfov = 1
                else:
                    sm.GetService('camera').PanCameraBy(-0.01 * dy, time=0, cache=True)
                    if ctrl:
                        camera.fieldOfView = -dx * 0.01 + fov
                        if camera.fieldOfView > FOV_MAX:
                            camera.fieldOfView = FOV_MAX
                        if camera.fieldOfView < FOV_MIN:
                            camera.fieldOfView = FOV_MIN
                    else:
                        camera.OrbitParent(-dx * fov * 0.2, 0.0)

    def ResetFov(self):
        if self.prefov is not None:
            camera = sm.GetService('sceneManager').GetRegisteredCamera('default')
            if camera is None:
                return
            to = FOV_MAX
            fr = camera.fieldOfView
            start, ndt = blue.os.GetSimTime(), 0.0
            while ndt != 1.0:
                ndt = min(blue.os.TimeDiffInMs(start, blue.os.GetSimTime()) / 1000.0, 1.0)
                camera.fieldOfView = mathUtil.Lerp(fr, to, ndt)
                blue.pyos.synchro.Yield()

            self.prefov = None
        self.resetfov = 0

    def ShowTargetingCursor(self):
        self.sr.tcursor.left = uicore.uilib.x - 1
        self.sr.tcursor.top = uicore.uilib.y
        self.sr.tcursor.state = uiconst.UI_DISABLED

    def HideTargetingCursor(self):
        self.sr.tcursor.state = uiconst.UI_HIDDEN

    def GetPick(self):
        if not trinity.app.IsActive():
            return (None, None)
        scene = sm.GetService('sceneManager').GetRegisteredScene('default')
        x, y = uicore.ScaleDpi(uicore.uilib.x), uicore.ScaleDpi(uicore.uilib.y)
        if scene:
            projection, view, viewport = uix.GetFullscreenProjectionViewAndViewport()
            pick = scene.PickObject(x, y, projection, view, viewport)
            if pick:
                return ('scene', pick)
        return (None, None)

    def OnMouseHover(self, *args):
        return
        picktype, pickobject = self.GetPick()
        if pickobject and hasattr(pickobject, 'translationCurve') and hasattr(pickobject.translationCurve, 'id'):
            itemID = pickobject.translationCurve.id
            slimItem = uix.GetBallparkRecord(itemID)
            if slimItem:
                slimItemName = uix.GetSlimItemName(slimItem)
                if slimItemName:
                    self.sr.hint = slimItemName

    def GetMenu(self, itemID = None):
        if self.locked:
            return []
        m = []
        cam = sm.GetService('sceneManager').GetRegisteredCamera('default')
        if cam is None:
            return
        if not itemID:
            picktype, pickobject = self.GetPick()
            if pickobject and hasattr(pickobject, 'translationCurve') and hasattr(pickobject.translationCurve, 'id'):
                itemID = pickobject.translationCurve.id
            if pickobject:
                if sm.GetService('posAnchor').IsActive():
                    if pickobject.name[:6].lower() == 'cursor':
                        m.append((uiutil.MenuLabel('UI/Inflight/POS/AnchorHere'), sm.GetService('posAnchor').SubmitAnchorPosSelect, ()))
                        m.append(None)
                        m.append((uiutil.MenuLabel('UI/Inflight/POS/CancelAnchoring'), sm.GetService('posAnchor').CancelAchorPosSelect, ()))
                        return m
        if not itemID:
            mm = []
            if not (eve.rookieState and eve.rookieState < 32):
                mm = self.GetSpaceMenu().GetMenu()
            m += [(uiutil.MenuLabel('UI/Inflight/ResetCamera'), sm.GetService('camera').ResetCamera, ())]
            m += [None, [uiutil.MenuLabel('UI/Inflight/ShowSystemInMapBrowser'), sm.GetService('menu').ShowInMapBrowser, (eve.session.solarsystemid2,)], None]
            return m + mm
        bp = sm.GetService('michelle').GetBallpark()
        if not bp:
            return m
        slimItem = bp.GetInvItem(itemID)
        if slimItem is None:
            return m
        pickid = slimItem.itemID
        groupID = slimItem.groupID
        categoryID = slimItem.categoryID
        if eve.session.shipid is None:
            return m
        m += sm.GetService('menu').CelestialMenu(slimItem.itemID, slimItem=slimItem)
        return m

    def ShowRadialMenuIndicator(self, slimItem, *args):
        if not slimItem:
            return
        bracket = sm.GetService('bracket').GetBracket(slimItem.itemID)
        if bracket is None:
            return
        bracket.ShowRadialMenuIndicator()

    def HideRadialMenuIndicator(self, slimItem, *args):
        if slimItem is None:
            return
        bracket = sm.GetService('bracket').GetBracket(slimItem.itemID)
        if bracket is None:
            return
        bracket.HideRadialMenuIndicator()

    def OnDropData(self, dragObj, nodes):
        if dragObj.__guid__ in ('listentry.DroneMainGroup', 'listentry.DroneSubGroup', 'listentry.DroneEntry'):
            DropDronesInSpace(dragObj, nodes)
        elif dragObj.__guid__ in ('xtriui.InvItem', 'listentry.InvItem'):
            deployItems = []
            for node in nodes:
                if node.item.ownerID != session.charid:
                    return
                if node.item.locationID != session.shipid:
                    return
                if HasDeployComponent(node.item.typeID):
                    deployItems.append(node.item)

            if deployItems:
                deploy.DeployAction(deployItems)
