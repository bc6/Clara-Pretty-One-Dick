#Embedded file name: eve/client/script/ui/shared/infoPanels\InfoPanelBase.py
import carbonui.const as uiconst
from carbonui.util.bunch import Bunch
import infoPanelConst
from infoPanelConst import MODE_NORMAL, MODE_COMPACT, MODE_COLLAPSED
import uiprimitives
import uicontrols
import util
import blue
import localization
import telemetry
from math import pi
import uthread

class InfoPanelBase(uicontrols.ContainerAutoSize):
    """ Base class for left-hand side info panels that are always visible"""
    __guid__ = 'uicls.InfoPanelBase'
    default_mode = MODE_COLLAPSED
    default_iconTexturePath = 'res:/UI/texture/icons/77_32_30.png'
    default_align = uiconst.TOTOP
    default_isModeFixed = False
    label = ''
    panelTypeID = None
    hasSettings = True
    isCollapsable = True
    headerCls = uicontrols.EveCaptionSmall
    MAINPADBOTTOM = 10
    HEADER_FADE_WIDTH = 20
    __notifyevents__ = ['ProcessUpdateInfoPanel']

    def __init__(self, **kw):
        uicontrols.ContainerAutoSize.__init__(self, **kw)
        attributesBunch = Bunch(**kw)
        self.PostApplyAttributes(attributesBunch)

    @telemetry.ZONE_FUNCTION
    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self._mode = None
        self.isInModeTransition = False
        self.isModeFixed = attributes.Get('isModeFixed', self.default_isModeFixed)
        self.topCont = uiprimitives.Container(name='topCont', parent=self, align=uiconst.TOTOP, state=uiconst.UI_NORMAL, height=28)
        if not self.isModeFixed:
            self.topCont.OnClick = self.OnTopContClick
            self.topCont.OnDblClick = self.OnTopContDblClick
            self.topCont.OnMouseEnter = self.OnTopContMouseEnter
            self.topCont.OnMouseExit = self.OnTopContMouseExit
        self.hoverBG = uiprimitives.Fill(bgParent=self.topCont, color=util.Color.WHITE, opacity=0.0)
        self.headerBtnCont = uiprimitives.Container(name='headerBtnCont', parent=self.topCont, align=uiconst.TOLEFT, width=infoPanelConst.LEFTPAD)
        self.headerCont = uiprimitives.Container(name='headerCont', parent=self.topCont)
        self.headerButton = self.ConstructHeaderButton()
        self.collapseArrow = uiprimitives.Sprite(parent=self.headerBtnCont, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/Neocom/arrowDown.png', pos=(6, 0, 7, 7), opacity=0.0)
        if not self.hasSettings:
            self.headerButton.pickState = uiconst.TR2_SPS_OFF
        self.mainCont = uicontrols.ContainerAutoSize(name='mainCont', parent=self, align=uiconst.TOTOP, padLeft=infoPanelConst.LEFTPAD, padBottom=self.MAINPADBOTTOM)

    def ConstructHeaderButton(self):
        import uicls
        return uicls.UtilMenu(name='headerButton', parent=self.headerBtnCont, align=uiconst.CENTERRIGHT, menuAlign=uiconst.TOPLEFT, pos=(0,
         0,
         self.topCont.height,
         self.topCont.height), iconSize=18, texturePath=self.default_iconTexturePath, GetUtilMenu=self.GetSettingsMenu)

    def PostApplyAttributes(self, attributes):
        mode = attributes.get('mode', self.default_mode)
        if not self.IsAvailable():
            self.Hide()
            self._mode = mode
        else:
            self.SetMode(mode, register=False)

    @staticmethod
    def IsAvailable():
        """ Is this info panel currently available for viewing """
        return True

    def GetMode(self):
        return self._mode

    def SetMode(self, mode, register = True):
        if mode == MODE_COLLAPSED and not self.isCollapsable:
            return
        if self.mode is not None and mode == self.mode:
            return
        if register:
            sm.GetService('infoPanel').SavePanelModeSetting(self.panelTypeID, mode)
        oldMode = self._mode
        self._mode = mode
        self.Update(oldMode)

    mode = property(GetMode, SetMode)

    def ProcessUpdateInfoPanel(self, panelTypeID):
        if panelTypeID is None or panelTypeID == self.panelTypeID:
            self.Update()

    def Update(self, oldMode = None):
        """ Update UI according to mode (NORMAL / COMPACT / COLLAPSED) """
        if not self.IsAvailable():
            self.Hide()
            return
        self.Show()
        self.isInModeTransition = True
        self.OnBeforeModeChanged(oldMode)
        try:
            if self.mode == MODE_NORMAL:
                if oldMode == MODE_COMPACT:
                    self.mainCont.opacity = 0.0
                    self.mainCont.height = 0
                    self.mainCont.padBottom = 0
                    self.EnableAutoSize()
                    self.mainCont.DisableAutoSize()
                    self.mainCont.Show()
                self.ConstructNormal()
            elif self.mode == MODE_COMPACT:
                self.ConstructCompact()
            elif self.mode == MODE_COLLAPSED:
                self.ConstructCollapsed()
            else:
                raise RuntimeError('Invalid infoPanel mode: %s' % self.mode)
            self.ModeTransition(oldMode)
        finally:
            self.isInModeTransition = False

    def ModeTransition(self, oldMode = None):
        """ 
        Set visibility according to new state and animate if going between states 
        If oldMode is None, it means we're initializing and don't want to animate
        """
        self.OnStartModeChanged(oldMode)
        if self.mode == MODE_COLLAPSED:
            if oldMode:
                self.AnimFadeOut()
            self._SetCollapsedState()
        elif self.mode == MODE_NORMAL:
            self.Show()
            uicore.animations.MorphScalar(self.collapseArrow, 'rotation', startVal=self.collapseArrow.rotation, endVal=0, duration=0.3)
            if oldMode == MODE_COLLAPSED:
                self.AnimFadeIn()
            elif oldMode == MODE_COMPACT:
                self.AnimFadeInMainCont()
            self._SetNormalState()
            sm.GetService('infoPanel').CheckAllPanelsFit(self.panelTypeID)
        elif self.mode == MODE_COMPACT:
            self.Show()
            uicore.animations.MorphScalar(self.collapseArrow, 'rotation', startVal=self.collapseArrow.rotation, endVal=pi / 2, duration=0.3)
            if oldMode == MODE_COLLAPSED:
                self.AnimFadeIn()
            elif oldMode == MODE_NORMAL:
                self.AnimFadeOutMainCont()
            self._SetCompactState()
        self.OnEndModeChanged(oldMode)

    def OnBeforeModeChanged(self, oldMode):
        """ Mode change is about to start. Construct method has not been called """
        pass

    def OnStartModeChanged(self, oldMode):
        """ Mode change has taken place, but animations haven't started """
        pass

    def OnEndModeChanged(self, oldMode):
        """ Mode change has completely finished, including animation """
        pass

    def _SetNormalState(self):
        self.mainCont.opacity = 1.0
        self.mainCont.EnableAutoSize()
        self.mainCont.Show()

    def _SetCollapsedState(self):
        self.Hide()
        self.mainCont.Show()
        self.mainCont.EnableAutoSize()
        self.mainCont.opacity = 1.0
        self.mainCont.padBottom = self.MAINPADBOTTOM
        self.mainCont.left = 0

    def _SetCompactState(self):
        self.mainCont.Hide()
        self.mainCont.EnableAutoSize()

    def AnimFadeIn(self):
        duration = 0.3
        self.mainCont.Show()
        _, height = self.mainCont.GetAutoSize()
        height += self.MAINPADBOTTOM
        height += self.topCont.height
        self.left = 5
        self.opacity = 0.0
        uicore.animations.MorphScalar(self, 'height', 0, height, duration=duration)
        blue.synchro.Sleep(100)
        uicore.animations.MorphScalar(self, 'left', 5, 0, duration=duration)
        uicore.animations.MorphScalar(self, 'padBottom', 0, self.default_padBottom, duration=duration)
        uicore.animations.FadeIn(self, duration=duration, sleep=True)

    def AnimFadeOut(self):
        duration = 0.3
        uicore.animations.FadeOut(self, duration=duration)
        blue.synchro.Sleep(100)
        uicore.animations.MorphScalar(self, 'left', 0, 5, duration=duration)
        uicore.animations.MorphScalar(self, 'height', self.height, 0, duration=duration)
        uicore.animations.MorphScalar(self, 'padBottom', self.padBottom, 0, duration=duration, sleep=True)

    def AnimFadeInMainCont(self):
        duration = 0.3
        _, height = self.mainCont.GetAutoSize()
        uicore.animations.MorphScalar(self.mainCont, 'height', 0, height, duration=duration)
        uicore.animations.MorphScalar(self.mainCont, 'padBottom', 0, self.MAINPADBOTTOM, duration=duration)
        blue.synchro.Sleep(100)
        uicore.animations.MorphScalar(self.mainCont, 'left', 5, 0, duration=duration)
        uicore.animations.FadeTo(self.mainCont, 0.0, 1.0, duration=duration, sleep=True)

    def AnimFadeOutMainCont(self):
        duration = 0.3
        self.mainCont.DisableAutoSize()
        uicore.animations.MorphScalar(self.mainCont, 'left', 0, 5, duration=duration)
        uicore.animations.FadeOut(self.mainCont, duration=duration)
        blue.synchro.SleepWallclock(100)
        uicore.animations.MorphScalar(self.mainCont, 'height', self.mainCont.height, 0, duration=duration)
        uicore.animations.MorphScalar(self.mainCont, 'padBottom', self.mainCont.padBottom, 0, duration=duration, sleep=True)

    def OnTopContMouseEnter(self, *args):
        uicore.animations.FadeIn(self.hoverBG, 0.05, duration=0.1)
        uicore.animations.FadeIn(self.collapseArrow, duration=0.3)

    def OnTopContMouseExit(self, *args):
        uicore.animations.FadeOut(self.hoverBG, duration=0.3)
        uicore.animations.FadeOut(self.collapseArrow, duration=0.3)

    def GetSettingsMenu(self, menuParent):
        pass

    def OnTopContClick(self, *args):
        if self.isInModeTransition:
            return
        if self.mode == MODE_NORMAL:
            self.SetMode(MODE_COMPACT)
        else:
            self.SetMode(MODE_NORMAL)

    def OnTopContDblClick(self, *args):
        self.SetMode(MODE_COLLAPSED)

    @classmethod
    def OnPanelContainerIconPressed(cls, *args):
        sm.GetService('infoPanel').OnPanelContainerIconPressed(cls.panelTypeID)

    @classmethod
    def GetClassHint(cls):
        if sm.GetService('infoPanel').GetModeForPanel(cls.panelTypeID) != MODE_COLLAPSED:
            return localization.GetByLabel(cls.label)

    def ConstructNormal(self):
        """ Construct Normal mode UI """
        pass

    def ConstructCompact(self):
        """ Construct compact mode UI """
        pass

    def ConstructCollapsed(self):
        """ Construct collapsed mode UI """
        pass
