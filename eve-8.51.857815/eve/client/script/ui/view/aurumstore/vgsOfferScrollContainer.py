#Embedded file name: eve/client/script/ui/view/aurumstore\vgsOfferScrollContainer.py
from carbonui.control.scrollContainer import ScrollContainer
from eve.client.script.ui.util.uiComponents import RunThreadOnce
LAZY_LOADING_BUFFER = 0.9
UPDATE_CONTENT_THREAD_KEY = '.'.join([__name__, 'UpdateContent'])

class OfferScrollContainer(ScrollContainer):
    default_name = 'OfferScrollContainer'
    pushContent = False

    def __init__(self, *args, **kwargs):
        ScrollContainer.__init__(self, *args, **kwargs)
        self.contentLoader = None
        self.runningScrollUpdate = False
        self.clipCont.clipChildren = False

    def RegisterContentLoader(self, contentLoader):
        if self.contentLoader:
            self.contentLoader.onUpdate.disconnect(self.UpdateContent)
        self.contentLoader = contentLoader
        self.contentLoader.onUpdate.connect(self.UpdateContent)

    def OnScrolledVertical(self, posFraction):
        self.UpdateContent()

    @RunThreadOnce(UPDATE_CONTENT_THREAD_KEY)
    def UpdateContent(self):
        while self.ShouldLoadAdditionalContent():
            self.contentLoader.LoadAdditionalContent()

        self._UpdateScrollbars()

    def ShouldLoadAdditionalContent(self):
        if not self.contentLoader.HasAdditionalContent():
            return False
        if not self.verticalScrollBar.display:
            return True
        scrollHandleBottom = self.verticalScrollBar.handlePos + self.verticalScrollBar.handleSize
        return scrollHandleBottom > LAZY_LOADING_BUFFER
