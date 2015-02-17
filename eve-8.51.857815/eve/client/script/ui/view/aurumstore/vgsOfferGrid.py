#Embedded file name: eve/client/script/ui/view/aurumstore\vgsOfferGrid.py
from carbonui.primitives.flowcontainer import FlowContainer
from eve.client.script.ui.view.aurumstore.vgsHelper import FormatAUR
from eve.client.script.ui.view.aurumstore.vgsOffer import VgsOffer
from eve.client.script.ui.view.aurumstore.vgsUiConst import CONTENT_PADDING, OFFER_COLUMNS
from fsdlite.signal import Signal
import carbonui.const as uiconst
MAX_OFFER_IMAGE_SIZE = 512

def UpdateCellSize(offer, cellWidth):
    offer.width = cellWidth
    offer.height = cellWidth


class OfferGrid(FlowContainer):
    default_name = 'OfferGrid'

    def __init__(self, incrementSize = 4, **kwargs):
        FlowContainer.__init__(self, **kwargs)
        self.offers = []
        self.index = 0
        self.incrementSize = incrementSize
        self.onUpdate = Signal()

    def SetOffers(self, offers):
        self.Flush()
        self.FlagAlignmentDirty()
        self.UpdateAlignment()
        self.index = 0
        self.offers = offers
        self.onUpdate()

    def GetOffers(self):
        return self.offers

    def SetParentWidth(self, parentWidth):
        self.parentWidth = parentWidth
        self.UpdateCellWidths()

    def _OnResize(self, *args):
        self.UpdateCellWidths()

    def UpdateCellWidths(self):
        cellWidth = self.GetCellWidth()
        for offerGridCell in self.children:
            UpdateCellSize(offerGridCell, cellWidth)
            self.FlagAlignmentDirty()

    def GetCellWidth(self):
        width, _ = self.GetAbsoluteSize()
        return (width - CONTENT_PADDING * (OFFER_COLUMNS - 1)) / OFFER_COLUMNS

    def HasAdditionalContent(self):
        return len(self.offers) > self.index

    def LoadAdditionalContent(self):
        for i in range(self.incrementSize):
            if self.index >= len(self.offers):
                break
            offer = self.offers[self.index]
            VgsOffer(parent=self, width=MAX_OFFER_IMAGE_SIZE, height=MAX_OFFER_IMAGE_SIZE, align=uiconst.NOALIGN, offer=offer, image=offer.imageUrl, state=uiconst.UI_NORMAL, upperText=offer.name, lowerText=FormatAUR(offer.price))
            self.index += 1

        self.UpdateCellWidths()
