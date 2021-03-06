#Embedded file name: eve/client/script/ui/shared/planet/dust\dustPins.py
import eveDustCommon.planetSurface as eveDustPlanetSurface
from eve.client.script.ui.shared.planet.planetUIPins import SpherePinStack
import eve.client.script.ui.shared.planet.planetCommon as planetCommonUI
import trinity
import math
import geo2
import blue
import uicls
import carbonui.const as uiconst
import uiprimitives
import uicontrols
import uiutil
import localization
RADIUS_PIN = 0.1
RADIUS_LOGO = RADIUS_PIN * 0.5
RADIUS_SHADOW = RADIUS_PIN * 1.2
RADIUS_PINEXTENDED = RADIUS_PIN * 1.65
SCALE_PINBASE = 1.01
SCALE_PINLIFTED = 1.0105
SCALE_ONGROUND = 1.001
SCALE_PINOTHERS = 1.0
PINSHADE = {const.objectiveStateCeasefire: (0.0, 0.0, 0.0, 0.4),
 const.objectiveStateMobilizing: (0.5, 0.5, 0.0, 0.4),
 const.objectiveStateWar: (0.5, 0.0, 0.0, 0.4),
 const.objectiveStateRebuilding: (0.0, 0.5, 0.0, 0.4)}
STATE_NAMES = {const.objectiveStateCeasefire: 'UI/PI/Common/Ceasefire',
 const.objectiveStateMobilizing: 'UI/PI/Common/AttackImminent',
 const.objectiveStateWar: 'UI/PI/Common/UnderAttack',
 const.objectiveStateRebuilding: 'UI/PI/Common/Protected'}

class DustBuildIndicatorPin(SpherePinStack):
    __guid__ = 'planet.ui.DustBuildIndicatorPin'

    def __init__(self, surfacePoint, typeID, groupID, transform):
        SpherePinStack.__init__(self, surfacePoint, 1.0)
        self.surfacePin = self.CreateSpherePin(textureName=self.GetIconByGroupID(groupID), layer=10, radius=RADIUS_LOGO, transform=transform, scale=SCALE_PINBASE, color=(1.0, 1.0, 1.0, 0.4))
        self.cannotBuild = self.CreateSpherePin(textureName='res:/UI/Texture/Planet/pin_base.dds', layer=11, radius=RADIUS_PIN, transform=transform, scale=SCALE_PINBASE, color=(0.3, 0.0, 0.0, 0.5))
        self.cannotBuild.display = False
        self.shadow = self.CreateSpherePin(textureName='res:/UI/Texture/Planet/disc_shadow.dds', layer=12, radius=RADIUS_SHADOW, transform=transform, scale=SCALE_ONGROUND, color=(0.0, 0.0, 0.0, 0.3))
        sm.GetService('planetUI').planetNav.SetFocus()

    def SetCanBuildIndication(self, canBuild):
        self.cannotBuild.display = not canBuild

    def GetIconByGroupID(self, groupID):
        icons = {2: 'res:/UI/Texture/Planet/command.dds'}
        return icons.get(groupID)


class PlanetBase(SpherePinStack):
    __guid__ = 'planet.ui.PlanetBase'

    def __init__(self, surfacePoint, pinKv, transform):
        SpherePinStack.__init__(self, surfacePoint, RADIUS_PINEXTENDED)
        self.pinKv = pinKv
        self.transform = transform
        conflictState = eveDustPlanetSurface.GetConflictState(self.pinKv.conflicts)
        self.border = self.CreateSpherePin(textureName='res:/UI/Texture/Planet/pin_base_y.dds', layer=0, radius=RADIUS_PINEXTENDED, transform=transform, scale=SCALE_PINBASE, color=(0.0, 0.0, 0.0, 0.0))
        self.border.display = False
        self.mainPin = self.CreateSpherePin(textureName='res:/UI/Texture/Planet/pin_base.dds', layer=1, radius=RADIUS_PIN, transform=transform, scale=SCALE_PINBASE, color=PINSHADE[conflictState])
        self.shadow = self.CreateSpherePin(textureName='res:/UI/Texture/Planet/disc_shadow.dds', layer=0, radius=RADIUS_SHADOW, transform=transform, scale=SCALE_ONGROUND, color=(0.0, 0.0, 0.0, 0.3))
        self.SetModel(RADIUS_PIN * 1.5)
        self.AssignIDsToPins()
        self.UIContainer = None

    def GetMenu(self):
        menu = []
        if self.pinKv.ownerID == session.corpid:
            if eveDustPlanetSurface.GetConflictState(self.pinKv.conflicts) == const.objectiveStateCeasefire:
                menu.append((uiutil.MenuLabel('UI/PI/Planet/Dust/RemoveGroundInstallation'), sm.GetService('planetUI').myPinManager.RemovePin, [self.pinKv.id]))
                menu.append((uiutil.MenuLabel('UI/PI/Planet/Dust/UpdatePlanetControl'), sm.GetService('planetUI').myPinManager.UpdatePlanetControl, []))
        elif eveDustPlanetSurface.GetConflictState(self.pinKv.conflicts, session.corpid) == const.objectiveStateCeasefire:
            menu.append((uiutil.MenuLabel('UI/PI/Planet/Dust/AttackInstallation'), sm.GetService('planetUI').myPinManager.AttackPin, [self.pinKv.id]))
        return menu

    def GetGMMenu(self):
        menu = []
        menu.append(('%s: %s' % ('PIN', self.pinKv.id), blue.pyos.SetClipboardData, [str(self.pinKv.id)]))
        ownerID = self.GetOwnerID()
        menu.append(('%s: %s' % ('Owner ID', ownerID), blue.pyos.SetClipboardData, [str(ownerID)]))
        menu.append(('GM Change Control', [('EVE System', sm.GetService('planetUI').myPinManager.GMUpdateControl, [const.ownerSystem]), ('My Corp', sm.GetService('planetUI').myPinManager.GMUpdateControl, [session.corpid])]))
        return menu

    def GetContainer(self, parent):
        return None

    def AssignIDsToPins(self):
        """
        Assign unique IDs to pins so we can recognise them when picking
        """
        for pin in self.spherePins:
            pin.name = '%s,%s' % (planetCommonUI.PINTYPE_NORMAL, self.pinKv.id)

        self.border.name = self.shadow.name = ''

    def SetModel(self, scale):
        graphic = cfg.invtypes.Get(self.pinKv.typeID).Graphic()
        self.model = None
        if graphic and graphic.graphicFile:
            graphicFile = str(graphic.graphicFile)
            graphicFile = graphicFile.replace(':/model', ':/dx9/model').replace('.blue', '.red')
            self.model = trinity.Load(graphicFile)
        if not self.model or self.model.__bluetype__ != 'trinity.EveTransform':
            self.model = trinity.Load('res:/dx9/model/worldobject/Orbital/UI/Terrestrial/Command/CommT_T1/CommT_T1.red')
        if not self.model:
            return
        EXT = 1.026
        self.model.scaling = (scale, scale, scale)
        self.model.sortValueMultiplier = 0.5
        self.model.translation = (EXT * self.surfacePoint.x, EXT * self.surfacePoint.y, EXT * self.surfacePoint.z)
        plnSurfRotMat = geo2.MatrixRotationAxis(geo2.Vec3Cross(geo2.Vec3Normalize(self.surfacePoint.GetAsXYZTuple()), (0.0, 1.0, 0.0)), -math.acos(geo2.Vec3Dot(geo2.Vec3Normalize(self.surfacePoint.GetAsXYZTuple()), (0.0, 1.0, 0.0))))
        rotQuat = geo2.QuaternionRotationMatrix(plnSurfRotMat)
        self.model.rotation = rotQuat
        self.model.name = '%s,%s' % (planetCommonUI.PINTYPE_NORMAL, self.pinKv.id)
        self.transform.children.append(self.model)

    def Remove(self):
        SpherePinStack.Remove(self)
        if self.model in self.transform.children:
            self.transform.children.remove(self.model)

    def Selected(self):
        uicls.UIEffects().MorphUI(self.mainPin, 'pinRadius', RADIUS_PIN * 1.5, time=250.0, float=1, newthread=1, maxSteps=100)
        parent = sm.GetService('planetUI').planetUIContainer
        self.UIContainer = DustBasePinContainer(parent=parent, pin=self)

    def Unselected(self):
        uicls.UIEffects().MorphUI(self.mainPin, 'pinRadius', RADIUS_PIN, time=250.0, float=1, newthread=1, maxSteps=100)
        if self.UIContainer:
            sm.GetService('planetUI').planetUIContainer.children.remove(self.UIContainer)

    def GetOwnerID(self):
        return self.pinKv.ownerID

    def GetTypeID(self):
        return self.pinKv.typeID


class DustBasePinContainer(uiprimitives.Container):
    __guid__ = 'planet.ui.DustBasePinContainer'
    default_height = 185
    default_width = 300
    default_state = uiconst.UI_NORMAL
    default_align = uiconst.TOPLEFT
    default_name = 'DustBasePinContainer'
    default_opacity = 0.0

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.pin = attributes.Get('pin', None)
        pad = self.pad = 3
        self.main = uiprimitives.Container(parent=self, name='main', pos=(0, 0, 0, 0), padding=(pad,
         pad,
         pad,
         pad), state=uiconst.UI_PICKCHILDREN, align=uiconst.TOALL)
        pad = const.defaultPadding
        self.sr.footer = uiprimitives.Container(name='footer', parent=self.main, align=uiconst.TOBOTTOM, pos=(0, 0, 0, 25), padding=(pad,
         pad,
         pad,
         pad))
        self.sr.underlay = uicontrols.WindowUnderlay(parent=self)
        self.sr.underlay.state = uiconst.UI_DISABLED
        self.header = self._DrawAlignTopCont(18, 'headerCont')
        self.closeBtn = uicontrols.Icon(name='close', icon='ui_38_16_220', parent=self.header, pos=(0, 0, 16, 16), align=uiconst.TOPRIGHT)
        self.closeBtn.OnClick = lambda : sm.GetService('planetUI').myPinManager.PinUnselected()
        self.headerText = uicontrols.EveLabelMedium(parent=self.header, align=uiconst.CENTER, state=uiconst.UI_NORMAL)
        self.headerText.text = cfg.invtypes.Get(self.pin.GetTypeID()).typeName
        uiprimitives.Line(parent=self.header, align=uiconst.TOBOTTOM)
        self.content = self._DrawAlignTopCont(180, 'contentCont', padding=(4, 4, 4, 4))
        iconX = 180
        itemHeight = 2
        ownerID = self.pin.GetOwnerID()
        conflictState = eveDustPlanetSurface.GetConflictState(self.pin.pinKv.conflicts)
        conflictText = localization.GetByLabel(STATE_NAMES[conflictState])
        self.conflictStateLabel = uicontrols.EveLabelMedium(parent=self.content, pos=(2,
         itemHeight,
         self.default_width - 10,
         16))
        self.conflictStateLabel.text = localization.GetByLabel('UI/PI/Planet/Dust/ConflictState', state=conflictText)
        itemHeight += 20
        if ownerID:
            self.ownerLabel = uicontrols.EveLabelMedium(parent=self.content, pos=(2,
             itemHeight,
             iconX,
             16))
            self.ownerLabel.text = localization.GetByLabel('UI/PI/Planet/Dust/DustPinOwner', player=ownerID)
            self.ownerIcon = uiprimitives.Container(parent=self.content, pos=(iconX,
             itemHeight,
             64,
             64), align=uiconst.RELATIVE)
            uiutil.GetLogoIcon(itemID=ownerID, parent=self.ownerIcon, name='ownercorplogo', acceptNone=False, align=uiconst.TOALL)
            itemHeight += 68
        if ownerID == session.corpid and conflictState == const.objectiveStateCeasefire:
            uicontrols.Button(parent=self.sr.footer, label=localization.GetByLabel('UI/PI/Planet/Dust/DestroyPin'), func=self.Terminate)
        elif ownerID != session.corpid and eveDustPlanetSurface.GetConflictState(self.pin.pinKv.conflicts, session.corpid) == const.objectiveStateCeasefire:
            uicontrols.Button(parent=self.sr.footer, label=localization.GetByLabel('UI/PI/Planet/Dust/AttackInstallation'), func=self.Attack)
        dw = uicore.desktop.width
        dh = uicore.desktop.height
        self.height = self.default_height
        self.width = self.default_width
        self.left = settings.user.ui.Get('planetContPositionX', (dw - self.width) / 2)
        self.top = settings.user.ui.Get('planetContPositionY', (dh - self.height) / 2)
        if self.left < 0:
            self.left = 0
        elif self.left > dw - self.width:
            self.left = dw - self.width
        if self.top < 0:
            self.top = 0
        elif self.top > dh - self.height:
            self.top = dh - self.height
        uicls.UIEffects().MorphUI(self, 'opacity', 1.0, time=250.0, float=1, newthread=1, maxSteps=100)

    def _DrawAlignTopCont(self, height, name, padding = (0, 0, 0, 0), state = uiconst.UI_PICKCHILDREN):
        return uiprimitives.Container(parent=self.main, name=name, pos=(0,
         0,
         0,
         height), padding=padding, state=state, align=uiconst.TOTOP)

    def OnMouseMove(self, *args):
        if uicore.uilib.leftbtn:
            dx, dy = uicore.uilib.dx, uicore.uilib.dy
            self.left += dx
            self.top += dy
            settings.user.ui.Set('planetContPositionX', self.left)
            settings.user.ui.Set('planetContPositionY', self.top)

    def Terminate(self, *args):
        if eve.Message('DestroyGroundObjective', {}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
            return
        sm.GetService('planetUI').myPinManager.RemovePin(self.pin.pinKv.id)
        self.Close()

    def Attack(self, *args):
        if eve.Message('CustomQuestion', {'header': localization.GetByLabel('UI/PI/Planet/Dust/AttackInstallation'),
         'question': localization.GetByLabel('UI/PI/Planet/Dust/ReallyAttackInstallation')}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
            return
        sm.GetService('planetUI').myPinManager.AttackPin(self.pin.pinKv.id)
        self.Close()
