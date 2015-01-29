#Embedded file name: eve/client/script/ui/inflight\bountyEscrowWnd.py
"""
Code for the bounty escrow window
"""
from carbonui.control.scrollContainer import ScrollContainer
from carbonui.primitives.container import Container
from carbonui.primitives.sprite import Sprite
from localization import GetByLabel
from eve.client.script.ui.control.buttons import Button
from eve.client.script.ui.control.eveIcon import GetLogoIcon, Icon
from eve.client.script.ui.control.eveLabel import EveLabelLarge, EveCaptionSmall, EveLabelSmall, EveLabelLargeBold, EveLabelMedium, EveLabelMediumBold, EveCaptionMedium
from eve.client.script.ui.control.eveWindow import Window
from eve.common.script.util.eveFormat import FmtISK
import carbonui.const as uiconst
FACTIONPATHBYESSTYPEID = {const.typeESSAmarr: 'res:/UI/Texture/Race/Amarr.png',
 const.typeESSCaldari: 'res:/UI/Texture/Race/Caldari.png',
 const.typeESSGallente: 'res:/UI/Texture/Race/Gallente.png',
 const.typeESSMinmatar: 'res:/UI/Texture/Race/Minmatar.png'}
CAPTIONBYESSTYPEID = {const.typeESSAmarr: 'UI/Inflight/Brackets/AmarrESS',
 const.typeESSCaldari: 'UI/Inflight/Brackets/CaldariESS',
 const.typeESSGallente: 'UI/Inflight/Brackets/GallenteESS',
 const.typeESSMinmatar: 'UI/Inflight/Brackets/MinmatarESS'}
CORPIDBYFACTIONID = {const.typeESSAmarr: 1000084,
 const.typeESSCaldari: 1000035,
 const.typeESSGallente: 1000120,
 const.typeESSMinmatar: 1000051}

class BountyEscrowWnd(Window):
    """
    This class draws the bounty escrow window
    """
    __guid__ = 'form.BountyEscrowWnd'
    default_width = 450
    default_height = 330
    default_minSize = (default_width, default_height)
    default_windowID = 'bountyEscrow'

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.SetTopparentHeight(0)
        self.bountyEscrow = attributes.bountyEscrow
        self.bountyAmount = attributes.bountyAmount
        self.component = attributes.component
        factionResPath = FACTIONPATHBYESSTYPEID[attributes.ESSTypeID]
        navyID = CORPIDBYFACTIONID[attributes.ESSTypeID]
        self.SetCaption(GetByLabel(CAPTIONBYESSTYPEID[attributes.ESSTypeID]))
        self.myContribution = 0
        self.amountInTags = 0
        mainCont = Container(name='mainCont', parent=self.sr.main, padding=const.defaultPadding)
        iconCont = Container(name='iconCont', parent=mainCont, align=uiconst.TOTOP, height=64)
        headerCont = Container(name='headerCont', parent=mainCont, align=uiconst.TOTOP, height=54, padBottom=6)
        buttonsCont = Container(name='buttonsCont', parent=mainCont, align=uiconst.TOBOTTOM, height=80, padTop=4, padBottom=4)
        listCont = Container(name='listCont', parent=mainCont, align=uiconst.TOALL, padBottom=14)
        factionLogo = Sprite(parent=iconCont, align=uiconst.CENTERTOP, width=64, height=64, texturePath=factionResPath)
        factionLogo.hint = cfg.eveowners.Get(navyID).name
        factionLogo.OnClick = (self.OpenNavyInfo, navyID)
        EveLabelLarge(text=GetByLabel('UI/Inflight/Brackets/TotalBounty'), parent=headerCont, maxLines=1, align=uiconst.CENTERTOP)
        EveCaptionMedium(text=FmtISK(self.bountyAmount, 0), parent=headerCont, maxLines=1, align=uiconst.CENTERTOP, state=uiconst.UI_NORMAL, top=16)
        contributorsCont = Container(name='contributorsCont', parent=listCont, align=uiconst.TOLEFT_PROP, width=0.45)
        self.tagsCont = Container(name='tagsCont', parent=listCont, align=uiconst.TORIGHT_PROP, width=0.45)
        topSpaceCont = Container(name='topSpaceCont', parent=listCont, align=uiconst.TOALL)
        self.contributersList = ScrollContainer(name='contributersList', parent=contributorsCont, align=uiconst.TOALL)
        shareCont = Container(name='shareCont', parent=buttonsCont, align=uiconst.TOLEFT_PROP, width=0.45)
        takeCont = Container(name='takeCont', parent=buttonsCont, align=uiconst.TORIGHT_PROP, width=0.45)
        spaceCont = Container(name='spaceCont', parent=buttonsCont, align=uiconst.TOALL)
        youGetLabel = EveLabelMedium(text=GetByLabel('UI/Inflight/Brackets/YouGet'), parent=shareCont, align=uiconst.CENTERTOP, top=1)
        myContribLabel = EveLabelLargeBold(text='', parent=shareCont, align=uiconst.CENTERTOP, top=16)
        shareLabel = EveLabelSmall(text=GetByLabel('UI/Inflight/Brackets/EveryoneGetsTheirShare'), parent=shareCont, align=uiconst.CENTERBOTTOM)
        shareBtn = Button(parent=shareCont, label=GetByLabel('UI/Inflight/Brackets/Share'), align=uiconst.TOBOTTOM, top=20, func=self.ShareContribution)
        orLabel = EveLabelLargeBold(text=GetByLabel('UI/Inflight/Brackets/Or'), parent=spaceCont, align=uiconst.CENTER, top=10)
        amountInTagsLabel = EveLabelLarge(text=GetByLabel('UI/Inflight/Brackets/AmountInTags', amount=FmtISK(0, 0)), parent=takeCont, align=uiconst.CENTERTOP, top=16)
        takeLabel = EveLabelSmall(text=GetByLabel('UI/Inflight/Brackets/OthersGetNothing'), parent=takeCont, align=uiconst.CENTERBOTTOM)
        takeAllBtn = Button(parent=takeCont, label=GetByLabel('UI/Inflight/Brackets/TakeAll'), align=uiconst.TOBOTTOM, top=20, func=self.TakeAll)
        self.LoadContributions(attributes.contributions)
        myContribLabel.SetText(FmtISK(self.myContribution, 0))
        self.LoadTags()
        amountInTagsLabel.SetText(GetByLabel('UI/Inflight/Brackets/AmountInTags', amount=FmtISK(self.amountInTags, 0)))

    def LoadContributions(self, contributions):
        if not contributions:
            return
        charIDs = {c.charID for c in contributions}
        cfg.eveowners.Prime(charIDs)
        for contribution in contributions:
            if contribution.charID == session.charid:
                self.myContribution = contribution.amount
            elif not contribution.amount:
                continue
            CollaboratorCont(parent=self.contributersList, charID=contribution.charID, amount=contribution.amount)

    def LoadTags(self):
        totalAmount = 0
        for tagTypeID, tagCount, iskAmount in self.component.tagCalculator.GetAllTagsAndAmount(self.bountyAmount):
            TagCont(parent=self.tagsCont, iskAmount=iskAmount, amount=tagCount, typeID=tagTypeID)
            totalAmount += iskAmount * tagCount

        self.amountInTags = totalAmount

    def ShareContribution(self, *args):
        self.bountyEscrow.DistributeEvenly()
        self.CloseByUser()

    def TakeAll(self, *args):
        self.bountyEscrow.TakeAll()
        self.CloseByUser()

    def OpenNavyInfo(self, navyID, *args):
        sm.GetService('info').ShowInfo(const.typeCorporation, navyID)


class CollaboratorCont(Container):
    """
    This class draws containers we use for contributers in a bounty pool
    """
    __guid__ = 'uicls.CollaboratorCont'
    default_height = 20
    default_state = uiconst.UI_NORMAL
    default_align = uiconst.TOTOP

    def ApplyAttributes(self, attributes):
        self.amountLabel = None
        Container.ApplyAttributes(self, attributes)
        charID = attributes.Get('charID', None)
        amount = attributes.Get('amount', 0)
        contribName = cfg.eveowners.Get(charID).name
        contribType = cfg.eveowners.Get(charID).typeID
        contributerName = GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=contribName, info=('showinfo', contribType, charID))
        mainCont = Container(name='mainCont', parent=self, padding=const.defaultPadding)
        self.nameLabel = EveLabelSmall(text=contributerName, parent=mainCont, maxLines=1, state=uiconst.UI_NORMAL)
        self.amountLabel = EveLabelSmall(text=FmtISK(amount, 0), parent=mainCont, align=uiconst.TORIGHT, maxLines=1)
        width, height = self.GetAbsoluteSize()
        self._OnSizeChange_NoBlock(width, height)

    def _OnSizeChange_NoBlock(self, newWidth, newHeight):
        Container._OnSizeChange_NoBlock(self, newWidth, newHeight)
        if self.amountLabel is not None:
            textWidth = self.amountLabel.textwidth
            availableTextWidth = newWidth - textWidth - 14
            self.nameLabel.SetRightAlphaFade(fadeEnd=availableTextWidth, maxFadeWidth=20)


class TagCont(Container):
    """
    This class draws containers we use for tags you get from a bounty pool
    """
    __guid__ = 'uicls.TagCont'
    default_height = 20
    default_state = uiconst.UI_NORMAL
    default_align = uiconst.TOTOP

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        typeID = attributes.Get('typeID', None)
        iskAmount = attributes.Get('iskAmount', 0)
        amount = attributes.Get('amount', 0)
        typeName = cfg.invtypes.Get(typeID).typeName
        mainCont = Container(name='mainCont', parent=self)
        iconCont = Container(name='iconCont', parent=mainCont, align=uiconst.TOLEFT, width=18)
        textCont = Container(name='textCont', parent=mainCont, align=uiconst.TOALL, padding=const.defaultPadding)
        icon = Icon(parent=iconCont, align=uiconst.TOALL, size=18, typeID=typeID, ignoreSize=True)
        icon.OnClick = (self.ShowInfo, None, typeID)
        icon.hint = typeName
        iskLabel = EveLabelSmall(text=FmtISK(iskAmount, 0), parent=textCont, align=uiconst.TORIGHT, maxLines=1)
        amountLabel = EveLabelSmall(text='%ix' % amount, parent=textCont, align=uiconst.TOLEFT, maxLines=1)
        if amount == 0:
            mainCont.opacity = 0.5

    def ShowInfo(self, itemID, typeID, *args):
        sm.GetService('info').ShowInfo(typeID, itemID)
