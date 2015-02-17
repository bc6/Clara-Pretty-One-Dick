#Embedded file name: eve/client/script/ui/services\menuAction.py
import types
from carbonui.control.menu import ClearMenuLayer
from eve.client.script.ui.control.glowSprite import GlowSprite
import util
import crimewatchConst
import uthread
import carbonui.const as uiconst
import uicontrols
import uiprimitives
import uix
import localization
import math
import base
import blue
import state
import uiutil
import log
import sys
from eve.client.script.ui.services.menuSvcExtras.movementFunctions import SetDefaultDist
from eve.client.script.ui.services.menuSvcExtras.movementFunctions import GetGlobalActiveItemKeyName
from eve.client.script.ui.services.menuSvcExtras.movementFunctions import DefaultWarpToLabel

class ActionMenu(uiprimitives.Container):
    __guid__ = 'xtriui.ActionMenu'

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.actionMenuOptions = {'UI/Commands/ShowInfo': ('ui_44_32_24', 0, 0, 0, 0),
         'UI/Inflight/LockTarget': ('ui_44_32_17', 0, 0, 0, 0),
         'UI/Inflight/UnlockTarget': ('ui_44_32_17', 0, 0, 0, 1),
         'UI/Inflight/ApproachObject': ('ui_44_32_23', 0, 0, 0, 0),
         'UI/Inflight/LookAtObject': ('ui_44_32_20', 0, 0, 0, 0),
         'UI/Inflight/ResetCamera': ('ui_44_32_20', 0, 0, 0, 1),
         'UI/Inflight/Submenus/KeepAtRange': ('ui_44_32_22', 0, 0, 1, 0),
         'UI/Inflight/OrbitObject': ('ui_44_32_21', 0, 0, 1, 0),
         'UI/Inflight/DockInStation': ('ui_44_32_9', 0, 0, 0, 0),
         'UI/Chat/StartConversation': ('ui_44_32_33', 0, 0, 0, 0),
         'UI/Commands/OpenCargo': ('ui_44_32_35', 0, 0, 0, 0),
         'UI/Commands/OpenMyCargo': ('ui_44_32_35', 0, 0, 0, 0),
         'UI/PI/Common/AccessCustomOffice': ('ui_44_32_35', 0, 0, 0, 0),
         'UI/Inflight/StopMyShip': ('ui_44_32_38', 0, 0, 0, 0),
         'UI/Inflight/StopMyCapsule': ('ui_44_32_38', 0, 0, 0, 0),
         'UI/Inflight/ActivateAutopilot': ('ui_44_32_12', 0, 0, 0, 0),
         'UI/Inflight/DeactivateAutopilot': ('ui_44_32_12', 0, 0, 0, 1),
         'UI/Inflight/EjectFromShip': ('ui_44_32_36', 0, 0, 0, 0),
         'UI/Inflight/SelfDestructShipOrPod': ('ui_44_32_37', 0, 0, 0, 0),
         'UI/Inflight/BoardShip': ('ui_44_32_40', 0, 0, 0, 0),
         'UI/Inflight/Jump': ('ui_44_32_39', 0, 0, 0, 0),
         'UI/Inflight/EnterWormhole': ('ui_44_32_39', 0, 0, 0, 0),
         'UI/Inflight/ActivateGate': ('ui_44_32_39', 0, 0, 0, 0),
         'UI/Drones/ScoopDroneToBay': ('ui_44_32_1', 0, 0, 0, 0),
         'UI/Commands/ReadNews': ('ui_44_32_47', 0, 0, 0, 0)}
        self.lastActionSerial = None
        self.sr.actionTimer = None
        self.itemID = None
        self.width = 134
        self.height = 134
        self.pickRadius = -1
        self.oldx = self.oldy = None
        uicore.event.RegisterForTriuiEvents(uiconst.UI_MOUSEUP, self.OnGlobalUp)
        self.mouseMoveCookie = uicore.event.RegisterForTriuiEvents(uiconst.UI_MOUSEMOVE, self.OnGlobalMove)

    def Load(self, slimItem, centerItem = None, setposition = 1):
        if not (uicore.uilib.leftbtn or uicore.uilib.midbtn):
            return
        actions = sm.StartService('menu').CelestialMenu(slimItem.itemID, slimItem=slimItem, ignoreTypeCheck=1)
        reasonsWhyNotAvailable = getattr(actions, 'reasonsWhyNotAvailable', {})
        if not (uicore.uilib.leftbtn or uicore.uilib.midbtn):
            return
        self.itemID = slimItem.itemID
        warptoLabel = DefaultWarpToLabel()[0]
        warpops = {warptoLabel: ('ui_44_32_18', 0, 0, 1, 0)}
        self.actionMenuOptions.update(warpops)
        serial = ''
        valid = {}
        inactive = None
        for each in actions:
            if each:
                if isinstance(each[0], tuple):
                    name = each[0][0]
                else:
                    name = each[0]
                if name in self.actionMenuOptions:
                    valid[name] = each
                    if type(each[1]) not in (str, unicode):
                        serial += '%s_' % name

        if not (uicore.uilib.leftbtn or uicore.uilib.midbtn):
            return
        if serial != self.lastActionSerial:
            uix.Flush(self)
            i = 0
            order = ['UI/Commands/ShowInfo',
             ['UI/Inflight/LockTarget', 'UI/Inflight/UnlockTarget'],
             ['UI/Inflight/ApproachObject', warptoLabel],
             'UI/Inflight/OrbitObject',
             'UI/Inflight/Submenus/KeepAtRange']
            default = [None, ['UI/Inflight/LookAtObject', 'UI/Inflight/ResetCamera'], None]
            lookAtString = 'UI/Inflight/LookAtObject'
            resetCameraString = 'UI/Inflight/ResetCamera'
            openCargoString = 'UI/Commands/OpenCargo'
            groups = {const.groupStation: [None, [lookAtString, resetCameraString], 'UI/Inflight/DockInStation'],
             const.groupCargoContainer: [None, [lookAtString, resetCameraString], openCargoString],
             const.groupMissionContainer: [None, [lookAtString, resetCameraString], openCargoString],
             const.groupSecureCargoContainer: [None, [lookAtString, resetCameraString], openCargoString],
             const.groupAuditLogSecureContainer: [None, [lookAtString, resetCameraString], openCargoString],
             const.groupFreightContainer: [None, [lookAtString, resetCameraString], openCargoString],
             const.groupSpawnContainer: [None, [lookAtString, resetCameraString], openCargoString],
             const.groupSpewContainer: [None, [lookAtString, resetCameraString], openCargoString],
             const.groupDeadspaceOverseersBelongings: [None, [lookAtString, resetCameraString], openCargoString],
             const.groupWreck: [None, [lookAtString, resetCameraString], openCargoString],
             const.groupStargate: [None, [lookAtString, resetCameraString], 'UI/Inflight/Jump'],
             const.groupWormhole: [None, [lookAtString, resetCameraString], 'UI/Inflight/EnterWormhole'],
             const.groupWarpGate: [None, [lookAtString, resetCameraString], 'UI/Inflight/ActivateGate'],
             const.groupBillboard: [None, [lookAtString, resetCameraString], 'UI/Commands/ReadNews'],
             const.groupAgentsinSpace: ['UI/Chat/StartConversation', [lookAtString, resetCameraString], None],
             const.groupDestructibleAgentsInSpace: ['UI/Chat/StartConversation', [lookAtString, resetCameraString], None],
             const.groupPlanetaryCustomsOffices: [None, [lookAtString, resetCameraString], 'UI/PI/Common/AccessCustomOffice']}
            categories = {const.categoryShip: ['UI/Chat/StartConversation', [lookAtString, resetCameraString], 'UI/Inflight/BoardShip'],
             const.categoryDrone: [None, [lookAtString, resetCameraString], 'UI/Drones/ScoopDroneToBay']}
            if slimItem.itemID == session.shipid:
                order = ['UI/Commands/ShowInfo',
                 'UI/Inflight/EjectFromShip',
                 ['UI/Inflight/StopMyShip', 'UI/Inflight/StopMyCapsule'],
                 ['UI/Inflight/ActivateAutopilot', 'UI/Inflight/DeactivateAutopilot'],
                 [lookAtString, resetCameraString]]
            elif slimItem.groupID in groups:
                order += groups[slimItem.groupID]
            elif slimItem.categoryID in categories:
                order += categories[slimItem.categoryID]
            else:
                order += default
            step = 360.0 / 8
            rad = 48
            angle = 180.0
            for actionName in order:
                if actionName is None:
                    angle += step
                    i += 1
                    continue
                if type(actionName) == list:
                    action = None
                    for each in actionName:
                        tryaction = valid.get(each, None)
                        if tryaction and type(tryaction[1]) not in (str, unicode):
                            actionName = each
                            action = tryaction
                            break

                    if action is None:
                        actionName = actionName[0]
                        if actionName in valid:
                            action = valid.get(actionName)
                        elif actionName in reasonsWhyNotAvailable:
                            action = (actionName, reasonsWhyNotAvailable.get(actionName))
                        else:
                            action = (actionName, localization.GetByLabel('UI/Menusvc/MenuHints/NoReasonGiven'))
                elif actionName in valid:
                    action = valid.get(actionName)
                elif actionName in reasonsWhyNotAvailable:
                    action = (actionName, reasonsWhyNotAvailable.get(actionName))
                else:
                    action = (actionName, localization.GetByLabel('UI/Menusvc/MenuHints/NoReasonGiven'))
                disabled = type(action[1]) in (str, unicode)
                props = self.actionMenuOptions[actionName]
                btnpar = uiprimitives.Container(parent=self, align=uiconst.TOPLEFT, width=40, height=40, state=uiconst.UI_NORMAL)
                btnpar.left = int(rad * math.cos(angle * math.pi / 180.0)) + (self.width - btnpar.width) / 2
                btnpar.top = int(rad * math.sin(angle * math.pi / 180.0)) + (self.height - btnpar.height) / 2
                btn = uiprimitives.Sprite(parent=btnpar, name='hudBtn', pos=(0, 0, 40, 40), state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/Shared/actionMenuBtn.png')
                btnpar.actionID = actionName
                btnpar.name = actionName
                btnpar.action = action
                btnpar.itemIDs = [slimItem.itemID]
                btnpar.killsub = props[3]
                btnpar.pickRadius = -1
                icon = uicontrols.Icon(icon=props[0], parent=btnpar, pos=(4, 4, 0, 0), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, idx=0)
                if disabled:
                    icon.color.a = 0.5
                    btn.color.a = 0.1
                if props[4]:
                    icon = uicontrols.Icon(icon='ui_44_32_8', parent=btnpar, pos=(5, 5, 0, 0), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, idx=0)
                angle += step
                i += 1

            self.lastActionSerial = serial
            if self.sr.actionTimer is None:
                self.sr.actionTimer = base.AutoTimer(1000, self.Load, slimItem, None, 0)
        if centerItem:
            self.left = max(0, min(uicore.desktop.width - self.width, centerItem.absoluteLeft - (self.width - centerItem.width) / 2))
            self.top = max(0, min(uicore.desktop.height - self.height, centerItem.absoluteTop - (self.height - centerItem.height) / 2))
        elif setposition:
            self.left = max(0, min(uicore.desktop.width - self.width, uicore.uilib.x - self.width / 2))
            self.top = max(0, min(uicore.desktop.height - self.height, uicore.uilib.y - self.height / 2))

    def OnGlobalUp(self, *args):
        if not self or self.destroyed:
            return
        if self.itemID and blue.os.TimeDiffInMs(self.expandTime, blue.os.GetWallclockTime()) < 100:
            sm.StartService('state').SetState(self.itemID, state.selected, 1)
        self.sr.actionTimer = None
        self.sr.updateAngle = None
        mo = uicore.uilib.mouseOver
        self.state = uiconst.UI_HIDDEN
        self.lastActionSerial = None
        if mo in self.children:
            uthread.new(self.OnBtnparClicked, mo)
        else:
            ClearMenuLayer()
        if not self.destroyed:
            uicore.event.UnregisterForTriuiEvents(self.mouseMoveCookie)

    def OnBtnparClicked(self, btnpar):
        sm.StartService('ui').StopBlink(btnpar)
        if btnpar.destroyed:
            ClearMenuLayer()
            return
        if btnpar.killsub and isinstance(btnpar.action[1], list):
            uthread.new(btnpar.action[1][0][2][0][0], btnpar.action[1][0][2][0][1][0])
            ClearMenuLayer()
            return
        if isinstance(btnpar.action[1], basestring):
            sm.StartService('gameui').Say(btnpar.action[1])
        else:
            try:
                apply(*btnpar.action[1:])
            except Exception as e:
                log.LogError(e, 'Failed executing action:', btnpar.action)
                log.LogException()
                sys.exc_clear()

        ClearMenuLayer()

    def OnGlobalMove(self, *args):
        mo = uicore.uilib.mouseOver
        lib = uicore.uilib
        for c in self.children:
            c.opacity = 1.0

        if mo in self.children:
            mo.opacity = 0.7
        if not lib.leftbtn:
            self.oldx = self.oldy = None
            return
        if self.oldx and self.oldy:
            dx, dy = self.oldx - lib.x, self.oldy - lib.y
            camera = sm.GetService('sceneManager').GetRegisteredCamera('default')
            if mo.name == 'blocker' and not lib.rightbtn:
                fov = camera.fieldOfView
                camera.OrbitParent(dx * fov * 0.2, -dy * fov * 0.2)
            elif lib.rightbtn:
                uicore.layer.inflight.zoomlooking = 1
                ClearMenuLayer()
        if hasattr(self, 'oldx') and hasattr(self, 'oldy'):
            self.oldx, self.oldy = lib.x, lib.y
        return 1

    def OnMouseWheel(self, *args):
        camera = sm.GetService('sceneManager').GetRegisteredCamera('default')
        if camera.__typename__ == 'EveCamera':
            camera.Dolly(uicore.uilib.dz * 0.001 * abs(camera.translationFromParent))
            camera.translationFromParent = sm.StartService('camera').CheckTranslationFromParent(camera.translationFromParent)
        return 1


class Action(uiprimitives.Container):
    __guid__ = 'xtriui.Action'
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.actionID = None
        self.disabled = attributes.get('disabled', False)
        self.Prepare_(icon=attributes.icon)

    def Prepare_(self, icon = None):
        opacity = 0.2 if self.disabled else 1.0
        self.icon = GlowSprite(parent=self, align=uiconst.TOALL, texturePath=icon, state=uiconst.UI_DISABLED, opacity=opacity, iconOpacity=1.0)
        self.sr.fill = uiprimitives.Fill(parent=self, state=uiconst.UI_HIDDEN)

    def LoadTooltipPanel(self, tooltipPanel, *args):
        tooltipPanel.LoadGeneric2ColumnTemplate()
        shortcutString = None
        reasonString = None
        distString = None
        keywords = {}
        if isinstance(self.action[1], basestring):
            reasonString = self.action[1]
            if self.actionID == 'UI/Inflight/WarpToWithinDistance':
                keywords['distance'] = sm.GetService('menu').GetDefaultActionDistance('WarpTo')
        else:
            if isinstance(self.action[0], uiutil.MenuLabel):
                actionNamePath, keywords = self.action[0]
            if self.actionID in ('UI/Inflight/OrbitObject', 'UI/Inflight/Submenus/KeepAtRange'):
                key = GetGlobalActiveItemKeyName(actionNamePath)
                current = sm.GetService('menu').GetDefaultActionDistance(key)
                if current is not None:
                    distString = util.FmtDist(current)
                else:
                    distString = localization.GetByLabel('UI/Menusvc/MenuHints/NoDistanceSet')
        if hasattr(self, 'cmdName'):
            shortcutString = uicore.cmd.GetShortcutStringByFuncName(self.cmdName)
        actionName = localization.GetByLabel(self.actionID, **keywords)
        if distString:
            hint = localization.GetByLabel('UI/Menusvc/MenuHints/SelectedItemActionWithDist', actionName=actionName, distanceString=distString)
        else:
            hint = actionName
        tooltipPanel.AddLabelShortcut(hint, shortcutString)
        if reasonString:
            tooltipPanel.AddLabelMedium(text=reasonString, colSpan=tooltipPanel.columns)

    def GetTooltipPointer(self):
        return uiconst.POINT_TOP_2

    def GetMenu(self):
        m = []
        label = ''
        key = GetGlobalActiveItemKeyName(self.actionID)
        if key == 'Orbit':
            label = uiutil.MenuLabel('UI/Inflight/SetDefaultOrbitDistance', {'typeName': self.actionID})
        elif key == 'KeepAtRange':
            label = uiutil.MenuLabel('UI/Inflight/SetDefaultKeepAtRangeDistance', {'typeName': self.actionID})
        elif key == 'WarpTo':
            label = uiutil.MenuLabel('UI/Inflight/SetDefaultWarpWithinDistance', {'typeName': self.actionID})
        if len(label) > 0:
            m.append((label, SetDefaultDist, (key,)))
        return m

    def OnMouseEnter(self, *args):
        if self.disabled:
            return
        if self.sr.Get('fill', None):
            if hasattr(self, 'action'):
                if 'EngageTarget' in self.action[0][0]:
                    crimewatchSvc = sm.GetService('crimewatchSvc')
                    droneInfo = self.action[2]
                    if len(self.itemIDs) > 1 and len(droneInfo) > 1 and isinstance(droneInfo[0], (types.MethodType, types.LambdaType)):
                        droneIDs = droneInfo[1]
                    else:
                        droneIDs = droneInfo
                    targetID = sm.GetService('target').GetActiveTargetID()
                    requiredSafetyLevel = crimewatchSvc.GetRequiredSafetyLevelForEngagingDrones(droneIDs, targetID)
                    if crimewatchSvc.CheckUnsafe(requiredSafetyLevel):
                        if requiredSafetyLevel == const.shipSafetyLevelNone:
                            color = crimewatchConst.Colors.Criminal.GetRGBA()
                        else:
                            color = crimewatchConst.Colors.Suspect.GetRGBA()
                        self.sr.fill.color.SetRGB(*color[:3])
            self.sr.fill.state = uiconst.UI_DISABLED
            self.sr.fill.opacity = 0.25
            uicore.animations.MorphScalar(self.icon, 'glowAmount', self.icon.glowAmount, 1.0, duration=uiconst.TIME_ENTRY)

    def OnMouseExit(self, *args):
        if self.sr.Get('fill', None):
            self.sr.fill.color.SetRGBA(1, 1, 1, 1)
            self.sr.fill.state = uiconst.UI_HIDDEN
            uicore.animations.MorphScalar(self.icon, 'glowAmount', self.icon.glowAmount, 0.0, duration=uiconst.TIME_ENTRY)

    def OnMouseDown(self, *args):
        if self.sr.Get('fill', None):
            self.sr.fill.color.a = 0.5
            uicore.animations.MorphScalar(self.icon, 'glowAmount', self.icon.glowAmount, 1.3, duration=uiconst.TIME_ENTRY)

    def OnMouseUp(self, *args):
        if self.sr.Get('fill', None):
            self.sr.fill.color.a = 0.25
            uicore.animations.MorphScalar(self.icon, 'glowAmount', self.icon.glowAmount, 1.0, duration=uiconst.TIME_ENTRY)

    def OnClick(self, *args):
        sm.StartService('ui').StopBlink(self)
        if self.destroyed:
            ClearMenuLayer()
            return
        if self.killsub and isinstance(self.action[1], list):
            uthread.new(self.action[1][0][1], self.action[1][0][2][0])
            ClearMenuLayer()
            return
        if isinstance(self.action[1], basestring):
            sm.StartService('gameui').Say(self.action[1])
        else:
            try:
                actionMenuLabel = self.action[0]
                labelPath = actionMenuLabel[0]
                if len(self.action) > 2 and self.action[2]:
                    funcArgs = self.action[2]
                    if sm.GetService('menu').CaptionIsInMultiFunctions(labelPath) and not isinstance(funcArgs[0], types.MethodType):
                        funcArgs = (funcArgs,)
                else:
                    funcArgs = ()
                apply(self.action[1], funcArgs)
            except Exception as e:
                log.LogError(e, 'Failed executing action:', self.action)
                log.LogException()
                sys.exc_clear()

        ClearMenuLayer()
