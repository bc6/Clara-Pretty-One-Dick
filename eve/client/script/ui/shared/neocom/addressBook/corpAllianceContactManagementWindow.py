#Embedded file name: eve/client/script/ui/shared/neocom/addressBook\corpAllianceContactManagementWindow.py
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
__author__ = 'aevar'

class CorpAllianceContactManagementWnd(uicontrols.Window):
    __guid__ = 'form.CorpAllianceContactManagementWnd'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        entityID = attributes.entityID
        level = attributes.level
        isContact = attributes.isContact
        contactType = attributes.contactType
        self.result = None
        self.SetCaption(localization.GetByLabel('UI/PeopleAndPlaces/ContactManagement'))
        self.minHeight = 110
        self.SetMinSize([250, self.minHeight])
        self.MakeUnResizeable()
        self.SetWndIcon()
        self.SetTopparentHeight(0)
        self.entityID = entityID
        self.level = level
        self.isContact = isContact
        self.notify = False
        self.contactType = contactType
        self.ConstructLayout()

    def ConstructLayout(self):
        topCont = uiprimitives.Container(name='topCont', parent=self.sr.main, align=uiconst.TOTOP, pos=(0, 0, 0, 76), padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        imgCont = uiprimitives.Container(name='imgCont', parent=topCont, align=uiconst.TOLEFT, pos=(0, 0, 64, 0), padding=(0,
         0,
         const.defaultPadding,
         0))
        topRightCont = uiprimitives.Container(name='topRightCont', parent=topCont, align=uiconst.TOALL)
        nameCont = uiprimitives.Container(name='nameCont', parent=topRightCont, align=uiconst.TOTOP, pos=(0, 0, 0, 20), padding=(0, 0, 0, 0))
        splitter = uiprimitives.Container(name='splitter', parent=topRightCont, align=uiconst.TOTOP, pos=(0, 0, 0, 1), padding=(0, 0, 0, 0))
        uiprimitives.Line(parent=splitter, align=uiconst.TOBOTTOM)
        levelCont = uiprimitives.Container(name='levelCont', parent=topRightCont, align=uiconst.TOALL)
        textCont = uiprimitives.Container(name='textCont', parent=levelCont, align=uiconst.TOTOP, pos=(0, 0, 0, 18))
        sliderCont = uiprimitives.Container(name='sliderCont', parent=levelCont, align=uiconst.TOTOP, pos=(0, 0, 0, 12))
        levelsCont = uiprimitives.Container(name='levelsCont', parent=levelCont, align=uiconst.TOTOP, pos=(0, 0, 0, 40))
        uiprimitives.Container(name='bottomCont', parent=self.sr.main, align=uiconst.TOALL, pos=(0, 0, 0, 0), padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        labels = sm.GetService('addressbook').GetContactLabels(self.contactType).values()
        if not self.isContact and len(labels):
            labelList = []
            labelCont = uiprimitives.Container(name='labelCont', parent=self.sr.main, align=uiconst.TOBOTTOM, pos=(0, 0, 0, 18), padding=(const.defaultPadding,
             0,
             0,
             const.defaultPadding))
            for label in labels:
                labelList.append((label.name, label.labelID))

            assignLabelText = localization.GetByLabel('UI/PeopleAndPlaces/AssignLabel')
            labelList.insert(0, (assignLabelText, None))
            self.labelsCombo = uicontrols.Combo(label='', parent=labelCont, options=labelList, name='labelscombo', adjustWidth=True)
            self.minHeight += labelCont.height
        self.standingList = {const.contactHighStanding: localization.GetByLabel('UI/PeopleAndPlaces/ExcellentStanding'),
         const.contactGoodStanding: localization.GetByLabel('UI/PeopleAndPlaces/GoodStanding'),
         const.contactNeutralStanding: localization.GetByLabel('UI/PeopleAndPlaces/NeutralStanding'),
         const.contactBadStanding: localization.GetByLabel('UI/PeopleAndPlaces/BadStanding'),
         const.contactHorribleStanding: localization.GetByLabel('UI/PeopleAndPlaces/TerribleStanding')}
        levelList = self.standingList.keys()
        levelList.sort()
        levelText = ''
        self.levelText = uicontrols.EveLabelMedium(text=levelText, parent=textCont, left=0, align=uiconst.TOPLEFT, width=170, state=uiconst.UI_DISABLED, idx=0)
        startVal = 0.5
        if self.isContact:
            startVal = self.level / 20.0 + 0.5
        self.sr.slider = self.AddSlider(sliderCont, 'standing', -10.0, 10.0, '', startVal=startVal)
        self.sr.slider.SetValue(startVal)
        self.levelSelector = uicls.StandingLevelSelector(name='levelCont', parent=levelsCont, align=uiconst.TOTOP, height=55, level=self.level)
        self.levelSelector.OnStandingLevelSelected = self.OnStandingLevelSelected
        charName = cfg.eveowners.Get(self.entityID).name
        uiutil.GetOwnerLogo(imgCont, self.entityID, size=64, noServerCall=True)
        label = uicontrols.EveLabelLargeBold(text=charName, parent=nameCont, left=0, top=2, align=uiconst.TOPLEFT, width=170, state=uiconst.UI_DISABLED, idx=0)
        nameCont.state = uiconst.UI_DISABLED
        nameCont.height = label.height + 5
        self.minHeight += nameCont.height
        topCont.height = max(topCont.height, nameCont.height + levelsCont.height + splitter.height + textCont.height)
        btnText = localization.GetByLabel('UI/PeopleAndPlaces/AddContact')
        if self.isContact:
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
        uthread.new(self.SetWindowSize)

    def AddSlider(self, where, config, minval, maxval, header, hint = '', startVal = 0):
        h = 10
        _par = uiprimitives.Container(name=config + '_slider', parent=where, align=uiconst.TOTOP, pos=(0, 0, 124, 10), padding=(0, 0, 0, 0))
        par = uiprimitives.Container(name=config + '_slider_sub', parent=_par, align=uiconst.TOPLEFT, pos=(0, 0, 124, 10), padding=(0, 0, 0, 0))
        slider = uicontrols.Slider(parent=par)
        lbl = uicontrols.EveLabelSmall(text='bla', parent=par, align=uiconst.TOPLEFT, width=200, left=-34, top=0)
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
        level = level / 20.0 + 0.5
        self.sr.slider.SlideTo(level)
        self.sr.slider.SetValue(level)

    def SetWindowSize(self):
        if self and not self.destroyed:
            self.height = self.minHeight
            self.SetMinSize([200, self.minHeight])

    def Confirm(self):
        if self.levelText.text == localization.GetByLabel('UI/PeopleAndPlaces/SelectStanding'):
            eve.Message('NoStandingsSelected')
            return
        relationshipID = round(self.sr.slider.value, 1)
        contactLabel = None
        if hasattr(self, 'labelsCombo'):
            contactLabel = self.labelsCombo.GetValue()
        self.result = (relationshipID, contactLabel)
        if getattr(self, 'isModal', None):
            self.SetModalResult(1)

    def Cancel(self):
        self.result = None
        if getattr(self, 'isModal', None):
            self.SetModalResult(0)
