#Embedded file name: eve/client/script/ui/view/aurumstore\aurumStoreContainer.py
import logging
import collections
import math
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.gradientSprite import GradientSprite
from eve.client.script.ui.control.eveSinglelineEdit import SinglelineEdit
from eve.client.script.ui.shared.redeem.redeemPanel import RedeemPanel
from eve.client.script.ui.util.uiComponents import RunThreadOnce
from eve.client.script.ui.view.aurumstore.vgsOffer import VgsOffer
from eve.client.script.ui.view.aurumstore.vgsOfferFilterBar import VgsOfferFilterBar
from eve.client.script.ui.view.aurumstore.vgsOfferGrid import OfferGrid, MAX_OFFER_IMAGE_SIZE
from eve.client.script.ui.view.aurumstore.vgsOfferScrollContainer import OfferScrollContainer
from carbonui.primitives.flowcontainer import FlowContainer
from carbonui.primitives.gridcontainer import GridContainer
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.util.focusUtil import postponeUntilFocus
from eve.client.script.ui.view.aurumstore.bannerReel import BannerReel
from eve.client.script.ui.view.aurumstore.vgsUiConst import CONTENT_PADDING, MAX_CONTENT_WIDTH, OFFER_COLUMNS
from eve.client.script.ui.view.aurumstore.vgsUiConst import BACKGROUND_COLOR, HEADER_BG_COLOR
from eve.client.script.ui.view.aurumstore.vgsUiConst import REDEEM_BUTTON_BACKGROUND_COLOR, REDEEM_BUTTON_FILL_COLOR
from eve.client.script.ui.view.aurumstore.vgsUiPrimitives import TAG_COLOR, CATEGORY_COLOR, VgsFilterCombo, LogoHomeButton, AurLabelHeader
from eve.client.script.ui.view.aurumstore.vgsUiPrimitives import ExitButton
from eve.client.script.ui.view.aurumstore.vgsUiPrimitives import HeaderBuyAurButton
from eve.client.script.ui.view.aurumstore.vgsUiPrimitives import CategoryButton
from eve.client.script.ui.view.aurumstore.vgsUiPrimitives import SubCategoryButton
import carbonui.const as uiconst
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
import localization
from eve.client.script.ui.view.viewStateConst import ViewState
logger = logging.getLogger(__name__)
HEADER_HEIGHT = 100
HEADER_PADDING = 2
CATEGORIES_HEIGHT = 36
AD_HEIGHT = 256
CAPTION_HEIGHT = 30
CAPTION_OFFSET = 35
SEARCH_BOX_WIDTH = 300
CONTENT_SLIP_UNDER_AREA_OPACITY = 0.8
SORT_PRICE_ASCENDING = 1
SORT_PRICE_DESCENDING = 2
SORT_NAME_ASCENDING = 3
SORT_NAME_DESCENDING = 4
DEFAULT_SORT_SELECTION = SORT_NAME_ASCENDING
PAGE_HOME = 1
PAGE_CATEGORY = 2
PAGE_SUBCATEGORY = 3
PAGE_SEARCH = 4
THREAD_KEY_LOAD_PAGE = 'VGS.LoadPage'
ProductOffer = collections.namedtuple('ProductOffer', ['url',
 'title',
 'image',
 'cost'])
SubCategory = collections.namedtuple('SubCategory', ['id', 'title'])

def SortByPrice(offers, ascending):
    return sorted(offers, key=lambda offer: offer.price, reverse=not ascending)


def SortByName(offers, ascending):
    return localization.util.Sort(offers, key=lambda offer: offer.name, reverse=not ascending)


def GetSortOrder():
    return settings.user.ui.Get('VgsOfferSortOrder', DEFAULT_SORT_SELECTION)


def SortOffers(offers):
    offerOrder = GetSortOrder()
    sortedOffers = offers
    if offerOrder == SORT_PRICE_DESCENDING:
        sortedOffers = SortByPrice(offers, False)
    elif offerOrder == SORT_PRICE_ASCENDING:
        sortedOffers = SortByPrice(offers, True)
    elif offerOrder == SORT_NAME_DESCENDING:
        sortedOffers = SortByName(offers, False)
    elif offerOrder == SORT_NAME_ASCENDING:
        sortedOffers = SortByName(offers, True)
    return sortedOffers


class Tag:

    def __init__(self, tagId, name):
        self.id = tagId
        self.name = name


class AurumStoreContainer(Container):
    default_name = 'AurumStoreContainer'
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.store = sm.GetService('vgsService').GetStore()
        self.tagsByCategoryId = {}
        self.selectedRootCategoryId = None
        self.selectedCategoryId = None
        self.activeTagsByRootCategoryId = {}
        self.page = None
        Fill(bgParent=self, color=BACKGROUND_COLOR)
        self.CreateRedeemingPanelLayout()
        self.CreateBaseLayout()
        self.CreateHeaderLayout()
        self.CreateContentLayout()
        self.SetFilterOptions()
        self.currentAurBalance = 0
        self._OnResize()

    def _OnResize(self, *args):
        top, left, width, height = self.GetAbsolute()
        contentWidth = min(MAX_CONTENT_WIDTH, width)
        self.leftContainer.width = (width - contentWidth) / 2
        self.contentContainer.width = contentWidth
        self.rightContainer.width = width - self.leftContainer.width - contentWidth
        self.redeemingPanel.width = width
        if hasattr(self, 'grid'):
            self.grid.SetParentWidth(self.contentContainer.width)
        self.SetSidebarContentMask()

    def CreateHeaderLayout(self):
        contentContainer = Container(parent=self.headerContainer, align=uiconst.TOTOP, height=CAPTION_HEIGHT, top=CAPTION_OFFSET)
        LogoHomeButton(parent=self.headerContainer, align=uiconst.TOPLEFT, onClick=self.OnClickHomeButton)
        ExitButton(parent=self.headerContainer, align=uiconst.TOPRIGHT, onClick=uicore.cmd.ToggleAurumStore, top=4, left=10, hint=localization.GetByLabel('UI/VirtualGoodsStore/ExitStore'))
        self.aurButton = HeaderBuyAurButton(parent=contentContainer, align=uiconst.TORIGHT, onClick=self._BuyAurum, padding=(4, 0, 4, 0), left=6)
        cont = Container(name='AurContainer', parent=contentContainer, align=uiconst.TORIGHT, width=200, padRight=8)
        self.aurLabel = AurLabelHeader(parent=cont, align=uiconst.CENTERRIGHT, height=32, amount=100, padTop=1)

    def _BuyAurum(self):
        sm.GetService('audio').SendUIEvent('store_aur')
        sm.GetService('viewState').GetView(ViewState.VirtualGoodsStore)._LogBuyAurum('TopButton')
        uicore.cmd.BuyAurumOnline()

    def SetSidebarContentMask(self):
        for container in (self.leftContainer, self.rightContainer):
            container.Flush()
            GradientSprite(name='OfferSlipGradient', align=uiconst.TOTOP, parent=container, rgbData=((0.0, BACKGROUND_COLOR[:3]),), alphaData=((0.0, CONTENT_SLIP_UNDER_AREA_OPACITY), (0.5, 1.0), (1.0, 1.0)), height=self.topContainer.height + self.filterContainer.height + HEADER_PADDING, rotation=math.pi / 2)

    def CreateBaseLayout(self):
        wholeWidthContainer = Container(parent=self, name='WholeWindowContainer', align=uiconst.TOALL)
        self.leftContainer = Container(parent=wholeWidthContainer, name='LeftSideBar', align=uiconst.TOLEFT)
        self.rightContainer = Container(parent=wholeWidthContainer, name='RightSideBar', align=uiconst.TORIGHT)
        self.contentContainer = Container(parent=wholeWidthContainer, name='Content', align=uiconst.TOLEFT)
        self.topContainer = ContainerAutoSize(name='Top Container', parent=self.contentContainer, align=uiconst.TOTOP)
        Fill(name='SlipUnderLayer', bgParent=self.topContainer, color=BACKGROUND_COLOR)
        self.headerContainer = Container(parent=self.topContainer, name='Header', align=uiconst.TOTOP, bgColor=HEADER_BG_COLOR, height=HEADER_HEIGHT, clipChildren=True)
        self.categoryContainer = Container(parent=self.topContainer, name='Categories', align=uiconst.TOTOP, height=CATEGORIES_HEIGHT, padTop=HEADER_PADDING, state=uiconst.UI_PICKCHILDREN)
        self.subCategoryContainer = Container(name='SubCategories', parent=self.topContainer, align=uiconst.TOTOP, padTop=HEADER_PADDING, bgColor=TAG_COLOR, state=uiconst.UI_PICKCHILDREN, clipChildren=True)
        self.subCategoryButtonContainer = FlowContainer(name='SubCategoryButtons', parent=self.subCategoryContainer, centerContent=True, align=uiconst.TOTOP, contentSpacing=(1, 0), state=uiconst.UI_PICKCHILDREN)
        self.filterContainer = Container(name='Filter', parent=self.contentContainer, align=uiconst.TOTOP, padTop=HEADER_PADDING, state=uiconst.UI_PICKCHILDREN, height=CATEGORIES_HEIGHT)

    def CreateContentLayout(self):
        self.contentScroll = OfferScrollContainer(parent=self.contentContainer, align=uiconst.TOALL)
        self.banner = BannerReel(parent=self.contentScroll, align=uiconst.TOTOP, bannerWidth=MAX_CONTENT_WIDTH, bannerHeight=AD_HEIGHT)
        self.grid = OfferGrid(parent=self.contentScroll, align=uiconst.TOTOP, contentSpacing=(CONTENT_PADDING, CONTENT_PADDING), padBottom=CONTENT_PADDING, columns=OFFER_COLUMNS, incrementSize=OFFER_COLUMNS)
        for x in xrange(4 * OFFER_COLUMNS):
            offer = VgsOffer(parent=self.grid, width=MAX_OFFER_IMAGE_SIZE, height=MAX_OFFER_IMAGE_SIZE, align=uiconst.NOALIGN)

        self.contentScroll.RegisterContentLoader(self.grid)

    def CreateRedeemingPanelLayout(self):
        instructionText = '<url=localsvc:service=vgsService&method=ShowRedeemUI>%s</url>' % (localization.GetByLabel('UI/RedeemWindow/ClickToInitiateRedeeming'),)
        self.redeemingPanel = RedeemPanel(parent=self, align=uiconst.TOBOTTOM, dragEnabled=False, instructionText=instructionText, redeemButtonBackgroundColor=REDEEM_BUTTON_BACKGROUND_COLOR, redeemButtonFillColor=REDEEM_BUTTON_FILL_COLOR)
        self.redeemingPanel.UpdateDisplay()

    def SelectCategory(self, categoryId):
        self.selectedRootCategoryId = categoryId
        for button in self.categoryButtons:
            if button.isActive and button.categoryId != categoryId:
                button.SetActive(False)

    def SelectSubCategory(self, subcategoryId):
        self.selectedCategoryId = subcategoryId
        for button in self.subcategoryButtons:
            if button.isActive and button.categoryId != subcategoryId:
                button.SetActive(False)

    def OnClickCategory(self, categoryId):
        self.LoadCategoryPage(categoryId)

    @RunThreadOnce(THREAD_KEY_LOAD_PAGE)
    def LoadCategoryPage(self, categoryId):
        if self.page == PAGE_CATEGORY and self.selectedRootCategoryId == categoryId and self.selectedCategoryId is None:
            return
        logger.debug('Loading category page: %s', categoryId)
        self.SelectCategory(categoryId)
        categoriesById = self.store.GetCategories()
        category = categoriesById[categoryId]
        subcategories = [ categoriesById[subCatId] for subCatId in category.subcategories ]
        subcategories = localization.util.Sort(subcategories, key=lambda c: c.name)
        self.SetSubCategories(subcategories)
        self.SelectSubCategory(None)
        self.SetOffersAndTags(categoryId)
        self.page = PAGE_CATEGORY

    def OnClickSubCategory(self, subcategoryId):
        self.LoadSubCategoryPage(subcategoryId)

    @RunThreadOnce(THREAD_KEY_LOAD_PAGE)
    def LoadSubCategoryPage(self, subcategoryId):
        if self.page == PAGE_SUBCATEGORY and self.selectedCategoryId == subcategoryId:
            return
        logger.debug('Loading sub category page: %s', subcategoryId)
        self.selectedCategoryId = subcategoryId
        self.SetOffersAndTags(subcategoryId)
        self.SelectSubCategory(subcategoryId)
        self.page = PAGE_SUBCATEGORY

    def SetOffersAndTags(self, categoryId):
        tags = self.store.GetTagsByCategoryId(categoryId)
        self.SetFilterTags(tags)
        tagIds = self.filterBar.GetSelectedFilterTagIds()
        offers = self.store.GetFilteredOffers(categoryId, tagIds)
        self.HideBanner()
        self.SetOffers(offers)

    @RunThreadOnce(THREAD_KEY_LOAD_PAGE)
    def OnClickHomeButton(self):
        self.LoadLandingPage()

    def LoadLandingPage(self):
        logger.debug('LoadLandingPage')
        if self.page == PAGE_HOME:
            return
        logger.debug('Loading landing page')
        self._SetSubCategories(None)
        self.SelectCategory(None)
        self.SelectSubCategory(None)
        self.SetFilterTags([])
        self.ShowBanner()
        offers = self.store.GetOffers().values()
        self.SetOffers(offers)
        self.page = PAGE_HOME

    @RunThreadOnce('VGS.ShowBanner')
    def ShowBanner(self):
        if self.banner.HasBanners() and not self.banner.display:
            self.banner.top = 0
            self.banner.display = True
            self.SetSubCategories(None)
            uicore.animations.MoveInFromTop(self.banner, amount=self.banner.height, sleep=True)

    @RunThreadOnce('VGS.HideBanner')
    def HideBanner(self):
        uicore.animations.MoveOutTop(self.banner, amount=self.banner.height, sleep=True)
        self.banner.top = 0
        self.banner.display = False

    @postponeUntilFocus
    def SetAUR(self, amount):
        logger.debug('SetAUR %s', amount)
        uicore.animations.MorphScalar(self, 'currentAurBalance', startVal=self.currentAurBalance, endVal=amount, curveType=uiconst.ANIM_SMOOTH, duration=1.5, callback=lambda : self.SetCurrentAurBalance(amount))

    def SetCurrentAurBalance(self, amount):
        self._currentAurBalance = amount
        self.aurLabel.SetAmount(self._currentAurBalance)

    def GetCurrentAurBalance(self):
        return self._currentAurBalance

    currentAurBalance = property(GetCurrentAurBalance, SetCurrentAurBalance)

    def SetCategories(self, categories):
        logger.debug('SetCategories %s', categories)
        self.categoryContainer.Flush()
        searchContainer = Container(name='SearchBox', parent=self.categoryContainer, width=SEARCH_BOX_WIDTH, align=uiconst.TORIGHT)
        categoryButtonsContainer = GridContainer(name='ButtonGrid', parent=self.categoryContainer, align=uiconst.TOALL, columns=len(categories), lines=1)
        tagById = self.store.GetTags()
        self.categoryButtons = []
        for category in categories:
            button = CategoryButton(parent=categoryButtonsContainer, categoryId=category.id, label=category.name, align=uiconst.TOALL, onClick=self.OnClickCategory, padRight=1)
            self.categoryButtons.append(button)
            tags = []
            for tagId in category.tagIds:
                tag = tagById.get(tagId)
                if tag:
                    tags.append(Tag(tag.id, tag.name))

            self.tagsByCategoryId[category.id] = tags

        iconContainer = Container(name='SearchIconContainer', parent=searchContainer, width=CATEGORIES_HEIGHT, align=uiconst.TOLEFT, bgColor=CATEGORY_COLOR)
        Sprite(parent=iconContainer, texturePath='res:/UI/Texture/Vgs/Search_icon.png', width=32, height=32, align=uiconst.CENTER)
        self.searchEdit = SinglelineEdit(parent=searchContainer, align=uiconst.TORIGHT, pos=(0,
         0,
         SEARCH_BOX_WIDTH - CATEGORIES_HEIGHT - 2,
         0), fontsize=16, padding=(1, 0, 0, 0), OnChange=self.Search, bgColor=TAG_COLOR)
        self.searchEdit.ShowClearButton(icon='res:/UI/Texture/Icons/73_16_45.png')
        self.searchEdit.SetHistoryVisibility(False)
        self.searchEdit.sr.background.Hide()

    @RunThreadOnce(THREAD_KEY_LOAD_PAGE)
    def Search(self, searchString):
        self.page = PAGE_SEARCH
        self.HideBanner()
        self.SelectSubCategory(None)
        self.SelectCategory(None)
        self._SetSubCategories(None)
        self.SetFilterTags([])
        sm.GetService('viewState').GetView(ViewState.VirtualGoodsStore).Search(searchString)

    @RunThreadOnce('VGS.SetSubCategories')
    def SetSubCategories(self, subcategories):
        self._SetSubCategories(subcategories)

    def _SetSubCategories(self, subcategories):
        self.subCategoryButtonContainer.Flush()
        self.subcategoryButtons = []
        if subcategories is None:
            if self.subCategoryContainer.height > 0:
                uicore.animations.MorphScalar(self.subCategoryContainer, attrName='height', startVal=self.subCategoryContainer.height, endVal=0, duration=0.5, callback=self.SetSidebarContentMask)
        else:
            if int(self.subCategoryContainer.height) != CATEGORIES_HEIGHT:
                uicore.animations.MorphScalar(self.subCategoryContainer, attrName='height', startVal=self.subCategoryContainer.height, endVal=CATEGORIES_HEIGHT, duration=0.5, sleep=False, callback=self.SetSidebarContentMask)
            for subcategory in subcategories:
                button = SubCategoryButton(parent=self.subCategoryButtonContainer, label=subcategory.name, align=uiconst.NOALIGN, height=CATEGORIES_HEIGHT, categoryId=subcategory.id, onClick=self.OnClickSubCategory)
                self.subcategoryButtons.append(button)

    def SetOffers(self, offers):
        if self.selectedCategoryId is None and self.selectedRootCategoryId is None:
            specialOffers = [ o for o in offers if o.label is not None ]
            notSpecialOffers = [ o for o in offers if o.label is None ]
            offers = SortOffers(specialOffers)
            offers.extend(SortOffers(notSpecialOffers))
        else:
            offers = SortOffers(offers)
        self.grid.SetOffers(offers)

    def SetFilterOptions(self):
        self.filterContainer.Flush()
        Fill(name='SlipUnderLayer', bgParent=self.filterContainer, color=BACKGROUND_COLOR, opacity=CONTENT_SLIP_UNDER_AREA_OPACITY, padTop=-HEADER_PADDING * 2)
        options = [(localization.GetByLabel('UI/VirtualGoodsStore/Sorting/ByPriceAscending'), SORT_PRICE_ASCENDING),
         (localization.GetByLabel('UI/VirtualGoodsStore/Sorting/ByPriceDescending'), SORT_PRICE_DESCENDING),
         (localization.GetByLabel('UI/VirtualGoodsStore/Sorting/ByNameAscending'), SORT_NAME_ASCENDING),
         (localization.GetByLabel('UI/VirtualGoodsStore/Sorting/ByNameDescending'), SORT_NAME_DESCENDING)]
        self.filterCombo = VgsFilterCombo(parent=self.filterContainer, align=uiconst.TORIGHT, options=options, callback=self.OnSortOrderChanged, select=GetSortOrder(), padding=(4, 2, 0, 4))
        self.filterBar = VgsOfferFilterBar(parent=self.filterContainer, onFilterChanged=self.OnFilterChanged)

    def SetFilterTags(self, tags):
        activeTags = self.activeTagsByRootCategoryId.get(self.GetSelectedRootCategoryId(), {})
        self.subCategoryContainer.state = uiconst.UI_PICKCHILDREN
        self.filterBar.SetTags(tags, activeTags)

    def OnSortOrderChanged(self, combo, key, value):
        settings.user.ui.Set('VgsOfferSortOrder', value)
        sm.GetService('viewState').GetView(ViewState.VirtualGoodsStore)._LogFilterChange(value)
        self.SetOffers(self.grid.GetOffers())

    def OnFilterChanged(self):
        tagIds = self.filterBar.GetSelectedFilterTagIds()
        rootCategoryId = self.GetSelectedRootCategoryId()
        self.activeTagsByRootCategoryId[rootCategoryId] = tagIds
        offers = self.store.GetFilteredOffers(self.selectedCategoryId or rootCategoryId, tagIds)
        self.SetOffers(offers)

    def GetSelectedCategoryId(self):
        return self.selectedCategoryId

    def GetSelectedRootCategoryId(self):
        return self.selectedRootCategoryId

    def OnMouseWheel(self, dz):
        self.contentScroll.OnMouseWheel(dz)
