#Embedded file name: eve/client/script/ui/shared\activatePlex.py
import carbonui.const as uiconst
from carbonui.primitives.container import Container
import localization
import uiprimitives
import uicontrols
import uix
import uthread
import blue
import functools
import util
import math
import searchUtil
from carbonui.primitives.gradientSprite import GradientSprite
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.control.searchinput import SearchInput
from eve.client.script.ui.control.buttons import ButtonIcon

class ActivatePlexWindow(uicontrols.Window):
    """
    Modal window opened by right clicking a PLEX. This presents the choices available
    when activating a PLEX, either to extend the current account subscription or
    adding additional character training queues.
    """
    __guid__ = 'form.ActivatePlexWindow'
    default_width = 420
    default_height = 100
    default_windowID = 'ActivatePlexWindow'
    default_topParentHeight = 0
    default_clipChildren = True
    default_isPinable = False
    LINE_COLOR = (1,
     1,
     1,
     0.2)
    BLUE_COLOR = (0.0,
     0.54,
     0.8,
     1.0)
    GRAY_COLOR = util.Color.GRAY5
    WHITE_COLOR = util.Color.WHITE
    CONFIRM_DELAY = 3000

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.MakeUnMinimizable()
        self.itemID = attributes['itemID']
        self.reloading = False
        self.confirmed = False
        self.highlight = None
        self.expireDate2 = None
        self.expireDate3 = None
        self.selectedEntry = None
        uthread.new(self.InitAll)

    def InitAll(self):
        self.Layout()
        self.Reload()
        uthread.new(self.UpdateTimersThread)

    def Layout(self):
        """
        Setup UI controls for this window.
        """
        self.HideHeader()
        self.MakeUnResizeable()
        self.container = uicontrols.ContainerAutoSize(parent=self.GetMainArea(), align=uiconst.TOTOP, alignMode=uiconst.TOTOP, state=uiconst.UI_PICKCHILDREN, padding=(15, 15, 15, 0), callback=self.OnContainerResized, opacity=0.0)
        uicontrols.EveLabelLargeBold(parent=self.container, align=uiconst.TOTOP, text=localization.GetByLabel('UI/ActivatePlex/ActivateHeading'))
        uicontrols.EveLabelMedium(parent=self.container, align=uiconst.TOTOP, text=localization.GetByLabel('UI/ActivatePlex/ActivateDescription'), color=self.GRAY_COLOR, padding=(0, 5, 0, 10))
        uiprimitives.Line(parent=self.container, align=uiconst.TOTOP, color=self.LINE_COLOR)
        slot1 = uicontrols.ContainerAutoSize(parent=self.container, align=uiconst.TOTOP, alignMode=uiconst.TOTOP, state=uiconst.UI_PICKCHILDREN, bgColor=(0, 0, 0, 0.3))
        self.slot1Background = uiprimitives.Fill(parent=slot1, color=self.BLUE_COLOR, opacity=0.0)
        self.slot1Title = uicontrols.EveLabelMediumBold(parent=slot1, align=uiconst.TOTOP, text=localization.GetByLabel('UI/ActivatePlex/GameTime'), padding=(60, 12, 140, 0), color=self.BLUE_COLOR)
        self.slot1Expiry = uicontrols.EveLabelMediumBold(parent=slot1, align=uiconst.TOTOP, text='', padding=(60, 0, 140, 10), color=self.GRAY_COLOR)
        self.slot1Button = uicontrols.Button(parent=slot1, label='', align=uiconst.CENTERRIGHT, fontsize=13, fixedwidth=120, fixedheight=30, pos=(10, 0, 0, 0))
        self.slot1Icon = Sprite(parent=slot1, texturePath='res:/UI/Texture/classes/CharacterSelection/plex_timer.png', align=uiconst.CENTERLEFT, pos=(15, 0, 32, 32))
        uiprimitives.Line(parent=self.container, align=uiconst.TOTOP, color=self.LINE_COLOR)
        slot2 = uicontrols.ContainerAutoSize(parent=self.container, align=uiconst.TOTOP, alignMode=uiconst.TOTOP, state=uiconst.UI_PICKCHILDREN, bgColor=(0, 0, 0, 0.3))
        self.slot2Background = uiprimitives.Fill(parent=slot2, color=self.BLUE_COLOR, opacity=0.0)
        self.slot2Title = uicontrols.EveLabelMediumBold(parent=slot2, align=uiconst.TOTOP, text='', padding=(60, 12, 140, 0), color=self.WHITE_COLOR)
        self.slot2Expiry = uicontrols.EveLabelMediumBold(parent=slot2, align=uiconst.TOTOP, text='', padding=(60, 0, 140, 10), color=self.GRAY_COLOR)
        self.slot2Button = uicontrols.Button(parent=slot2, label='', align=uiconst.CENTERRIGHT, fontsize=13, fixedwidth=120, fixedheight=30, pos=(10, 0, 0, 0))
        self.slot2Icon = Sprite(parent=slot2, texturePath='res:/UI/Texture/Icons/add_training_queue.png', align=uiconst.CENTERLEFT, pos=(15, 0, 32, 32))
        uiprimitives.Line(parent=self.container, align=uiconst.TOTOP, color=self.LINE_COLOR)
        slot3 = uicontrols.ContainerAutoSize(parent=self.container, align=uiconst.TOTOP, alignMode=uiconst.TOTOP, state=uiconst.UI_PICKCHILDREN, bgColor=(0, 0, 0, 0.3))
        self.slot3Background = uiprimitives.Fill(parent=slot3, color=self.BLUE_COLOR, opacity=0.0)
        self.slot3Title = uicontrols.EveLabelMediumBold(parent=slot3, align=uiconst.TOTOP, text='', padding=(60, 12, 140, 0), color=self.WHITE_COLOR)
        self.slot3Expiry = uicontrols.EveLabelMediumBold(parent=slot3, align=uiconst.TOTOP, text='', padding=(60, 0, 140, 10), color=self.GRAY_COLOR)
        self.slot3Button = uicontrols.Button(parent=slot3, label='', align=uiconst.CENTERRIGHT, fontsize=13, fixedwidth=120, fixedheight=30, pos=(10, 0, 0, 0))
        self.slot3Icon = Sprite(parent=slot3, texturePath='res:/UI/Texture/Icons/add_training_queue.png', align=uiconst.CENTERLEFT, pos=(15, 0, 32, 32))
        uiprimitives.Line(parent=self.container, align=uiconst.TOTOP, color=self.LINE_COLOR)
        slot4 = Container(parent=self.container, align=uiconst.TOTOP, alignMode=uiconst.TOTOP, state=uiconst.UI_PICKCHILDREN, bgColor=(0, 0, 0, 0.3), height=70)
        self.slot4Background = uiprimitives.Fill(parent=slot4, color=self.BLUE_COLOR, opacity=0.0)
        self.slot4Title = uicontrols.EveLabelMediumBold(parent=slot4, align=uiconst.TOTOP, text=localization.GetByLabel('UI/ActivatePlex/Donate'), padding=(60, 12, 140, 0), color=self.BLUE_COLOR)
        self.slot4Edit = SearchInput(parent=slot4, align=uiconst.TOTOP, padding=(60, 0, 140, 10), height=18, color=self.GRAY_COLOR, GetSearchEntries=self.Search, OnSearchEntrySelected=self.OnSearchEntrySelected, hinttext=localization.GetByLabel('UI/ActivatePlex/SearchHint'))
        self.slot4Edit.SetHistoryVisibility(False)
        self.entryContainer = Container(parent=slot4, align=uiconst.TOTOP, state=uiconst.UI_PICKCHILDREN, padding=(60, 0, 140, 10), height=32, bgColor=(0, 0, 0, 0.3))
        self.entryContainer.display = False
        self.slot4Button = uicontrols.Button(parent=slot4, label='', align=uiconst.CENTERRIGHT, fontsize=13, fixedwidth=120, fixedheight=30, pos=(10, 0, 0, 0))
        self.slot4Button.Disable()
        self.slot4Icon = Sprite(parent=slot4, texturePath='res:/UI/Texture/classes/CharacterSelection/plex_timer.png', align=uiconst.CENTERLEFT, pos=(15, 0, 32, 32))
        self.entryContainerIcon = Sprite(parent=self.entryContainer, texturePath='', align=uiconst.CENTERLEFT, pos=(0, 0, 32, 32))
        clipContainer = Container(parent=self.entryContainer, clipChildren=True, padding=(40, 0, 36, 0))
        self.entryContainerTitle = uicontrols.EveLabelMediumBold(parent=clipContainer, align=uiconst.CENTERLEFT, text='', width=150)
        self.entryContainerButton = uicontrols.ButtonIcon(parent=self.entryContainer, texturePath='res:/UI/Texture/Icons/73_16_210.png', align=uiconst.TOPRIGHT, func=self.ResetSearch, width=16, height=16, iconSize=16)
        uiprimitives.Line(parent=self.container, align=uiconst.TOTOP, color=self.LINE_COLOR)
        self.closeButton = uicontrols.Button(parent=self.container, label='', func=self.Close, align=uiconst.TOTOP, fontsize=13, padding=(120, 10, 120, 30))
        uicore.animations.FadeTo(self.container, startVal=0.0, endVal=1.0, duration=0.5)

    def OnSearchEntrySelected(self, result, *args, **kwargs):
        owner = result[0].info
        self.selectedEntry = owner.ownerID
        self.entryContainerIcon.texturePath = sm.GetService('photo').GetPortrait(owner.ownerID, 64)
        self.entryContainerTitle.text = cfg.eveowners.Get(owner.ownerID).ownerName
        self.slot4Edit.SetValue('')
        self.slot4Edit.display = False
        self.slot4Button.SetHint(localization.GetByLabel('UI/ActivatePlex/DonateButtonHint', charactername=cfg.eveowners.Get(owner.ownerID).ownerName))
        self.slot4Button.Enable()
        self.entryContainer.display = True
        self.DisableButtons(donate=False)

    def ResetSearch(self, *args, **kwargs):
        self.selectedEntry = None
        self.slot4Edit.display = True
        self.entryContainer.display = False
        self.slot4Button.SetHint('')
        self.slot4Button.Disable()
        uicore.registry.SetFocus(self.slot4Edit)
        self.EnableButtons(donate=False)

    def Search(self, searchString):
        if len(searchString) < 3:
            return []
        else:
            return searchUtil.SearchCharacters(searchString)

    def Reload(self, delay = 0, force = False):
        """
        Refetch data and update the state of the window.
        """
        try:
            self.reloading = True
            blue.pyos.synchro.SleepWallclock(delay)
            if self.destroyed:
                return
            daysLeft = sm.GetService('charactersheet').GetSubscriptionDays(force)
            queues = sm.GetService('skillqueue').GetMultipleCharacterTraining(force).items()
            if daysLeft:
                self.slot1Expiry.text = localization.GetByLabel('UI/ActivatePlex/Expires', expiryDate=blue.os.GetWallclockTime() + daysLeft * const.DAY)
                self.slot1Button.SetHint(localization.GetByLabel('UI/ActivatePlex/AddHint', expiryDate=blue.os.GetWallclockTime() + (daysLeft + 30) * const.DAY))
            else:
                self.slot1Expiry.text = localization.GetByLabel('UI/ActivatePlex/ExpiresNever')
            self.slot1Button.SetLabel(localization.GetByLabel('UI/ActivatePlex/Add'))
            self.slot1Button.func = functools.partial(self.OnConfirmButton, self.slot1Button, self.OnAddTime)
            if len(queues) < 1:
                self.expireDate2 = None
                self.slot2Title.text = localization.GetByLabel('UI/ActivatePlex/AdditionalQueueNotActive')
                self.slot2Title.color = self.GRAY_COLOR
                self.slot2Icon.opacity = 0.3
                self.slot2Button.SetLabel(localization.GetByLabel('UI/ActivatePlex/Activate'))
                self.slot2Button.SetHint(localization.GetByLabel('UI/ActivatePlex/ActivateHint', expiryDate=blue.os.GetWallclockTime() + 30 * const.DAY))
                self.slot2Button.func = functools.partial(self.OnConfirmButton, self.slot2Button, self.OnAddQueue, 2, None)
            if len(queues) < 2:
                self.expireDate3 = None
                self.slot3Title.text = localization.GetByLabel('UI/ActivatePlex/AdditionalQueueNotActive')
                self.slot3Title.color = self.GRAY_COLOR
                self.slot3Icon.opacity = 0.3
                self.slot3Button.SetLabel(localization.GetByLabel('UI/ActivatePlex/Activate'))
                self.slot3Button.SetHint(localization.GetByLabel('UI/ActivatePlex/ActivateHint', expiryDate=blue.os.GetWallclockTime() + 30 * const.DAY))
                self.slot3Button.func = functools.partial(self.OnConfirmButton, self.slot3Button, self.OnAddQueue, 3, None)
            for index, (trainingID, trainingExpiry) in enumerate(sorted(queues)):
                if index == 0:
                    self.expireDate2 = trainingExpiry
                    self.slot2Title.text = localization.GetByLabel('UI/ActivatePlex/AdditionalQueueActive')
                    self.slot2Title.color = self.BLUE_COLOR
                    self.slot2Icon.opacity = 1.0
                    self.slot2Button.SetLabel(localization.GetByLabel('UI/ActivatePlex/Extend'))
                    self.slot2Button.SetHint(localization.GetByLabel('UI/ActivatePlex/ExtendHint', expiryDate=trainingExpiry + 30 * const.DAY))
                    self.slot2Button.func = functools.partial(self.OnConfirmButton, self.slot2Button, self.OnAddQueue, 2, trainingID)
                elif index == 1:
                    self.expireDate3 = trainingExpiry
                    self.slot3Title.text = localization.GetByLabel('UI/ActivatePlex/AdditionalQueueActive')
                    self.slot3Title.color = self.BLUE_COLOR
                    self.slot3Icon.opacity = 1.0
                    self.slot3Button.SetLabel(localization.GetByLabel('UI/ActivatePlex/Extend'))
                    self.slot3Button.SetHint(localization.GetByLabel('UI/ActivatePlex/ExtendHint', expiryDate=trainingExpiry + 30 * const.DAY))
                    self.slot3Button.func = functools.partial(self.OnConfirmButton, self.slot3Button, self.OnAddQueue, 3, trainingID)

            self.slot4Button.func = functools.partial(self.OnConfirmButton, self.slot4Button, self.OnDonate)
            self.slot4Button.SetLabel(localization.GetByLabel('UI/ActivatePlex/DonateHint'))
            for btn in (self.slot1Button,
             self.slot2Button,
             self.slot3Button,
             self.slot4Button):
                btn.SetColor(None)

            self.EnableButtons()
            if len(queues) == 0:
                self.slot3Button.Disable()
            if self.selectedEntry is None:
                self.slot4Button.Disable()
            else:
                self.slot1Button.Disable()
                self.slot2Button.Disable()
                self.slot3Button.Disable()
            if self.confirmed:
                self.slot1Button.state = uiconst.UI_HIDDEN
                self.slot2Button.state = uiconst.UI_HIDDEN
                self.slot3Button.state = uiconst.UI_HIDDEN
                self.slot4Button.state = uiconst.UI_HIDDEN
                self.closeButton.SetLabel(localization.GetByLabel('UI/Generic/OK'))
            else:
                self.slot1Button.state = uiconst.UI_NORMAL
                self.slot2Button.state = uiconst.UI_NORMAL
                self.slot3Button.state = uiconst.UI_NORMAL
                self.slot4Button.state = uiconst.UI_NORMAL
                self.closeButton.SetLabel(localization.GetByLabel('UI/Generic/Cancel'))
            if self.highlight == 1:
                uicore.animations.FadeTo(self.slot1Background, self.slot3Background.opacity, 0.1, duration=0.3)
                self.closeButton.Blink(blinks=1)
                self.highlight = None
            elif self.highlight == 2:
                uicore.animations.FadeTo(self.slot2Background, self.slot3Background.opacity, 0.1, duration=0.3)
                self.closeButton.Blink(blinks=1)
                self.highlight = None
            elif self.highlight == 3:
                uicore.animations.FadeTo(self.slot3Background, self.slot3Background.opacity, 0.1, duration=0.3)
                self.closeButton.Blink(blinks=1)
                self.highlight = None
            self.UpdateTimers()
        finally:
            self.reloading = False

    def UpdateTimersThread(self):
        """
        Thread which runs and updates any countdown timers.
        """
        while not self.destroyed:
            blue.pyos.synchro.SleepWallclock(1000)
            self.UpdateTimers()

    def UpdateTimers(self):
        """
        The reload method will set expireDate2 and expireDate3 to indicate whether we should be counting down.
        """
        if self.expireDate2:
            timeRemaining = localization.formatters.FormatTimeIntervalShortWritten(self.expireDate2 - blue.os.GetWallclockTime(), showFrom='day', showTo='second')
            self.slot2Expiry.text = localization.GetByLabel('UI/ActivatePlex/Ends', timeRemaining=timeRemaining)
        else:
            self.slot2Expiry.text = ''
        if self.expireDate3:
            timeRemaining = localization.formatters.FormatTimeIntervalShortWritten(self.expireDate3 - blue.os.GetWallclockTime(), showFrom='day', showTo='second')
            self.slot3Expiry.text = localization.GetByLabel('UI/ActivatePlex/Ends', timeRemaining=timeRemaining)
        else:
            self.slot3Expiry.text = ''

    def OnContainerResized(self):
        """
        Callback for the parent auto resized container, we set the overall window height
        to fit the contents of the resizeable container here. This allows localized text
        to wrap around and push out the height of this window.
        """
        self.height = self.container.height

    def OnConfirmButton(self, button, *args):
        """
        Click handler for a button that modifies the visual state to wait for
        a second confirmation click.
        """
        if not self.reloading:
            self.DisableButtons()
            button.Enable()
            button.func = functools.partial(*args[:-1])
            button.SetLabel(localization.GetByLabel('UI/ActivatePlex/Confirm'))
            button.SetColor(self.BLUE_COLOR)
            self.Reload(self.CONFIRM_DELAY)

    def DisableButtons(self, donate = True):
        """
        Disables all of the slot buttons.
        """
        self.slot1Button.Disable()
        self.slot2Button.Disable()
        self.slot3Button.Disable()
        if donate:
            self.slot4Button.Disable()

    def EnableButtons(self, donate = True):
        """
        Re-enables all of the slot buttons.
        """
        self.slot1Button.Enable()
        self.slot2Button.Enable()
        self.slot3Button.Enable()
        if donate:
            self.slot4Button.Enable()

    def OnAddTime(self, button):
        """
        Add 30 days of game time to an existing account subscription.
        """
        if not self.confirmed:
            self.confirmed = True
            self.highlight = 1
            self.Reload()
            try:
                sm.RemoteSvc('userSvc').ApplyPilotLicence(self.itemID)
                self.Reload(force=True)
            except UserError:
                self.Close()
                raise

    def OnAddQueue(self, slot, trainingID, button):
        """
        Activae or extend the time on an existing multiple character training queue.
        """
        if not self.confirmed:
            self.confirmed = True
            self.highlight = slot
            self.Reload()
            try:
                sm.RemoteSvc('userSvc').ApplyMultiCharactersTrainingSlot(self.itemID, trainingID=trainingID)
                self.Reload(force=True)
            except UserError:
                self.Close()
                raise

    def OnDonate(self, *args, **kwargs):
        """
        Donate 30 days of game time to an account subscription.
        """
        if not self.confirmed and self.selectedEntry:
            self.confirmed = True
            self.Reload()
            try:
                sm.RemoteSvc('userSvc').ApplyPilotLicence(self.itemID, applyOnCharacterID=self.selectedEntry)
                self.ResetSearch()
            except UserError:
                self.Close()
                raise
