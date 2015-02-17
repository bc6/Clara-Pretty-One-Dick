#Embedded file name: eve/client/script/ui/control\eveBaseLink.py
from carbonui.control.baselink import BaseLinkCore
import log
import blue
import urlparse
import localization
import carbonui.const as uiconst
from carbon.common.script.util.commonutils import StripTags
from utillib import KeyVal
from carbonui.util.bunch import Bunch
from carbonui.control.menuLabel import MenuLabel
from carbonui.util.various_unsorted import GetBrowser
from carbonui.util.stringManip import TruncateStringTo
from carbonui.primitives.fill import Fill
from carbonui.control.label import LabelCore
from eve.client.script.ui.podGuide.podGuideUtil import OpenPodGuide, GetTermShortText
HINTLABELS = {'showinfo': 'UI/Commands/ShowInfo',
 'contract': 'UI/Contracts/ShowContract',
 'note': 'UI/Notepad/ShowNote',
 'fleet': 'UI/Fleet/ClickToJoinFleet',
 'localsvc': None,
 'showrouteto': 'UI/Map/Navigation/ShowRoute',
 'fitting': 'UI/Fitting/ShowFitting',
 'preview': 'UI/Preview/Preview',
 'CertEntry': 'UI/Commands/ShowInfo',
 'recruitmentAd': 'UI/Corporations/CorporationWindow/Recruitment/OpenCorpAd',
 'podGuideLink': None,
 'joinChannel': 'UI/Chat/ChannelWindow/JoinChannel',
 'killReport': 'UI/Corporations/Wars/Killmails/KillReport',
 'tutorial': 'UI/Commands/OpenTutorial',
 'overviewPreset': 'UI/Overview/ProfileLinkHint'}

class BaseLink(BaseLinkCore):
    __guid__ = 'uicontrols.BaseLink'

    def ClickGameLinks(self, parent, URL):
        """
            Game specific options
            returns True if the link was used
        """
        import form
        if URL.startswith('eve:/'):
            self.GetFromCluster(parent, URL)
            return True
        if URL.startswith('showinfo:'):
            self.ShowInfo(URL[9:])
            return True
        if URL.startswith('showrouteto:'):
            self.ShowRouteTo(URL[12:])
            return True
        if URL.startswith('showinmap:'):
            self.ShowInMap(URL[10:])
            return True
        if URL.startswith('cmd:/'):
            sm.GetService('slash').SlashCmd(URL[4:])
            return True
        if URL.startswith('evebrowser:'):
            uicore.cmd.OpenBrowser(URL[11:])
            return True
        if URL.startswith('evemail:'):
            self.EveMail(URL[8:])
            return True
        if URL.startswith('evemailto:'):
            self.EveMail(URL[10:])
            return True
        if URL.startswith('note:'):
            self.Note(URL[5:])
            return True
        if URL.startswith('fleetmission:'):
            self.FleetMission(URL[13:])
            return True
        if URL.startswith('contract:'):
            self.Contract(URL[9:])
            return True
        if URL.startswith('fleet:'):
            self.AskJoinFleet(URL[6:])
            return True
        if URL.startswith('CertEntry:'):
            myArgs = URL[10:]
            certID, level = myArgs.split('//')
            abstractinfo = KeyVal(certificateID=int(certID), level=int(level))
            sm.StartService('info').ShowInfo(const.typeCertificate, abstractinfo=abstractinfo)
            return True
        if URL.startswith('fleetmenu:'):
            self.FleetMenu(URL[len('fleetmenu:'):])
            return True
        if URL.startswith('celestialmenu:'):
            self.CelestialMenu(URL[len('celestialmenu:'):])
            return True
        if URL.startswith('fitting:'):
            sm.StartService('fittingSvc').DisplayFittingFromString(URL[len('fitting:'):])
            return True
        if URL.startswith('preview:'):
            sm.GetService('preview').PreviewType(URL[len('preview:'):])
            return True
        if URL.startswith('warNegotiation:'):
            warNegotiationID = int(URL.split(':')[1])
            form.WarSurrenderWnd.Open(warNegotiationID=warNegotiationID, isRequest=False)
            return True
        if URL.startswith('killReport:'):
            killID, hashValue = URL.split(':')[1:]
            killID = int(killID)
            kill = sm.RemoteSvc('warStatisticMgr').GetKillMail(killID, hashValue)
            if kill is not None:
                from eve.client.script.ui.shared.killReportUtil import OpenKillReport
                OpenKillReport(kill)
            return True
        if URL.startswith('warReport:'):
            warID = URL[10:]
            form.WarReportWnd.CloseIfOpen()
            form.WarReportWnd.Open(create=1, warID=int(warID))
            return True
        if URL.startswith('tutorial:'):
            tutorialID = URL[len('tutorial:'):]
            sm.GetService('tutorial').OpenTutorialFromOutside(int(tutorialID), ask=True, ignoreSettings=True)
            return True
        if URL.startswith('recruitmentAd:'):
            myArgs = URL[14:]
            corpID, adID = myArgs.split('//')
            sm.GetService('corp').OpenCorpAdInNewWindow(int(corpID), int(adID))
            return True
        if URL.startswith('scannerAction:'):
            action = URL[14:]
            sm.GetService('scanSvc').ClickLink(action)
            return True
        if URL.startswith('podGuideLink:'):
            podGuideID = int(URL[len('podGuideLink:'):])
            OpenPodGuide(podGuideID)
            return True
        if URL.startswith('overviewPreset:'):
            if isinstance(parent, LabelCore):
                overviewName, url = getattr(parent, '_dragLinkData', ('', None))
                overviewName = StripTags(overviewName)
            else:
                overviewName = getattr(parent, 'linkText', '')
            overviewName = StripTags(overviewName)
            presetString = URL[len('overviewPreset:'):]
            parts = presetString.split('//')
            presetKey = (parts[0], int(parts[1]))
            sm.GetService('overviewPresetSvc').LoadSettings(presetKey, overviewName)
            return True
        if URL.startswith('joinChannel:'):
            channelID = URL[12:]
            corpID = None
            adID = None
            if '//' in channelID:
                channelID, corpID, adID = channelID.split('//')
            channelID = int(channelID)
            if channelID and not sm.GetService('LSC').IsJoined(channelID):
                sm.GetService('LSC').JoinOrLeaveChannel(channelID)
                if adID is not None:
                    sm.GetService('corp').LogCorpRecruitmentEvent(['corporationID',
                     'allianceID',
                     'channelID',
                     'applyingCorporationID',
                     'adID'], 'JoinRecruitingChannel', session.corpid, session.allianceid, channelID, corpID, adID)
            return True
        return False

    @classmethod
    def PrepareDrag(cls, dragContainer, dragSource, *args):
        from eve.client.script.ui.control.eveLabel import Label
        dragData = dragContainer.dragData[0]
        displayText = TruncateStringTo(dragData.displayText, 24, '...')
        label = Label(parent=dragContainer, text=StripTags(displayText), align=uiconst.TOPLEFT, bold=True)
        Fill(parent=dragContainer, color=(0, 0, 0, 0.3), padding=(-10, -2, -10, -2))
        dragContainer.width = label.textwidth
        dragContainer.height = label.textheight
        return (2, label.textheight)

    def CanOpenBrowser(self, *args):
        return getattr(eve.session, 'charid', None)

    def GetLinkMenu(self, parent, url):
        m = []
        if url.startswith('showinfo:'):
            ids = url[9:].split('//')
            try:
                typeID = int(ids[0])
                itemID = None
                bookmark = None
                filterFunc = None
                if len(ids) > 1:
                    itemID = int(ids[1])
                if len(ids) > 2:
                    invtype = cfg.invtypes.Get(typeID)
                    if invtype.categoryID == const.categoryBlueprint:
                        filterFunc = {localization.GetByLabel('UI/Commands/ShowInfo')}
                    else:
                        bookmark = self.GetBookmark(ids, itemID, typeID)
                m += sm.GetService('menu').GetMenuFormItemIDTypeID(itemID, typeID, bookmark, ignoreMarketDetails=0, filterFunc=filterFunc)
                m += sm.GetService('menu').GetGMTypeMenu(typeID, divs=True)
                for item in m:
                    if item is not None:
                        if item[0] == localization.GetByLabel('UI/Inventory/ItemActions/SetNewPasswordForContainer'):
                            m.remove(item)

            except:
                log.LogTraceback('failed to convert string to ids in Browser:ShowInfo')
                return []

        else:
            if url.startswith('preview:'):
                return []
            if url.startswith('contract:'):
                m += [(MenuLabel('UI/Contracts/ShowContract'), self.Contract, (url[9:],))]
                return m
        for eachUrlOption in HINTLABELS.keys():
            if url.startswith(eachUrlOption):
                return m

        if self.ValidateURL(url):
            url = url.replace('&amp;', '&')
            url = self.GetFixedURL(parent, url)
            m += [(MenuLabel('UI/Browser/OpenLinkInNewTab'), self.UrlHandlerDelegate, (parent,
               'NewView',
               url,
               True))]
            m += [(MenuLabel('UI/Common/Open'), self.UrlHandlerDelegate, (parent,
               'GoTo',
               url,
               False))]
        if url.lower().startswith('http'):
            m += [(MenuLabel('/Carbon/UI/Commands/CopyURL'), self.CopyUrl, (url,))]
        return m

    def GetFixedURL(self, parent, url):
        browser = GetBrowser(parent)
        currentURL = None
        if browser and hasattr(browser.sr, 'currentURL'):
            currentURL = browser.sr.currentURL
        return urlparse.urljoin(currentURL, url)

    def GetStandardLinkHint(self, url):
        if url.startswith('showinfo'):
            parsedArgs = BaseLink().ParseShowInfo(url[9:])
            if not parsedArgs:
                return localization.GetByLabel('UI/Commands/ShowInfo')
            typeID, itemID, data = parsedArgs
            typeInfo = cfg.invtypes.GetIfExists(typeID)
            if typeInfo:
                category = typeInfo.Category()
                if category.categoryID == const.categorySkill:
                    hintText = localization.GetByLabel('UI/Common/ShowTypeInfo', groupName=category.name)
                else:
                    hintText = localization.GetByLabel('UI/Common/ShowTypeInfo', groupName=typeInfo.Group().name)
            else:
                hintText = localization.GetByLabel('UI/Common/ShowInfo')
            return hintText
        if url.startswith('podGuideLink'):
            podGuideID = int(url[len('podGuideLink:'):])
            return localization.GetByMessageID(GetTermShortText(podGuideID))
        for k, v in HINTLABELS.iteritems():
            if url.startswith('%s:' % k):
                if v is None:
                    return v
                return localization.GetByLabel(v)

        return url

    def GetLinkFormat(self, url, linkState = None, linkStyle = None):
        linkState = linkState or uiconst.LINK_IDLE
        linkStyle = linkStyle or uiconst.LINKSTYLE_REGULAR
        fmt = Bunch()
        if linkStyle == uiconst.LINKSTYLE_SUBTLE:
            if linkState in (uiconst.LINK_ACTIVE, uiconst.LINK_HOVER):
                fmt.color = -256
            elif linkState in (uiconst.LINK_IDLE, uiconst.LINK_DISABLED):
                if url.startswith('showinfo'):
                    fmt.color = -1
                elif url.startswith('http'):
                    fmt.color = -23040
                else:
                    fmt.color = -552162
        elif linkState in (uiconst.LINK_ACTIVE, uiconst.LINK_HOVER):
            fmt.color = -256
            fmt.underline = True
        elif linkState in (uiconst.LINK_IDLE, uiconst.LINK_DISABLED):
            if url.startswith('showinfo'):
                fmt.color = -23040
            elif url.startswith('http'):
                fmt.color = -23040
            else:
                fmt.color = -552162
        fmt.bold = True
        return fmt

    def GetBookmark(self, ids, itemID, typeID):
        x, y, z, agentIDString, locationNumber, locationType = (float(ids[2]),
         float(ids[3]),
         float(ids[4]),
         ids[5],
         int(ids[6]),
         ids[7])
        agentIDList = [ int(s) for s in agentIDString.split(',') ]
        bookmark = KeyVal()
        bookmark.ownerID = eve.session.charid
        bookmark.itemID = itemID
        bookmark.typeID = typeID
        bookmark.flag = None
        bookmark.memo = ''
        bookmark.created = blue.os.GetWallclockTime()
        bookmark.x = x
        bookmark.y = y
        bookmark.z = z
        bookmark.locationID = itemID
        bookmark.agentID = agentIDList[0]
        bookmark.referringAgentID = agentIDList[1] if len(agentIDList) == 2 else None
        bookmark.locationNumber = locationNumber
        bookmark.locationType = locationType
        if bookmark.locationType == 'dungeon' or bookmark.locationType == 'agenthomebase':
            bookmark.deadspace = 1
        return bookmark

    def GetBadUrls(self, *args):
        return ['shellexec:',
         'eve:/',
         'localsvc:',
         'showinfo:',
         'showrouteto:',
         'showinmap:',
         'cmd:/',
         'evemail:',
         'evemailto:',
         'note:',
         'contract:',
         'evebrowser:']

    def UrlHandlerDelegate(self, parent, funcName, args, newTab = False):
        handler = getattr(self, 'URLHandler', None)
        if not handler and getattr(parent, 'sr', None) and getattr(parent.sr, 'node', None):
            handler = getattr(parent.sr.node, 'URLHandler', None)
        if handler:
            func = getattr(handler, funcName, None)
            if func:
                apply(func, (args,))
                return
        if not args.startswith('http'):
            self.ClickGameLinks(parent, args)
        else:
            uicore.cmd.OpenBrowser(args, newTab=newTab)

    def GetFromCluster(self, parent, url):
        proto, servicename, action = url.split('/')
        html = sm.RemoteSvc(servicename).Request(action)
        parent.sr.browser.LoadHTML(html)

    def Note(self, noteID):
        import form
        noteWindow = form.Notepad.Open()
        noteWindow.ShowNote(noteID)

    def FleetMission(self, args):
        ids = args.split('//')
        try:
            agentID = int(ids[0])
            charID = int(ids[1])
        except:
            log.LogError('failed to convert string to ids in Browser:Mission. Args:', args)
            return

        sm.GetService('agents').PopupMissionJournal(agentID, charID)

    def Contract(self, args):
        ids = args.split('//')
        try:
            contractID = int(ids[1])
            solarSystemID = int(ids[0])
        except:
            log.LogError('failed to convert string to ids in Browser:ShowInfo. Args:', args)
            return

        sm.GetService('contracts').ShowContract(contractID)

    def AskJoinFleet(self, args):
        try:
            fleetID = int(args)
        except:
            log.LogError('failed to convert string to ids in Browser:AskJoinFleet. Args:', args)
            return

        sm.GetService('fleet').AskJoinFleetFromLink(fleetID)

    def EveMail(self, url):
        receivers = []
        subject = None
        body = None
        if url.find('::') != -1:
            r, s, m = url.split('::')
            receivers = [r]
            subject = s
            body = m.replace('\r', '').replace('\n', '<br>')
        else:
            receivers = [url]
        sm.GetService('mailSvc').SendMsgDlg(toCharacterIDs=receivers, subject=subject, body=body)

    def ParseShowInfo(self, args):
        if args.startswith('showinfo:'):
            args = args[9:]
        ids = args.split('//')
        try:
            typeID = int(ids[0])
            itemID = None
            data = None
            if len(ids) > 1:
                itemID = int(ids[1])
            if len(ids) > 2:
                data = ids[2:]
            return (typeID, itemID, data)
        except:
            log.LogError('failed to convert string to ids in Browser:ShowInfo. Args:', args)
            return

    def ShowInfo(self, args):
        parsedArgs = self.ParseShowInfo(args)
        if not parsedArgs:
            return
        typeID, itemID, data = parsedArgs
        typeObj = cfg.invtypes.Get(typeID)
        if typeObj.categoryID == const.categoryAbstract:
            abstractinfo = KeyVal()
            if typeID == const.typeCertificate:
                abstractinfo.certificateID = itemID
            sm.GetService('info').ShowInfo(typeID, itemID, abstractinfo=abstractinfo)
        elif typeObj.categoryID == const.categoryBlueprint and data:
            try:
                copy, runs, material, productivity = data
                abstractinfo = KeyVal(categoryID=const.categoryBlueprint, runs=int(runs), isCopy=bool(int(copy)), productivityLevel=int(productivity), materialLevel=int(material))
                if itemID == 0:
                    itemID = None
                sm.GetService('info').ShowInfo(typeID, itemID, abstractinfo=abstractinfo)
            except:
                log.LogInfo('Could not convert blueprint extra data to valid parameters', data)

        else:
            sm.GetService('info').ShowInfo(typeID, itemID)

    def ShowInMap(self, args):
        """
            supports only one id now
        """
        try:
            solarsystemIDs = [ int(ssID) for ssID in args.split('//') ]
        except:
            log.LogError('failed to convert string to ids in Browser:ShowInMap. Args:', args)
            return

        sm.GetService('viewState').ActivateView('starmap', interestID=solarsystemIDs[0])

    def ShowRouteTo(self, args):
        fromto = args.split('::')
        if len(fromto) not in (1, 2):
            log.LogError('failed to convert string to id in Browser:ShowRouteTo. Args:', args)
            return
        for i in fromto:
            try:
                id = int(i)
            except:
                log.LogError('failed to convert string to id in Browser:ShowRouteTo. Args:', args)
                return

        if eve.session.stationid:
            sm.GetService('station').CleanUp()
        destinationID = int(fromto[0])
        sourceID = None
        if len(fromto) == 2:
            sourceID = int(fromto[1])
        sm.GetService('viewState').ActivateView('starmap', interestID=sourceID or session.regionid, drawRoute=(sourceID, destinationID))

    def FleetMenu(self, text):
        self.menu = sm.GetService('menu').FleetMenu(int(text))
        self.menu.ShowMenu(self)

    def CelestialMenu(self, text):
        self.menu = sm.GetService('menu').CelestialMenu(int(text))
        self.menu.ShowMenu(self)


from carbonui.control.baselink import BaseLinkCoreOverride
BaseLinkCoreOverride.__bases__ = (BaseLink,)

def GetCharIDFromTextLink(node):
    if node.Get('__guid__', None) != 'TextLink':
        return
    if not (node.Get('url', '').startswith('showinfo:137') or node.Get('url', '').startswith('showinfo:138')):
        return
    parts = node.Get('url', '').split('//')
    charID = int(parts[-1])
    return charID
