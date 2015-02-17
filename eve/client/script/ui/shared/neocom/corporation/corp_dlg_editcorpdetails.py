#Embedded file name: eve/client/script/ui/shared/neocom/corporation\corp_dlg_editcorpdetails.py
import blue
from eve.client.script.ui.control.checkbox import Checkbox
from eve.client.script.ui.control.infoIcon import MoreInfoIcon
import uiprimitives
import uicontrols
import util
import uix
import uiutil
from eve.client.script.ui.control import entries as listentry
import carbonui.const as uiconst
import uicls
import localization
import random

class CorpDetails(uicontrols.Window):
    __guid__ = 'form.CorpDetails'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.ShowLoad()
        self.SetCaption(self.caption)
        self.DefineButtons(uiconst.OK, okLabel=localization.GetByLabel('UI/Generic/Submit'), okFunc=self.Submit)
        self.SetMinSize([320, 410], 1)
        self.SetWndIcon()
        self.SetTopparentHeight(0)
        self.pickingTicker = 0
        self.layerNumSelected = None
        self.sr.prefs = [None,
         None,
         None,
         None,
         None,
         None]
        self.sr.priorlogo = (None, None, None, None, None, None)
        self.sr.priordesc = self.description
        self.sr.priorurl = self.url
        self.sr.priortaxRate = self.taxRate
        par = uiprimitives.Container(name='logoControl', parent=self.sr.main, align=uiconst.TOTOP, height=100, width=310, padding=(5, 5, 5, 0))
        self.sr.logocontrol = uiprimitives.Container(name='controlpanel', parent=par, height=100, width=160, align=uiconst.CENTER)
        self.sr.inputcontrol = uiprimitives.Container(name='controlpanel', parent=self.sr.main, align=uiconst.TOALL, pos=(0, 0, 0, 0), padding=(5, 5, 5, 0))
        top = uix.GetTextHeight(localization.GetByLabel('UI/Corporations/CorpDetails/CorpName'))
        if boot.region == 'optic':
            defaultCorpName = localization.GetByLabel('UI/Corporations/CorpDetails/DefaultCorpName')
        else:
            defaultCorpName = localization.GetByLabel('UI/Corporations/CorpDetails/DefaultCorpName', localization.const.LOCALE_SHORT_ENGLISH)
        self.sr.corpNameEdit_container = uiprimitives.Container(name='corpNameEdit_container', parent=self.sr.inputcontrol, align=uiconst.TOTOP, height=56)
        self.sr.corpNameEdit = uicontrols.SinglelineEdit(name='nameEdit', parent=self.sr.corpNameEdit_container, setvalue=defaultCorpName, align=uiconst.TOTOP, maxLength=100, label=localization.GetByLabel('UI/Corporations/CorpDetails/CorpName'), top=top)
        self.sr.corpNameEdit_container.height = self.sr.corpNameEdit.height + top + const.defaultPadding
        top = uix.GetTextHeight(localization.GetByLabel('UI/Corporations/CorpDetails/Ticker'))
        self.sr.corpTickerEdit_container = uiprimitives.Container(name='corpTickerEdit_container', parent=self.sr.inputcontrol, align=uiconst.TOTOP, height=56)
        btn = uicontrols.Button(parent=self.sr.corpTickerEdit_container, label=localization.GetByLabel('UI/Corporations/CorpDetails/Ticker'), align=uiconst.BOTTOMRIGHT, func=self.GetPickTicker, idx=0)
        self.sr.corpTickerEdit = uicontrols.SinglelineEdit(name='corpTickerEdit', parent=self.sr.corpTickerEdit_container, setvalue='', align=uiconst.TOPLEFT, maxLength=5, label=localization.GetByLabel('UI/Corporations/CorpDetails/Ticker'), top=top, width=min(300 - btn.width, 240))
        self.sr.corpTickerEdit_container.height = self.sr.corpTickerEdit.height + top + const.defaultPadding
        top = uix.GetTextHeight(localization.GetByLabel('UI/Corporations/CorpDetails/MemberLimit'))
        self.sr.memberLimit_container = uiprimitives.Container(name='memberLimit_container', parent=self.sr.inputcontrol, align=uiconst.TOTOP, height=24)
        btn = uicontrols.Button(parent=self.sr.memberLimit_container, label=localization.GetByLabel('UI/Corporations/CorpDetails/UpdateWithMySkills'), align=uiconst.BOTTOMRIGHT, func=self.UpdateWithSkills, idx=0)
        uicontrols.EveLabelSmall(text=localization.GetByLabel('UI/Corporations/CorpDetails/MemberLimit'), parent=self.sr.memberLimit_container, left=0, top=0, state=uiconst.UI_NORMAL)
        self.sr.memberLimit = uicontrols.EveLabelMedium(text='123', parent=self.sr.memberLimit_container, left=2, top=top, state=uiconst.UI_DISABLED, idx=0)
        self.sr.memberLimit_container.height = self.sr.memberLimit.height + top + const.defaultPadding
        top = uix.GetTextHeight(localization.GetByLabel('UI/Corporations/CorpDetails/TaxRate'))
        self.sr.taxRateEdit_container = uiprimitives.Container(name='taxRateEdit_container', parent=self.sr.inputcontrol, align=uiconst.TOTOP, height=24)
        self.sr.taxRateEdit = uicontrols.SinglelineEdit(name='taxRateEdit', parent=self.sr.taxRateEdit_container, floats=(0.0, 100.0, 1), setvalue=self.taxRate, align=uiconst.TOPLEFT, label=localization.GetByLabel('UI/Corporations/CorpDetails/TaxRate'), top=top)
        self.sr.taxRateEdit_container.height = self.sr.taxRateEdit.height + top + const.defaultPadding
        top = uix.GetTextHeight('http://')
        self.sr.urlEdit_container = uiprimitives.Container(name='urlEdit_container', parent=self.sr.inputcontrol, align=uiconst.TOTOP)
        self.sr.urlEdit = uicontrols.SinglelineEdit(name='urlEdit', parent=self.sr.urlEdit_container, setvalue=self.url, maxLength=2048, align=uiconst.TOTOP, label=localization.GetByLabel('UI/Corporations/CorpDetails/HomePage'), top=top)
        self.sr.urlEdit_container.height = self.sr.urlEdit.height + top + const.defaultPadding + 20
        self.friendlyFireCont = uiprimitives.Container(name='friendlyFireCont', parent=self.sr.inputcontrol, align=uiconst.TOBOTTOM, height=24)
        self.friendlyFireCb = Checkbox(name='friendlyFireCb', parent=self.friendlyFireCont, text=localization.GetByLabel('UI/Corporations/CorpUIHome/AllowFriendlyFire'), checked=False, align=uiconst.TOLEFT, width=200)
        helpIcon = MoreInfoIcon(parent=self.friendlyFireCont, align=uiconst.TOPRIGHT, hint=localization.GetByLabel('UI/Corporations/FriendlyFire/Description'))
        top = uix.GetTextHeight(localization.GetByLabel('UI/Corporations/CorpDetails/Description'))
        self.sr.descEdit_container = uiprimitives.Container(name='descEdit_container', parent=self.sr.inputcontrol, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        uicontrols.EveLabelSmall(text=localization.GetByLabel('UI/Corporations/CorpDetails/Description'), parent=self.sr.descEdit_container, top=-16)
        self.sr.descEdit = uicls.EditPlainText(setvalue=self.description, parent=self.sr.descEdit_container, maxLength=4000, showattributepanel=1)
        self.logopicker = uicls.CorpLogoPickerContainer(parent=self.sr.logocontrol, pos=(100, 0, 57, 90), align=uiconst.TOPLEFT)

    def GetLogoLibShape(self, graphicID):
        return const.graphicCorpLogoLibShapes.get(graphicID, const.graphicCorpLogoLibShapes[const.graphicCorpLogoLibNoShape])

    def GetLogoLibColor(self, graphicID):
        color, blendMode = const.graphicCorpLogoLibColors.get(graphicID, (1.0, 1.0, 1.0, 1.0))
        return (color, blendMode)

    def SetupLogo(self, shapes = [None, None, None], colors = [None, None, None]):
        i = 0
        self.sr.layerpics = []
        for each in ['layerPic1', 'layerPic2', 'layerPic3']:
            btn = uiprimitives.Sprite(parent=getattr(self.logopicker, each), pos=(0, 0, 0, 0), align=uiconst.TOALL, color=(1.0, 0.0, 1.0, 0.0))
            btn.OnClick = (self.ClickPic, i)
            self.sr.layerpics.append(btn)
            texturePath = self.GetLogoLibShape(shapes[i])
            btn.LoadTexture(texturePath)
            btn.SetRGB(1.0, 1.0, 1.0, 1.0)
            self.corpLogo.SetLayerShapeAndColor(layerNum=i, shapeID=shapes[i], colorID=colors[i])
            self.sr.prefs[i] = shapes[i]
            i += 1

        i = 0
        self.sr.layercols = []
        for each in ['layerStyle1', 'layerStyle2', 'layerStyle3']:
            btn = uiprimitives.Fill(parent=getattr(self.logopicker, each), pos=(0, 0, 0, 0), align=uiconst.TOALL, color=(1.0, 1.0, 1.0, 0.0), state=uiconst.UI_NORMAL)
            btn.OnClick = (self.ClickCol, i, btn)
            self.sr.layercols.append(btn)
            if colors[i]:
                newshader = blue.resMan.LoadObject(util.GraphicFile(colors[i]))
                color, blendMode = self.GetLogoLibColor(colors[i])
                btn.SetRGB(*color)
                self.sr.prefs[i + 3] = colors[i]
            i = i + 1

    def PickPic(self, sender, *args):
        """
        A new texture has been picked for the layer defined by self.layerNumSelected.
        Apply the texture to the preview logo
        """
        if self.layerNumSelected is not None:
            shapeID = sender.sr.identifier
            texturePath = self.GetLogoLibShape(shapeID)
            self.sr.layerpics[self.layerNumSelected].LoadTexture(texturePath)
            self.corpLogo.SetLayerShapeAndColor(layerNum=self.layerNumSelected, shapeID=shapeID)
            if not self.sr.prefs[self.layerNumSelected + 3]:
                self.sr.layerpics[self.layerNumSelected].SetRGB(1.0, 1.0, 1.0, 1.0)
            self.sr.prefs[self.layerNumSelected] = sender.sr.identifier

    def PickCol(self, sender, *args):
        """
        A new color has been picked for the layer defined by self.layerNumSelected.
        Apply the color to the preview logo
        """
        if self.layerNumSelected is not None:
            colorID = sender.sr.identifier
            color, blendMode = self.GetLogoLibColor(colorID)
            self.sr.layercols[self.layerNumSelected].SetRGB(*color)
            self.corpLogo.SetLayerShapeAndColor(layerNum=self.layerNumSelected, colorID=colorID)
            self.sr.prefs[self.layerNumSelected + 3] = colorID

    def ClickPic(self, idx):
        """
        A logo layer pic has been clicked; Open the logo layer selection pop-up
        """
        if not self.sr.Get('shapes', None):
            top = self.corpLogo.top + self.corpLogo.height
            self.sr.shapes = uiprimitives.Container(name='shapes_container', parent=self.sr.main, align=uiconst.CENTERTOP, height=220, width=280, idx=0, top=top)
            self.sr.shapes.state = uiconst.UI_HIDDEN
            shapescroll = uicontrols.Scroll(parent=self.sr.shapes, padding=(const.defaultPadding,
             const.defaultPadding,
             const.defaultPadding,
             const.defaultPadding))
            self.AddCloseButton(self.sr.shapes)
            self.sr.underlay = uicontrols.WindowUnderlay(parent=self.sr.shapes)
            x = 0
            scrolllist = []
            icons = []
            graphicIDs = const.graphicCorpLogoLibShapes.keys()
            graphicIDs.sort()
            for graphicID in graphicIDs:
                texturePath = self.GetLogoLibShape(graphicID)
                icons.append((texturePath,
                 None,
                 graphicID,
                 self.PickPic))
                x += 1
                if x == 4:
                    scrolllist.append(listentry.Get('Icons', {'icons': icons}))
                    icons = []
                    x = 0

            if len(icons):
                scrolllist.append(listentry.Get('Icons', {'icons': icons}))
            self.sr.shapes.state = uiconst.UI_NORMAL
            shapescroll.Load(fixedEntryHeight=64, contentList=scrolllist)
        self.layerNumSelected = idx
        self.sr.shapes.top = self.corpLogo.top + self.corpLogo.height
        if self.sr.Get('colors', None):
            self.sr.colors.state = uiconst.UI_HIDDEN
        self.sr.shapes.state = uiconst.UI_NORMAL
        self.sr.shapes.SetOrder(0)

    def DoNothing(self, *args):
        pass

    def AddCloseButton(self, panel):
        uiprimitives.Container(name='push', parent=panel.children[0], align=uiconst.TOBOTTOM, height=4, idx=0)
        buttondad = uiprimitives.Container(name='btnparent', parent=panel.children[0], align=uiconst.TOBOTTOM, height=16, idx=0)
        uicontrols.Button(parent=buttondad, label=localization.GetByLabel('UI/Generic/Close'), align=uiconst.CENTER, func=self.HidePanel, args=panel)

    def HidePanel(self, panel, *args):
        if panel:
            panel.state = uiconst.UI_HIDDEN

    def ClickCol(self, idx, sender):
        """
        A logo layer color has been clicked; Open the logo layer color selection pop-up
        """
        if not self.sr.Get('colors', None):
            self.sr.colors = uiprimitives.Container(name='colors_container', parent=self.sr.main, align=uiconst.CENTERTOP, height=128, width=150, idx=0)
            colorscroll = uicontrols.Scroll(parent=self.sr.colors, padding=(const.defaultPadding,
             const.defaultPadding,
             const.defaultPadding,
             const.defaultPadding))
            self.AddCloseButton(self.sr.colors)
            self.sr.underlay = uicontrols.WindowUnderlay(parent=self.sr.colors)
            x = 0
            scrolllist = []
            icons = []
            graphicIDs = const.graphicCorpLogoLibColors.keys()
            graphicIDs.sort()
            for graphicID in graphicIDs:
                color, blendMode = self.GetLogoLibColor(graphicID)
                icons.append((None,
                 color,
                 graphicID,
                 self.PickCol))
                x += 1
                if x == 4:
                    scrolllist.append(listentry.Get('Icons', {'icons': icons}))
                    icons = []
                    x = 0

            if len(icons):
                scrolllist.append(listentry.Get('Icons', {'icons': icons[:]}))
            self.sr.colors.state = uiconst.UI_NORMAL
            colorscroll.Load(fixedEntryHeight=32, contentList=scrolllist)
        self.layerNumSelected = idx
        self.sr.colors.top = self.corpLogo.top + self.corpLogo.height
        if self.sr.Get('shapes', None):
            self.sr.shapes.state = uiconst.UI_HIDDEN
        self.sr.colors.state = uiconst.UI_NORMAL
        uiutil.SetOrder(self.sr.colors, 0)

    def Confirm(self, *args):
        pass

    def MouseDown(self, sender, *args):
        if self.sr.Get('colors', None):
            self.sr.colors.state = uiconst.UI_HIDDEN
        if self.sr.Get('shapes', None):
            self.sr.shapes.state = uiconst.UI_HIDDEN

    def UpdateWithSkills(self, *args):
        if sm.GetService('corp').UpdateCorporationAbilities() is None:
            return
        corp = sm.GetService('corp').GetCorporation(eve.session.corpid, 1)
        self.sr.memberLimit.text = str(corp.memberLimit)

    def GetPickTicker(self, *args):
        if self.pickingTicker == 1:
            return
        self.pickingTicker = 1
        self.PickTicker()
        self.pickingTicker = 0

    def PickTicker(self, *args):
        corpName = self.sr.corpNameEdit.GetValue()
        if len(corpName.strip()) == 0:
            eve.Message('EnterCorporationName')
            return
        suggestions = sm.GetService('corp').GetSuggestedTickerNames(corpName)
        if not suggestions or len(suggestions) == 0:
            eve.Message('NoCorpTickerNameSuggestions')
            return
        tmplist = []
        for each in suggestions:
            tmplist.append((each.tickerName, each.tickerName))

        ret = uix.ListWnd(tmplist, 'generic', localization.GetByLabel('UI/Corporations/CorpDetails/SelectTicker'), None, 1)
        if ret is not None and len(ret):
            self.sr.corpTickerEdit.SetValue(ret[0])


class EditCorpDetails(CorpDetails):
    __guid__ = 'form.EditCorpDetails'
    default_windowID = 'editcorpdetails'

    def ApplyAttributes(self, attributes):
        corp = sm.GetService('corp').GetCorporation()
        self.caption = localization.GetByLabel('UI/Corporations/EditCorpDetails/EditCorpDetailsCaption')
        self.corporationName = corp.corporationName
        self.description = corp.description
        self.url = corp.url
        self.taxRate = corp.taxRate * 100.0
        self.applicationsEnabled = corp.isRecruiting
        CorpDetails.ApplyAttributes(self, attributes)
        self.friendlyFireCont.display = False
        self.sr.corpNameEdit_container.state = uiconst.UI_HIDDEN
        self.sr.corpTickerEdit_container.state = uiconst.UI_HIDDEN
        self.name = 'editcorp'
        self.result = {}
        self.sr.priorlogo = (corp.shape1,
         corp.shape2,
         corp.shape3,
         corp.color1,
         corp.color2,
         corp.color3)
        shapes = [corp.shape1, corp.shape2, corp.shape3]
        colors = [corp.color1, corp.color2, corp.color3]
        self.corpLogo = uiutil.GetLogoIcon(itemID=session.corpid, acceptNone=False, pos=(0, 0, 90, 90))
        self.sr.logocontrol.children.insert(0, self.corpLogo)
        self.SetupLogo(shapes, colors)
        self.sr.memberLimit.text = str(corp.memberLimit)
        self.sr.main.state = uiconst.UI_NORMAL
        self.HideLoad()

    def Submit(self, *args):
        myCorp = sm.GetService('corp').GetCorporation()
        shape1, shape2, shape3, color1, color2, color3 = self.sr.prefs
        if self.sr.priorlogo != (shape1,
         shape2,
         shape3,
         color1,
         color2,
         color3):
            if eve.Message('AskAcceptLogoChangeCost', {'cost': const.corpLogoChangeCost}, uiconst.YESNO, default=uiconst.ID_NO) == uiconst.ID_YES:
                sm.GetService('corp').UpdateLogo(shape1, shape2, shape3, color1, color2, color3, None)
        if self.sr.priordesc != self.sr.descEdit.GetValue() or self.sr.priorurl != self.sr.urlEdit.GetValue() or self.sr.priortaxRate != self.sr.taxRateEdit.GetValue():
            urlvalue = self.sr.urlEdit.GetValue() and self.sr.urlEdit.GetValue().strip()
            if urlvalue:
                urlvalue = util.FormatUrl(urlvalue)
            sm.GetService('corp').UpdateCorporation(self.sr.descEdit.GetValue().strip(), urlvalue, self.sr.taxRateEdit.GetValue() / 100.0, self.applicationsEnabled)
            sm.GetService('corpui').ResetWindow(bShowIfVisible=1)
        self.Close()


class CreateCorp(CorpDetails):
    __guid__ = 'form.CreateCorp'
    __nonpersistvars__ = ['result']
    default_windowID = 'createcorp'

    def ApplyAttributes(self, attributes):
        self.caption = localization.GetByLabel('UI/Corporations/CreateCorp/CreateCorpCaption')
        self.corporationName = ''
        self.description = localization.GetByLabel('UI/Corporations/CreateCorp/EnterDescriptionHere')
        self.url = 'http://'
        self.taxRate = 0.0
        self.applicationsEnabled = True
        CorpDetails.ApplyAttributes(self, attributes)
        self.name = 'createcorp'
        self.sr.memberLimit_container.state = uiconst.UI_HIDDEN
        self.result = {}
        randomNumber = random.choice(const.graphicCorpLogoLibShapes.keys())
        self.corpLogo = uicls.CorpIcon(acceptNone=False, pos=(0, 0, 90, 90))
        self.sr.logocontrol.children.insert(0, self.corpLogo)
        self.SetupLogo([randomNumber, const.graphicCorpLogoLibNoShape, const.graphicCorpLogoLibNoShape], [None, None, None])
        self.sr.main.state = uiconst.UI_NORMAL

    def Submit(self, *args):
        corpName = self.sr.corpNameEdit.GetValue()
        if len(corpName.strip()) == 0:
            raise UserError('EnterCorporationName')
        corpTicker = self.sr.corpTickerEdit.GetValue()
        if len(corpTicker.strip()) == 0:
            raise UserError('EnterTickerName')
        if not session.stationid:
            raise UserError('CanOnlyCreateCorpInStation')
        description = self.sr.descEdit.GetValue().strip()
        taxRate = self.sr.taxRateEdit.GetValue() / 100.0
        url = self.sr.urlEdit.GetValue()
        applicationsEnabled = self.applicationsEnabled
        friendlyFireEnabled = self.friendlyFireCb.GetValue()
        shape1, shape2, shape3, color1, color2, color3 = self.sr.prefs
        sm.GetService('corp').AddCorporation(corpName, corpTicker, description, url, taxRate, shape1, shape2, shape3, color1, color2, color3, applicationsEnabled=applicationsEnabled, friendlyFireEnabled=friendlyFireEnabled)
        self.Close()


class CorpLogoPicker(uiprimitives.Container):
    __guid__ = 'uicls.CorpLogoPickerContainer'
    default_name = 'corplogosubpar'
    default_state = uiconst.UI_NORMAL
    default_align = uiconst.TOPLEFT

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        FRAME_COLOR = util.Color.GetGrayRGBA(0.4, 1.0)
        layer1 = uiprimitives.Container(parent=self, name='layer1', pos=(0, 0, 50, 30), align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL)
        self.layerPic1 = uiprimitives.Container(parent=layer1, name='layerPic1', pos=(3, 3, 24, 24), align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL)
        uicontrols.Frame(parent=self.layerPic1, color=FRAME_COLOR)
        self.layerStyle1 = uiprimitives.Container(parent=layer1, name='layerStyle1', pos=(26, 3, 24, 24), align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL)
        uicontrols.Frame(parent=self.layerStyle1, color=FRAME_COLOR)
        layer2 = uiprimitives.Container(parent=self, name='layer2', pos=(0, 30, 50, 30), align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL)
        self.layerPic2 = uiprimitives.Container(parent=layer2, name='layerPic2', pos=(3, 3, 24, 24), align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL)
        uicontrols.Frame(parent=self.layerPic2, color=FRAME_COLOR)
        self.layerStyle2 = uiprimitives.Container(parent=layer2, name='layerStyle2', pos=(26, 3, 24, 24), align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL)
        uicontrols.Frame(parent=self.layerStyle2, color=FRAME_COLOR)
        layer3 = uiprimitives.Container(parent=self, name='layer3', pos=(0, 60, 50, 30), align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL)
        self.layerPic3 = uiprimitives.Container(parent=layer3, name='layerPic3', pos=(3, 3, 24, 24), align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL)
        uicontrols.Frame(parent=self.layerPic3, color=FRAME_COLOR)
        self.layerStyle3 = uiprimitives.Container(parent=layer3, name='layerStyle3', pos=(26, 3, 24, 24), align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL)
        uicontrols.Frame(parent=self.layerStyle3, color=FRAME_COLOR)
