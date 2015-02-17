#Embedded file name: eve/client/script/ui/station/stationmanagement\facilityStandingsWindow.py
import uicls
import uiprimitives
import uicontrols
import util
import carbonui.const as uiconst
import localization

class FacilityStandingsWindow(uicontrols.Window):
    __guid__ = 'form.FacilityStandingsWindow'
    default_windowID = 'facilityStandingsWindow'
    default_topParentHeight = 0
    default_clipChildren = 1
    default_iconNum = 'res:/ui/Texture/WindowIcons/settings.png'
    WIDTH_COLLAPSED = 270
    WIDTH_EXPANDED = 445
    HEIGHT = 190
    HOVER_ALPHA = 1.0
    NORMAL_ALPHA = 0.8

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.facilityID = attributes.facilityID
        self.facilityName = attributes.facilityName
        self.facilitySvc = sm.GetService('facilitySvc')
        self.taxes = self.facilitySvc.GetFacilityTaxes(self.facilityID)
        self.taxRates = [util.KeyVal(key='taxCorporation', value=self.taxes.taxCorporation),
         util.KeyVal(key='taxAlliance', value=self.taxes.taxAlliance),
         util.KeyVal(key='taxStandingsHorrible', standing=const.contactHorribleStanding, value=self.taxes.taxStandingsHorrible),
         util.KeyVal(key='taxStandingsBad', standing=const.contactBadStanding, value=self.taxes.taxStandingsBad),
         util.KeyVal(key='taxStandingsNeutral', standing=const.contactNeutralStanding, value=self.taxes.taxStandingsNeutral),
         util.KeyVal(key='taxStandingsGood', standing=const.contactGoodStanding, value=self.taxes.taxStandingsGood),
         util.KeyVal(key='taxStandingsHigh', standing=const.contactHighStanding, value=self.taxes.taxStandingsHigh)]
        self.standingLevel = const.contactHorribleStanding
        for taxRate in self.taxRates[2:]:
            if taxRate.value is not None:
                self.standingLevel = taxRate.standing
                break

        self.effects = uicls.UIEffects()
        self.scope = 'all'
        self.SetWndIcon(self.iconNum, size=32)
        self.SetMinSize([self.WIDTH_COLLAPSED, self.HEIGHT])
        self.SetCaption(localization.GetByLabel('UI/Menusvc/ConfigureFacility'))
        self.MakeUnResizeable()
        self.Layout()
        self.Redraw()

    def Layout(self):
        self.nameLabel = uicontrols.EveLabelSmall(text=self.facilityName, parent=self.sr.main, state=uiconst.UI_NORMAL, left=15, top=13)
        self.corporationContainer = uiprimitives.Container(align=uiconst.TOPLEFT, parent=self.sr.main, width=self.WIDTH_COLLAPSED, height=25, top=26)
        self.corporationLabel = uicontrols.EveLabelSmall(text=localization.GetByLabel('UI/PI/OrbitalConfigurationWindow/CorporationTax'), parent=self.corporationContainer, state=uiconst.UI_NORMAL, left=15, top=17)
        self.LayoutTaxInput(self.taxRates[0], self.corporationContainer, 140, 13)
        self.allianceContainer = uiprimitives.Container(align=uiconst.TOPLEFT, parent=self.sr.main, width=220, height=25, top=52)
        self.allianceCheckbox = uicontrols.Checkbox(parent=self.allianceContainer, text=localization.GetByLabel('UI/PI/OrbitalConfigurationWindow/AllianceTax'), checked=self.taxes.taxAlliance is not None, padding=(13, 13, 0, 0), callback=self.Redraw)
        self.LayoutTaxInput(self.taxRates[1], self.allianceContainer, 140, 13)
        self.standingsCheckboxContainer = uiprimitives.Container(align=uiconst.TOPLEFT, parent=self.sr.main, width=220, height=25, top=78)
        self.standingsCheckbox = uicontrols.Checkbox(parent=self.standingsCheckboxContainer, text=localization.GetByLabel('UI/PI/OrbitalConfigurationWindow/Standing'), checked=self.AnyStandingsSet(), padding=(13, 13, 0, 0), callback=self.Redraw)
        self.standingsContainer = uiprimitives.Container(name='standingsContainer', parent=self.sr.main, align=uiconst.TOPLEFT, padding=(0, 0, 0, 0), left=self.WIDTH_COLLAPSED, width=self.WIDTH_EXPANDED - self.WIDTH_COLLAPSED, height=144, opacity=0)
        uiprimitives.Line(parent=self.standingsContainer, align=uiconst.TOLEFT, color=(1.0, 1.0, 1.0, 0.25))
        self.standingLevelSelector = uicls.StandingLevelSelector(name='standingLevelSelector', parent=self.standingsContainer, align=uiconst.TOPLEFT, level=self.standingLevel, padding=(20, 0, 0, 0), width=90, height=200, top=10, vertical=True, callback=self.Redraw)
        for i, taxRate in enumerate(self.taxRates[2:]):
            self.LayoutTaxInput(taxRate, self.standingsContainer, 50, 10 + i * 26)

        self.footer = uiprimitives.Container(parent=self.sr.main, name='footer', align=uiconst.TOBOTTOM, height=32)
        btns = [(localization.GetByLabel('UI/Common/Submit'), self.Submit, None), (localization.GetByLabel('UI/Common/Cancel'), self.Cancel, None)]
        uicontrols.ButtonGroup(btns=btns, subalign=uiconst.CENTER, parent=self.footer, line=True, alwaysLite=False)
        self.width = [self.WIDTH_COLLAPSED, self.WIDTH_EXPANDED][int(self.standingsCheckbox.GetValue())]

    def LayoutTaxInput(self, taxRate, parent, left = 0, top = 0):
        taxRateValue = taxRate.value
        taxRateInput = uicontrols.SinglelineEdit(parent=parent, name='taxRateEdit', align=uiconst.TOPLEFT, setvalue='0.0' if taxRateValue is None else str(100 * taxRateValue), width=90, left=left, top=top, idx=0)
        taxRatePercent = uicontrols.EveLabelMedium(align=uiconst.TOPLEFT, text='%', parent=parent, left=left + 97, top=top + 2)
        taxRateInput.FloatMode(minfloat=0, maxfloat=10000)
        taxRate.input = taxRateInput

    def OnMouseEnterInteractable(self, obj, *args):
        obj.SetOpacity(self.HOVER_ALPHA)

    def OnMouseExitInteractable(self, obj, *args):
        obj.SetOpacity(self.NORMAL_ALPHA)

    def Redraw(self, *args):
        """ Handles visibility of the tax rate fields based on having picked
        a minimum standing / allow alliance. """
        level = self.standingLevelSelector.GetValue()
        taxRateVisible = True
        for taxRate in self.taxRates[2:]:
            if taxRate.standing == level:
                taxRateVisible = False
            self.SetTaxRateVisible(taxRate.input, taxRateVisible)

        self.SetTaxRateVisible(self.taxRates[1].input, not self.allianceCheckbox.GetValue())
        if self.standingsCheckbox.GetValue():
            self.ResizeWindowWidth(self.WIDTH_EXPANDED)
            self.ShowElement(self.standingsContainer)
        else:
            self.HideElement(self.standingsContainer)
            self.ResizeWindowWidth(self.WIDTH_COLLAPSED)

    def ResizeWindowWidth(self, width):
        self.effects.MorphUIMassSpringDamper(self, 'width', width, newthread=True, float=0, dampRatio=0.99, frequency=15.0)

    def HideElement(self, element):
        self.effects.MorphUIMassSpringDamper(element, 'opacity', 0, dampRatio=0.99, frequency=30.0)

    def ShowElement(self, element):
        self.effects.MorphUIMassSpringDamper(element, 'opacity', 1, dampRatio=0.99, frequency=30.0)

    def SetTaxRateVisible(self, field, visible):
        """ UI helper method, pass in a text field and whether to show or hide it.
        Performs a soft fade animation and hides the text / disables input. """
        if visible and field.state == uiconst.UI_NORMAL:
            field.hiddenValue = field.GetValue()
            field.SetText(localization.GetByLabel('UI/PI/Common/CustomsOfficeAccessDenied'))
            field.SelectNone()
            field.state = uiconst.UI_DISABLED
            field.sr.text.SetAlpha(0.5)
            self.effects.MorphUIMassSpringDamper(field, 'opacity', 0.5, dampRatio=0.99)
        elif not visible and field.state == uiconst.UI_DISABLED:
            field.SetValue(field.hiddenValue)
            field.hiddenValue = None
            field.state = uiconst.UI_NORMAL
            field.sr.text.SetAlpha(1)
            self.effects.MorphUIMassSpringDamper(field, 'opacity', 1, dampRatio=0.99)

    def GetTaxRateValue(self, field):
        if field.state == uiconst.UI_DISABLED:
            return
        value = getattr(field, 'hiddenValue', None)
        if value is None:
            value = field.GetValue()
        return value / 100

    def AnyStandingsSet(self):
        return any((s is not None for s in [self.taxes.taxStandingsHorrible,
         self.taxes.taxStandingsBad,
         self.taxes.taxStandingsNeutral,
         self.taxes.taxStandingsGood,
         self.taxes.taxStandingsHigh]))

    def Submit(self, *args):
        taxRateValues = {taxRate.key:self.GetTaxRateValue(taxRate.input) for taxRate in self.taxRates}
        if not self.allianceCheckbox.GetValue():
            taxRateValues['taxAlliance'] = None
        if not self.standingsCheckbox.GetValue():
            taxRateValues['taxStandingsHorrible'] = None
            taxRateValues['taxStandingsBad'] = None
            taxRateValues['taxStandingsNeutral'] = None
            taxRateValues['taxStandingsGood'] = None
            taxRateValues['taxStandingsHigh'] = None
        self.facilitySvc.SetFacilityTaxes(self.facilityID, taxRateValues)
        self.CloseByUser()

    def Cancel(self, *args):
        self.CloseByUser()
