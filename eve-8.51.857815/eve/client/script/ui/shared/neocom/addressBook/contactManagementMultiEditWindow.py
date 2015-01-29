#Embedded file name: eve/client/script/ui/shared/neocom/addressBook\contactManagementMultiEditWindow.py
import math
import sys
import service
import uiprimitives
import uicontrols
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.frame import Frame
import uthread
import uix
import uiutil
import form
import util
from eve.client.script.ui.control import entries as listentry
import carbonui.const as uiconst
import uicls
import log
import localization
import telemetry
from eve.client.script.ui.shared.neocom.evemail import ManageLabelsBase

class ContactManagementMultiEditWnd(uicontrols.Window):
    __guid__ = 'form.ContactManagementMultiEditWnd'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        entityIDs = attributes.entityIDs
        contactType = attributes.contactType
        self.result = None
        self.SetCaption(localization.GetByLabel('UI/PeopleAndPlaces/ContactManagement'))
        self.SetMinSize([250, 100])
        self.MakeUnResizeable()
        self.SetWndIcon()
        self.SetTopparentHeight(0)
        self.entityIDs = entityIDs
        self.level = None
        self.contactType = contactType
        self.ConstructLayout()

    def ConstructLayout(self):
        topCont = ContainerAutoSize(name='topCont', parent=self.sr.main, align=uiconst.TOTOP, padding=const.defaultPadding, callback=self.OnMainContainerSizeChanged)
        self.mainContainer = topCont
        charnameList = ''
        for entityID in self.entityIDs:
            charName = cfg.eveowners.Get(entityID).name
            if charnameList == '':
                charnameList = '%s' % charName
            else:
                charnameList = '%s, %s' % (charnameList, charName)

        uicontrols.EveLabelLargeBold(text=charnameList, parent=topCont, align=uiconst.TOTOP, state=uiconst.UI_DISABLED)
        uiprimitives.Line(parent=topCont, align=uiconst.TOTOP, padding=(0, 4, 0, 4))
        self.standingList = {const.contactHighStanding: localization.GetByLabel('UI/PeopleAndPlaces/ExcellentStanding'),
         const.contactGoodStanding: localization.GetByLabel('UI/PeopleAndPlaces/GoodStanding'),
         const.contactNeutralStanding: localization.GetByLabel('UI/PeopleAndPlaces/NeutralStanding'),
         const.contactBadStanding: localization.GetByLabel('UI/PeopleAndPlaces/BadStanding'),
         const.contactHorribleStanding: localization.GetByLabel('UI/PeopleAndPlaces/TerribleStanding')}
        levelList = self.standingList.keys()
        levelList.sort()
        levelText = self.standingList.get(self.level)
        self.levelText = uicontrols.EveLabelMedium(text=levelText, parent=topCont, align=uiconst.TOTOP, state=uiconst.UI_DISABLED)
        if self.contactType != 'contact':
            bottomCont = uiprimitives.Container(name='bottomCont', parent=topCont, align=uiconst.TOTOP, height=40, padding=const.defaultPadding)
            startVal = 0.5
            sliderContainer = uiprimitives.Container(parent=bottomCont, name='sliderContainer', align=uiconst.CENTERTOP, height=20, width=210)
            self.sr.slider = self.AddSlider(sliderContainer, 'standing', -10.0, 10.0, '', startVal=startVal)
            self.sr.slider.SetValue(startVal)
            boxCont = bottomCont
            iconPadding = 28
        else:
            boxCont = uiprimitives.Container(name='boxCont', parent=topCont, align=uiconst.TOTOP, height=55)
            iconPadding = 6
        levelSelectorContainer = uiprimitives.Container(parent=boxCont, name='levelSelectorContainer', align=uiconst.TOTOP, pos=(0, 0, 0, 55))
        self.levelSelector = uicls.StandingLevelSelector(name='levelSelector', parent=levelSelectorContainer, align=uiconst.CENTERTOP, pos=(0,
         14,
         100 + iconPadding * 4,
         55), iconPadding=iconPadding)
        self.levelSelector.OnStandingLevelSelected = self.OnStandingLevelSelected
        btnText = localization.GetByLabel('UI/PeopleAndPlaces/EditContact')
        self.btnGroup = uicontrols.ButtonGroup(btns=[[btnText,
          self.Confirm,
          (),
          81,
          1,
          1,
          0], [localization.GetByLabel('UI/Common/Buttons/Cancel'),
          self.Cancel,
          (),
          81,
          0,
          0,
          0]], parent=self.sr.main, idx=0)
        if self.level is None:
            self.levelText.text = localization.GetByLabel('UI/PeopleAndPlaces/SelectStanding')
            btn = self.btnGroup.GetBtnByLabel(btnText)
            uicore.registry.SetFocus(btn)

    def OnMainContainerSizeChanged(self, *args, **kwds):
        self.SetMinSize([250, self.mainContainer.height + 55], refresh=True)

    def AddSlider(self, where, config, minval, maxval, header, hint = '', startVal = 0):
        h = 10
        _par = uiprimitives.Container(name=config + '_slider', parent=where, align=uiconst.TOTOP, pos=(0, 0, 210, 10), padding=(0, 0, 0, 0))
        par = uiprimitives.Container(name=config + '_slider_sub', parent=_par, align=uiconst.TOPLEFT, pos=(0, 0, 210, 10), padding=(0, 0, 0, 0))
        slider = uicontrols.Slider(parent=par)
        lbl = uicontrols.EveLabelSmall(text='bla', parent=par, align=uiconst.TOPLEFT, width=200, left=0, top=0)
        setattr(self.sr, '%sLabel' % config, lbl)
        lbl.name = 'label'
        slider.SetSliderLabel = self.SetSliderLabel
        lbl.state = uiconst.UI_HIDDEN
        slider.Startup(config, minval, maxval, None, header, startVal=startVal)
        if startVal < minval:
            startVal = minval
        slider.value = startVal
        slider.name = config
        slider.hint = hint
        slider.OnSetValue = self.OnSetValue
        return slider

    def SetSliderLabel(self, label, idname, dname, value):
        self.sr.standingLabel.text = localization.GetByLabel('UI/AddressBook/SliderLabel', value=round(value, 1), standingText=uix.GetStanding(round(value, 1)))

    def OnSetValue(self, *args):
        self.levelText.text = self.sr.standingLabel.text

    def OnStandingLevelSelected(self, level):
        if self.contactType != 'contact':
            level = level / 20.0 + 0.5
            self.sr.slider.SlideTo(level)
            self.sr.slider.SetValue(level)
        else:
            self.level = level
            self.levelText.text = self.standingList.get(self.level)

    def Confirm(self):
        if self.contactType != 'contact':
            if self.levelText.text == localization.GetByLabel('UI/PeopleAndPlaces/SelectStanding'):
                eve.Message('NoStandingsSelected')
                return
            relationshipID = round(self.sr.slider.value, 1)
        else:
            if self.level is None:
                eve.Message('NoStandingsSelected')
                return
            relationshipID = self.level
        self.result = relationshipID
        if getattr(self, 'isModal', None):
            self.SetModalResult(1)

    def Cancel(self):
        self.result = None
        if getattr(self, 'isModal', None):
            self.SetModalResult(0)
