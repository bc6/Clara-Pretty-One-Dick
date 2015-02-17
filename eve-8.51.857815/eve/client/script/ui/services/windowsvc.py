#Embedded file name: eve/client/script/ui/services\windowsvc.py
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
from eve.client.script.ui.control.eveWindowUnderlay import FillUnderlay
import service
import uicontrols
import uiutil
import form
import util
import carbonui.const as uiconst
import telemetry
from eve.client.script.ui.inflight.scanner import Scanner
from eve.client.script.ui.inflight.scannerFiles.directionalScanner import DirectionalScanner
import evegraphics.settings as gfxsettings

class WindowMgr(service.Service):
    __guid__ = 'svc.window'
    __servicename__ = 'window'
    __displayname__ = 'Window Service'
    __dependencies__ = ['form']
    __exportedcalls__ = {'CloseContainer': [],
     'OpenWindows': []}
    __notifyevents__ = ['DoSessionChanging',
     'OnSessionChanged',
     'ProcessRookieStateChange',
     'OnEndChangeDevice',
     'ProcessDeviceChange',
     'OnBlurredBufferCreated',
     'OnHideUI',
     'OnShowUI']
    __startupdependencies__ = ['settings']

    def Run(self, memStream = None):
        self.LogInfo('Starting Window Service')

    def Stop(self, memStream = None):
        self.LogInfo('Stopping Window Service')
        service.Service.Stop(self)

    def ProcessRookieStateChange(self, state):
        if sm.GetService('connection').IsConnected():
            self.OpenWindows()

    def ProcessDeviceChange(self, *args):
        self.PreDeviceChange_DesktopLayout = uicontrols.Window.GetDesktopWindowLayout()

    def OnEndChangeDevice(self, change, *args):
        if 'BackBufferHeight' in change or 'BackBufferWidth' in change:
            self.RealignWindows()
            sm.GetService('device').SetupUIScaling()

    def ValidateWindows(self):
        """
        Sanity checks if any window is completely outside (undrag-able) of the 
        desktop and pushes it back in if so.
        """
        d = uicore.desktop
        all = uicore.registry.GetValidWindows(1, floatingOnly=True)
        for wnd in all:
            if wnd.align != uiconst.RELATIVE:
                continue
            wnd.left = max(-wnd.width + 64, min(d.width - 64, wnd.left))
            wnd.top = max(0, min(d.height - wnd.GetCollapsedHeight(), wnd.top))

    def DoSessionChanging(self, isRemote, session, change):
        if not eve.session.charid:
            for layer in (uicore.layer.starmap,):
                for each in layer.children:
                    each.Close()

    def OnSessionChanged(self, isRemote, session, change):
        if sm.GetService('connection').IsConnected() and 'locationid' in change:
            self.OpenWindows()

    def OnHideUI(self, *args):
        self.UpdateIntersectionBackground()

    def OnShowUI(self, *args):
        self.UpdateIntersectionBackground()

    def ResetWindowSettings(self):
        closeStacks = []
        triggerUpdate = []
        for each in uicore.registry.GetWindows():
            if not isinstance(each, uicontrols.WindowCore):
                continue
            if each.isDialog:
                continue
            if each.parent != uicore.layer.main:
                uiutil.Transplant(each, uicore.layer.main)
            if isinstance(each, uicontrols.WindowStackCore):
                closeStacks.append(each)
            else:
                triggerUpdate.append(each)
                each.sr.stack = None
                each.state = uiconst.UI_HIDDEN
                each.align = uiconst.TOPLEFT
                each.ShowHeader()
                each.ShowBackground()

        for each in closeStacks:
            each.Close()

        uicontrols.Window.ResetAllWindowSettings()
        favorClasses = [form.LSCChannel,
         form.ActiveItem,
         form.OverView,
         form.DroneView,
         form.WatchListPanel]
        done = []
        for cls in favorClasses:
            for each in triggerUpdate:
                if each not in done and isinstance(each, cls):
                    each.InitializeSize()
                    each.InitializeStatesAndPosition()
                    done.append(each)

        for each in triggerUpdate:
            if each not in done:
                each.InitializeSize()
                each.InitializeStatesAndPosition()

        settings.user.ui.Delete('targetOrigin')
        sm.GetService('target').ArrangeTargets()

    def RealignWindows(self):
        desktopLayout = getattr(self, 'PreDeviceChange_DesktopLayout', None)
        if desktopLayout:
            uicontrols.Window.LoadDesktopWindowLayout(desktopLayout)
        self.PreDeviceChange_DesktopLayout = None
        sm.GetService('target').ArrangeTargets()

    @telemetry.ZONE_METHOD
    def OpenWindows(self):
        if not (eve.rookieState and eve.rookieState < 10):
            wndsToCheck = [util.KeyVal(cls=form.MailWindow, cmd=uicore.cmd.OpenMail),
             util.KeyVal(cls=form.Wallet, cmd=uicore.cmd.OpenWallet),
             util.KeyVal(cls=form.Corporation, cmd=uicore.cmd.OpenCorporationPanel),
             util.KeyVal(cls=form.AssetsWindow, cmd=uicore.cmd.OpenAssets),
             util.KeyVal(cls=form.Channels, cmd=uicore.cmd.OpenChannels),
             util.KeyVal(cls=form.Journal, cmd=uicore.cmd.OpenJournal),
             util.KeyVal(cls=form.Logger, cmd=uicore.cmd.OpenLog),
             util.KeyVal(cls=form.CharacterSheet, cmd=uicore.cmd.OpenCharactersheet),
             util.KeyVal(cls=form.AddressBook, cmd=uicore.cmd.OpenPeopleAndPlaces),
             util.KeyVal(cls=form.RegionalMarket, cmd=uicore.cmd.OpenMarket),
             util.KeyVal(cls=form.Notepad, cmd=uicore.cmd.OpenNotepad)]
            if session.stationid2:
                sm.GetService('gameui').ScopeCheck(['station', 'station_inflight'])
                wndsToCheck += [util.KeyVal(cls=form.Inventory, cmd=uicore.cmd.OpenInventory, windowID=('InventoryStation', None)), util.KeyVal(cls=form.StationItems, cmd=uicore.cmd.OpenHangarFloor), util.KeyVal(cls=form.StationShips, cmd=uicore.cmd.OpenShipHangar)]
                if session.corpid:
                    wndsToCheck.append(util.KeyVal(cls=form.StationCorpDeliveries, cmd=uicore.cmd.OpenCorpDeliveries, windowID=form.Inventory.GetWindowIDFromInvID(('StationCorpDeliveries', session.stationid2))))
                    office = sm.GetService('corp').GetOffice()
                    if office:
                        wndsToCheck.append(util.KeyVal(cls=form.StationCorpHangars, cmd=uicore.cmd.OpenCorpHangar, windowID=form.Inventory.GetWindowIDFromInvID(('StationCorpHangars', office.itemID))))
                        for i in xrange(7):
                            invID = ('StationCorpHangar', office.itemID, i)
                            wndsToCheck.append(util.KeyVal(cls=form.Inventory, cmd=self._OpenCorpHangarDivision, windowID=form.Inventory.GetWindowIDFromInvID(invID), args=(invID,)))

            elif session.solarsystemid and session.shipid:
                sm.GetService('gameui').ScopeCheck(['inflight', 'station_inflight'])
                wndsToCheck += [util.KeyVal(cls=form.Inventory, cmd=uicore.cmd.OpenInventory, windowID=('InventorySpace', None)), util.KeyVal(cls=Scanner, cmd=uicore.cmd.OpenScanner), util.KeyVal(cls=DirectionalScanner, cmd=uicore.cmd.OpenDirectionalScanner)]
            else:
                sm.GetService('gameui').ScopeCheck()
            try:
                uicore.cmd.openingWndsAutomatically = True
                for checkWnd in wndsToCheck:
                    try:
                        cls = checkWnd.cls
                        cmd = checkWnd.cmd
                        windowID = getattr(checkWnd, 'windowID', cls.default_windowID)
                        args = getattr(checkWnd, 'args', ())
                        stackID = cls.GetRegisteredOrDefaultStackID()
                        wnd = uicontrols.Window.GetIfOpen(windowID)
                        if type(windowID) == tuple:
                            windowID = windowID[0]
                        isOpen = uicore.registry.GetRegisteredWindowState(windowID, 'open', False)
                        isMinimized = uicore.registry.GetRegisteredWindowState(windowID, 'minimized', False)
                        if isOpen and (stackID or not isMinimized) and not wnd:
                            cmd(*args)
                    except Exception as e:
                        self.LogException('Failed at opening window')

            finally:
                uicore.cmd.openingWndsAutomatically = False

        form.Lobby.CloseIfOpen()
        if session.stationid2:
            if not (eve.rookieState and eve.rookieState < 5):
                form.Lobby.Open()

    def _OpenCorpHangarDivision(self, invID):
        form.Inventory.OpenOrShow(invID=invID, usePrimary=False, toggle=False)

    def OnBlurredBufferCreated(self):
        self.UpdateIntersectionBackground()

    def GetWindowIntersectionRects(self):
        """
        Returns a list of rects that represents the intersection areas between all open windows
        """
        ret = set()
        wndRects = self.GetWindowRects()
        numWnds = len(wndRects)
        for i in xrange(numWnds):
            for j in xrange(i + 1, numWnds):
                wnd1 = wndRects[i]
                wnd2 = wndRects[j]
                if self.IsIntersecting(wnd1, wnd2):
                    ret.add(self.GetIntersection(wnd1, wnd2))

        return ret

    def UpdateIntersectionBackground(self):
        desktop = uicore.uilib.desktopBlurredBg
        if not desktop:
            return
        rects = self.GetWindowIntersectionRects()
        desktop.Flush()
        for x1, y1, x2, y2 in rects:
            cont = Container(parent=desktop, pos=(x1,
             y1,
             x2 - x1,
             y2 - y1), align=uiconst.TOPLEFT, padding=1)
            fill = FillUnderlay(bgParent=cont, opacity=0.5)

        desktop.UpdateAlignmentAsRoot()

    def IsIntersecting(self, wnd1, wnd2):
        l1, t1, r1, b1 = wnd1
        l2, t2, r2, b2 = wnd2
        hoverlaps = True
        voverlaps = True
        if l1 > r2 or r1 < l2:
            hoverlaps = False
        if t1 > b2 or b1 < t2:
            voverlaps = False
        return hoverlaps and voverlaps

    def GetIntersection(self, wnd1, wnd2):
        l1, t1, r1, b1 = wnd1
        l2, t2, r2, b2 = wnd2
        left = max(l1, l2)
        top = max(t1, t2)
        right = min(r1, r2)
        bottom = min(b1, b2)
        return (left,
         top,
         right,
         bottom)

    def GetWindowRects(self):
        windows = uicore.registry.GetValidWindows()
        ret = [ (wnd.displayX,
         wnd.displayY,
         wnd.displayX + wnd.displayWidth,
         wnd.displayY + wnd.displayHeight) for wnd in windows ]
        neocom = sm.GetService('neocom').neocom
        if neocom:
            l, t, w, h = neocom.GetAbsolute()
            ret.append((l,
             t,
             l + w,
             t + h))
        return ret

    def CloseContainer(self, invID):
        self.LogInfo('WindowSvc.CloseContainer request for id:', invID)
        checkIDs = (('loot', invID),
         ('lootCargoContainer', invID),
         'shipCargo_%s' % invID,
         'drones_%s' % invID,
         'containerWindow_%s' % invID)
        for windowID in checkIDs:
            wnd = uicontrols.Window.GetIfOpen(windowID=windowID)
            if wnd:
                wnd.Close()
                self.LogInfo('  WindowSvc.CloseContainer closing:', windowID)

    def GetCameraLeftOffset(self, width, align = None, left = 0, *args):
        try:
            offsetUI = gfxsettings.Get(gfxsettings.UI_OFFSET_UI_WITH_CAMERA)
        except gfxsettings.UninitializedSettingsGroupError:
            offsetUI = False

        if not offsetUI:
            return 0
        offset = int(gfxsettings.Get(gfxsettings.UI_CAMERA_OFFSET))
        if not offset:
            return 0
        if align in [uiconst.CENTER, uiconst.CENTERTOP, uiconst.CENTERBOTTOM]:
            camerapush = int(offset / 100.0 * uicore.desktop.width / 3.0)
            allowedOffset = int((uicore.desktop.width - width) / 2) - 10
            if camerapush < 0:
                return max(camerapush, -allowedOffset - left)
            if camerapush > 0:
                return min(camerapush, allowedOffset + left)
        return 0
