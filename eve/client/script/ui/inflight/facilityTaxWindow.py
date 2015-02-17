#Embedded file name: eve/client/script/ui/inflight\facilityTaxWindow.py
import uicls
import uiprimitives
import uicontrols
import util
import carbonui.const as uiconst
import localization

class FacilityTaxWindow(uicontrols.Window):
    __guid__ = 'form.FacilityTaxWindow'
    default_windowID = 'FacilityTaxWindow'
    default_topParentHeight = 0
    default_clipChildren = 1
    HOVER_ALPHA = 1.0
    NORMAL_ALPHA = 0.8
    default_iconNum = 'res:/ui/Texture/WindowIcons/settings.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.facilityName = attributes.facilityName
        self.facilityID = attributes.facilityID
        self.facilitySvc = sm.GetService('facilitySvc')
        self.taxRate = util.KeyVal(value=self.facilitySvc.GetFacilityTaxes(self.facilityID).taxCorporation)
        self.scope = 'all'
        self.SetWndIcon(self.iconNum, size=32)
        self.width = 270
        self.height = 130
        self.SetCaption(localization.GetByLabel('UI/Menusvc/ConfigureFacility'))
        self.MakeUnResizeable()
        self.Layout()

    def Layout(self):
        self.corporationContainer = uiprimitives.Container(align=uiconst.TOPLEFT, parent=self.sr.main, width=self.width, height=25, top=20)
        self.nameLabel = uicontrols.EveLabelSmall(text=self.facilityName, parent=self.corporationContainer, state=uiconst.UI_NORMAL, left=15, top=-15)
        self.corporationLabel = uicontrols.EveLabelSmall(text=localization.GetByLabel('UI/Industry/FacilityTax'), parent=self.corporationContainer, state=uiconst.UI_NORMAL, left=15, top=8)
        self.LayoutTaxInput(self.taxRate, self.corporationContainer, 15, 30)
        self.footer = uiprimitives.Container(parent=self.sr.main, name='footer', align=uiconst.TOBOTTOM, height=32)
        btns = [(localization.GetByLabel('UI/Common/Submit'), self.Submit, None), (localization.GetByLabel('UI/Common/Cancel'), self.Cancel, None)]
        uicontrols.ButtonGroup(btns=btns, subalign=uiconst.CENTER, parent=self.footer, line=True, alwaysLite=False)

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

    def Submit(self, *args):
        taxRateValues = {'taxCorporation': self.taxRate.input.GetValue() / 100,
         'taxAlliance': None,
         'taxStandingsHorrible': None,
         'taxStandingsBad': None,
         'taxStandingsNeutral': None,
         'taxStandingsGood': None,
         'taxStandingsHigh': None}
        self.facilitySvc.SetFacilityTaxes(self.facilityID, taxRateValues)
        self.CloseByUser()

    def Cancel(self, *args):
        self.CloseByUser()
