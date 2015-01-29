#Embedded file name: eve/client/script/ui/login/charSelection\characterSelection.py
"""
    This file contains the UI code for the character selection screen
"""
import uiprimitives
import uix
import blue
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.util.uiComponents import ButtonEffect, Component
import uthread
import log
import service
import uicls
import carbonui.const as uiconst
import ccUtil
import localization
import itertoolsext
import uiutil
import corebrowserutil
import math
from carbonui.primitives.container import Container
from eve.client.script.ui.shared.redeem.redeemPanel import RedeemPanel
from eve.client.script.ui.login.charSelection.timeLeftCounters import CountDownCont
import xml.etree.ElementTree as ET
from eve.client.script.ui.services.evePhotosvc import NONE_PATH
from eveexceptions.exceptionEater import ExceptionEater
from eve.client.script.ui.login.charSelection.characterSlots import SmallCharacterSlot, SmallEmptySlot, DeleteButton, CharacterDetailsLocation as CharLocation
import evegraphics.settings as gfxsettings
import eve.client.script.ui.login.charSelection.characterSelectionUtils as csUtil
import eve.client.script.ui.login.charSelection.characterSelectionColors as csColors
import gatekeeper
LOGO_WIDTH = 405
LOGO_HEIGHT = 160
MINIMUM_LOGOHEIGHT = 90
LOGO_PADDING = 40
BG_WIDTH = 2117
BG_HEIGHT = 1200
FEATURE_BAR_HEIGHT = 100
BANNER_WIDTH = 550
BANNER_HEIGHT = 80

class CharacterSelection(uicls.LayerCore):
    __notifyevents__ = ['OnSetDevice',
     'OnJumpQueueMessage',
     'OnCharacterHandler',
     'OnUIRefresh',
     'OnUIScalingChange',
     'OnTokensRedeemed',
     'OnGraphicSettingsChanged',
     'OnUIoffsetChanged',
     'OnRedeemingQueueUpdated']
    minSidePadding = 50

    def OnSetDevice(self):
        """
        When device settings change we may have to resize some of our
        UI components. If the setup/behavior of UI elemnts are changed
        this function will have to be updated.
        """
        if not self.isopen:
            return
        self.OnRefreshScreen()

    def OnUIRefresh(self):
        self.OnRefreshScreen()

    def OnUIScalingChange(self, *args):
        self.OnRefreshScreen()

    def OnGraphicSettingsChanged(self, changes):
        if gfxsettings.UI_CAMERA_OFFSET in changes:
            self.ChangeUIoffset()

    def OnUIoffsetChanged(self):
        self.ChangeUIoffset()

    def ChangeUIoffset(self):
        cameraOffset = settings.user.ui.offsetUIwithCamera
        uiOffsetWithCamera = settings.user.ui.cameraOffset
        if self.uiOffset != (cameraOffset, uiOffsetWithCamera):
            self.OnRefreshScreen()

    def OnCloseView(self):
        self.isTabStop = False
        screen = self.selectionScreen
        self.selectionScreen = None
        self.ClearBackground()
        if screen is not None and not screen.destroyed:
            screen.Close()
        sm.GetService('dynamicMusic').UpdateDynamicMusic()

    def OnJumpQueueMessage(self, msgtext, ready):
        if ready:
            log.LogInfo('Jump Queue: ready, slamming through...')
            self.__Confirm(sm.GetService('jumpQueue').GetPreparedQueueCharID())
        else:
            log.LogInfo('Jump Queue: message=', msgtext)
            sm.GetService('gameui').Say(msgtext)

    def OnCharacterHandler(self, *_):
        self.SetData()
        self.OnRefreshScreen()

    def GetChars(self):
        return sm.GetService('cc').GetCharactersToSelect()

    def ReduceCharacterGraphics(self):
        """Sets the graphics to low for character creation"""
        gfxsettings.Set(gfxsettings.GFX_CHAR_FAST_CHARACTER_CREATION, True, pending=False)
        gfxsettings.Set(gfxsettings.GFX_CHAR_CLOTH_SIMULATION, 0, pending=False)
        gfxsettings.Set(gfxsettings.GFX_CHAR_TEXTURE_QUALITY, 2, pending=False)

    def OnOpenView(self):
        self.isTabStop = True
        self.remoteCharacterSvc = sm.RemoteSvc('charUnboundMgr')
        self.mapSvc = sm.GetService('map')
        self.SetData()
        self.OnRefreshScreen()
        self.AnimateScreenIn()
        sm.GetService('dynamicMusic').UpdateDynamicMusic()
        sm.GetService('audio').SendUIEvent('character_selection_start')

    def SetData(self, force = False):
        characterSelectionData = self.GetCharacterSelectionData(force=force)
        self.chars = characterSelectionData.GetChars()
        self.subscriptionEndTimes = characterSelectionData.GetSubscriptionEndTime()
        self.numSlotsOwnedByUser = characterSelectionData.GetNumCharacterSlots()
        self.slotsToDisplay = characterSelectionData.GetMaxServerCharacters()
        self.currentAdInfo = None
        self.adImageFetched = False
        self.showAd = True
        self.countDownCont = None

    def OnRefreshScreen(self):
        uicore.registry.SetFocus(self)
        self.ready = False
        self.countDownThread = None
        self.characterSlotList = []
        self.uiOffset = (0, 0)
        self.maxFullSlotSize = None
        self.Flush()
        self.ClearBackground()
        self.selectionScreen = Container(name='selectionScreen', parent=self, state=uiconst.UI_PICKCHILDREN)
        self.InitUI()
        self.AddBackground()
        self.AddFeatureContainer()
        self.LoadCharacterSlots()
        self.SetRedeemPanelMode()
        self.AdjustFeatureBarPosition()
        self.CollapseOrExpandSlots(animate=False, loadingSlots=False)
        self.AdjustLogo()
        self.SetTimer()
        self.loadingWheel = uicls.LoadingWheel(parent=self.selectionScreen, align=uiconst.CENTER, state=uiconst.UI_NORMAL, idx=0)
        self.loadingWheel.display = False

    def AnimateScreenIn(self):
        uicore.animations.MorphScalar(self.bg, 'opacity', startVal=0.0, endVal=1.0, duration=1.0)
        uicore.animations.MorphScalar(self.logo, 'opacity', startVal=0.0, endVal=1.0, duration=0.5, timeOffset=0.5)
        uicore.animations.MorphScalar(self.featureContainer, 'opacity', startVal=0.0, endVal=1.0, duration=0.5, timeOffset=1.5)
        if self.countDownCont:
            uicore.animations.MorphScalar(self.countDownCont, 'opacity', startVal=0.0, endVal=1.0, duration=0.3, timeOffset=2.0)
        slotDelay = 0.5
        uthread.new(self.PlaySound_thread, event='character_selection_animstart', sleepTime=slotDelay)
        for idx, eachSlot in self.slotsByIdx.iteritems():
            baseAnimationOffset = slotDelay + idx * 0.1
            eachSlot.AnimateSlotIn(animationOffset=baseAnimationOffset, soundFunction=self.PlaySound_thread, charContHeight=self.charactersCont.height)

    def PlaySound_thread(self, event, sleepTime):
        blue.pyos.synchro.Sleep(1000 * sleepTime)
        sm.GetService('audio').SendUIEvent(event)

    def AnimateScreenOut(self, excludeSlotForCharID):
        self.selectionScreen.state = uiconst.UI_DISABLED
        slotDelay = 0.5
        slots = self.slotsByIdx.values()
        slots = sorted(slots, key=lambda x: x.slotIdx, reverse=True)
        counter = 0
        uthread.new(self.PlaySound_thread, event='character_selection_animstart', sleepTime=slotDelay)
        for eachSlot in slots:
            if eachSlot.charID == excludeSlotForCharID:
                continue
            baseAnimationOffset = slotDelay + counter * 0.1
            eachSlot.AnimateSlotOut(animationOffset=baseAnimationOffset, soundFunction=self.PlaySound_thread, charContHeight=self.charactersCont.height)
            counter += 1

        uicore.animations.MorphScalar(self.logo, 'opacity', startVal=1.0, endVal=0.0, duration=0.5, timeOffset=2.0)
        uicore.animations.MorphScalar(self.featureContainer, 'opacity', startVal=1.0, endVal=0.0, duration=0.3, timeOffset=0)
        if self.redeemPanel.HasRedeemItems():
            uicore.animations.MorphScalar(self.redeemPanel, 'opacity', startVal=1.0, endVal=0.0, duration=0.3, timeOffset=0)
        if self.countDownCont:
            uicore.animations.MorphScalar(self.countDownCont, 'opacity', startVal=1.0, endVal=0.0, duration=0.3, timeOffset=3.0)

    def EnableScreen(self):
        self.selectionScreen.state = uiconst.UI_PICKCHILDREN
        self.AnimateScreenIn()

    def GetCharacterSelectionData(self, force = False):
        return sm.GetService('cc').GetCharacterSelectionData(force=force)

    def InitUI(self):
        self.selectionScreen.Flush()
        self.redeemPanel = RedeemPanel(parent=self.selectionScreen, collapseCallback=self.ExitRedeemMode, expandCallback=self.EnterRedeemMode, dragEnabled=True, instructionText=localization.GetByLabel('UI/RedeemWindow/DragAndDropToGive'), redeemButtonBorderColor=csColors.REDEEM_BORDER, redeemButtonBackgroundColor=csColors.REDEEM_BORDER_BACKGROUND, redeemButtonFillColor=csColors.REDEEM_BORDER_FILL, textColor=csColors.REDEEM_PANEL_AVAILABLE_TEXT, redeemPanelBackgroundColor=csColors.REDEEM_PANEL_FILL)
        self.topBorder = Container(name='topBorder', parent=self.selectionScreen, align=uiconst.TOTOP_NOPUSH, height=40, state=uiconst.UI_PICKCHILDREN)
        self.centerArea = Container(name='centerAra', parent=self.selectionScreen, align=uiconst.TOALL, state=uiconst.UI_PICKCHILDREN)
        self.logoCont = Container(parent=self, name='logoCont', align=uiconst.TOTOP_NOPUSH, height=100, state=uiconst.UI_NORMAL)
        self.logo = uiprimitives.Sprite(parent=self.logoCont, texturePath='res:/UI/Texture/classes/CharacterSelection/logo.png', align=uiconst.CENTER, pos=(0,
         0,
         LOGO_WIDTH,
         LOGO_HEIGHT))
        self.charactersCont = Container(name='charactersCont', parent=self.centerArea, align=uiconst.CENTER, state=uiconst.UI_PICKCHILDREN, width=1050, height=600)
        self.SetupCharacterSlots()

    def AddBackground(self):
        clientHeight = uicore.desktop.height
        percentOfClientHeight = float(clientHeight) / BG_HEIGHT
        newHeight = clientHeight
        newWidth = int(percentOfClientHeight * BG_WIDTH)
        self.bg = uiprimitives.Sprite(parent=uicore.desktop, name='charselBackground', texturePath='res:/UI/Texture/classes/CharacterSelection/background.png', align=uiconst.CENTER, pos=(0,
         0,
         newWidth,
         newHeight), state=uiconst.UI_DISABLED)
        self.bgOverlay = uiprimitives.Fill(bgParent=uicore.desktop, color=(0, 0, 0, 1.0))

    def ClearBackground(self):
        if getattr(self, 'bg', None):
            self.bg.Close()
            self.bgOverlay.Close()
        if getattr(self, 'logoCont', None):
            self.logoCont.Close()

    def OnTokensRedeemed(self, redeemedItems, charID):
        self.redeemPanel.RedeemItems(redeemedItems)
        if not self.redeemPanel.HasRedeemItems():
            self.redeemPanel.HidePanel()

    def ExitRedeemMode(self, animate = True):
        self.redeemPanel.CollapsePanel(animate=animate, duration=csUtil.COLLAPSE_TIME)

    def EnterRedeemMode(self, animate = True):
        self.redeemPanel.ExpandPanel(animate=animate, duration=csUtil.COLLAPSE_TIME)

    def CollapseOrExpandSlots(self, animate = True, loadingSlots = False):
        shouldShipBeVisible = self.ShouldShipBeVisible()
        self.ChangeSlotCollapsedState(animate=animate, loadingSlots=loadingSlots)
        for eachSlot in self.slotsByIdx.itervalues():
            if shouldShipBeVisible:
                eachSlot.ExpandSlot(animate=animate)
            else:
                eachSlot.CollapseSlot(animate=animate)

    def ShouldShipBeVisible(self):
        """
            Checking if the ship should be visible. This depends on the client's height, and whether ads or
            redeeming panel are present (and visible)
        """
        if self.maxFullSlotSize:
            maxFullSlotSize = self.maxFullSlotSize
        else:
            l, ct, cw, ch = self.charactersCont.GetAbsolute()
            maxFullSlotSize = ch
        redeemPanelHeight = self.redeemPanel.GetHeight()
        emptySpace = uicore.desktop.height - maxFullSlotSize
        if emptySpace < 2 * (MINIMUM_LOGOHEIGHT + LOGO_PADDING) or emptySpace < FEATURE_BAR_HEIGHT + redeemPanelHeight:
            shipVisible = False
        else:
            shipVisible = True
        return shipVisible

    def ChangeSlotCollapsedState(self, animate, loadingSlots = False):
        """
            Collapses or expands the character container if needed.
            Will also shift it up, depending on client size, and whether there are ads or redeeming panel.
            We prefer it to stay in the center, but if the slot is collapsed, we want it to shift up as it
            gets smaller, resulting it staying at the same distance from top.
            If we don't have enough space for ads or redeeming panel, we shift the characters up to make room.
        """
        shouldShipBeVisible = self.ShouldShipBeVisible()
        maxCurrentCharacterSlotHeight = self.GetMaxCharacterSlotHeight(shipVisible=shouldShipBeVisible)
        charactersContTop = 0
        diff = self.charactersCont.height - maxCurrentCharacterSlotHeight
        if animate or loadingSlots and not self.redeemPanel.IsCollapsed():
            charactersContTop = min(0, int(-diff / 2.0))
        freeSpace = uicore.desktop.height - maxCurrentCharacterSlotHeight

        def FindExtraShift(componentHeight):
            shift = 0
            if freeSpace / 2.0 < componentHeight:
                shift = componentHeight - int(freeSpace / 2.0)
            return shift

        bgOffset = 0
        extraShift = 0
        if self.redeemPanel.HasRedeemItems() and not self.redeemPanel.IsCollapsed():
            bgOffset = -self.redeemPanel.GetPanelHeight()
            extraShift = FindExtraShift(self.redeemPanel.height)
        if extraShift:
            charactersContTop = min(charactersContTop, -extraShift)
        uicore.animations.MorphScalar(self.logo, 'opacity', startVal=self.logo.opacity, endVal=1.0, duration=csUtil.COLLAPSE_TIME)
        if extraShift:
            cl, ct, cw, ch = self.charactersCont.GetAbsolute()
            if ct - extraShift < self.logoCont.height - LOGO_PADDING / 2:
                uicore.animations.MorphScalar(self.logo, 'opacity', startVal=self.logo.opacity, endVal=0.05, duration=csUtil.COLLAPSE_TIME)
        if animate:
            uicore.animations.MorphScalar(self.bg, 'top', startVal=self.bg.top, endVal=bgOffset, duration=csUtil.COLLAPSE_TIME)
            uicore.animations.MorphScalar(self.charactersCont, 'height', startVal=self.charactersCont.height, endVal=maxCurrentCharacterSlotHeight, duration=csUtil.COLLAPSE_TIME)
            uicore.animations.MorphScalar(self.charactersCont, 'top', startVal=self.charactersCont.top, endVal=charactersContTop, duration=csUtil.COLLAPSE_TIME)
        else:
            self.bg.top = bgOffset
            uicore.animations.StopAnimation(self.charactersCont, 'height')
            self.charactersCont.height = maxCurrentCharacterSlotHeight
            self.charactersCont.top = charactersContTop

    def AdjustFeatureBarPosition(self):
        """
            Adjusting the size of the ad container so the ad displays fairly centered below the character slots
        """
        shouldShipBeVisible = self.ShouldShipBeVisible()
        maxCurrentCharacterSlotHeight = self.GetMaxCharacterSlotHeight(shouldShipBeVisible)
        redeemPanelButtonHeight = self.redeemPanel.GetButtonHeight()
        availableHeight = int((uicore.desktop.height - maxCurrentCharacterSlotHeight) / 2.0) - redeemPanelButtonHeight
        self.featureContainer.top = int(availableHeight / 2.0) + redeemPanelButtonHeight - FEATURE_BAR_HEIGHT / 2

    def GetMaxCharacterSlotHeight(self, shipVisible = True):
        if self.characterSlotList:
            return max((slot.GetSlotHeight(shipVisible=shipVisible) for slot in self.characterSlotList))
        else:
            return max([ slot.GetSlotHeight(shipVisible=shipVisible) for slot in self.slotsByIdx.itervalues() ])

    def SetupCharacterSlots(self):
        self.characterSlotList = []
        self.slotsByCharID = {}
        self.slotsByIdx = {}
        self.slotsToDisplay = min(self.numSlotsOwnedByUser + 1, self.slotsToDisplay)
        paddingFromImage = SmallCharacterSlot.GetExtraWidth()
        spaceForEachSlot = (uicore.desktop.width - 2 * self.minSidePadding) / self.slotsToDisplay
        maxSize = SmallCharacterSlot.maxImageSize + paddingFromImage
        spaceForEachSlot = min(maxSize, spaceForEachSlot)
        occupiedSlots = len(self.chars[:self.slotsToDisplay])
        for idx in xrange(occupiedSlots):
            slot = SmallCharacterSlot(name='characterSlot_%s' % idx, parent=self.charactersCont, callback=self.EnterGameWithCharacter, deleteCallback=self.Terminate, undoDeleteCallback=self.UndoTermination, terminateCallback=self.Terminate, slotIdx=idx, width=spaceForEachSlot)
            slot.OnMouseEnter = (self.OnSlotOnMouseEnter, slot)
            slot.OnMouseExit = (self.OnSlotMouseExit, slot)
            self.characterSlotList.append(slot)
            self.slotsByIdx[idx] = slot

        for idx in xrange(occupiedSlots, self.slotsToDisplay):
            if idx > self.numSlotsOwnedByUser - 1:
                callback = self.GoBuySlot
                ownSlot = False
            else:
                callback = self.CreateCharacter
                ownSlot = True
            slot = SmallEmptySlot(name='emptySlot_%s' % idx, parent=self.charactersCont, callback=callback, slotIdx=idx, width=spaceForEachSlot, ownSlot=ownSlot)
            self.slotsByIdx[idx] = slot
            slot.OnMouseEnter = (self.OnSlotOnMouseEnter, slot)
            slot.OnMouseExit = (self.OnSlotMouseExit, slot)

        self.charactersCont.width = spaceForEachSlot * self.slotsToDisplay
        self.SetUIOffset()

    def SetUIOffset(self):
        cameraOffset = settings.user.ui.offsetUIwithCamera
        uiOffsetWithCamera = settings.user.ui.cameraOffset
        push = sm.GetService('window').GetCameraLeftOffset(self.charactersCont.width, align=uiconst.CENTER, left=0)
        self.uiOffset = (cameraOffset, uiOffsetWithCamera)
        self.charactersCont.left = push
        self.logo.left = push

    def LoadCharacterSlots(self):
        allSlots = self.characterSlotList[:]
        for characterInfo in self.chars[:self.slotsToDisplay]:
            charID = characterInfo.characterID
            characterSlot = allSlots.pop(0)
            self.LoadSlotForCharacter(charID, characterSlot)
            characterSlot.SetMouseExitState()

        if self.characterSlotList:
            maxShipIconHeight = max((slot.GetShipAndLocationContHeight() for slot in self.characterSlotList))
        else:
            shipPadding = CharLocation.paddingShipAlignmentTop + CharLocation.paddingShipAlignmentBottom
            maxShipIconHeight = CharLocation.minShipSize + CharLocation.locationContHeight + shipPadding
        for slot in self.slotsByIdx.itervalues():
            slot.SetShipContHeight(maxShipIconHeight)

        maxSlotHeight = self.GetMaxCharacterSlotHeight()
        self.maxFullSlotSize = maxSlotHeight
        self.charactersCont.height = maxSlotHeight
        self.ready = True

    def LoadSlotForCharacter(self, charID, characterSlot):
        self.slotsByCharID[charID] = characterSlot
        characterDetails = self.GetCharacterSelectionData().GetCharInfo(charID)
        characterSlot.LoadSlot(charID, characterDetails)

    def SetRedeemPanelMode(self):
        self.redeemPanel.UpdateDisplay(animate=True, timeOffset=0)
        if not self.redeemPanel.HasRedeemItems():
            self.ExitRedeemMode(animate=False)
            return
        if self.redeemPanel.IsCollapsed():
            self.ExitRedeemMode(animate=False)
            self.redeemPanel.CollapsePanel(animate=False)
        else:
            self.EnterRedeemMode(animate=False)
            self.redeemPanel.ExpandPanel(animate=False)

    def AddFeatureContainer(self):
        """ Create a container for the NES button and for banner ads """
        distanceFromBottom = self.redeemPanel.GetButtonHeight()
        self.featureContainer = Container(parent=self.selectionScreen, name='featureContainer', align=uiconst.TOBOTTOM_NOPUSH, height=FEATURE_BAR_HEIGHT, top=distanceFromBottom)
        innerFeatureContainer = Container(parent=self.featureContainer, name='innerFeatureCont', align=uiconst.CENTER, width=834, height=FEATURE_BAR_HEIGHT)
        self.openStoreContainer = Container(name='openStoreContainer', parent=innerFeatureContainer, state=uiconst.UI_PICKCHILDREN, align=uiconst.CENTER, width=270, height=90)
        OpenStoreButton(parent=self.openStoreContainer, align=uiconst.CENTER, onClick=uicore.cmd.ToggleAurumStore)
        self.adSpriteContainer = Container(name='adSpriteContainer ', parent=innerFeatureContainer, align=uiconst.CENTERRIGHT, width=BANNER_WIDTH, height=BANNER_HEIGHT)
        self.adSprint = uiprimitives.Sprite(name='adSprite', parent=self.adSpriteContainer, state=uiconst.UI_NORMAL, width=BANNER_WIDTH, height=BANNER_HEIGHT)
        DeleteButton(parent=self.adSpriteContainer, name='closeAdButton', align=uiconst.TOPRIGHT, pos=(2, 2, 16, 16), texturePath='res:/UI/Texture/Icons/Plus_Small.png', state=uiconst.UI_NORMAL, color=(0.5, 0.5, 0.5, 1.0), callback=self.CloseAd, hint=localization.GetByLabel('UI/Common/Buttons/Close'), rotation=math.pi / 4.0, idx=0)
        self.DisplayAd()

    def AdjustLogo(self):
        cl, ct, cw, ch = self.charactersCont.GetAbsolute()
        if ct > 0:
            availableHeightAbove = ct
        else:
            availableHeightAbove = int((uicore.desktop.height - self.maxFullSlotSize) / 2.0)
        logoContHeight = max(availableHeightAbove, MINIMUM_LOGOHEIGHT + LOGO_PADDING)
        self.logoCont.height = logoContHeight
        self.logo.display = True
        availableHeightForLogo = logoContHeight - LOGO_PADDING
        percentage = max(0.55, min(1.0, availableHeightForLogo / float(LOGO_HEIGHT)))
        newHeight = int(percentage * LOGO_HEIGHT)
        newWidth = int(percentage * LOGO_WIDTH)
        self.logo.height = newHeight
        self.logo.width = newWidth

    def SetTimer(self):
        if itertoolsext.any(self.subscriptionEndTimes.values()):
            self.countDownCont = CountDownCont(parent=self.topBorder, align=uiconst.TOTOP, height=self.topBorder.height, timers=self.subscriptionEndTimes)

    def OnSlotOnMouseEnter(self, slot, *args):
        if not slot.mouseOverState:
            sm.GetService('audio').SendUIEvent('character_hover_picture')
        for eachSlot in self.slotsByIdx.itervalues():
            if eachSlot.charID:
                characterData = self.GetCharacterSelectionData().GetCharInfo(eachSlot.charID)
                deletePrepTime = characterData.GetDeletePrepareTime()
                if deletePrepTime:
                    continue
            if eachSlot == slot:
                eachSlot.SetMouseOverState(animate=True)
            else:
                eachSlot.SetMouseExitState(animate=True)

    def OnSlotMouseExit(self, slot, *args):
        if uiutil.IsUnder(uicore.uilib.mouseOver, slot):
            return
        slot.SetMouseExitState(animate=True)

    def GoBuySlot(self, slotSelected):
        uicore.cmd.OpenAccountManagement()

    def CreateCharacter(self, slotSelected):
        self.CreateNewCharacter()

    def EnterGameWithCharacter(self, slotSelected):
        characterData = self.GetCharacterSelectionData().GetCharInfo(slotSelected.charID)
        deletePrepTime = characterData.GetDeletePrepareTime()
        if deletePrepTime is not None:
            return
        slotSelected.SetMouseOverState()
        slotSelected.PlaySelectedAnimation()
        self.ConfirmWithCharID(slotSelected.charID)
        if sm.GetService('jumpQueue').GetPreparedQueueCharID():
            boundCharacterService = sm.RemoteSvc('charMgr')
            gatekeeper.Initialize(lambda args: boundCharacterService.GetCohortsForCharacter)
            experimentSvc = sm.StartService('experimentClientSvc')
            experimentSvc.Initialize(languageID=session.languageID)

    def CreateNewCharacter(self):
        if not self.ready:
            eve.Message('Busy')
            return
        lowEnd = gfxsettings.GetDeviceClassification() == gfxsettings.DEVICE_LOW_END
        msg = uiconst.ID_YES
        if not sm.StartService('device').SupportsSM3():
            msg = eve.Message('AskMissingSM3', {}, uiconst.YESNO, default=uiconst.ID_NO)
        if msg != uiconst.ID_YES:
            return
        msg = uiconst.ID_YES
        if not lowEnd and ccUtil.SupportsHigherShaderModel():
            msg = eve.Message('AskUseLowShader', {}, uiconst.YESNO, default=uiconst.ID_NO)
        if msg != uiconst.ID_YES:
            return
        if lowEnd:
            msg2 = eve.Message('ReduceGraphicsSettings', {}, uiconst.YESNO, default=uiconst.ID_NO)
            if msg2 == uiconst.ID_YES:
                self.ReduceCharacterGraphics()
        eve.Message('CCNewChar')
        uthread.new(sm.GetService('gameui').GoCharacterCreation, askUseLowShader=0)

    def CreateNewAvatar(self, charID):
        charData = self.GetCharacterSelectionData().GetCharInfo(charID)
        charDetails = charData.charDetails
        if charData.GetPaperDollState == const.paperdollStateForceRecustomize:
            eve.Message('ForcedPaperDollRecustomization')
        uthread.new(sm.GetService('gameui').GoCharacterCreation, charID, charDetails.gender, charDetails.bloodlineID, dollState=charData.GetPaperDollState())

    def Confirm(self):
        if not self.characterSlotList:
            return
        slot = self.characterSlotList[0]
        self.EnterGameWithCharacter(slot)

    def ConfirmWithCharID(self, charID, *_):
        log.LogInfo('Character selection: Character selection confirmation')
        if not self.ready:
            log.LogInfo('Character selection: Denied character selection confirmation, not ready')
            eve.Message('Busy')
            return
        isInSync = self.WaitForClockSynchroAndGetSynchroState()
        if not isInSync:
            eve.Message('ClockSynchroInProgress')
            return
        if sm.GetService('jumpQueue').GetPreparedQueueCharID() != charID:
            self.__Confirm(charID)

    def WaitForClockSynchroAndGetSynchroState(self):
        for x in xrange(300):
            if not sm.GetService('connection').IsClockSynchronizing():
                return True
            if x > 30:
                log.general.Log('Clock synchronization still in progress after %d seconds' % x, log.LGINFO)
            blue.pyos.synchro.SleepWallclock(1000)

        return not sm.GetService('connection').IsClockSynchronizing()

    def EnterAsCharacter(self, charID, loadDungeon, secondChoiceID):
        MAX_RETRIES = 10
        RETRY_SECONDS = 6
        for numTries in xrange(MAX_RETRIES):
            try:
                sm.GetService('sessionMgr').PerformSessionChange('charsel', self.remoteCharacterSvc.SelectCharacterID, charID, loadDungeon, secondChoiceID)
                return
            except UserError as e:
                if e.msg == 'SystemCheck_SelectFailed_Loading' and numTries < MAX_RETRIES - 1:
                    log.LogNotice('System is currently loading. Retrying %s/%s' % (numTries, MAX_RETRIES))
                    blue.pyos.synchro.SleepWallclock(RETRY_SECONDS * 1000)
                else:
                    self.EnableScreen()
                    raise

        self.EnableScreen()

    def __Confirm(self, charID, secondChoiceID = None):
        charData = self.GetCharacterSelectionData().GetCharInfo(charID)
        dollState = charData.GetPaperDollState()
        sm.GetService('cc').StoreCurrentDollState(dollState)
        if dollState in (const.paperdollStateForceRecustomize, const.paperdollStateNoExistingCustomization):
            self.CreateNewAvatar(charID)
            return
        self.ready = False
        self.TryEnterGame(charID, secondChoiceID)
        if charID:
            petitionMessage = charData.GetPetitionMessage()
            if petitionMessage:
                uthread.new(sm.GetService('petition').CheckNewMessages)
            mailCount = charData.GetUnreaddMailCount()
            notificationCount = charData.GetUnreadNotificationCount()
            if mailCount + notificationCount > 0:
                uthread.new(sm.GetService('mailSvc').CheckNewMessages_thread, mailCount, notificationCount)

    def TryEnterGame(self, charID, secondChoiceID):
        loadingHeader = localization.GetByLabel('UI/CharacterSelection/CharacterSelection')
        loadingText = localization.GetByLabel('UI/CharacterSelection/EnterGameAs', char=charID)
        sm.GetService('audio').SendUIEvent('msg_OnLogin_play')
        sm.GetService('audio').SendUIEvent('msg_OnConnecting_play')
        self.ShowLoading()
        try:
            eve.Message('OnCharSel')
            sm.GetService('jumpQueue').PrepareQueueForCharID(charID)
            try:
                if not eve.session.role & service.ROLE_NEWBIE and settings.user.ui.Get('bornDaysAgo%s' % charID, 0) > 30:
                    settings.user.ui.Set('doTutorialDungeon%s' % charID, 0)
                loadDungeon = settings.user.ui.Get('doTutorialDungeon%s' % charID, 1)
                self.selectionScreen.state = uiconst.UI_DISABLED
                self.AnimateScreenOut(excludeSlotForCharID=charID)
                self.EnterAsCharacter(charID, loadDungeon, secondChoiceID)
                settings.user.ui.Set('doTutorialDungeon%s' % charID, 0)
                settings.user.ui.Set('doTutorialDungeon', 0)
            except UserError as e:
                self.EnableScreen()
                if e.msg == 'SystemCheck_SelectFailed_Full':
                    solarSystemID = e.args[1]['system'][1]
                    self.SelectAlternativeSolarSystem(charID, solarSystemID, secondChoiceID)
                    return
                if e.msg != 'SystemCheck_SelectFailed_Queued':
                    sm.GetService('jumpQueue').PrepareQueueForCharID(None)
                    raise
            except:
                self.EnableScreen()
                sm.GetService('jumpQueue').PrepareQueueForCharID(None)
                raise

        except:
            self.EnableScreen()
            self.HideLoading()
            sm.GetService('loading').FadeOut()
            self.ready = True
            raise

    def SelectAlternativeSolarSystem(self, charID, solarSystemID, secondChoiceID = None):
        neighbors = self.mapSvc.GetNeighbors(solarSystemID)
        if secondChoiceID is None:
            selectText = localization.GetByLabel('UI/CharacterSelection/SelectAlternativeSystem')
        else:
            selectText = localization.GetByLabel('UI/CharacterSelection/SelectAnotherAlternativeSystem')
            secondChoiceNeighbors = self.mapSvc.GetNeighbors(secondChoiceID)
            neighbors.extend(secondChoiceNeighbors)
        systemSecClass = self.mapSvc.GetSecurityClass(solarSystemID)
        validNeighbors = []
        for ssid in neighbors:
            if ssid == secondChoiceID or ssid == solarSystemID:
                continue
            if self.mapSvc.GetSecurityClass(ssid) != systemSecClass:
                continue
            systemItem = self.mapSvc.GetItem(ssid)
            regionID = self.mapSvc.GetRegionForSolarSystem(ssid)
            regionItem = self.mapSvc.GetItem(regionID)
            factionID = systemItem.factionID
            factionName = ''
            if factionID:
                factionName = cfg.eveowners.Get(factionID).ownerName
            label = '%s<t>%s<t>%s<t>%s' % (systemItem.itemName,
             regionItem.itemName,
             self.mapSvc.GetSecurityStatus(ssid),
             factionName)
            validNeighborTuple = (label, ssid, None)
            validNeighbors.append(validNeighborTuple)

        loadingSvc = sm.StartService('loading')
        self.HideLoading()
        loadingSvc.FadeOut()
        scrollHeaders = [localization.GetByLabel('UI/Common/LocationTypes/SolarSystem'),
         localization.GetByLabel('UI/Common/LocationTypes/Region'),
         localization.GetByLabel('UI/Common/Security'),
         localization.GetByLabel('UI/Sovereignty/Sovereignty')]
        ret = uix.ListWnd(validNeighbors, None, localization.GetByLabel('UI/CharacterSelection/SystemCongested'), selectText, 1, scrollHeaders=scrollHeaders, minw=555)
        if ret:
            self.__Confirm(charID, ret[1])
        else:
            sm.StartService('jumpQueue').PrepareQueueForCharID(None)
            self.ready = True

    def Terminate(self, charID, *args):
        if not self.ready:
            eve.Message('Busy')
            return
        try:
            self.ready = 0
            characterData = self.GetCharacterSelectionData().GetCharInfo(charID)
            deletePrepTime = characterData.GetDeletePrepareTime()
            if deletePrepTime:
                now = blue.os.GetWallclockTime()
                if deletePrepTime < now:
                    self.DeleteCharacter(charID, characterData.charDetails.gender)
                else:
                    timeLeft = deletePrepTime - now
                    infoMsg = localization.GetByLabel('UI/CharacterSelection/AlreadyInBiomassQueue', charID=charID, timeLef=timeLeft)
                    eve.Message('CustomInfo', {'info': infoMsg})
            else:
                self.SubmitToBiomassQueue(charID)
        finally:
            self.ready = 1

    def DeleteCharacter(self, charID, gender):
        eve.Message('CCTerminate')
        if eve.Message('AskDeleteCharacter', {'charID': charID}, uiconst.YESNO) != uiconst.ID_YES:
            return
        progressHeader = localization.GetByLabel('UI/CharacterSelection/RecyclingCharacter', charID=charID)
        self.ShowLoading()
        if gender == const.genderFemale:
            beginMsg = 'CCTerminateForGoodFemaleBegin'
            endMsg = 'CCTerminateForGoodFemale'
        else:
            beginMsg = 'CCTerminateForGoodMaleBegin'
            endMsg = 'CCTerminateForGoodMale'
        eve.Message(beginMsg)
        try:
            error = self.remoteCharacterSvc.DeleteCharacter(charID)
            eve.Message(endMsg)
        finally:
            self.HideLoading()
            self.ready = 1

        if error:
            eve.Message(error)
            return
        self.SetData(force=True)
        self.OnRefreshScreen()

    def SubmitToBiomassQueue(self, charID):
        if eve.Message('AskSubmitToBiomassQueue', {'charID': charID}, uiconst.YESNO) != uiconst.ID_YES:
            return
        ret = self.remoteCharacterSvc.PrepareCharacterForDelete(charID)
        if ret:
            eve.Message('SubmitToBiomassQueueConfirm', {'charID': charID,
             'when': ret - blue.os.GetWallclockTime()})
        self.UpdateSlot(charID)

    def UndoTermination(self, charID, *args):
        sm.RemoteSvc('charUnboundMgr').CancelCharacterDeletePrepare(charID)
        self.UpdateSlot(charID)

    def UpdateSlot(self, charID):
        self.GetCharacterSelectionData(force=True)
        slot = self.slotsByCharID.get(charID, None)
        if slot:
            characterDetails = self.GetCharacterSelectionData().GetCharInfo(charID)
            slot.RefreshCharacterDetails(characterDetails)
            slot.SetDeleteUI()
        else:
            self.OnRefreshScreen()

    def DisplayAd(self):
        if self.currentAdInfo == -1:
            self.showAd = False
        if not self.showAd:
            self.adSpriteContainer.state = uiconst.UI_HIDDEN
            return
        if self.currentAdInfo is None:
            uthread.new(self.FetchAdInfo_thread)
        elif not self.adImageFetched:
            uthread.new(self.LoadAd, inThread=True)
        else:
            self.LoadAd()

    def FetchAdInfo_thread(self):
        adInfo = self.GetAdToDisplay()
        self.currentAdInfo = adInfo
        self.LoadAd(inThread=True)

    def LoadAd(self, inThread = False):
        if self.currentAdInfo == -1:
            self.showAd = False
            self.adSpriteContainer.state = uiconst.UI_HIDDEN
            return
        with ExceptionEater('Failed to load ad'):
            self.OpenAd(self.currentAdInfo, inThread=inThread)

    def GetAdToDisplay(self):
        try:
            targetedAds, nonTargetedAds = self.FindAvailableAds()
        except Exception as e:
            log.LogError('Failed to fetch ads, e = ', e)
            return -1

        ads = targetedAds + nonTargetedAds
        for ad in ads:
            didShowAd = settings.public.ui.Get('CSS_AdAlreadyDisplayed_%s' % ad.adID, False)
            if not didShowAd:
                return ad

        return -1

    def FindAvailableAds(self):
        adUrl = csUtil.GetCharacterSelectionAdPageUrl(session.languageID)
        feed = corebrowserutil.GetStringFromURL(adUrl).read()
        root = ET.fromstring(feed)
        namespaces = csUtil.xmlNamespaces
        itemlist = root.findall('atom:entry', namespaces=namespaces)
        targetedAds = []
        nonTargetedAds = []
        if session.userType == const.userTypeTrial:
            target = csUtil.adTrialTerm
        else:
            charData = self.GetCharacterSelectionData()
            creationDate = charData.GetUserCreationDate()
            now = blue.os.GetWallclockTime()
            if now - 6 * const.MONTH30 < creationDate:
                target = csUtil.adMediumTerm
            else:
                target = csUtil.adAdvancedTerm
        for eachItem in itemlist:
            with ExceptionEater('Failed to parse ad'):
                imageEntry = eachItem.find('ccpmedia:group/ccpmedia:content', namespaces=namespaces)
                linkEntry = eachItem.find('ccpmedia:group/ccpmedia:description', namespaces=namespaces)
                adID = eachItem.find('atom:id', namespaces=namespaces).text
                link = linkEntry.text
                imageUrl = imageEntry.attrib['url']
                imageWidth = imageEntry.attrib['width']
                imageHeight = imageEntry.attrib['height']
                adInfo = uiutil.Bunch(link=link, imageUrl=imageUrl, width=int(imageWidth), height=int(imageHeight), adID=adID)
                if eachItem.find("atom:category[@term='%s']" % target, namespaces=namespaces) is not None:
                    targetedAds.append(adInfo)
                elif eachItem.find('atom:category', namespaces=namespaces) is None:
                    nonTargetedAds.append(adInfo)

        return (targetedAds, nonTargetedAds)

    def OpenAd(self, adInfo, inThread = False):
        tex, w, h = sm.GetService('photo').GetTextureFromURL(adInfo.imageUrl)
        adImageFetched = True
        if tex.resPath == NONE_PATH:
            log.LogError('Did not get a valid image for the character selection screen ad')
            return
        self.adSprint.texture = tex
        self.adSprint.url = adInfo.link
        self.adSprint.OnClick = (self.ClickAd, adInfo.link)
        self.openStoreContainer.align = uiconst.CENTERLEFT
        settings.public.ui.Set('CSS_AdAlreadyDisplayed_%s' % adInfo.adID, True)

    def CloseAd(self):
        uicore.animations.FadeOut(self.adSpriteContainer, duration=0.5, sleep=True)
        self.adSpriteContainer.display = False
        self.showAd = False

    def ClickAd(self, url):
        if url.startswith(('https://', 'http://')):
            uthread.new(self.ClickURL, url)
        else:
            log.LogError('Not valid ad path, no ad displayed. Path = ', url)

    def ClickURL(self, url, *args):
        blue.os.ShellExecute(url)

    def ShowLoading(self, forceOn = 0):
        try:
            self.loadingWheel.forcedOn = forceOn
            self.loadingWheel.Show()
        except:
            log.LogError('Failed to show the loading wheel')

    def HideLoading(self, forceOff = 0):
        try:
            if not self.loadingWheel.forcedOn or forceOff:
                self.loadingWheel.Hide()
                self.loadingWheel.forcedOn = 0
        except:
            log.LogError('Failed to hide the loading wheel')


@Component(ButtonEffect(opacityIdle=0.0, opacityHover=0.4, opacityMouseDown=0.5, bgElementFunc=lambda parent, _: parent.highlight))

class OpenStoreButton(Container):
    default_name = 'OpenStoreButton'
    default_width = 270
    default_height = 90
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        Sprite(name='Logo', bgParent=self, texturePath='res:/UI/Texture/Vgs/storeLogo.png', align=uiconst.CENTER)
        self.highlight = Sprite(name='Highlight', bgParent=self, texturePath='res:/UI/Texture/Vgs/storeLogoGlow.png', align=uiconst.CENTER)
        self.onClick = attributes.onClick

    def OnClick(self):
        self.onClick()
