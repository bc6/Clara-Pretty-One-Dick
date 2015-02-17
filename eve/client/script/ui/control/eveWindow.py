#Embedded file name: eve/client/script/ui/control\eveWindow.py
from carbonui.control.window import WindowCore
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from eve.client.script.ui.control.buttons import ButtonIcon
from eve.client.script.ui.control.eveIcon import Icon
from eve.client.script.ui.control.buttonGroup import ButtonGroup
from eve.client.script.ui.control.eveLabel import EveLabelSmall
from eve.client.script.ui.control.eveWindowUnderlay import WindowUnderlay
import carbonui.const as uiconst
from eve.client.script.ui.control.glowSprite import GlowSprite
from eve.client.script.ui.control.themeColored import FillThemeColored
import uiprimitives
import uiutil
import types
import base
import localization
from eve.client.script.ui.shared.neocom.neocom.neocomCommon import BTNTYPE_WINDOW

class Window(WindowCore):
    __guid__ = 'uicontrols.Window'
    default_state = uiconst.UI_HIDDEN
    default_pinned = False
    default_isPinable = True
    default_iconNum = 'res:/UI/Texture/WindowIcons/other.png'
    default_topParentHeight = 52
    default_width = 256
    default_height = 128
    default_scope = None

    def ApplyAttributes(self, attributes):
        self.default_parent = uicore.layer.main
        self._pinned = False
        self._pinable = self.default_isPinable
        self.showforward = False
        self.showback = False
        self.isBlinking = False
        self.iconNum = attributes.get('iconNum', self.GetDefaultWndIcon())
        self.scope = attributes.get('scope', self.default_scope)
        self.topParentHeight = attributes.get('topParentHeight', self.default_topParentHeight)
        WindowCore.ApplyAttributes(self, attributes)

    def GetMainArea(self):
        return self.sr.main

    def Prepare_(self):
        self.Prepare_Layout()
        self.Prepare_Header_()
        self.Prepare_LoadingIndicator_()
        self.Prepare_Background_()
        self.Prepare_ScaleAreas_()

    def Prepare_Layout(self):
        self.sr.headerParent = uiprimitives.Container(parent=self.sr.maincontainer, name='headerParent', align=uiconst.TOTOP, pos=(0, 0, 0, 22))
        self.sr.topParent = uiprimitives.Container(parent=self.sr.maincontainer, name='topParent', align=uiconst.TOTOP, clipChildren=True)
        self.sr.mainIcon = GlowSprite(parent=self.sr.topParent, name='mainicon', pos=(0, 0, 64, 64), state=uiconst.UI_HIDDEN)
        self.sr.main = uiprimitives.Container(parent=self.sr.maincontainer, name='main', align=uiconst.TOALL)
        self.SetTopparentHeight(self.topParentHeight)

    def Prepare_Header_(self):
        top = uiprimitives.Container(parent=self.sr.headerParent, name='top', align=uiconst.TOALL, padding=(2, 2, 2, 0))
        self.sr.captionParent = uiprimitives.Container(parent=top, name='captionParent', align=uiconst.TOALL, clipChildren=True)
        self.sr.caption = EveLabelSmall(text='', parent=self.sr.captionParent, left=8, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT)
        self.headerFill = FillThemeColored(bgParent=top, opacity=0.5)

    def Prepare_LoadingIndicator_(self):
        WindowCore.Prepare_LoadingIndicator_(self)
        self.sr.loadingIndicator.icons = [ 'ui_38_16_%s' % (210 + i) for i in xrange(8) ]

    def Prepare_HeaderButtons_(self):
        self.sr.headerButtons = ContainerAutoSize(name='headerButtons', state=uiconst.UI_PICKCHILDREN, align=uiconst.TOPRIGHT, parent=self.sr.maincontainer, pos=(4, 4, 0, 16), idx=0)
        isStack = isinstance(self, self.GetStackClass())
        if isStack:
            closeHint = localization.GetByLabel('UI/Control/EveWindow/CloseStack')
            minimizeHint = localization.GetByLabel('UI/Control/EveWindow/MinimizeStack')
        else:
            closeHint = localization.GetByLabel('UI/Common/Buttons/Close')
            minimizeHint = localization.GetByLabel('UI/Control/EveWindow/Minimize')
        helpHint = localization.GetByLabel('UI/Control/EveWindow/Help')
        pinFunc = self.TogglePinState
        if self.IsPinned():
            pinhint = localization.GetByLabel('UI/Control/EveWindow/Unpin')
        else:
            pinhint = localization.GetByLabel('UI/Control/EveWindow/Pin')
        if self.IsCompact():
            compactHint = localization.GetByLabel('/Carbon/UI/Controls/Window/DisableCompactMode')
            compactFunc = self.UnCompact
            compactIcon = 'res:/UI/Texture/icons/38_16_258.png'
        else:
            compactHint = localization.GetByLabel('/Carbon/UI/Controls/Window/EnableCompactMode')
            compactFunc = self.Compact
            compactIcon = 'res:/UI/Texture/icons/38_16_259.png'
        for texturePath, name, hint, showflag, clickfunc in [('res:/UI/Texture/icons/38_16_220.png',
          'close',
          closeHint,
          self.IsKillable(),
          self.CloseByUser),
         ('res:/UI/Texture/icons/38_16_221.png',
          'minimize',
          minimizeHint,
          self.IsMinimizable(),
          self.Minimize),
         ('res:/UI/Texture/icons/38_16_222.png',
          'pin',
          pinhint,
          self.IsPinable(),
          pinFunc),
         (compactIcon,
          'compact',
          compactHint,
          self.IsCompactable(),
          compactFunc)]:
            if not showflag:
                continue
            btn = ButtonIcon(parent=self.sr.headerButtons, align=uiconst.TORIGHT, width=16, texturePath=texturePath, hint=hint, func=clickfunc)

    def Prepare_Background_(self):
        self.sr.underlay = WindowUnderlay(parent=self)
        self.sr.underlay.SetState(uiconst.UI_DISABLED)

    def GetDefaultWndIcon(self):
        return self.default_iconNum

    def GetNeocomGroupIcon(self):
        """ Returns the icon which should be used for this window in the Neocom """
        return self.iconNum

    def GetNeocomGroupLabel(self):
        """ Returns the label which should be used for this window in the Neocom """
        return self.GetCaption()

    def GetNeocomButtonType(self):
        return BTNTYPE_WINDOW

    def SetWndIcon(self, iconNum = None, headerIcon = 0, size = 64, fullPath = None, mainTop = -3, mainLeft = 0, hidden = False, **kw):
        self.iconNum = iconNum or self.GetDefaultWndIcon()
        if hidden:
            return
        icon = self.sr.mainIcon
        if not icon:
            return
        if iconNum is None:
            icon.state = uiconst.UI_HIDDEN
            return
        icon.state = uiconst.UI_DISABLED
        icon.LoadIcon(iconNum or fullPath, ignoreSize=True)
        icon.top = mainTop
        icon.left = mainLeft
        if headerIcon:
            icon.width = icon.height = 16
            icon.left = 4
            icon.top = 0
            uiutil.Transplant(icon, uiutil.GetChild(self, 'captionParent'))
            if self.sr.caption:
                self.sr.caption.left = 24
            self.sr.headerIcon = icon

    def SetTopparentHeight(self, height):
        self.sr.topParent.height = height

    def HideMainIcon(self):
        self.sr.mainIcon.state = uiconst.UI_HIDDEN

    def SetUtilMenu(self, utilMenuFunc):
        if self.sr.tab:
            self.sr.tab.SetUtilMenu(utilMenuFunc)
        else:
            self.sr.caption.left = 20
            from eve.client.script.ui.control.utilMenu import UtilMenu
            utilMenu = UtilMenu(menuAlign=uiconst.TOPLEFT, parent=self.sr.captionParent, align=uiconst.TOPLEFT, GetUtilMenu=utilMenuFunc, texturePath='res:/UI/Texture/Icons/73_16_50.png', pos=(const.defaultPadding,
             1,
             14,
             14))

    def SetHeaderIcon(self, iconNo = 'ui_73_16_50', shiftLabel = 12, hint = None, size = 16):
        par = self.sr.captionParent
        if self.sr.headerIcon:
            self.sr.headerIcon.Close()
            self.sr.headerIcon = None
        if iconNo is None:
            if self.sr.caption:
                self.sr.caption.left = 8
        else:
            self.sr.headerIcon = Icon(icon=iconNo, parent=par, pos=(4,
             0,
             size,
             size), align=uiconst.RELATIVE, ignoreSize=True)
            self.sr.headerIcon.SetAlpha(0.8)
            self.sr.headerIcon.OnMouseEnter = self.HeaderIconMouseEnter
            self.sr.headerIcon.OnMouseExit = self.HeaderIconMouseExit
            self.sr.headerIcon.expandOnLeft = 1
            if self.sr.caption:
                self.sr.caption.left = 8 + shiftLabel
        self.headerIconNo = iconNo
        self.headerIconHint = hint
        if self.sr.tab:
            self.sr.tab.SetIcon(iconNo, 14, hint)

    def HeaderIconMouseEnter(self, *args):
        self.sr.headerIcon.SetAlpha(1.0)

    def HeaderIconMouseExit(self, *args):
        self.sr.headerIcon.SetAlpha(0.8)

    def TogglePinState(self, *args):
        if self.IsPinned():
            self.Unpin()
        else:
            self.Pin()

    def Pin(self, delegate = 1, *args, **kwds):
        self.sr.underlay.Pin()
        if self.headerFill:
            self.headerFill.opacity = 0.2
        self._SetPinned(True)
        if delegate:
            shift = uicore.uilib.Key(uiconst.VK_SHIFT)
            ctrl = uicore.uilib.Key(uiconst.VK_CONTROL)
            if shift or ctrl:
                if shift:
                    alignedWindows = self.FindConnectingWindows()
                else:
                    alignedWindows = self.FindConnectingWindows('bottom')
                for each in alignedWindows:
                    if each == self:
                        continue
                    each.Pin(0)

        self.RefreshHeaderButtonsIfVisible()

    def Unpin(self, delegate = 1, *args, **kwds):
        self.sr.underlay.UnPin()
        if self.headerFill:
            self.headerFill.opacity = 0.5
        self._SetPinned(False)
        if delegate:
            shift = uicore.uilib.Key(uiconst.VK_SHIFT)
            ctrl = uicore.uilib.Key(uiconst.VK_CONTROL)
            if shift or ctrl:
                if shift:
                    alignedWindows = self.FindConnectingWindows()
                else:
                    alignedWindows = self.FindConnectingWindows('bottom')
                for each in alignedWindows:
                    if each == self:
                        continue
                    each.Unpin(0)

        self.RefreshHeaderButtonsIfVisible()

    def HideHeaderFill(self):
        self.headerFill.Hide()

    def MakePinable(self):
        self._pinable = True
        self.RefreshHeaderButtonsIfVisible()

    def MakeUnpinable(self):
        self._pinable = False
        self.RefreshHeaderButtonsIfVisible()

    def SetActive(self, *args):
        if self.InStack():
            self.GetStack().SetActive()
        self.sr.underlay.AnimEntry()
        if self.display:
            self.SetNotBlinking()
        self.OnSetActive_(self)
        sm.ScatterEvent('OnWindowSetActive', self)

    def OnSetInactive(self, *args):
        if self.InStack():
            self.GetStack().OnSetInactive()
        self.sr.underlay.AnimExit()
        sm.ScatterEvent('OnWindowSetInctive', self)

    def SetBlinking(self):
        if uicore.registry.GetActive() == self:
            return
        self.isBlinking = True
        sm.ScatterEvent('OnWindowStartBlinking', self)

    def SetNotBlinking(self):
        self.isBlinking = False
        sm.ScatterEvent('OnWindowStopBlinking', self)

    def IsPinned(self):
        return self._pinned

    def IsPinable(self):
        return self._pinable

    def _SetPinned(self, isPinned):
        self._pinned = isPinned
        self.RegisterState('_pinned')

    def IsBlinking(self):
        return self.isBlinking

    def DefineButtons(self, buttons, okLabel = None, okFunc = 'default', args = 'self', cancelLabel = None, cancelFunc = 'default', okModalResult = 'default', default = None):
        if okLabel is None:
            okLabel = localization.GetByLabel('UI/Common/Buttons/OK')
        if cancelLabel is None:
            cancelLabel = localization.GetByLabel('UI/Common/Buttons/Cancel')
        if getattr(self.sr, 'bottom', None) is None:
            self.sr.bottom = uiutil.FindChild(self, 'bottom')
            if not self.sr.bottom:
                self.sr.bottom = uiprimitives.Container(name='bottom', parent=self.sr.maincontainer, align=uiconst.TOBOTTOM, height=24, idx=0)
        if self.sr.bottom is None:
            return
        self.sr.bottom.Flush()
        if buttons is None:
            self.sr.bottom.state = uiconst.UI_HIDDEN
            return
        self.sr.bottom.height = 24
        if okModalResult == 'default':
            okModalResult = uiconst.ID_OK
        if okFunc == 'default':
            okFunc = self.ConfirmFunction
        if cancelFunc == 'default':
            cancelFunc = self.ButtonResult
        if isinstance(buttons, (types.ListType, types.TupleType)):
            btns = []
            for btn in buttons:
                if btn.id == uiconst.ID_CANCEL:
                    cancelButton = 1
                else:
                    cancelButton = 0
                btns.append([btn.label,
                 self.ButtonResult,
                 None,
                 None,
                 btn.id,
                 0,
                 cancelButton])

        elif buttons == uiconst.OK:
            btns = [[okLabel,
              okFunc,
              args,
              None,
              okModalResult,
              1,
              0]]
        elif buttons == uiconst.OKCANCEL:
            btns = [[okLabel,
              okFunc,
              args,
              None,
              okModalResult,
              1,
              0], [cancelLabel,
              cancelFunc,
              args,
              None,
              uiconst.ID_CANCEL,
              0,
              1]]
        elif buttons == uiconst.OKCLOSE:
            closeLabel = localization.GetByLabel('UI/Common/Buttons/Close')
            btns = [[okLabel,
              okFunc,
              args,
              None,
              okModalResult,
              1,
              0], [closeLabel,
              self.CloseByUser,
              args,
              None,
              uiconst.ID_CLOSE,
              0,
              1]]
        elif buttons == uiconst.YESNO:
            yesLabel = localization.GetByLabel('UI/Common/Buttons/Yes')
            noLabel = localization.GetByLabel('UI/Common/Buttons/No')
            btns = [[yesLabel,
              self.ButtonResult,
              args,
              None,
              uiconst.ID_YES,
              1,
              0], [noLabel,
              self.ButtonResult,
              args,
              None,
              uiconst.ID_NO,
              0,
              0]]
        elif buttons == uiconst.YESNOCANCEL:
            yesLabel = localization.GetByLabel('UI/Common/Buttons/Yes')
            noLabel = localization.GetByLabel('UI/Common/Buttons/No')
            btns = [[yesLabel,
              self.ButtonResult,
              args,
              None,
              uiconst.ID_YES,
              1,
              0], [noLabel,
              self.ButtonResult,
              args,
              None,
              uiconst.ID_NO,
              0,
              0], [cancelLabel,
              cancelFunc,
              args,
              None,
              uiconst.ID_CANCEL,
              0,
              1]]
        elif buttons == uiconst.CLOSE:
            closeLabel = localization.GetByLabel('UI/Common/Buttons/Close')
            btns = [[closeLabel,
              self.CloseByUser,
              args,
              None,
              uiconst.ID_CANCEL,
              0,
              1]]
        elif type(okLabel) == types.ListType or type(okLabel) == types.TupleType:
            btns = []
            for index in xrange(len(okLabel)):
                label = okLabel[index]
                additionalArguments = {'Function': okFunc,
                 'Arguments': args,
                 'Cancel Label': cancelLabel,
                 'Cancel Function': cancelFunc,
                 'Modal Result': okModalResult,
                 'Default': default}
                for argName in additionalArguments:
                    if type(additionalArguments[argName]) in (types.ListType, types.TupleType) and len(additionalArguments[argName]) > index:
                        additionalArguments[argName] = additionalArguments[argName][index]

                cancel = additionalArguments['Modal Result'] == uiconst.ID_CANCEL
                btns.append([label,
                 additionalArguments['Function'],
                 additionalArguments['Arguments'],
                 None,
                 additionalArguments['Modal Result'],
                 additionalArguments['Default'],
                 cancel])

        else:
            btns = [[okLabel,
              okFunc,
              args,
              None,
              okModalResult,
              1,
              0]]
        if default is not None:
            for each in btns:
                each[5] = each[4] == default

        buttonGroup = ButtonGroup(btns=btns, parent=self.sr.bottom, unisize=1)
        self.sr.bottom.height = max(24, buttonGroup.height)
        self.sr.bottom.state = uiconst.UI_PICKCHILDREN

    SetButtons = DefineButtons

    def NoSeeThrough(self):
        solidBackground = uiprimitives.Fill(name='solidBackground', color=(0.0, 0.0, 0.0, 1.0), padding=(2, 2, 2, 2))
        self.sr.underlay.background.append(solidBackground)
        self.MakeUnpinable()

    def SetScope(self, scope):
        self.scope = scope

    def CloseByUser(self, *args):
        """
        Calling this method to close a window registers the _open attribute as False, so
        the window will not open up automatically on session change.
        """
        if not self.IsKillable():
            return
        WindowCore.CloseByUser(self)

    def SetMainIconSize(self, size = 64):
        self.sr.mainIcon.width = self.sr.mainIcon.height = size

    def Collapse(self, forceCollapse = False, checkchain = 1, *args):
        if not self._collapseable or not forceCollapse and self.IsCollapsed():
            return
        if self.sr.topParent:
            self.sr.topParent.state = uiconst.UI_HIDDEN
        if self.sr.bottom:
            self.sr.bottom.state = uiconst.UI_HIDDEN
        if self.sr.main:
            self.sr.main.state = uiconst.UI_HIDDEN
        WindowCore.Collapse(self, forceCollapse, checkchain, args)

    def Expand(self, checkchain = 1, *args):
        WindowCore.Expand(self, checkchain, args)
        if self.sr.topParent:
            self.sr.topParent.state = uiconst.UI_PICKCHILDREN
        if self.sr.bottom:
            self.sr.bottom.state = uiconst.UI_PICKCHILDREN
        if self.sr.main:
            self.sr.main.state = uiconst.UI_PICKCHILDREN

    def OnResize_(self, *args):
        self.OnResizeUpdate(self)

    def OnResizeUpdate(self, *args):
        pass

    def GetStackClass(self):
        from eve.client.script.ui.control.eveWindowStack import WindowStack
        return WindowStack

    def HideHeaderButtons(self):
        self._hideHeaderButtons = True

    def UnhideHeaderButtons(self):
        self._hideHeaderButtons = False

    def ShowHeaderButtons(self, refresh = False, *args):
        if getattr(self, '_hideHeaderButtons', False):
            return
        if refresh and self.sr.headerButtons:
            self.sr.headerButtons.Close()
            self.sr.headerButtons = None
        if self.sr.stack or self.GetAlign() != uiconst.RELATIVE or uicore.uilib.leftbtn or getattr(self, 'isImplanted', False):
            return
        if not self.sr.headerButtons:
            self.Prepare_HeaderButtons_()
        if self.sr.headerButtons:
            w = self.sr.headerButtons.width
            if self.sr.captionParent:
                self.sr.captionParent.padRight = w + 6
            if self.sr.loadingIndicator:
                self.sr.loadingIndicator.left = w + self.sr.headerButtons.left
            self.sr.headerButtons.Show()
            self.sr.headerButtonsTimer = base.AutoTimer(1000, self.CloseHeaderButtons)

    def IndicateStackable(self, wnd = None):
        if wnd is None:
            if self.sr.snapIndicator:
                self.sr.snapIndicator.Close()
                self.sr.snapIndicator = None
            return
        if not wnd.IsStackable() or not self.IsStackable():
            return
        if self.sr.snapIndicator is None:
            self.sr.snapIndicator = FillThemeColored(parent=None, colorType=uiconst.COLORTYPE_UIHILIGHTGLOW, align=uiconst.TOTOP_NOPUSH, height=20, padding=(2, 2, 2, 0))
        si = self.sr.snapIndicator
        si.state = uiconst.UI_DISABLED
        if si.parent != wnd:
            uiutil.Transplant(si, wnd, idx=0)
        else:
            uiutil.SetOrder(si, 0)

    def GetUtilMenuFunc(self):
        return getattr(self, 'utilMenuFunc', None)

    def InitializeStatesAndPosition(self, *args, **kwds):
        self.startingup = 1
        pinned = self.GetRegisteredState('pinned')
        if pinned:
            self.Pin(delegate=False)
        else:
            self.Unpin(delegate=False)
        WindowCore.InitializeStatesAndPosition(self, *args, **kwds)
        self.startingup = 0

    @classmethod
    def GetSideOffset(cls):
        if uicore.layer.sidePanels:
            return uicore.layer.sidePanels.GetSideOffset()
        return (0, 0)

    def GetRegisteredState(self, stateName):
        if stateName == 'locked':
            if self.GetRegisteredState('pinned') and settings.char.windows.Get('lockwhenpinned', False):
                return True
        return WindowCore.GetRegisteredState(self, stateName)

    def IsLocked(self):
        return self._locked or self.IsPinned() and settings.char.windows.Get('lockwhenpinned', False)

    def DefineIcons(self, icon, customicon = None, mainTop = -3):
        import types
        if customicon is not None:
            iconNo = customicon
        else:
            mapping = {uiconst.INFO: 'res:/ui/Texture/WindowIcons/info.png',
             uiconst.WARNING: 'res:/ui/Texture/WindowIcons/warning.png',
             uiconst.QUESTION: 'res:/ui/Texture/WindowIcons/question.png',
             uiconst.ERROR: 'res:/ui/Texture/WindowIcons/stop.png',
             uiconst.FATAL: 'res:/UI/Texture/WindowICons/criminal.png'}
            if type(icon) == types.StringType:
                iconNo = icon
            else:
                iconNo = mapping.get(icon, 'res:/ui/Texture/WindowIcons/warning.png')
        self.SetWndIcon(iconNo, mainTop=mainTop)

    def ConfirmFunction(self, button, *args):
        uicore.registry.Confirm(button)

    def HideBackground(self):
        self.HideUnderlay()
        for each in self.children[:]:
            if each.name.startswith('_lite'):
                each.Close()

    def ShowBackground(self):
        self.ShowUnderlay()
        liteState = self.IsPinned()

    def ShowDialog(self, modal = False, state = uiconst.UI_NORMAL):
        if modal:
            self.NoSeeThrough()
        return WindowCore.ShowDialog(self, modal, state)

    @classmethod
    def GetDefaultLeftOffset(cls, width, align = None, left = 0):
        return sm.GetService('window').GetCameraLeftOffset(width, align, left)

    @classmethod
    def ToggleOpenClose(cls, *args, **kwds):
        """ 
            1) If window isn't open, open it
            2) Else, if window isn't fully visible and on top, make it
            3) Else, close the window
        """
        wnd = cls.GetIfOpen(windowID=kwds.get('windowID', None))
        if wnd:
            wasCollapsed = wnd.IsCollapsed()
            if wasCollapsed:
                wnd.Expand()
            if wnd.sr.stack:
                if wnd.sr.stack.GetActiveWindow() != wnd:
                    wnd.Maximize()
                    return wnd
                obscured = wnd.sr.stack.ObscuredByOtherWindows()
            else:
                obscured = wnd.ObscuredByOtherWindows()
            if wnd.IsMinimized():
                wnd.Maximize()
                return wnd
            if obscured:
                uicore.registry.SetFocus(wnd)
                return wnd
            if not wasCollapsed:
                wnd.CloseByUser()
        else:
            return cls.Open(*args, **kwds)

    def ObscuredByOtherWindows(self):
        """
        Finds out if another window overlapps self. Another window overlapps self if its area intersects us and
        it is higher than us in the window stack.
        """
        intersecting = self.GetIntersectingWindows()
        for wnd in intersecting:
            if self not in uicore.layer.main.children:
                return False
            if wnd not in uicore.layer.main.children:
                continue
            if uicore.layer.main.children.index(self) > uicore.layer.main.children.index(wnd):
                return True

        return False

    def _Minimize(self, animate = True):
        if self.destroyed or self.IsMinimized():
            return
        self.OnStartMinimize_(self)
        self._changing = True
        self._SetMinimized(True)
        uicore.registry.CheckMoveActiveState(self)
        if animate:
            x, y = sm.GetService('neocom').GetMinimizeToPos(self)
            x = float(x) / uicore.desktop.width
            y = float(y) / uicore.desktop.height
            t = uiprimitives.Transform(parent=uicore.layer.main, state=uiconst.UI_DISABLED, align=uiconst.TOALL, scalingCenter=(x, y), idx=0)
            wasCacheContent = self.cacheContents
            self.cacheContents = False
            self.SetParent(t)
            uicore.animations.Tr2DFlipOut(t, duration=0.3)
            uicore.animations.FadeOut(t, duration=0.25, sleep=True)
            self.SetParent(uicore.layer.main)
            self.cacheContents = wasCacheContent
            t.Close()
        self.state = uiconst.UI_HIDDEN
        self.OnEndMinimize_(self)
        self._changing = False
        sm.ScatterEvent('OnWindowMinimized', self)

    @classmethod
    def GetSettingsVersion(cls):
        return 1


from carbonui.control.window import WindowCoreOverride
WindowCoreOverride.__bases__ = (Window,)
