#Embedded file name: eve/client/script/ui/login/charSelection\timeLeftCounters.py
"""
    This file contains the subscription counters on the character selection screen
"""
import uicontrols
import uiprimitives
import carbonui.const as uiconst
import localization
import blue
from carbonui.util.various_unsorted import IsUnder
from carbonui.primitives.container import Container
import eve.client.script.ui.login.charSelection.characterSelectionUtils as csUtil
import eve.client.script.ui.login.charSelection.characterSelectionColors as csColors

class CountDownCont(Container):
    """
        This is a container that holds all the subscription counters (subscription, 2nd/3rd character, trial)
    """

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.subscriptionTimers = attributes.timers
        self.subTimeEnd = self.subscriptionTimers.subscriptionEndTime
        self.trainingEndTimes = self.subscriptionTimers.trainingEndTimes
        uiprimitives.Fill(bgParent=self, color=csColors.SUBSCRIPTION_BORDER_FILL)
        if session.userType == const.userTypeTrial:
            if not self.subTimeEnd:
                return
            iconPath = 'res:/UI/Texture/classes/CharacterSelection/trial_timer.png'
            timer = CountDownTimer(parent=self, endTime=self.subTimeEnd, iconPath=iconPath, callback=self.GoToAccountMgmt, hintMessage='UI/CharacterSelection/TrialExpiryHint', addButton=True, btnText=localization.GetByLabel('UI/CharacterSelection/SubscribeToEve'))
        else:
            if self.subTimeEnd:
                iconPath = 'res:/UI/Texture/classes/CharacterSelection/plex_timer.png'
                timer = CountDownTimer(parent=self, endTime=self.subTimeEnd, iconPath=iconPath, callback=self.GoToAccountMgmt, hintMessage='UI/CharacterSelection/SubscriptionExpiryHint')
            if self.trainingEndTimes:
                trainingSlotNumber = 2
                iconPath = 'res:/UI/Texture/classes/CharacterSelection/skillbook_timer.png'
                for endTime in self.trainingEndTimes:
                    hintMessage = 'UI/CharacterSelection/QueueExpiryHint%d' % trainingSlotNumber
                    timer = CountDownTimer(parent=self, endTime=endTime.trainingEnds, iconPath=iconPath, callback=self.GoToAccountMgmt, hintMessage=hintMessage)
                    trainingSlotNumber += 1

    def GoToAccountMgmt(self, *args):
        uicore.cmd.OpenAccountManagement()


class CountDownTimer(Container):
    """
        this is a counter for each type of subscription
    """
    default_align = uiconst.TOLEFT
    default_state = uiconst.UI_NORMAL
    default_width = 72
    default_height = 64
    default_padLeft = 4
    default_padTop = 4
    default_padBottom = 4
    default_padRight = 4

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        endTime = attributes.endTime
        iconPath = attributes.iconPath
        addButton = attributes.get('addButton', False)
        self.callback = attributes.get('callback', None)
        hintMessage = attributes.get('hintMessage', None)
        if hintMessage:
            self.hint = localization.GetByLabel(hintMessage, endTime=endTime)
        self.highlight = uiprimitives.Fill(bgParent=self, color=(0.8, 0.8, 0.8, 0.2))
        self.highlight.display = False
        icon = uiprimitives.Sprite(parent=self, pos=(0, 0, 32, 32), align=uiconst.CENTERLEFT, texturePath=iconPath, state=uiconst.UI_DISABLED)
        now = blue.os.GetWallclockTime()
        timeLeft = max(0L, endTime - now)
        timeLeftText = localization.formatters.FormatTimeIntervalWritten(long(timeLeft), showFrom='day', showTo='day')
        self.label = uicontrols.EveLabelLarge(parent=self, pos=(8, 0, 0, 0), align=uiconst.CENTERRIGHT, text=timeLeftText, state=uiconst.UI_DISABLED)
        if timeLeft < csUtil.WARNING_TIME:
            self.label.SetRGB(1, 0, 0, 1)
        self.width = icon.width + self.label.textwidth + self.label.left + 4
        if self.callback:
            self.OnClick = self.callback
        if addButton:
            btnText = attributes.get('btnText', '')
            self.AddButton(btnText=btnText)

    def AddButton(self, btnText = ''):
        buyBtn = uicontrols.Button(name='buyBtn', label=btnText, parent=self, align=uiconst.CENTERRIGHT, func=self.callback, pos=(4, 0, 0, 0))
        btnMouseExit = buyBtn.OnMouseExit
        buyBtn.OnMouseExit = (self.OnButtonMouseExit, btnMouseExit)
        self.label.left += buyBtn.width + 8
        self.width += buyBtn.width

    def OnMouseEnter(self, *args):
        self.highlight.display = True

    def OnMouseExit(self, *args):
        if not IsUnder(uicore.uilib.mouseOver, self):
            self.highlight.display = False

    def OnButtonMouseExit(self, btnMouseExitFunction):
        if uicore.uilib.mouseOver != self:
            self.OnMouseExit()
        btnMouseExitFunction()

    def OnClick(self, *args):
        if self.callback:
            self.callback()
