#Embedded file name: eve/client/script/ui/login\loginII.py
import zlib
import uicontrols
import blue
import uiprimitives
import uthread
import uix
import carbonui.const as uiconst
import mathUtil
import sys
import types
import corebrowserutil
import log
import trinity
import audio2
import uicls
import nodemanager
import locks
import bluepy
import pytelemetry.zoning as telemetry
import const
import localization
import memorySnapshot
import utillib
import carbon.common.script.util.format as fmtutil
import evegraphics.utils as gfxutils
from eveexceptions import UserError
from serverInfo import *
from eve.client.script.util.webutils import WebUtils

def GetVersion():
    buildno = 'Undefined'
    try:
        buildno = '%s.%s' % (boot.keyval['version'].split('=', 1)[1], boot.build)
    except:
        log.LogException()

    return buildno


try:
    if not GetServerInfo().isLive:
        if prefs.GetValue('nominidump', 0):
            log.general.Log('Running against a test server. Crash minidump is NOT active because of nominidump=1 in prefs.ini', log.LGNOTICE)
        else:
            log.general.Log('Running against a test server. Crash minidump is active. You can disable this with nominidump=1 in prefs.ini', log.LGNOTICE)
            blue.os.miniDump = True
except:
    log.LogException()

class Login(uicls.LayerCore):
    __guid__ = 'form.LoginII'
    __notifyevents__ = ['OnEndChangeDevice', 'OnGraphicSettingsChanged', 'ProcessUIRefresh']
    isTopLevelWindow = True

    def OnCloseView(self):
        systemmenu = uicore.layer.systemmenu
        if systemmenu.isopen:
            uthread.new(systemmenu.CloseMenu)
        self.Reset()
        sm.GetService('sceneManager').SetActiveScene(None)
        sm.UnregisterNotify(self)
        del self.scene.curveSets[:]
        self.scene = None
        self.ship = None
        self.Flush()

    def ProcessUIRefresh(self):
        if self.isopen:
            if self.reloading:
                self.pendingReload = 1
                return
            currentUsername = self.usernameEditCtrl.GetValue()
            currentPassword = self.passwordEditCtrl.GetValue()
            self.reloading = 1
            self.Layout(False, None, currentUsername, currentPassword)
            self.reloading = 0
            if self.pendingReload:
                self.pendingReload = 0

    def OnEndChangeDevice(self, *args):
        if self.isopen:
            if self.reloading:
                self.pendingReload = 1
                return
            currentUsername = self.usernameEditCtrl.GetValue()
            currentPassword = self.passwordEditCtrl.GetValue()
            self.reloading = 1
            activePanelArgs = self.pushButtons.GetSelected()
            self.Layout(1, activePanelArgs, currentUsername, currentPassword)
            self.reloading = 0
            if self.pendingReload:
                self.pendingReload = 0
                self.OnEndChangeDevice()

    @telemetry.ZONE_METHOD
    def Reset(self):
        self.serverStatus = {}
        self.serverStatusTextControl = None
        self.serverStatusTextFunc = None
        self.serverNameTextControl = None
        self.serverPlayerCountTextControl = None
        self.serverVersionTextControl = None
        self.eulaParent = None
        self.eulaCRC = None
        self.eulaBrowser = None
        self.eulaBlock = None
        self.eulaclosex = None
        self.mainBrowserParent = None
        self.mainBrowser = None
        self.usernameEditCtrl = None
        self.passwordEditCtrl = None
        self.motdParent = None
        self.motdLabel = None
        self.connecting = False
        self.pushButtons = None
        self.waitingForEula = 0
        self.acceptbtns = None
        self.scrollText = None
        self.reloading = 0
        self.pendingReload = 0
        self.maintabs = None
        self.isShowingUpdateDialog = False

    @telemetry.ZONE_METHOD
    def OnOpenView(self):
        memorySnapshot.AutoMemorySnapshotIfEnabled('Login_OnOpenView')
        self.Reset()
        uthread.worker('login::StatusTextWorker', self.__StatusTextWorker)
        blue.resMan.Wait()
        self.serverName = utillib.GetServerName()
        self.serverIP = GetServerIP(self.serverName)
        self.serverName = GetServerName(self.serverIP)
        self.serverPort = utillib.GetServerPort()
        self.firstCheck = True
        self.isShowingUpdateDialog = False
        self.Layout()
        sm.ScatterEvent('OnClientReady', 'login')
        self.isopen = 1
        uthread.new(self.UpdateServerStatus)
        sm.ScatterEvent('OnClientStageChanged', 'login')

    def GetEulaConfirmation(self):
        self.waitingForEula = 1
        self.eulaclosex.state = uiconst.UI_HIDDEN
        self.eulaBlock = uiprimitives.Fill(parent=self.eulaParent.parent, idx=self.eulaParent.parent.children.index(self.eulaParent) + 1, state=uiconst.UI_NORMAL, color=(0.0, 0.0, 0.0, 0.75))
        par = uiprimitives.Container(name='btnpar', parent=self.eulaBrowser, align=uiconst.TOBOTTOM, height=40, idx=0)
        self.scrollText = uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Login/ScrollToBottom'), parent=par, align=uiconst.CENTER, idx=0, state=uiconst.UI_NORMAL)
        btns = uicontrols.ButtonGroup(btns=[[localization.GetByLabel('UI/Login/Accept'),
          self.AcceptEula,
          2,
          81,
          uiconst.ID_OK,
          0,
          0], [localization.GetByLabel('UI/Login/Decline'),
          self.ClickExit,
          (),
          81,
          uiconst.ID_CANCEL,
          0,
          1]], line=0)
        btns.state = uiconst.UI_HIDDEN
        par.children.insert(0, btns)
        self.acceptbtns = btns
        self.pushButtons.SelectByID('eula')
        self.eulaBrowser.OnUpdatePosition = self.ScrollingEula
        self.waitingForEula = 1

    def ClickExit(self, *args):
        uicore.cmd.CmdQuitGame()

    def AcceptEula(self, *args):
        self.eulaBlock.Close()
        self.eulaclosex.state = uiconst.UI_NORMAL
        self.acceptbtns.parent.Close()
        self.waitingForEula = 0
        self.OnButtonDeselected('eula')
        self.acceptbtns = None
        self.scrollText = None
        self.eulaBlock = None
        settings.public.generic.Set('eulaCRC', self.eulaCRC)
        uthread.new(self.LoadMotd)

    def ScrollingEula(self, scroll, *args):
        if self.eulaBrowser.viewing == 'eula_ccp':
            proportion = scroll.GetScrollProportion()
            if proportion >= 1.0 and self.acceptbtns:
                self.acceptbtns.state = uiconst.UI_NORMAL
                if self.scrollText:
                    self.scrollText.state = uiconst.UI_HIDDEN

    def FadeSplash(self, sprite):
        blue.pyos.synchro.SleepWallclock(500)
        sm.GetService('ui').Fade(1.0, 0.0, sprite)
        sprite.Close()

    @telemetry.ZONE_METHOD
    def Layout(self, reloading = 0, pushBtnArgs = None, setUsername = None, setPassword = None):
        if not reloading:
            self.sceneLoadedEvent = locks.Event('loginScene')
            uthread.new(self.LoadScene)
        self.eulaInited = 0
        self.Flush()
        borderHeight = uicore.desktop.height / 6
        par = uiprimitives.Container(name='underlayContainer', parent=self, align=uiconst.TOTOP, height=borderHeight)
        self.sr.underlay2 = uicontrols.WindowUnderlay(parent=par)
        self.sr.underlay2.padding = (-16, -16, -16, 0)
        bottomPar = uiprimitives.Container(name='underlayContainer_Bottom', parent=self, align=uiconst.TOBOTTOM, height=borderHeight + 6)
        bottomUnderlay = uicontrols.WindowUnderlay(parent=bottomPar)
        bottomUnderlay.padding = (-16, 6, -16, -16)
        if trinity.app.fullscreen:
            closex = uicontrols.Icon(icon='ui_73_16_49', parent=self, pos=(0, 1, 0, 0), align=uiconst.TOPRIGHT, idx=0, state=uiconst.UI_NORMAL, hint=localization.GetByLabel('UI/Login/QuitGame'))
            closex.OnClick = self.ClickExit
            closex.sr.hintAbRight = uicore.desktop.width - 16
            closex.sr.hintAbTop = 16
        self.mainBrowserParent = uiprimitives.Container(name='mainBrowserParent', parent=self, align=uiconst.CENTER, state=uiconst.UI_HIDDEN, width=800, height=440, idx=0)
        self.mainBrowser = uicontrols.Edit(parent=self.mainBrowserParent, padding=(8, 18, 8, 8), readonly=1)
        mainclosex = uicontrols.Icon(icon='ui_38_16_220', parent=self.mainBrowserParent, pos=(2, 1, 0, 0), align=uiconst.TOPRIGHT, idx=0, state=uiconst.UI_NORMAL)
        mainclosex.OnClick = self.CloseMenu
        wndUnderlay = uicontrols.WindowUnderlay(parent=self.mainBrowserParent)
        self.eulaParent = uiprimitives.Container(name='eulaParent', parent=self, align=uiconst.CENTER, state=uiconst.UI_HIDDEN, width=800, height=440, idx=0)
        eulaCont = uiprimitives.Container(name='eulaCont', parent=self.eulaParent, align=uiconst.TOALL, padding=(0, 18, 0, 0))
        browser = uicontrols.Edit(parent=eulaCont, padding=(6, 6, 6, 6), readonly=1)
        browser.sr.scrollcontrols.state = uiconst.UI_NORMAL
        browser.viewing = 'eula_ccp'
        self.eulaBrowser = browser
        self.sr.eulaUnderlay = uicontrols.WindowUnderlay(parent=self.eulaParent)
        self.maintabs = uicontrols.TabGroup(name='maintabs', parent=eulaCont, idx=0, tabs=[[localization.GetByLabel('UI/Login/EULA/EveEULAHeader'),
          browser,
          self,
          'eula_ccp'], [localization.GetByLabel('UI/Login/EULA/ThirdPartyEULAHeader'),
          browser,
          self,
          'eula_others']], groupID='eula', autoselecttab=0)
        self.eulaclosex = uicontrols.Icon(icon='ui_38_16_220', parent=self.eulaParent, pos=(2, 1, 0, 0), align=uiconst.TOPRIGHT, idx=0, state=uiconst.UI_NORMAL)
        self.eulaclosex.OnClick = self.CloseMenu
        bottomArea = uiprimitives.Container(name='bottomArea', parent=bottomPar, idx=0, pos=(0, 0, 0, 0))
        bottomSub = uiprimitives.Container(name='bottomSub', parent=bottomArea, align=uiconst.CENTER, idx=0, height=bottomPar.height, width=800)
        knownUserNames = settings.public.ui.Get('usernames', [])
        editswidth = 120
        if borderHeight <= 100:
            editstop = 30
        else:
            editstop = 40
        editsleft = (bottomSub.width - editswidth) / 2
        edit = uicontrols.SinglelineEdit(name='username', parent=bottomSub, pos=(editsleft,
         editstop,
         editswidth,
         0), maxLength=64)
        edit.SetHistoryVisibility(0)
        t1 = uicontrols.EveLabelSmall(text=localization.GetByLabel('UI/Login/Username'), parent=edit, top=3, state=uiconst.UI_DISABLED, color=(1.0, 1.0, 1.0, 0.75))
        if knownUserNames:
            ops = [ (name, name) for name in knownUserNames ]
            edit.LoadCombo('usernamecombo', ops, self.OnComboChange, comboIsTabStop=0)
        edit.SetValue(setUsername or settings.public.ui.Get('username', ''))
        edit.OnReturn = self.Confirm
        self.usernameEditCtrl = edit
        edit = uicontrols.SinglelineEdit(name='password', parent=bottomSub, pos=(editsleft,
         edit.top + edit.height + 6,
         editswidth,
         0), maxLength=64)
        t2 = uicontrols.EveLabelSmall(text=localization.GetByLabel('UI/Login/Password'), parent=edit, top=3, state=uiconst.UI_DISABLED, color=(1.0, 1.0, 1.0, 0.75))
        edit.SetPasswordChar(u'\u2022')
        edit.SetValue(setPassword or '')
        edit.OnReturn = self.Confirm
        self.passwordEditCtrl = edit
        if sm.GetService('gameui').UsingSingleSignOn():
            self.usernameEditCtrl.state = self.passwordEditCtrl.state = uiconst.UI_HIDDEN
            editswidth = 0
        tw = max(t1.textwidth, t2.textwidth)
        t1.left = t2.left = -tw - 6
        connectBtn = uicontrols.Button(parent=bottomSub, label=localization.GetByLabel('UI/Login/Connect'), func=self.Connect, pos=(editsleft,
         edit.top + edit.height + 4,
         0,
         0), fixedwidth=120, btn_default=1)
        statusContainer = uiprimitives.Container(parent=bottomSub, left=editsleft + editswidth + 6, top=editstop)
        self.serverNameTextControl = uicontrols.EveLabelSmall(text=localization.GetByLabel('UI/Login/CheckingStatus'), parent=statusContainer, align=uiconst.TOTOP, state=uiconst.UI_DISABLED)
        self.serverStatusTextControl = uicontrols.EveLabelSmall(parent=statusContainer, align=uiconst.TOTOP, state=uiconst.UI_DISABLED)
        self.serverPlayerCountTextControl = uicontrols.EveLabelSmall(parent=statusContainer, align=uiconst.TOTOP, state=uiconst.UI_DISABLED)
        self.serverVersionTextControl = uicontrols.EveLabelSmall(parent=statusContainer, align=uiconst.TOTOP, state=uiconst.UI_DISABLED)
        self.motdParent = uiprimitives.Container(name='motdParent', parent=self, align=uiconst.CENTERBOTTOM, top=borderHeight + 16, width=400, height=64, state=uiconst.UI_HIDDEN)
        motdLabel = uicontrols.EveLabelMedium(parent=self.motdParent, align=uiconst.CENTER, width=360, state=uiconst.UI_NORMAL)
        self.motdLabel = motdLabel
        uicontrols.BumpedUnderlay(parent=self.motdParent, name='background')
        versionstr = localization.GetByLabel('UI/Login/Version', versionNumber=GetVersion())
        uicontrols.EveLabelSmall(text=versionstr, parent=self, left=6, top=6, idx=0, state=uiconst.UI_NORMAL)
        self.pushButtons = uicls.ToggleButtonGroup(parent=bottomPar, align=uiconst.CENTERTOP, idx=0, top=12, width=120, callback=self.OnButtonSelected)
        for btnID, label, panel in (('settings', localization.GetByLabel('UI/Login/Settings'), None), ('eula', localization.GetByLabel('UI/Login/EULA/EULAHeader'), self.eulaParent)):
            self.pushButtons.AddButton(btnID, label, panel)

        if boot.region == 'optic':
            self.eulaCRC = zlib.adler32(str(boot.version))
        else:
            self.eulaCRC = zlib.adler32(buffer(self.GetEulaCCP()))
        eulaAgreed = True
        if not eulaAgreed:
            self.GetEulaConfirmation()
        else:
            if pushBtnArgs:
                self.pushButtons.SelectByID(pushBtnArgs)
            uthread.new(self.LoadMotd, bool(pushBtnArgs))
            if trinity.app.IsActive():
                if settings.public.ui.Get('username', ''):
                    uicore.registry.SetFocus(self.passwordEditCtrl)
                else:
                    uicore.registry.SetFocus(self.usernameEditCtrl)
        if boot.region != 'optic':
            esrbNoticeHeight = 70
            esrbNoticeWidth = 200
            allowedSizes = [1.0, 0.9, 0.8]
            desktopWidth = uicore.desktop.width
            useHeight = int(esrbNoticeHeight * 0.7)
            useWidth = int(esrbNoticeWidth * 0.7)
            for multiplier in allowedSizes:
                tempWidth = esrbNoticeWidth * multiplier
                if tempWidth <= desktopWidth * 0.11:
                    useWidth = int(tempWidth)
                    useHeight = int(esrbNoticeHeight * multiplier)
                    break

            cont = uiprimitives.Container(name='esrbParent', parent=bottomArea, align=uiconst.TOPLEFT, top=editstop, width=useWidth, height=useHeight, state=uiconst.UI_NORMAL, idx=0, left=20)
            sprite = uiprimitives.Sprite(name='ESRB', parent=cont, align=uiconst.TOALL, state=uiconst.UI_DISABLED, color=(1.0, 1.0, 1.0, 1.0), lockAspect=1, texturePath='res:/UI/Texture/ESRBnotice.dds')
            sprite.rectWidth = esrbNoticeWidth
            sprite.rectHeight = esrbNoticeHeight
            uthread.new(uix.FadeCont, cont, 0, after=6000, fadeTime=500.0)

    def Load(self, key, *args):
        self.eulaBrowser.viewing = key
        text = ''
        if key == 'eula_others':
            eula = self.GetEulaOthers()
            text = localization.GetByLabel('UI/Login/ScrollToEveBottom')
        else:
            eula = self.GetEulaCCP()
            text = localization.GetByLabel('UI/Login/ScrollToBottom')
        if self.scrollText is not None:
            self.scrollText.text = text
        self.eulaBrowser.LoadHTML(eula)

    def OnGraphicSettingsChanged(self, changes):
        if self.isopen and 'shaderQuality' in changes and getattr(self, 'scene', None):
            self.CheckHeightMaps()

    @telemetry.ZONE_METHOD
    def CheckHeightMaps(self):
        if 'LO' in trinity.GetShaderModel():
            heightMapParams = nodemanager.FindNodes(self.scene, 'HeightMap', 'trinity.TriTexture2DParameter')
            for param in heightMapParams:
                param.resourcePath = param.resourcePath.replace('_hi.dds', '_lo.dds')

        else:
            heightMapParams = nodemanager.FindNodes(self.scene, 'HeightMap', 'trinity.TriTexture2DParameter')
            for param in heightMapParams:
                param.resourcePath = param.resourcePath.replace('_lo.dds', '_hi.dds')

    @telemetry.ZONE_METHOD
    def LoadScene(self):
        self.camera = trinity.Load('res:/dx9/scene/login_screen_camera.red')
        self.scene = trinity.Load('res:/dx9/scene/login_screen.red')
        if gfxutils.BlockStarfieldOnLionOSX():
            self.scene.starfield = None
        blue.resMan.Wait()
        self.CheckHeightMaps()
        stations = self.scene.Find('trinity.EveStation2')
        for station in stations:
            station.PlayAnimationEx('NormalLoop', 0, 0, 0.2)

        self.camera.audio2Listener = audio2.GetListener(0)
        sm.GetService('sceneManager').SetActiveCamera(self.camera)
        sm.GetService('sceneManager').SetActiveScene(self.scene)
        sm.GetService('dynamicMusic').UpdateDynamicMusic()
        self.sceneLoadedEvent.set()
        blue.pyos.synchro.Yield()

    def OnEsc(self):
        if not self.waitingForEula and self.pushButtons is not None:
            btnID = self.pushButtons.GetSelected()
            if btnID:
                self.OnButtonDeselected(btnID)
            else:
                self.pushButtons.SelectByID('settings')

    def OnButtonDeselected(self, btnID = None):
        self.pushButtons.DeselectAll()
        if btnID == 'settings' and not self.reloading:
            sys = uicore.layer.systemmenu
            if sys.isopen:
                uthread.new(sys.CloseMenu)

    def CloseMenu(self, *args):
        uicore.cmd.OnEsc()

    @telemetry.ZONE_METHOD
    def OnButtonSelected(self, btnID):
        self.loadingPushButton = btnID
        self.motdParent.state = uiconst.UI_HIDDEN
        self.suppressMotd = True
        if btnID == 'settings':
            sys = uicore.layer.systemmenu
            if not sys.isopen:
                uthread.new(sys.OpenView)
        else:
            sys = uicore.layer.systemmenu
            if sys.isopen:
                uthread.new(sys.CloseMenu)
        if btnID == 'eula':
            self.LoadEula()
        self.loadingPushButton = 0

    def OnComboChange(self, combo, header, value, *args):
        self.usernameEditCtrl.SetValue(value)
        self.passwordEditCtrl.SetValue('')
        uicore.registry.SetFocus(self.passwordEditCtrl)

    def GetEulaCCP(self, *args):
        return localization.GetByLabel('EULA/EveEULA', tabName=localization.GetByLabel('UI/Login/EULA/ThirdPartyEULAHeader'))

    def GetEulaOthers(self, *args):
        tgEula = ''
        if blue.win32.IsTransgaming():
            tgEula = localization.GetByLabel('EULA/TransGaming')
        else:
            tgEula = localization.GetByLabel('EULA/DirectX')
        return tgEula + '<p><p>' + localization.GetByLabel('EULA/Chrome') + '<p><p>' + localization.GetByLabel('EULA/Xiph')

    @telemetry.ZONE_METHOD
    def LoadMotd(self, hidden = False):
        ip = self.serverIP
        try:
            extraParam = WebUtils.GetWebRequestParameters()
            if self.IsChina():
                url = WEB_EVE + '/motd.html?server=%s&%s'
                encoding = 'gbk'
            else:
                url = WEB_EVE + '/motd/%s?%s'
                encoding = 'utf-8'
            ret = corebrowserutil.GetStringFromURL(url % (ip, extraParam)).read()
        except Exception as e:
            log.LogError('Failed to fetch motd', e)
            sys.exc_clear()
            ret = ''

        if self.motdParent and not self.motdParent.destroyed:
            if ret and ret.startswith('MOTD '):
                ret = ret[5:]
                self.motdText = ret.decode(encoding, 'replace')
                if hidden:
                    self.motdParent.state = uiconst.UI_HIDDEN
                else:
                    self.motdParent.state = uiconst.UI_NORMAL
                self.motdLabel.text = self.motdText
                self.motdParent.height = max(32, self.motdLabel.textheight + 10)
            else:
                self.motdParent.state = uiconst.UI_HIDDEN

    def LoadEula(self, *args):
        if getattr(self, 'eulaInited', 0):
            uicore.registry.SetFocus(self.eulaBrowser)
            return
        self.maintabs.SelectByIdx(0)
        uicore.registry.SetFocus(self.eulaBrowser)
        self.eulaInited = 1

    @telemetry.ZONE_METHOD
    def __StatusTextWorker(self):
        while not eve.session.userid:
            blue.pyos.synchro.SleepWallclock(750)
            try:
                if getattr(self, 'serverStatusTextFunc', None) is not None:
                    if not getattr(self, 'connecting', 0):
                        self.__SetServerStatusText(refreshOnNone=True)
            except:
                log.LogException('Exception in status text worker')
                sys.exc_clear()

    @telemetry.ZONE_METHOD
    def __SetServerStatusText(self, refreshOnNone = False):
        if self.serverStatusTextFunc is None:
            self.ClearServerStatus()
            return
        statusText = apply(self.serverStatusTextFunc[0])
        if statusText is None:
            self.ClearServerStatus()
            if refreshOnNone:
                uthread.new(self.UpdateServerStatus, False)
            return
        serverversion, serverbuild, serverUserCount = self.serverStatusTextFunc[1:]
        self.SetNameText(localization.GetByLabel('UI/Login/ServerStatus/Server', serverName=self.serverName))
        label, parameters = statusText
        self.SetStatusText(localization.GetByLabel('UI/Login/ServerStatus/Status', statusText=localization.GetByLabel(label, **parameters)))
        if serverUserCount is not None:
            self.SetPlayerCountText(localization.GetByLabel('UI/Login/ServerStatus/PlayerCount', players=int(serverUserCount)))
        eve.serverVersion = serverversion
        eve.serverBuild = serverbuild
        if serverversion and serverbuild:
            if '%.2f' % serverversion != '%.2f' % boot.version or serverbuild > boot.build:
                self.SetVersionText(localization.GetByLabel('UI/Login/ServerStatus/VersionIncompatible', serverVersion=serverversion, serverBuild=serverbuild))

    def IsChina(self):
        return boot.region == 'optic'

    def GetIsAutoPatch(self, allowPatch):
        isAutoPatch = False
        if self.IsChina():
            isAutoPatch = self.serverIP == LIVE_SERVER1 or self.serverIP == LIVE_SERVER2 or self.serverIP in [TEST_SERVER1, TEST_SERVER2, TEST_SERVER3] or prefs.GetValue('forceAutopatch', 0) == 1
        else:
            isAutoPatch = self.serverIP == LIVE_SERVER or self.serverIP in [TEST_SERVER1, TEST_SERVER2, TEST_SERVER3] or prefs.GetValue('forceAutopatch', 0) == 1
        if not allowPatch:
            isAutoPatch = False
        return isAutoPatch

    def IsServerPortValid(self):
        try:
            int(self.serverPort)
        except Exception as e:
            log.LogError(e)
            sys.exc_clear()
            self.SetStatusText(localization.GetByLabel('UI/Login/InvalidPortNumber', port=self.serverPort))
            self.serverStatusTextFunc = None
            return False

        return True

    def UpdateServerStatus(self, allowPatch = True):
        self.InternalUpdateServerStatus(allowPatch=allowPatch, bootbuild=boot.build, bootversion=boot.version)

    def DisplayOutOfDateMessageAndQuitGame(self, reason = None):
        self.isShowingUpdateDialog = True
        uicore.Message('LoginUpdateAvailable', {'info': 'Client is out of date'})
        uicore.cmd.DoQuitGame()

    def CompareVersionsAndAct(self, bootbuild, bootversion, isAutoPatch, serverbuild, serverversion, statusMessage):
        if statusMessage is not None and 'Incompatible' in statusMessage[0] or '%.2f' % serverversion != '%.2f' % bootversion or serverbuild > bootbuild:
            if serverbuild > bootbuild and isAutoPatch:
                self.DisplayOutOfDateMessageAndQuitGame('OutOfDate')

    def GetActualStatusMessage(self, serverUserCount, serverbuild, serverversion, statusMessage):
        self.serverStatusTextFunc = None
        if type(statusMessage) in (types.LambdaType, types.FunctionType, types.MethodType):
            self.serverStatusTextFunc = (statusMessage,
             serverversion,
             serverbuild,
             serverUserCount)
        else:
            self.serverStatusTextFunc = (lambda : statusMessage,
             serverversion,
             serverbuild,
             serverUserCount)
        self.__SetServerStatusText()
        resolvedStatusMessage = apply(self.serverStatusTextFunc[0])
        messagePart = resolvedStatusMessage[0]
        return messagePart

    @telemetry.ZONE_METHOD
    def InternalUpdateServerStatus(self, allowPatch, bootbuild, bootversion):
        self.SetStatusText(localization.GetByLabel('UI/Login/CheckingStatus'))
        self.serverStatusTextFunc = None
        blue.pyos.synchro.Yield()
        if self.isShowingUpdateDialog:
            return
        if not self.IsServerPortValid():
            return
        serverUserCount = serverversion = serverbuild = servercodename = None
        isAutoPatch = self.GetIsAutoPatch(allowPatch)
        try:
            log.LogInfo('checking status of %s' % self.serverIP)
            try:
                if self.firstCheck:
                    forceQueueCheck = True
                    self.firstCheck = False
                else:
                    forceQueueCheck = False
                statusMessage, serverStatus = sm.GetService('machoNet').GetServerStatus('%s:%s' % (self.serverIP, self.serverPort), forceQueueCheck=forceQueueCheck)
            except UserError as e:
                if e.msg == 'AlreadyConnecting':
                    sys.exc_clear()
                    return
                raise

            if not self.isopen:
                return
            self.serverStatus[self.serverIP] = (serverStatus.get('cluster_usercount', None),
             serverStatus.get('boot_version', None),
             serverStatus.get('boot_build', None),
             str(serverStatus.get('boot_codename', const.responseUnknown)),
             serverStatus.get('update_info', const.responseUnknown))
            serverUserCount, serverversion, serverbuild, servercodename, updateinfo = self.serverStatus[self.serverIP]
            if serverUserCount:
                uthread.new(self.StartXFire, str(fmtutil.FmtAmt(serverUserCount)))
            actualStatusMsg = self.GetActualStatusMessage(serverUserCount, serverbuild, serverversion, statusMessage)
            if serverversion and serverbuild:
                self.CompareVersionsAndAct(bootbuild, bootversion, isAutoPatch, serverbuild, serverversion, actualStatusMsg)
            elif actualStatusMsg is not None and 'IncompatibleProtocol' in actualStatusMsg:
                self.DisplayOutOfDateMessageAndQuitGame('Incompatable protocol')
            else:
                raise Exception('Invalid answer from server GetServerStatus')
        except Exception as e:
            log.LogError(e)
            sys.exc_clear()
            self.SetStatusText(localization.GetByLabel('UI/Login/UnableToConnect', IP=self.serverIP, port=self.serverPort))
            self.serverStatusTextFunc = None

    def StartXFire(self, serverUserCount):
        blue.pyos.synchro.SleepWallclock(5000)
        sm.StartService('xfire').AddKeyValue('Users', serverUserCount)

    def SetNameText(self, text):
        if self.serverNameTextControl and not self.serverNameTextControl.destroyed:
            self.serverNameTextControl.text = text

    def SetStatusText(self, text):
        if self.serverStatusTextControl and not self.serverStatusTextControl.destroyed:
            self.serverStatusTextControl.text = text

    def SetPlayerCountText(self, text):
        if self.serverPlayerCountTextControl and not self.serverPlayerCountTextControl.destroyed:
            self.serverPlayerCountTextControl.text = text

    def SetVersionText(self, text):
        if self.serverVersionTextControl and not self.serverVersionTextControl.destroyed:
            self.serverVersionTextControl.text = text

    def ClearServerStatus(self, *args):
        self.SetStatusText('')
        self.serverStatusTextFunc = None
        return True

    def Confirm(self):
        memorySnapshot.AutoMemorySnapshotIfEnabled('Login_Confirm')
        self.Connect()

    def Connect(self, *args):
        if not self.waitingForEula:
            uthread.new(self._Connect)

    @telemetry.ZONE_METHOD
    def _Connect(self):
        if self.connecting:
            return
        self.connecting = True
        giveFocus = None
        try:
            if sm.GetService('gameui').UsingSingleSignOn():
                for arg in blue.pyos.GetArg()[1:]:
                    if arg.startswith('/ssoToken'):
                        try:
                            argName, token = arg.split('=')
                        except:
                            raise RuntimeError('Invalid format of SSO token, should be /ssoToken=<token>')

                sm.GetService('gameui').DoLogin(token)
                return
            user = self.usernameEditCtrl.GetValue()
            password = fmtutil.PasswordString(self.passwordEditCtrl.GetValue(raw=1))
            giveFocus = None
            if user is None or len(user) == 0:
                giveFocus = 'username'
            if password is None or len(password) == 0:
                giveFocus = 'password' if giveFocus is None else giveFocus
            if giveFocus is not None:
                eve.Message('LoginAuthFailed')
                self.CancelLogin()
                self.SetFocus(giveFocus)
                return
            log.LogInfo('server: %s selected' % self.serverIP)
            blue.pyos.synchro.Yield()
            if self.serverPort == sm.StartService('machoNet').defaultProxyPortOffset:
                if self.serverIP not in self.serverStatus:
                    self.UpdateServerStatus()
                try:
                    serverUserCount, serverversion, serverbuild, servercodename, updateinfo = self.serverStatus[self.serverIP]
                    if serverbuild > boot.build:
                        if self.serverIP == LIVE_SERVER:
                            if eve.Message('PatchLiveServerConnectWrongVersion', {'serverVersion': serverbuild,
                             'clientVersion': boot.build}, uiconst.YESNO) == uiconst.ID_YES:
                                self.UpdateServerStatus()
                        else:
                            eve.Message('PatchTestServerWarning', {'serverVersion': serverbuild,
                             'clientVersion': boot.build})
                        self.CancelLogin()
                        return
                except:
                    log.LogInfo('No serverStatus found for server %s' % self.serverIP)
                    sys.exc_clear()
                    eve.Message('UnableToConnectToServer')
                    self.CancelLogin()
                    return

            sm.GetService('loading').ProgressWnd(localization.GetByLabel('UI/Login/LoggingIn'), localization.GetByLabel('UI/Login/ConnectingToCluster'), 1, 100)
            blue.pyos.synchro.Yield()
            eve.Message('OnConnecting')
            blue.pyos.synchro.Yield()
            eve.Message('OnConnecting2')
            blue.pyos.synchro.Yield()
            try:
                sm.GetService('connection').Login([user,
                 password,
                 self.serverIP,
                 self.serverPort,
                 0])
            except:
                self.CancelLogin()
                raise

            settings.public.ui.Set('username', user or '-')
            prefs.newbie = 0
            knownUserNames = settings.public.ui.Get('usernames', [])[:]
            if user and user not in knownUserNames:
                knownUserNames.append(user)
                settings.public.ui.Set('usernames', knownUserNames)
        except UserError as e:
            if e.msg.startswith('LoginAuthFailed'):
                giveFocus = 'password'
            eve.Message(e.msg, e.dict)
            self.CancelLogin()
            self.SetFocus(giveFocus)
        finally:
            if not self.destroyed:
                self.connecting = 0

    def CancelLogin(self):
        sm.GetService('loading').CleanUp()

    def SetFocus(self, where = None):
        if where is None:
            return
        if where == 'username':
            uicore.registry.SetFocus(self.usernameEditCtrl)
        elif where == 'password':
            self.passwordEditCtrl.SetValue('')
            uicore.registry.SetFocus(self.passwordEditCtrl)


servers = SERVERS
exports = {'login.servers': servers,
 'login.GetServerIP': GetServerIP,
 'login.GetServerName': GetServerName,
 'login.GetServerInfo': GetServerInfo}
