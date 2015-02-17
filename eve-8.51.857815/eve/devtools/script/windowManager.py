#Embedded file name: eve/devtools/script\windowManager.py
import uiprimitives
import uicontrols
import form
import carbonui.const as uiconst
import inspect

class WindowManager(uicontrols.Window):
    """ An Insider window which makes it easy to open up other EVE windows """
    __guid__ = 'form.WindowManager'
    default_windowID = 'WindowManager'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.SetWndIcon(None)
        self.SetCaption('Window manager')
        self.SetTopparentHeight(10)
        self.SetMinSize([360, 220])
        options = []
        windowList = list(form.__dict__)
        windowList.sort()
        for i, f in enumerate(windowList):
            cp = form.__getattribute__(f)
            if inspect.isclass(cp) and issubclass(cp, uicontrols.Window):
                options.append((f, i))

        topCont = uiprimitives.Container(name='params', parent=self.sr.main, align=uiconst.TOTOP, pad=(5, 5, 5, 5), pos=(0, 10, 0, 30))
        self.mainCont = uiprimitives.Container(name='params', parent=self.sr.main, align=uiconst.TOTOP, pos=(0, 0, 0, 50), padding=(5, 15, 5, 5))
        self.extrasCont = uiprimitives.Container(name='params', parent=self.sr.main, align=uiconst.TOALL, padding=(5, 15, 5, 5))
        self.combo = uicontrols.Combo(parent=topCont, label='Select window', options=options, name='', select=settings.user.ui.Get('windowManagerOpenWindow'), callback=self.OnComboChanged, pos=(5, 0, 0, 0), width=150, align=uiconst.TOPLEFT)
        self.startupArgs = uicontrols.SinglelineEdit(name='', label='attributes', parent=topCont, setvalue='', align=uiconst.TOPLEFT, left=165, width=100)
        uicontrols.Button(parent=topCont, label='Load', align=uiconst.RELATIVE, func=self.OpenWindow, pos=(300, 0, 0, 0))
        self.filenameEdit = uicontrols.SinglelineEdit(name='', label='Location', parent=self.mainCont, setvalue='', align=uiconst.TOTOP, top=15, readonly=True)
        uicontrols.Label(text='RELOAD', parent=self.extrasCont, top=10, state=uiconst.UI_NORMAL)
        uiprimitives.Line(parent=self.extrasCont, align=uiconst.TOTOP)
        buttonCont = uiprimitives.Container(name='buttonCont', parent=self.extrasCont, align=uiconst.TOTOP, pos=(0, 30, 0, 30))
        uicontrols.Button(parent=buttonCont, label='ShipUI', align=uiconst.TOLEFT, func=self.ReloadShipUI)
        uicontrols.Button(parent=buttonCont, label='NEOCOM', align=uiconst.TOLEFT, func=self.ReloadNeocom, padLeft=1)
        uicontrols.Button(parent=buttonCont, label='Info Panels', align=uiconst.TOLEFT, func=self.ReloadInfoPanels, padLeft=1)
        uicontrols.Button(parent=buttonCont, label='Lobby', align=uiconst.TOLEFT, func=self.ReloadLobby, padLeft=1)
        uicontrols.Button(parent=buttonCont, label='Overview', align=uiconst.TOLEFT, func=self.ReloadOverview, padLeft=1)
        uicontrols.Button(parent=buttonCont, label='Mapbrowser', align=uiconst.TOLEFT, func=self.ReloadMapBrowser, padLeft=1)
        self.UpdateInfo(self.combo.GetKey(), self.combo.GetValue())

    def OnComboChanged(self, combo, key, index):
        self.UpdateInfo(key, index)

    def UpdateInfo(self, key, index):
        window = form.__getattribute__(key)
        self.filenameEdit.SetValue(window.ApplyAttributes.func_code.co_filename)
        settings.user.ui.Set('windowManagerOpenWindow', index)

    def OpenWindow(self, *args):
        windowName = self.combo.GetKey()
        windowClass = form.__getattribute__(windowName)
        windowClass.CloseIfOpen()
        attributes = {}
        try:
            attributesStr = self.startupArgs.GetValue()
            if attributesStr:
                for s in attributesStr.split(','):
                    keyword, value = s.split('=')
                    keyword = keyword.strip()
                    value = value.strip()
                    try:
                        if value.find('.') != -1:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        pass

                    if value == 'None':
                        value = None
                    attributes[keyword] = value

        except:
            eve.Message('CustomInfo', {'info': 'attributes must be on the form: attr1=1, attr2=Some random text'})
            raise

        windowClass.Open(**attributes)

    def ReloadShipUI(self, *args):
        if eve.session.stationid is None:
            uicore.layer.shipui.CloseView()
            uicore.layer.shipui.OpenView()

    def ReloadNeocom(self, *args):
        sm.GetService('neocom').Reload()

    def ReloadInfoPanels(self, *args):
        sm.GetService('infoPanel').Reload()

    def ReloadLobby(self, *args):
        if session.stationid:
            form.Lobby.CloseIfOpen()
            form.Lobby.Open()

    def ReloadMapBrowser(self, *args):
        form.MapBrowserWnd.CloseIfOpen()
        uicore.cmd.OpenMapBrowser()

    def ReloadOverview(self, *args):
        form.OverView.CloseIfOpen()
        if session.solarsystemid:
            sm.GetService('tactical').InitOverview()
        form.ActiveItem.CloseIfOpen()
        if session.solarsystemid:
            sm.GetService('tactical').InitSelectedItem()
        form.DroneView.CloseIfOpen()
        if session.solarsystemid:
            sm.GetService('tactical').InitDrones()
