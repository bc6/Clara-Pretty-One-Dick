#Embedded file name: eve/client/script/ui/shared\activateMultiTraining.py
import blue
import functools
import localization
import math
import uthread
import util
import carbonui.const as uiconst
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.fill import Fill
from carbonui.primitives.gradientSprite import GradientSprite
from carbonui.primitives.line import Line
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.control.buttons import Button
from eve.client.script.ui.control.eveLabel import EveLabelLargeBold, EveLabelMedium, EveLabelMediumBold
from eve.client.script.ui.control.eveWindow import Window
from eve.client.script.ui.control.eveWindowUnderlay import RaisedUnderlay

class ActivateMultiTrainingWindow(Window):
    """
    """
    __guid__ = 'form.ActivateMultiTrainingWindow'
    default_width = 420
    default_heigt = 100
    default_windowID = 'ActivateMultiTrainingWindow'
    default_topParentHeight = 0
    default_clipChildren = True
    default_isPinable = False
    GRAY_COLOR = util.Color.GRAY5
    GREEN_COLOR = (0.0, 1.0, 0.0, 0.8)
    LINE_COLOR = (1, 1, 1, 0.2)
    WHITE_COLOR = util.Color.WHITE
    CONFIRM_DELAY = 3000

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.itemID = attributes['itemID']
        self.expireDate1 = None
        self.expireDate2 = None
        self.reloading = False
        self.confirmed = False
        self.highlight = None
        self.Layout()
        self.Reload()
        uthread.new(self.UpdateTimersThread)

    def Layout(self):
        self.HideHeader()
        self.MakeUnResizeable()
        self.container = ContainerAutoSize(parent=self.GetMainArea(), align=uiconst.TOTOP, alignMode=uiconst.TOTOP, state=uiconst.UI_PICKCHILDREN, padding=(15, 15, 15, 0), callback=self.OnContainerResized)
        EveLabelLargeBold(parent=self.container, align=uiconst.TOTOP, text=localization.GetByLabel('UI/ActivateMultiTraining/ActivateHeading'))
        EveLabelMedium(parent=self.container, align=uiconst.TOTOP, text=localization.GetByLabel('UI/ActivateMultiTraining/ActivateDescription'), color=self.GRAY_COLOR, padding=(0, 5, 0, 10))
        Line(parent=self.container, align=uiconst.TOTOP, color=self.LINE_COLOR)
        slot1 = ContainerAutoSize(parent=self.container, align=uiconst.TOTOP, alignMode=uiconst.TOTOP, state=uiconst.UI_PICKCHILDREN, bgColor=(0, 0, 0, 0.3))
        self.slot1Background = Fill(parent=slot1, color=self.GREEN_COLOR, opacity=0.0)
        self.slot1Title = EveLabelMediumBold(parent=slot1, align=uiconst.TOTOP, text='', padding=(60, 12, 140, 0), color=self.WHITE_COLOR)
        self.slot1Expiry = EveLabelMediumBold(parent=slot1, align=uiconst.TOTOP, text='', padding=(60, 0, 140, 10), color=self.GRAY_COLOR)
        self.slot1Button = Button(parent=slot1, label='', align=uiconst.CENTERRIGHT, fontsize=13, fixedwidth=120, fixedheight=30, pos=(10, 0, 0, 0))
        self.slot1Button.confirmHilite = GradientSprite(bgParent=self.slot1Button, rotation=-math.pi / 2, rgbData=[(0, self.GREEN_COLOR[:3])], alphaData=[(0, 0.5), (0.3, 0.2), (0.6, 0.14)], opacity=0.0)
        self.slot1Icon = Sprite(parent=slot1, texturePath='res:/UI/Texture/Icons/add_training_queue.png', align=uiconst.CENTERLEFT, pos=(15, 0, 32, 32))
        Line(parent=self.container, align=uiconst.TOTOP, color=self.LINE_COLOR)
        slot2 = ContainerAutoSize(parent=self.container, align=uiconst.TOTOP, alignMode=uiconst.TOTOP, state=uiconst.UI_PICKCHILDREN, bgColor=(0, 0, 0, 0.3))
        self.slot2Background = Fill(parent=slot2, color=self.GREEN_COLOR, opacity=0.0)
        self.slot2Title = EveLabelMediumBold(parent=slot2, align=uiconst.TOTOP, text='', padding=(60, 12, 140, 0), color=self.WHITE_COLOR)
        self.slot2Expiry = EveLabelMediumBold(parent=slot2, align=uiconst.TOTOP, text='', padding=(60, 0, 140, 10), color=self.GRAY_COLOR)
        self.slot2Button = Button(parent=slot2, label='', align=uiconst.CENTERRIGHT, fontsize=13, fixedwidth=120, fixedheight=30, pos=(10, 0, 0, 0))
        self.slot2Button.confirmHilite = GradientSprite(bgParent=self.slot2Button, rotation=-math.pi / 2, rgbData=[(0, self.GREEN_COLOR[:3])], alphaData=[(0, 0.5), (0.3, 0.2), (0.6, 0.14)], opacity=0.0)
        self.slot2Icon = Sprite(parent=slot2, texturePath='res:/UI/Texture/Icons/add_training_queue.png', align=uiconst.CENTERLEFT, pos=(15, 0, 32, 32))
        Line(parent=self.container, align=uiconst.TOTOP, color=self.LINE_COLOR)
        self.closeButton = Button(parent=self.container, label=localization.GetByLabel('UI/Generic/Cancel'), func=self.Close, align=uiconst.TOTOP, fontsize=13, padding=(120, 10, 120, 30))

    def Reload(self, delay = 0, force = False):
        try:
            self.reloading = True
            blue.pyos.synchro.SleepWallclock(delay)
            if self.destroyed:
                return
            queues = sm.GetService('skillqueue').GetMultipleCharacterTraining(force).items()
            if len(queues) < 1:
                self.expireDate1 = None
                self.slot1Title.text = localization.GetByLabel('UI/ActivateMultiTraining/AdditionalQueueNotActive')
                self.slot1Title.color = self.GRAY_COLOR
                self.slot1Icon.opacity = 0.3
                self.slot1Button.SetLabel(localization.GetByLabel('UI/ActivateMultiTraining/Activate'))
                self.slot1Button.SetHint(localization.GetByLabel('UI/ActivateMultiTraining/ActivateHint', expiryDate=blue.os.GetWallclockTime() + 30 * const.DAY))
                self.slot1Button.func = functools.partial(self.OnConfirmButton, self.slot1Button, self.OnAddQueue, 2, None)
            if len(queues) < 2:
                self.expireDate2 = None
                self.slot2Title.text = localization.GetByLabel('UI/ActivateMultiTraining/AdditionalQueueNotActive')
                self.slot2Title.color = self.GRAY_COLOR
                self.slot2Icon.opacity = 0.3
                self.slot2Button.SetLabel(localization.GetByLabel('UI/ActivateMultiTraining/Activate'))
                self.slot2Button.SetHint(localization.GetByLabel('UI/ActivateMultiTraining/ActivateHint', expiryDate=blue.os.GetWallclockTime() + 30 * const.DAY))
                self.slot2Button.func = functools.partial(self.OnConfirmButton, self.slot2Button, self.OnAddQueue, 3, None)
            for index, (trainingID, trainingExpiry) in enumerate(sorted(queues)):
                if index == 0:
                    self.expireDate1 = trainingExpiry
                    self.slot1Title.text = localization.GetByLabel('UI/ActivateMultiTraining/AdditionalQueueActive')
                    self.slot1Title.color = self.GREEN_COLOR
                    self.slot1Icon.opacity = 1.0
                    self.slot1Button.SetLabel(localization.GetByLabel('UI/ActivateMultiTraining/Extend'))
                    self.slot1Button.SetHint(localization.GetByLabel('UI/ActivateMultiTraining/ExtendHint', expiryDate=trainingExpiry + 30 * const.DAY))
                    self.slot1Button.func = functools.partial(self.OnConfirmButton, self.slot1Button, self.OnAddQueue, 1, trainingID)
                elif index == 1:
                    self.expireDate2 = trainingExpiry
                    self.slot2Title.text = localization.GetByLabel('UI/ActivateMultiTraining/AdditionalQueueActive')
                    self.slot2Title.color = self.GREEN_COLOR
                    self.slot2Icon.opacity = 1.0
                    self.slot2Button.SetLabel(localization.GetByLabel('UI/ActivateMultiTraining/Extend'))
                    self.slot2Button.SetHint(localization.GetByLabel('UI/ActivateMultiTraining/ExtendHint', expiryDate=trainingExpiry + 30 * const.DAY))
                    self.slot2Button.func = functools.partial(self.OnConfirmButton, self.slot2Button, self.OnAddQueue, 2, trainingID)

            uicore.animations.FadeTo(self.slot1Button.confirmHilite, self.slot1Button.confirmHilite.opacity, 0.0, duration=0.3)
            uicore.animations.FadeTo(self.slot2Button.confirmHilite, self.slot2Button.confirmHilite.opacity, 0.0, duration=0.3)
            self.EnableButtons()
            if len(queues) == 0:
                self.slot2Button.Disable()
            if self.confirmed:
                self.slot1Button.state = uiconst.UI_HIDDEN
                self.slot2Button.state = uiconst.UI_HIDDEN
                self.closeButton.SetLabel(localization.GetByLabel('UI/Generic/OK'))
            else:
                self.slot1Button.state = uiconst.UI_NORMAL
                self.slot2Button.state = uiconst.UI_NORMAL
                self.closeButton.SetLabel(localization.GetByLabel('UI/Generic/Cancel'))
            if self.highlight == 1:
                uicore.animations.FadeTo(self.slot1Background, self.slot1Background.opacity, 0.1, duration=0.3)
                self.closeButton.Blink(blinks=1)
                self.highlight = None
            elif self.highlight == 2:
                uicore.animations.FadeTo(self.slot2Background, self.slot2Background.opacity, 0.1, duration=0.3)
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
            button.SetLabel(localization.GetByLabel('UI/ActivateMultiTraining/Confirm'))
            uicore.animations.FadeTo(button.confirmHilite, button.confirmHilite.opacity, 1.0, duration=0.3)
            self.Reload(self.CONFIRM_DELAY)

    def OnAddQueue(self, slot, trainingID, button):
        """
        Activae or extend the time on an existing multiple character training queue.
        """
        if not self.confirmed:
            self.confirmed = True
            self.highlight = slot
            self.Reload()
            try:
                sm.RemoteSvc('userSvc').ActivateMultiTraining(self.itemID, trainingID=trainingID)
                self.Reload(force=True)
            except UserError:
                self.Close()
                raise

    def UpdateTimers(self):
        """
        The reload method will set expireDate1 and expireDate2 to indicate whether we should be counting down.
        """
        if self.expireDate1:
            timeRemaining = localization.formatters.FormatTimeIntervalShortWritten(self.expireDate1 - blue.os.GetWallclockTime(), showFrom='day', showTo='second')
            self.slot1Expiry.text = localization.GetByLabel('UI/ActivateMultiTraining/Ends', timeRemaining=timeRemaining)
        else:
            self.slot1Expiry.text = ''
        if self.expireDate2:
            timeRemaining = localization.formatters.FormatTimeIntervalShortWritten(self.expireDate2 - blue.os.GetWallclockTime(), showFrom='day', showTo='second')
            self.slot2Expiry.text = localization.GetByLabel('UI/ActivateMultiTraining/Ends', timeRemaining=timeRemaining)
        else:
            self.slot2Expiry.text = ''

    def DisableButtons(self):
        """
        Disables all of the slot buttons.
        """
        self.slot1Button.Disable()
        self.slot2Button.Disable()

    def EnableButtons(self):
        """
        Enables all the slot buttons.
        """
        self.slot1Button.Enable()
        self.slot2Button.Enable()
