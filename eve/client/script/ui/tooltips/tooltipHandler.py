#Embedded file name: eve/client/script/ui/tooltips\tooltipHandler.py
import uthread
import log
import blue
import weakref
import carbonui.const as uiconst
from carbonui.control.menu import ObjectHasMenu
from carbonui.util.mouseTargetObject import MouseTargetObject
from eve.client.script.ui.control.pointerPanel import FadeOutPanelAndClose
from eve.client.script.ui.control.tooltips import TooltipPanel, TooltipGeneric, TooltipPersistentPanel
from eve.client.script.ui.tooltips.tooltipUtil import RefreshTooltipForOwner as RefreshTooltipForOwnerUtil
FADEOUT_FAST = 0.1
LOAD_ABORTED = 1
LOAD_LOADED = 2
LOAD_NOTLOADED = 3
SLEEPTIME_COOLDOWN = 500
TOOLTIP_DELAY_MIN = 5
TOOLTIP_DELAY_MAX = 3005
TOOLTIP_SETTINGS_GENERIC = 'tooltipDelayGeneric'
TOOLTIP_DELAY_GENERIC = 250
TOOLTIP_DELAY_GAMEPLAY = 250
TOOLTIP_SETTINGS_MODULE = 'tooltipDelayModule'
TOOLTIP_DELAY_MODULE = 700
TOOLTIP_SETTINGS_BRACKET = 'tooltipDelayBracket'
TOOLTIP_DELAY_BRACKET = 50

class TooltipHandler(object):
    lastMouseOver = None
    lastMousePosition = (-1, -1)
    lastCloseTime = None
    lastAuxiliaryTooltipStr = None
    tooltipPanel = None
    tooltipHint = None
    dirty = True
    tooltipThread = None
    persistentTooltips = None

    def __init__(self, *args, **kwds):
        self.persistentTooltips = weakref.WeakKeyDictionary()

    def RefreshTooltipForOwner(self, owner):
        return RefreshTooltipForOwnerUtil(owner)

    def GetPersistentTooltipByOwner(self, owner):
        if owner.destroyed:
            return
        if owner in self.persistentTooltips:
            panel = self.persistentTooltips[owner]
            if not (panel.destroyed or panel.beingDestroyed):
                return panel

    def LoadPersistentTooltip(self, owner, loadFunction = None, loadArguments = None, parent = None, customPointDirection = None, customPositionRect = None, customTooltipClass = None):
        if owner.destroyed:
            return
        currentTooltip = self.GetPersistentTooltipByOwner(owner)
        if currentTooltip and not (currentTooltip.destroyed or currentTooltip.beingDestroyed):
            FadeOutPanelAndClose(currentTooltip, duration=FADEOUT_FAST)
        tooltipClass = customTooltipClass or TooltipPersistentPanel
        if parent is None:
            parent = uicore.layer.menu
        tooltipPanel = tooltipClass(parent=parent, owner=owner, idx=0, state=uiconst.UI_DISABLED)
        self.persistentTooltips[owner] = tooltipPanel
        loadFunction = loadFunction or getattr(tooltipPanel, 'LoadTooltip', None)
        if loadFunction and loadArguments:
            loadFunction(*loadArguments)
        elif loadFunction:
            loadFunction(tooltipPanel, owner)
        uthread.new(tooltipPanel.ShowPanel, owner)
        return tooltipPanel

    def RefreshTooltip(self):
        if self.dirty:
            uthread.new(self._UpdateTooltip)

    def FlagTooltipsDirty(self, *args, **kwds):
        if not uicore.isRunning:
            return
        self.dirty = True

    UpdateTooltip = FlagTooltipsDirty

    def HaveVisibleTooltipPanel(self):
        return self.tooltipPanel and not (self.tooltipPanel.destroyed or self.tooltipPanel.beingDestroyed)

    def HaveVisibleTooltipHint(self):
        return self.tooltipHint and not (self.tooltipHint.destroyed or self.tooltipHint.beingDestroyed)

    def _CloseTooltipPanel(self):
        if self.HaveVisibleTooltipPanel():
            FadeOutPanelAndClose(self.tooltipPanel, duration=FADEOUT_FAST)
            self.tooltipPanel = None

    def _CloseTooltipHint(self):
        if self.HaveVisibleTooltipHint():
            FadeOutPanelAndClose(self.tooltipHint, duration=FADEOUT_FAST)
            self.tooltipHint = None

    def _UpdateTooltip(self):
        currentMouseOver = uicore.uilib.mouseOver
        currentAuxiliaryTooltipStr = uicore.uilib.auxiliaryTooltip
        if ObjectHasMenu(currentMouseOver) and not self.IsUnderTooltip(currentMouseOver):
            self._CloseTooltipPanel()
            self._CloseTooltipHint()
            self.lastMouseOver = None
            return
        self.dirty = False
        if currentMouseOver is self.lastMouseOver and not self.HaveVisibleTooltipPanel() and self.HaveVisibleTooltipHint():
            hint = self.GetHintFromUIObject(currentMouseOver)
            if hint:
                self.tooltipHint.SetTooltipString(hint, currentMouseOver)
                return
        currentPosition = (uicore.uilib.x, uicore.uilib.y)
        newPosition = currentPosition != self.lastMousePosition
        self.lastMousePosition = currentPosition
        if not newPosition and (self.HaveVisibleTooltipPanel() or self.HaveVisibleTooltipHint()):
            showInstant = True
        else:
            showInstant = False
            if hasattr(currentMouseOver, 'GetTooltipDelay'):
                tooltipDelay = currentMouseOver.GetTooltipDelay()
            else:
                tooltipDelay = settings.user.ui.Get(TOOLTIP_SETTINGS_GENERIC, TOOLTIP_DELAY_GENERIC)
            initTime = int(max(TOOLTIP_DELAY_MIN, min(tooltipDelay, TOOLTIP_DELAY_MAX)))
            renewTime = initTime / 5
            if self.HaveVisibleTooltipPanel() or self.HaveVisibleTooltipHint():
                sleepTime = renewTime
            elif self.lastCloseTime and blue.os.TimeDiffInMs(self.lastCloseTime, blue.os.GetWallclockTime()) < SLEEPTIME_COOLDOWN:
                sleepTime = renewTime
            else:
                sleepTime = initTime
            blue.synchro.SleepWallclock(sleepTime)
            if currentMouseOver is not uicore.uilib.mouseOver:
                return
        newMouseOver = currentMouseOver is not self.lastMouseOver or currentAuxiliaryTooltipStr is not self.lastAuxiliaryTooltipStr
        self.lastMouseOver = currentMouseOver
        self.lastAuxiliaryTooltipStr = currentAuxiliaryTooltipStr
        panelLoaded = LOAD_NOTLOADED
        if self.HaveVisibleTooltipPanel() and self.tooltipPanel.owner is currentMouseOver:
            return
        if newMouseOver or self.tooltipPanel and (self.tooltipPanel.destroyed or self.tooltipPanel.beingDestroyed):
            panelLoaded = self._LoadTooltipPanel(currentMouseOver, showInstant)
            if panelLoaded == LOAD_ABORTED:
                return
        if panelLoaded == LOAD_NOTLOADED:
            hint = self.GetHintFromUIObject(currentMouseOver)
            if hint:
                if self.HaveVisibleTooltipPanel() and not self.IsUnderTooltip(currentMouseOver):
                    FadeOutPanelAndClose(self.tooltipPanel, duration=FADEOUT_FAST)
                if not self.tooltipHint or self.tooltipHint.destroyed or self.tooltipHint.beingDestroyed:
                    self.tooltipHint = TooltipGeneric(parent=uicore.layer.hint, idx=0)
                self.tooltipHint.SetTooltipString(hint, currentMouseOver)
            else:
                self._CloseTooltipHint()

    def _LoadTooltipPanel(self, owner, showInstant = False):
        tooltipPanelClassInfo = getattr(owner, 'tooltipPanelClassInfo', None)
        if not tooltipPanelClassInfo and hasattr(owner, 'GetTooltipPanelClassInfo'):
            tooltipPanelClassInfo = owner.GetTooltipPanelClassInfo()
        tooltipLoadFunction = getattr(owner, 'LoadTooltipPanel', None)
        panelLoaded = LOAD_NOTLOADED
        if tooltipLoadFunction or tooltipPanelClassInfo:
            if tooltipPanelClassInfo:
                tooltipPanel = tooltipPanelClassInfo.CreateTooltip(parent=uicore.layer.menu, owner=owner, idx=0)
            else:
                tooltipPanel = TooltipPanel(parent=uicore.layer.menu, owner=owner, idx=0, state=uiconst.UI_DISABLED)
                tooltipPanel.columns = 1
                tooltipPanel.margin = 0
                tooltipPanel.cellPadding = 0
                tooltipPanel.cellSpacing = 0
            preTooltipPanel = self.tooltipPanel
            self.tooltipPanel = tooltipPanel
            if tooltipPanelClassInfo:
                tooltipPanel.LoadTooltip()
            else:
                try:
                    owner.LoadTooltipPanel(tooltipPanel, owner)
                except:
                    tooltipPanel.Close()
                    raise

            if owner.destroyed or tooltipPanel.destroyed:
                return LOAD_ABORTED
            if len(tooltipPanel.children):
                panelLoaded = LOAD_LOADED
                if preTooltipPanel and not (preTooltipPanel.destroyed or preTooltipPanel.beingDestroyed):
                    FadeOutPanelAndClose(preTooltipPanel, duration=FADEOUT_FAST)
                self._CloseTooltipHint()
                if showInstant:
                    tooltipPanel.opacity = 1.0
                if tooltipPanel.pickState == uiconst.TR2_SPS_ON:
                    MouseTargetObject(tooltipPanel)
                uthread.new(tooltipPanel.ShowPanel, owner)
            else:
                tooltipPanel.Close()
                self.tooltipPanel = None
        return panelLoaded

    def GetHintFromUIObject(self, uiObject):
        hint = uiObject.GetHint()
        if hint is None and getattr(uiObject, 'sr', None):
            hint = uiObject.sr.Get('hint', None)
        if hint and not isinstance(hint, (str, unicode)):
            log.LogWarn('Tooltips only supports hints as strings', hint)
            return
        if uicore.uilib.auxiliaryTooltip:
            if hint:
                hint += '<br>' + uicore.uilib.auxiliaryTooltip
            else:
                hint = uicore.uilib.auxiliaryTooltip
        return hint

    def IsUnderTooltip(self, uiObject):
        """returns True if uiObject is nested under tooltip menu"""
        parent = uiObject.parent
        if not parent:
            return False
        if isinstance(parent, TooltipPanel):
            return True
        return self.IsUnderTooltip(parent)
