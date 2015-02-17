#Embedded file name: eve/client/script/ui/services\tutorialWindow.py
import math
from carbonui import const as uiconst, const
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.control.buttons import Button
from eve.client.script.ui.control.eveWindowUnderlay import WindowUnderlay, BlurredSceneUnderlay
from eve.client.script.ui.services.tutoriallib import TutorialColor, TutorialConstants, TutorialPageState
from eve.client.script.ui.shared.neocom.help import HelpWindow
from eve.common.lib import appConst as const, appConst
import localization
import uthread
import uicontrols
import service
import uiprimitives
import blue
import log
import util
import uicls
RESUME_TUTORIAL_HINT_DURATION_SEC = 60

class TutorialWindow(uicontrols.Window):
    __guid__ = 'form.TutorialWindow'
    default_windowID = 'aura9'
    default_width = 350
    default_height = 240
    defaultClipperHeight = 132
    default_iconNum = 'res:/UI/Texture/WindowIcons/tutorial.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.scope = 'all'
        self.sr.browser = uicontrols.Edit(parent=self.sr.main, padding=const.defaultPadding, readonly=1)
        self.sr.browser.HideBackground(True)
        self.sr.browser.AllowResizeUpdates(0)
        self.sr.browser.sr.window = self
        m = uicls.UtilMenu(menuAlign=uiconst.TOPRIGHT, parent=self.sr.topParent, align=uiconst.TOPRIGHT, left=const.defaultPadding, top=18, GetUtilMenu=self.SettingMenu, texturePath='res:/UI/Texture/Icons/73_16_50.png')
        self.nextFunc = attributes.nextFunc
        self.backFunc = attributes.backFunc
        self.onStartScalingWidth = None
        self.onStartScalingHeight = None
        self.constrainScreen = True
        if self.sr.stack is not None:
            self.sr.stack.RemoveWnd(self, 0, 0)
        if sm.GetService('tutorial').IsTutorialWindowUnkillable():
            self.MakeUnKillable()
            repairSysSkill = sm.GetService('skills').HasSkill(const.typeRepairSystems)
            shieldOpsSkill = sm.GetService('skills').HasSkill(const.typeShieldOperations)
            if repairSysSkill or shieldOpsSkill:
                self.MakeKillable()
        Sprite(parent=self.sr.topParent, name='mainicon', pos=(0, 2, 64, 64), texturePath='res:/UI/Texture/Icons/74_64_13.png')
        self.HideHeader()
        self.MakeUnstackable()
        self.SetMinSize([350, 220])
        self.imgpar = uiprimitives.Container(name='imgpar', parent=self.sr.main, align=uiconst.TOLEFT, width=64, idx=4, state=uiconst.UI_HIDDEN, clipChildren=1)
        imgparclipper = uiprimitives.Container(name='imgparclipper', parent=self.imgpar, align=uiconst.TOALL, left=5, top=5, width=5, height=5, clipChildren=1)
        self.img = uiprimitives.Sprite(parent=imgparclipper, align=uiconst.RELATIVE, left=1, top=1)
        self.bottomCont = uiprimitives.Container(name='bottom', parent=self.sr.maincontainer, align=uiconst.TOBOTTOM, height=32, idx=0)
        self.backBtn = Button(parent=self.bottomCont, label=localization.GetByLabel('UI/Commands/Back'), name='tutorialBackBtn', func=self.backFunc, align=uiconst.TOLEFT, padding=(8, 0, 0, 6))
        self.nextBtn = Button(parent=self.bottomCont, label=localization.GetByLabel('UI/Commands/Next'), name='tutorialNextBtn', func=self.nextFunc, align=uiconst.TORIGHT, padding=(0, 0, 8, 6), btn_default=1)
        self.Confirm = self.nextFunc
        self.sr.text = uicontrols.EveLabelMedium(text='', parent=self.bottomCont, state=uiconst.UI_DISABLED, align=uiconst.CENTER)
        top = self.tTop = uiprimitives.Container(name='tTop', parent=self.sr.topParent, align=uiconst.TOALL, padding=(64, 0, 24, 0), idx=0)
        self.captionText = uicontrols.EveLabelLarge(text='', parent=top, align=uiconst.TOTOP, top=10, state=uiconst.UI_DISABLED)
        self.captionText.OnSizeChanged = self.CheckTopHeight
        self.subcaption = uicontrols.Label(text='', parent=top, align=uiconst.TOTOP, state=uiconst.UI_DISABLED, fontsize=18, color=TutorialColor.HINT_FRAME)
        self.sr.browser.AllowResizeUpdates(1)
        self.SetParent(uicore.layer.abovemain)
        uicore.animations.SpSwoopBlink(self.blinkFill, rotation=math.pi - 0.5, duration=3.0, loops=TutorialConstants.NUM_BLINKS)
        uicore.animations.SpSwoopBlink(self.blinkBorder, rotation=math.pi - 0.5, duration=3.0, loops=TutorialConstants.NUM_BLINKS)

    def Prepare_Background_(self):
        self.sr.underlay = WindowUnderlay(parent=self, name='underlay', state=uiconst.UI_DISABLED)
        self.blinkFill = uiprimitives.Sprite(bgParent=self.sr.underlay, name='blinkFill', texturePath='res:/UI/Texture/classes/Tutorial/fill_no_border.png', state=uiconst.UI_DISABLED, color=(1, 1, 1, 0.5))
        self.blinkBorder = uiprimitives.Sprite(bgParent=self.sr.underlay, name='blinkBorder', texturePath='res:/UI/Texture/classes/Tutorial/border.png', state=uiconst.UI_DISABLED, color=TutorialColor.HINT_FRAME)
        uicontrols.Frame(name='frame', bgParent=self.sr.underlay, color=TutorialColor.WINDOW_FRAME, frameConst=uiconst.FRAME_BORDER1_CORNER0)
        BlurredSceneUnderlay(bgParent=self.sr.underlay)

    def RegisterPositionAndSize(self, key = None, windowID = None):
        uicontrols.Window.RegisterPositionAndSize(self, key, windowID)
        self.currentBottom = self.top + self.height

    def SettingMenu(self, menuParent):
        shouldAutoReszie = settings.char.windows.Get('tutorialShouldAutoReszie', 1)
        menuParent.AddCheckBox(text=localization.GetByLabel('UI/Tutorial/AutoResizeTutorialWindow'), checked=shouldAutoReszie, callback=(self.ChangeAutoResize, not shouldAutoReszie))
        menuParent.AddDivider()
        menuParent.AddIconEntry(icon='res:/UI/Texture/Icons/38_16_190.png', text=localization.GetByLabel('UI/Tutorial/OpenTutorialsMenu'), callback=self.OpenTutorialList)

    def OpenTutorialList(self):
        wnd = HelpWindow.GetIfOpen()
        if wnd:
            wnd.Maximize()
            wnd.sr.mainTabs.ShowPanelByName(localization.GetByLabel('UI/Help/Tutorials'))
        else:
            wnd = HelpWindow.Open(showPanel=localization.GetByLabel('UI/Help/Tutorials'))

    def ChangeAutoResize(self, shouldAutoReszie):
        settings.char.windows.Set('tutorialShouldAutoReszie', shouldAutoReszie)
        self.CheckHeight()

    def ToggleMinimize(self):
        """
        The method is overridden for the tutorial window since it lives in a different layer and can't stack
        If window is minimized, maximize it
        If window is not minimized and in front, minimize it
        """
        if not self.IsMinimizable():
            return
        if self.IsMinimized():
            self.Maximize()
        else:
            self.Minimize()

    @staticmethod
    def default_top(*args):
        return uicore.desktop.height - 270

    @staticmethod
    def default_left(*args):
        leftpush, rightpush = uicontrols.Window.GetSideOffset()
        return uicore.desktop.width - 360 - rightpush

    def _OnClose(self, *args):
        uthread.new(sm.GetService('tutorial').Cleanup)

    def OnStartScale_(self, wnd, *args):
        self.onStartScalingWidth = self.width
        self.onStartScalingHeight = self.height

    def OnEndScale_(self, wnd, *args):
        uicontrols.Window.OnEndScale_(self, wnd, *args)
        if abs(self.onStartScalingHeight - self.height) > 5 or abs(self.onStartScalingWidth - self.width) > 5:
            settings.char.windows.Set('tutorialShouldAutoReszie', 0)

    def CloseByUser(self, *args):
        tutorialSvc = sm.GetService('tutorial')
        tut = tutorialSvc.GetCurrentTutorial()
        if tut is not None:
            if hasattr(self, 'startTime'):
                totaltime = (blue.os.GetWallclockTime() - self.startTime) / const.SEC
            else:
                totaltime = 0
            timeSpentInPage = (blue.os.GetWallclockTime() - tutorialSvc.pageTime) / const.SEC
            try:
                numClicks = uicore.uilib.GetGlobalClickCount() - tutorialSvc.numMouseClicks
                numKeys = uicore.uilib.GetGlobalKeyDownCount() - tutorialSvc.numKeyboardClicks
            except:
                numClicks = numKeys = 0

            if not getattr(self, 'done', 0):
                tutorialSvc.SetSequenceStatus(tut.sequenceID, tut.tutorialID, tut.pageNo, 'aborted')
                with util.ExceptionEater('eventLog'):
                    tutorialSvc.LogTutorialEvent(['tutorialID',
                     'pageNo',
                     'sequenceID',
                     'timeInTutorial',
                     'numMouseClicks',
                     'numKeyboardClicks',
                     'reason',
                     'timeInPage'], 'Closed', tut.tutorialID, tut.pageNo, tut.sequenceID, totaltime, numClicks, numKeys, 'aborted', timeSpentInPage)
            else:
                tutorialSvc.SetSequenceStatus(tut.sequenceID, tut.tutorialID, tut.pageNo, 'done')
                with util.ExceptionEater('eventLog'):
                    tutorialSvc.LogTutorialEvent(['tutorialID',
                     'pageNo',
                     'sequenceID',
                     'timeInTutorial',
                     'numMouseClicks',
                     'numKeyboardClicks',
                     'reason',
                     'timeInPage'], 'Closed', tut.tutorialID, tut.pageNo, tut.sequenceID, totaltime, numClicks, numKeys, 'done', timeSpentInPage)
        tutorialSvc.Cleanup()
        if settings.char.windows.Get('tutorialShouldAutoReszie', 1):
            self.display = False
            cw, currentClipperHeight = self.sr.browser.sr.clipper.GetAbsoluteSize()
            self.ChangeWindowHeight(currentClipperHeight, self.defaultClipperHeight)
            self.RegisterPositionAndSize()
        self.Close()
        if getattr(self, 'showTutorialReminder', True):
            uthread.new(self._TutorialReminder)

    def _TutorialReminder(self):
        blue.pyos.synchro.SleepWallclock(1000)
        tutorialSvc = sm.GetService('tutorial')
        tutorialSvc.uipointerSvc.PointTo('neocom.tutorial', localization.GetByLabel('UI/Tutorial/ResumeTutorialPointer'))
        blue.pyos.synchro.SleepWallclock(RESUME_TUTORIAL_HINT_DURATION_SEC * 1000)
        browser = tutorialSvc.GetTutorialBrowser(create=False)
        if browser is None:
            tutorialSvc.uipointerSvc.ClearPointers()

    def CheckTopHeight(self):
        h = 0
        for each in self.tTop.children:
            if each.state != uiconst.UI_HIDDEN:
                h += each.height + each.top

        self.SetTopparentHeight(max(74, h))

    def CheckHeight(self, *args):
        browser = self.sr.browser
        shouldAutoReszie = settings.char.windows.Get('tutorialShouldAutoReszie', 1)
        if shouldAutoReszie:
            cw, currentClipperHeight = browser.sr.clipper.GetCurrentAbsoluteSize()
            if not currentClipperHeight:
                cw, currentClipperHeight = browser.sr.clipper.GetAbsoluteSize()
            contentHeight = browser.GetContentHeight()
            self.ChangeWindowHeight(currentClipperHeight, contentHeight + 10)
            browser.scrollEnabled = 1
        else:
            browser.scrollEnabled = 1
            uthread.new(self.ShowScrollControlIfNeeded)

    def ChangeWindowHeight(self, currentClipperHeight, contentHeight):
        if self.defaultClipperHeight is None:
            return
        if self.defaultClipperHeight > contentHeight and self.defaultClipperHeight <= currentClipperHeight:
            diff = currentClipperHeight - self.defaultClipperHeight
            uicore.animations.MorphScalar(self, 'height', startVal=self.height, endVal=self.height - diff, duration=0.2, loops=1, curveType=2, callback=None, sleep=False)
            uicore.animations.MorphScalar(self, 'top', startVal=self.top, endVal=max(self.top + diff, 0), duration=0.2, loops=1, curveType=2, callback=None, sleep=True)
        else:
            diff = currentClipperHeight - max(contentHeight, self.defaultClipperHeight)
            uicore.animations.MorphScalar(self, 'height', startVal=self.height, endVal=self.height - diff, duration=0.2, loops=1, curveType=2, callback=None, sleep=False)
            uicore.animations.MorphScalar(self, 'top', startVal=self.top, endVal=max(self.top + diff, 0), duration=0.2, loops=1, curveType=2, callback=None, sleep=True)

    def ShowScrollControlIfNeeded(self, *args):
        if self.sr.browser.scrollingRange:
            self.sr.browser.sr.scrollcontrols.state = uiconst.UI_NORMAL

    def LoadImage(self, imagePath):
        if not blue.ResFile().Open(imagePath):
            log.LogError('Image not found in res:', imagePath)
            return
        texture, tWidth, tHeight, bw, bh = sm.GetService('photo').GetTextureFromURL(imagePath, sizeonly=1, dontcache=1)
        self.img.state = uiconst.UI_NORMAL
        self.img.SetTexturePath(imagePath)
        self.img.width = tWidth
        self.img.height = tHeight
        self.imgpar.width = min(128, tWidth) + self.img.left + 5
        if self.imgpar.state != uiconst.UI_DISABLED:
            self.imgpar.state = uiconst.UI_DISABLED

    def LoadAndGiveGoodies(self, goodies, tutorialID, pageID, pageNo):
        goodieHtml = ''
        if len(goodies) != 0:
            if goodies[0] == -1:
                goodieHtml += '\n                        <br>\n                        <font size=12>%s</font>\n                        <br><br>\n                ' % localization.GetByLabel('UI/Tutorial/TutorialGoodie/AlreadyReceived')
                return goodieHtml
            for goodie in goodies:
                invtype = cfg.invtypes.Get(goodie.invTypeID)
                goodieHtml += '\n                        <hr>\n                        <p>\n                        <img style=margin-right:0;margin-bottom:0 src="typeicon:typeID=%s&bumped=1&showFitting=0" align=left>\n                        <font size=20 margin-left=20>%s</font>\n                        <a href=showinfo:%s><img style:vertical-align:bottom src="icon:38_208" size=16 alt="%s"></a>\n                        <br><br>\n                        </p>\n                    ' % (goodie.invTypeID,
                 invtype.typeName,
                 goodie.invTypeID,
                 localization.GetByLabel('UI/Commands/ShowInfo'))

            sm.GetService('tutorial').GiveGoodies(tutorialID, pageID, pageNo)
            return goodieHtml

    def LoadTutorial(self, tutorialID = None, pageNo = None, pageID = None, sequenceID = None, force = 0, VID = None, skipCriteria = False, checkBack = 0, diffMouseClicks = 0, diffKeyboardClicks = 0):
        self.sr.browser.scrollEnabled = 0
        self.backBtn.state = uiconst.UI_HIDDEN
        self.nextBtn.state = uiconst.UI_HIDDEN
        self.backBtn.Blink(0)
        self.nextBtn.Blink(0)
        self.sr.text.text = ''
        self.done = 0
        self.reverseBack = 0
        imagePath = None
        pageCount = None
        body = '\n            <html>\n            <head>\n            <LINK REL="stylesheet" TYPE="text/css" HREF="res:/ui/css/tutorial.css">\n            </head>\n            <body>'
        tutData = None
        if VID:
            tutData = sm.RemoteSvc('tutorialSvc').GetTutorialInfo(VID)
        elif tutorialID:
            tutData = sm.GetService('tutorial').GetTutorialInfo(tutorialID)
        if tutData:
            fadeOut = uicore.animations.FadeOut(self.sr.browser.sr.clipper, duration=0.05, loops=1, curveType=2, callback=None, sleep=False)
            if self and self.destroyed:
                return
            pageCount = len(tutData.pages)
            if pageNo == -1:
                pageNo = pageCount
            else:
                pageNo = pageNo or 1
            if pageNo > pageCount:
                log.LogWarn('Open Tutorial Page Failed:, have page %s but max %s pages. falling back to page 1 :: tutorialID: %s, sequenceID: %s, VID: %s' % (pageNo,
                 pageCount,
                 tutorialID,
                 sequenceID,
                 VID))
                pageNo = 1
            with util.ExceptionEater('eventLog'):
                sm.GetService('tutorial').LogTutorialEvent(['tutorialID', 'pageNo', 'openedByUser'], 'OpenTutorial', tutorialID, pageNo, force)
            dispPageNo, dispPageCount = pageNo, pageCount
            pageData = tutData.pages[pageNo - 1]
            caption = self.captionText
            loop = 1
            while 1:
                captionTextParts = localization.GetByMessageID(tutData.tutorial[0].tutorialNameID).split(':')
                if len(captionTextParts) > 1:
                    tutorialNumber = captionTextParts[0]
                    rest = ':'.join(captionTextParts[1:]).strip()
                    captionText = '%s: %s' % (tutorialNumber, rest)
                else:
                    captionText = localization.GetByMessageID(tutData.tutorial[0].tutorialNameID)
                caption.text = captionText
                if pageData and pageData.pageNameID:
                    self.subcaption.text = localization.GetByMessageID(pageData.pageNameID)
                    self.subcaption.state = uiconst.UI_DISABLED
                else:
                    self.subcaption.state = uiconst.UI_HIDDEN
                if caption.textheight < 52 or not loop:
                    break
                caption.fontsize = 13
                caption.letterspace = 0
                caption.last = (0, 0)
                loop = 0

            if sequenceID:
                check = []
                seqTutData = sm.GetService('tutorial').GetTutorialInfo(tutorialID)
                for criteria in seqTutData.criterias:
                    cd = sm.GetService('tutorial').GetCriteria(criteria.criteriaID)
                    if cd is None:
                        continue
                    check.append(criteria)

                closeToEnd = 0
                for criteria in seqTutData.pagecriterias:
                    if criteria.pageID == pageData.pageID:
                        check.append(criteria)
                        closeToEnd = 1
                    elif not closeToEnd:
                        cd = sm.GetService('tutorial').GetCriteria(criteria.criteriaID)
                        if cd is None:
                            continue
                        if not cd.criteriaName.startswith('rookieState'):
                            continue
                        check.append(criteria)

                actionData = seqTutData.actions
                pageActionData = seqTutData.pageactions
            else:
                check = [ c for c in tutData.criterias ]
                for criteria in tutData.pagecriterias:
                    if criteria.pageID == pageData.pageID:
                        check.append(criteria)

                actionData = tutData.actions
                pageActionData = tutData.pageactions
            actions = [ sm.GetService('tutorial').GetAction(action.actionID) for action in actionData ]
            actions += [ sm.GetService('tutorial').GetAction(action.actionID) for action in pageActionData if action.pageID == pageData.pageID ]
            preRookieState = eve.rookieState
            if skipCriteria:
                criteriaCheck = None
            else:
                criteriaCheck = sm.GetService('tutorial').ParseCriterias(check, 'tut', self, tutorialID)
            if not self or getattr(self, 'sr', None) is None:
                return
            if criteriaCheck:
                if preRookieState:
                    eve.SetRookieState(preRookieState)
                body += '<br>' + localization.GetByMessageID(criteriaCheck.messageTextID)
                with util.ExceptionEater('eventLog'):
                    sm.GetService('tutorial').LogTutorialEvent(['tutorialID',
                     'pageNo',
                     'sequenceID',
                     'clickedByUser',
                     'errorMessageID',
                     'numMouseClicks',
                     'numKeyboardClicks'], 'CriteriaNotMet', tutorialID, pageNo, sequenceID, force, criteriaCheck.messageTextID, diffMouseClicks, diffKeyboardClicks)
                if pageNo > 1 or sequenceID and sm.GetService('tutorial').GetNextInSequence(tutorialID, sequenceID, -1):
                    self.backBtn.state = uiconst.UI_NORMAL
                if sm.GetService('tutorial').waitingForWarpConfirm == False:
                    self.nextBtn.state = uiconst.UI_NORMAL
                    self.nextBtn.OnClick = sm.GetService('tutorial').Reload
                    self.Confirm = sm.GetService('tutorial').Reload
                    self.nextBtn.SetLabel(localization.GetByLabel('UI/Commands/Next'))
                    self.sr.text.text = ''
                self.backBtn.OnClick = self.backFunc
                if checkBack:
                    self.reverseBack = 1
            else:
                sm.GetService('tutorial').ParseActions(actions)
                self.sr.text.text = localization.GetByLabel('UI/Tutorial/PageOf', num=dispPageNo, total=dispPageCount)
                if pageNo > 1 or sequenceID and sm.GetService('tutorial').GetNextInSequence(tutorialID, sequenceID, -1):
                    self.backBtn.state = uiconst.UI_NORMAL
                sm.GetService('tutorial').SetCriterias(check)
                if pageData:
                    page = pageData
                    body += '%s' % localization.GetByMessageID(page.textID)
                    self.nextBtn.state = uiconst.UI_NORMAL
                    self.nextBtn.OnClick = self.nextFunc
                    self.Confirm = self.nextFunc
                    self.backBtn.OnClick = self.backFunc
                    if pageNo < pageCount or sequenceID and sm.GetService('tutorial').GetNextInSequence(tutorialID, sequenceID):
                        self.nextBtn.SetLabel(localization.GetByLabel('UI/Commands/Next'))
                    else:
                        self.nextBtn.SetLabel(localization.GetByLabel('UI/Commands/Done'))
                        self.done = 1
                    imagePath = page.imagePath
                else:
                    body += '\n                        Page %s was not found in this tutorial.\n                        ' % pageNo
        else:
            self.captionText.text = localization.GetByLabel('UI/Tutorial/EveTutorials')
            body = '%s %s' % (localization.GetByLabel('UI/Tutorial/UnknownTutorial'), tutorialID)
        body += '</body></html>'
        blue.pyos.synchro.Yield()
        self.CheckTopHeight()
        self.LoadHTML('', newThread=0)
        if self.state == uiconst.UI_HIDDEN:
            self.Maximize()
        if imagePath:
            self.LoadImage(imagePath)
            self.sr.browser.left = self.img.width
        else:
            if self.imgpar.state != uiconst.UI_HIDDEN:
                self.imgpar.state = uiconst.UI_HIDDEN
            self.sr.browser.left = const.defaultPadding
        blue.pyos.synchro.Yield()
        goodies = sm.RemoteSvc('tutorialLocationSvc').GetTutorialGoodies(tutorialID, pageID, pageNo)
        goodieHtml = self.LoadAndGiveGoodies(goodies, tutorialID, pageID, pageNo)
        if goodieHtml:
            body += '<br>%s' % goodieHtml
        self.LoadHTML(body, newThread=0)
        self.SetCaption(localization.GetByLabel('UI/Tutorial/EveTutorials'))
        if not hasattr(self, 'startTime') or not hasattr(self, 'current') or self.current.sequenceID != sequenceID:
            self.startTime = blue.os.GetWallclockTime()
        tutorialPageState = TutorialPageState(tutorialID, pageNo, pageID, pageCount, sequenceID, VID, pageData.pageActionID)
        settings.char.generic.Set('tutorialPageState', tuple(tutorialPageState))
        settings.char.generic.Delete('tutorialCompleted')
        self.current = tutorialPageState
        if sequenceID:
            if self.done:
                sm.GetService('tutorial').SetSequenceStatus(sequenceID, tutorialID, pageNo, 'done')
            else:
                sm.GetService('tutorial').SetSequenceStatus(sequenceID, tutorialID, pageNo)
            if not sm.GetService('tutorial').CheckTutorialDone(sequenceID, tutorialID):
                sm.GetService('tutorial').SetSequenceDoneStatus(sequenceID, tutorialID, pageNo)
        for page in tutData.pages:
            if page.pageID == pageID or page.pageNumber == pageNo:
                if not criteriaCheck:
                    translatedText = localization.GetByMessageID(page.uiPointerTextID)
                    sm.GetService('uipointerSvc').PointTo(page.uiPointerID, translatedText)
                    break

        fadeOut.Stop()
        uicore.animations.FadeIn(self.sr.browser.sr.clipper, endVal=1.0, duration=0.3, loops=1, curveType=2, callback=None, sleep=False)
        self.CheckHeight()

    def LoadHTML(self, html, newThread = 1):
        self.ShowLoad()
        self.sr.browser.LoadHTML(html, newThread=newThread)

    def LoadEnd(self):
        self.HideLoad()

    def Reload(self, forced = 1, *args):
        if not self.sr.browser:
            return
        uthread.new(self.sr.browser.LoadHTML, None, scrollTo=self.sr.browser.GetScrollProportion())
