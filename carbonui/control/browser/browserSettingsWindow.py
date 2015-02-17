#Embedded file name: carbonui/control/browser\browserSettingsWindow.py
"""
This file contains the browser's General Settings UI. This is where all
browser-wide settings should be stored.
"""
import carbonui.const as uiconst
import blue
import browserutil
import corebrowserutil
import localization
from carbonui.control.window import WindowCoreOverride as Window
from carbonui.control.label import LabelOverride as Label
from carbonui.control.singlelineedit import SinglelineEditCoreOverride as SinglelineEdit
from carbonui.control.buttons import ButtonCoreOverride as Button
from carbonui.control.checkbox import CheckboxCoreOverride as Checkbox
from carbonui.primitives.container import Container
from carbonui.primitives.line import Line

class BrowserSettingsWindowCore(Window):
    __guid__ = 'uicls.BrowserSettingsWindowCore'
    default_windowID = 'BrowserSettingsWindow'

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.showNavigationBar = settings.user.ui.Get('browserShowNavBar', True)
        self.showStatusBar = settings.user.ui.Get('browserShowStatusBar', True)
        self.SetCaption(localization.GetByLabel('UI/Browser/BrowserSettings/BrowserSettingsCaption'))
        self.SetButtons(uiconst.OKCLOSE, okLabel=localization.GetByLabel('UI/Browser/BrowserSettings/SaveChanges'), okFunc=self.Save, okModalResult=uiconst.ID_NONE)
        main = self.GetMainArea()
        main.clipChildren = 0
        main.padding = 6
        c = Container(name='homeCont', parent=main, align=uiconst.TOTOP, height=32)
        l = Container(name='left', parent=c, align=uiconst.TOLEFT, width=100, state=uiconst.UI_PICKCHILDREN)
        r = Container(name='right', parent=c, align=uiconst.TORIGHT, width=80, state=uiconst.UI_PICKCHILDREN)
        text = Label(text=localization.GetByLabel('UI/Browser/BrowserSettings/Homepage'), align=uiconst.TOALL, state=uiconst.UI_DISABLED, parent=l, left=0, top=4, width=2)
        top = (text.textheight - 16) / 2 + 2 if text.textheight > 16 else 0
        totalTop = top
        btn = Button(parent=r, label=localization.GetByLabel('UI/Browser/BrowserSettings/ResetHomepage'), func=self.ResetHomePage, pos=(0,
         top,
         0,
         0), align=uiconst.TOPRIGHT)
        if btn.width > 80:
            r.width = btn.width
        self.homeEdit = SinglelineEdit(name='homeEdit', setvalue=settings.user.ui.Get('HomePage2', browserutil.DefaultHomepage()), align=uiconst.TOTOP, pos=(0,
         top,
         0,
         0), parent=c)
        Line(parent=main, align=uiconst.TOTOP, color=(0.5, 0.5, 0.5, 0.75))
        self.showHideContainer = Container(name='showHideContainer', parent=main, align=uiconst.TOTOP, height=35, top=0, state=uiconst.UI_PICKCHILDREN)
        self.showStatusBarCbx = Checkbox(text=localization.GetByLabel('UI/Browser/BrowserSettings/ShowStatusBar'), parent=self.showHideContainer, configName='', retval=0, checked=self.showStatusBar)
        self.showNavBarCbx = Checkbox(text=localization.GetByLabel('UI/Browser/BrowserSettings/ShowNavigationBar'), parent=self.showHideContainer, configName='', retval=0, checked=self.showNavigationBar)
        Line(parent=main, align=uiconst.TOTOP, color=(0.5, 0.5, 0.5, 0.75))
        self.cacheContainer = Container(name='cacheContainer', parent=main, align=uiconst.TOTOP, height=26, top=8, state=uiconst.UI_PICKCHILDREN)
        l = Container(name='cacheLeft', parent=self.cacheContainer, align=uiconst.TOLEFT, width=100, state=uiconst.UI_PICKCHILDREN)
        r = Container(name='cacheRight', parent=self.cacheContainer, align=uiconst.TORIGHT, width=80, state=uiconst.UI_PICKCHILDREN)
        if not blue.win32.IsTransgaming():
            text = Label(text=localization.GetByLabel('UI/Browser/BrowserSettings/CacheLocation'), align=uiconst.TOLEFT, state=uiconst.UI_DISABLED, parent=l, padding=(2, 4, 2, 4))
            top = (text.textheight - 16) / 2 + 2 if text.textheight > 16 else 0
            totalTop += top
            btn = Button(parent=r, label=localization.GetByLabel('UI/Browser/BrowserSettings/ResetCacheLocation'), func=self.ResetCacheLocation, pos=(0,
             top,
             0,
             0), align=uiconst.TOPRIGHT)
            if btn.width > r.width:
                r.width = btn.width
            if text.textwidth > l.width:
                l.width = text.textwidth + 4
            self.cacheEdit = SinglelineEdit(name='cacheEdit', setvalue=settings.public.generic.Get('BrowserCache', corebrowserutil.DefaultCachePath()), align=uiconst.TOTOP, pos=(0,
             top,
             0,
             0), parent=self.cacheContainer)
            explainContainer = Container(name='cacheExplainContainer', parent=main, align=uiconst.TOTOP, height=26)
            Label(text=localization.GetByLabel('UI/Browser/BrowserSettings/CacheCaption'), align=uiconst.TOALL, state=uiconst.UI_DISABLED, parent=explainContainer, padLeft=4, fontsize=10)
            totalTop += 26
            clearCacheContainer = Container(name='clearCacheContainer', parent=main, align=uiconst.TOTOP, height=14)
            btn = Button(parent=clearCacheContainer, label=localization.GetByLabel('UI/Browser/BrowserSettings/ClearCache'), func=self.ClearCache)
            btn.hint = (localization.GetByLabel('UI/Browser/BrowserSettings/ClearCacheHint'),)
            totalTop += 16
        else:
            totalTop -= 32
        self.SetMinSize((500, 204 + totalTop))
        sm.StartService('sites')

    def ResetHomePage(self, *args):
        settings.user.ui.Set('HomePage2', browserutil.DefaultHomepage())
        self.homeEdit.SetValue(settings.user.ui.Get('HomePage2', browserutil.DefaultHomepage()))

    def ResetCacheLocation(self, *args):
        settings.public.generic.Set('BrowserCache', corebrowserutil.DefaultCachePath())
        self.cacheEdit.SetValue(corebrowserutil.DefaultCachePath())

    def Save(self, *args):
        url = self.homeEdit.GetValue().strip()
        if url and url.find('://') < 0:
            url = 'http://' + url
            self.homeEdit.SetValue(url)
        settings.user.ui.Set('HomePage2', url)
        if not blue.win32.IsTransgaming():
            cachePath = self.cacheEdit.GetValue().strip()
            cachePath = blue.paths.ResolvePath(cachePath)
            if cachePath:
                self.cacheEdit.SetValue(cachePath)
            settings.public.generic.Set('BrowserCache', cachePath)
        show = bool(self.showStatusBarCbx.GetValue())
        if bool(self.showStatusBar) != show:
            self.showStatusBar = show
            settings.user.ui.Set('browserShowStatusBar', show)
            sm.ScatterEvent('OnBrowserShowStatusBarChange')
        show = bool(self.showNavBarCbx.GetValue())
        if bool(self.showNavigationBar) != show:
            self.showNavigationBar = show
            settings.user.ui.Set('browserShowNavBar', show)
            sm.ScatterEvent('OnBrowserShowNavigationBarChange')

    def ClearCache(self, *args):
        if uicore.Message('BrowserClearCache', {}, uiconst.YESNO) == uiconst.ID_YES:
            from carbonui.control.browser.browserWindow import BrowserWindowCore
            for wnd in uicore.registry.GetWindows()[:]:
                if issubclass(wnd.__class__, BrowserWindowCore):
                    wnd.Close()

            sm.GetService('browserHostManager').RestartBrowserHost(clearCache=True)
            self.CloseByUser()


class BrowserSettingsWindowCoreOverride(BrowserSettingsWindowCore):
    pass
