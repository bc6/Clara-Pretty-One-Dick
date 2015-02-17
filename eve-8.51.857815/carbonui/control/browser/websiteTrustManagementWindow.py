#Embedded file name: carbonui/control/browser\websiteTrustManagementWindow.py
"""
This window is used to manage trusted and ignored sites. I've migrated it out of sites.py
in order to improve the granularity of our file structure.

The window primarily relies upon the Sites service (in sites.py) which actually implements
the trusted/ignored logic.
"""
import carbonui.const as uiconst
import uthread
import localization
from carbonui.control.scrollentries import ScrollEntryNode, SE_GenericCore
from carbonui.primitives.container import Container
from carbonui.primitives.line import Line
from carbonui.control.window import WindowCoreOverride as Window
from carbonui.control.label import LabelOverride as Label
from carbonui.control.singlelineedit import SinglelineEditCoreOverride as SinglelineEdit
from carbonui.control.buttons import ButtonCoreOverride as Button
from carbonui.control.scroll import ScrollCoreOverride as Scroll

class WebsiteTrustManagementWindowCore(Window):
    __guid__ = 'uicls.WebsiteTrustManagementWindowCore'
    __notifyevents__ = ['OnTrustedSitesChange']
    default_windowID = 'WebsiteTrustManagementWindow'

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        initialUrl = attributes.initialUrl
        self.SetCaption(localization.GetByLabel('UI/Browser/TrustedSites'))
        self.SetMinSize((368, 300))
        mainArea = self.GetMainArea()
        mainArea.top = 2
        self.inputContainer = Container(name='inputContainer', parent=mainArea, align=uiconst.TOTOP, height=50)
        self.bodyContainer = Container(name='bodyContainer', parent=mainArea, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        self.trustContainer = Container(name='trustContainer', parent=self.bodyContainer, align=uiconst.TOTOP, height=76)
        self.ignoreContainer = Container(name='ignoreContainer', parent=self.bodyContainer, align=uiconst.TOBOTTOM, height=76)
        urlInputContainer = Container(name='urlInputContainer', parent=self.inputContainer, align=uiconst.TOTOP, height=22, top=3)
        inputButtonContainer = Container(name='urlInputButtonContainer', parent=self.inputContainer, align=uiconst.TOBOTTOM, height=20, padRight=4)
        self.urlText = Label(text=localization.GetByLabel('UI/Browser/EditBookmarks/URL'), parent=urlInputContainer, align=uiconst.TOLEFT, padLeft=6, state=uiconst.UI_DISABLED, uppercase=1, fontsize=10, letterspace=1)
        self.urlInput = SinglelineEdit(name='urlInput', parent=urlInputContainer, align=uiconst.TOTOP, padRight=const.defaultPadding, padLeft=const.defaultPadding)
        self.trustBtn = Button(parent=inputButtonContainer, label=localization.GetByLabel('UI/Browser/TrustSite'), align=uiconst.TORIGHT, padLeft=4, padBottom=3, func=self.TrustSite)
        self.trustBtn.hint = localization.GetByLabel('UI/Browser/TrustManagementTrustHint')
        self.ignoreBtn = Button(parent=inputButtonContainer, label=localization.GetByLabel('UI/Browser/IgnoreSite'), align=uiconst.TORIGHT, padLeft=4, padBottom=3, func=self.IgnoreSite)
        self.ignoreBtn.hint = localization.GetByLabel('UI/Browser/TrustManagementIgnoreHint')
        trustBtnContainer = Container(name='trustBtnContainer', parent=self.trustContainer, align=uiconst.TOBOTTOM, height=22, padRight=4)
        trustRemoveBtn = Button(parent=trustBtnContainer, label=localization.GetByLabel('UI/Commands/Remove'), align=uiconst.TORIGHT, padLeft=4, padBottom=3, func=self.RemoveTrustedSite)
        trustRemoveBtn.hint = localization.GetByLabel('UI/Browser/TrustManagementRemoveTrustHint')
        trustTextContainer = Container(name='trustTextContainer', parent=self.trustContainer, align=uiconst.TOTOP, height=14)
        Label(text=localization.GetByLabel('UI/Browser/TrustedSites'), parent=trustTextContainer, state=uiconst.UI_DISABLED, fontsize=10, left=10, top=3)
        trustScrollContainer = Container(name='trustScrollContainer', parent=self.trustContainer, align=uiconst.TOALL)
        self.trustScroll = Scroll(parent=trustScrollContainer, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        ignoreBtnContainer = Container(name='ignoreBtnContainer', parent=self.ignoreContainer, align=uiconst.TOBOTTOM, height=22, padRight=4)
        ignoreRemoveBtn = Button(parent=ignoreBtnContainer, label=localization.GetByLabel('UI/Commands/Remove'), align=uiconst.TORIGHT, padLeft=4, padBottom=3, func=self.RemoveIgnoredSite)
        ignoreRemoveBtn.hint = localization.GetByLabel('UI/Browser/TrustManagementRemoveIgnoredHint')
        ignoreTextContainer = Container(name='ignoreTextContainer', parent=self.ignoreContainer, align=uiconst.TOTOP, height=14)
        Label(text=localization.GetByLabel('UI/Browser/IgnoredSites'), parent=ignoreTextContainer, state=uiconst.UI_DISABLED, fontsize=10, left=10, top=3)
        ignoreScrollContainer = Container(name='ignoreScrollContainer', parent=self.ignoreContainer, align=uiconst.TOALL)
        self.ignoreScroll = Scroll(parent=ignoreScrollContainer, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        self.inited = 1
        self.sitesSvc = sm.GetService('sites')
        self.RefreshSites()
        if initialUrl is not None:
            self.urlInput.SetValue(initialUrl)

    def _OnResize(self, *args):
        uthread.new(self.__OnResize, *args)

    def __OnResize(self, *args):
        if not getattr(self, 'inited', False):
            return
        bodyHeight = self.bodyContainer.absoluteBottom - self.bodyContainer.absoluteTop
        halfSize = int(bodyHeight / 2)
        if halfSize * 2 != bodyHeight:
            self.trustContainer.height = halfSize + 1
        else:
            self.trustContainer.height = halfSize
        self.ignoreContainer.height = halfSize

    def TrustSite(self, *args):
        value = self.urlInput.GetValue()
        if not value:
            eve.Message('trustedSiteManagementPleaseEnterUrl')
            return
        value = value.strip()
        if value is not None and len(value) > 0:
            self.sitesSvc.AddTrustedSite(value)
        else:
            eve.Message('trustedSiteManagementPleaseEnterUrl')

    def IgnoreSite(self, *args):
        value = self.urlInput.GetValue()
        if not value:
            eve.Message('trustedSiteManagementPleaseEnterUrl')
            return
        value = value.strip()
        if value is not None and len(value) > 0:
            self.sitesSvc.AddIgnoredSite(value)
        else:
            eve.Message('trustedSiteManagementPleaseEnterUrl')

    def RemoveTrustedSite(self, *args):
        selected = self.trustScroll.GetSelected()
        if not len(selected):
            eve.Message('trustedSiteManagementPleaseSelectSite')
            return
        for entry in selected:
            self.sitesSvc.RemoveTrustedSite(entry.retval)

    def RemoveIgnoredSite(self, *args):
        selected = self.ignoreScroll.GetSelected()
        if not len(selected):
            eve.Message('trustedSiteManagementPleaseSelectSite')
            return
        for entry in selected:
            self.sitesSvc.RemoveTrustedSite(entry.retval)

    def OnTrustedSitesChange(self, *etc):
        self.RefreshSites()

    def OnGetTrustMenu(self, entry):
        return [(localization.GetByLabel('UI/Commands/Remove'), sm.GetService('sites').RemoveTrustedSite, (entry.sr.node.retval,))]

    def RefreshSites(self):
        trustScrollList = []
        ignoreScrollList = []
        for key, value in self.sitesSvc.GetTrustedSites().iteritems():
            if value.auto:
                continue
            trustScrollList.append(ScrollEntryNode(decoClass=SE_GenericCore, label=key, retval=key, trustData=value, GetMenu=self.OnGetTrustMenu))

        for key, value in self.sitesSvc.GetIgnoredSites().iteritems():
            if value.auto:
                continue
            ignoreScrollList.append(ScrollEntryNode(decoClass=SE_GenericCore, label=key, retval=key, trustData=value, GetMenu=self.OnGetTrustMenu))

        self.trustScroll.Load(contentList=trustScrollList)
        self.ignoreScroll.Load(contentList=ignoreScrollList)


class WebsiteTrustManagementWindowCoreOverride(WebsiteTrustManagementWindowCore):
    pass
