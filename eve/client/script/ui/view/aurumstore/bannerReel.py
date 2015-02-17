#Embedded file name: eve/client/script/ui/view/aurumstore\bannerReel.py
import logging
import urlparse
from carbonui.primitives.container import Container
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.fill import Fill
from carbonui.primitives.sprite import Sprite
import carbonui.const as uiconst
from eve.client.script.ui.view.viewStateConst import ViewState
import uthread
from carbon.common.script.util.timerstuff import AutoTimer
from eve.client.script.ui.util.uiComponents import ButtonEffect, Component
from vgsclient.banners import GetBanners
import blue
log = logging.getLogger(__name__)
DEFAULT_BANNER_WIDTH = 800
DEFAULT_BANNER_HEIGHT = 200
BUTTON_WIDTH = 18
BUTTON_HEIGHT = 18
BANNER_FEED_CHANNEL_ID = 90
TRANSITION_DELAY_AUTO = 7500
TRANSITION_DELAY_MANUAL = 15000
PLEX_TARGET_KEY = 'plex'
AURUM_TARGET_KEY = 'aurum'
PLEX_TARGET_DEFAULT_VALUE = 'https://secure.eveonline.com/PLEX/?utm_source=new%20eden%20store&utm_medium=banner&utm_content=plex&utm_campaign=plex'
AURUM_TARGET_DEFAULT_VALUE = 'https://secure.eveonline.com/AurStore/?utm_source=new%20eden%20store&utm_medium=banner&utm_content=aurum&utm_campaign=aurum'

class BannerReel(ContainerAutoSize):
    default_name = 'AdBannerReel'
    default_clipChildren = True

    def ApplyAttributes(self, attributes):
        ContainerAutoSize.ApplyAttributes(self, attributes)
        bannerWidth = attributes.bannerWidth or DEFAULT_BANNER_WIDTH
        bannerHeight = attributes.bannerHeight or DEFAULT_BANNER_HEIGHT
        imageContainer = Container(name='imageContainer', parent=self, align=uiconst.TOTOP, width=bannerWidth, height=bannerHeight, clipChildren=True)
        self.bannerSprite = Sprite(name='bannerSprite', parent=imageContainer, align=uiconst.CENTER, width=bannerWidth, height=bannerHeight)
        self.transitionSprite = Sprite(name='animSprite', parent=imageContainer, align=uiconst.CENTER, width=bannerWidth, height=bannerHeight)
        bottomContainer = Container(parent=self, align=uiconst.TOTOP, height=BUTTON_HEIGHT + 8)
        self.buttonContainer = ContainerAutoSize(name='buttonContainer', parent=bottomContainer, align=uiconst.CENTER, height=BUTTON_HEIGHT)
        self.transitionTimer = None
        self.banners = []
        uthread.new(self._CreateBanners)

    def _OnClose(self):
        self.transitionTimer = None

    def HasBanners(self):
        """ Returns True if one or more banners are available. Otherwise return False """
        return len(self.banners) > 0

    def _CreateBanners(self):
        globalConfig = sm.GetService('machoNet').GetGlobalConfig()
        self.bannerTargets = {PLEX_TARGET_KEY: globalConfig.get('newedenstore.banner_target.plex', PLEX_TARGET_DEFAULT_VALUE),
         AURUM_TARGET_KEY: globalConfig.get('newedenstore.banner_target.aurum', AURUM_TARGET_DEFAULT_VALUE)}
        self.banners = GetBanners(session.languageID, boot.region, BANNER_FEED_CHANNEL_ID)
        if not self.HasBanners():
            self.display = False
            return
        self.currentBannerIndex = 0
        self.buttons = {}
        self.selectedButton = None
        for index, (bannerImageUrl, action) in enumerate(self.banners):
            self.buttons[bannerImageUrl] = BannerButton(parent=self.buttonContainer, align=uiconst.TOLEFT, bannerReel=self, bannerIndex=index)

        self.transitionTimer = AutoTimer(TRANSITION_DELAY_AUTO, self._AdvanceToNextBanner)
        self._SetBanner(self.currentBannerIndex)

    def _AdvanceToNextBanner(self):
        """ Show the next banner in the cycle, wrapping back to the start if required """
        nextBannerIndex = self.currentBannerIndex + 1
        if nextBannerIndex >= len(self.banners):
            nextBannerIndex = 0
        self._SetBanner(nextBannerIndex)

    def _SetBanner(self, bannerIndex, nextDelay = TRANSITION_DELAY_AUTO):
        """
        Show a banner that triggers an action when clicked.
        :param bannerIndex: Identifies which banner to show (index in to self.banners)
        :param nextDelay: Time delay (ms) to wait until the next auto transition
        """
        self.currentBannerIndex = bannerIndex
        bannerImageUrl, action = self.banners[self.currentBannerIndex]
        log.debug('_SetBanner %d (%s)', bannerIndex, bannerImageUrl)
        texture, w, h = sm.GetService('photo').GetTextureFromURL(bannerImageUrl)
        self.transitionSprite.texture = self.bannerSprite.texture
        self.bannerSprite.opacity = 0
        self.bannerSprite.texture = texture
        uicore.animations.FadeIn(self.bannerSprite)
        self.bannerSprite.OnClick = (self.OnBannerClicked, action, bannerImageUrl)
        if self.selectedButton is not None:
            self.selectedButton.SetSelected(False)
        self.selectedButton = self.buttons[bannerImageUrl]
        self.selectedButton.SetSelected(True)
        if self.transitionTimer is not None:
            self.transitionTimer.Reset(nextDelay)

    def OnBannerClicked(self, action, bannerImageUrl):
        log.debug('OnBannerClicked (%s)', action)
        if action.count('=') != 1:
            log.warn("Invalid banner action syntax: '%s' (should look like 'offerid=123')", action)
            return
        actionKey, actionValue = action.strip().lower().split('=')
        sm.GetService('viewState').GetView(ViewState.VirtualGoodsStore)._LogBannerClick(bannerImageUrl, actionKey, actionValue)
        if actionKey.strip() == 'offerid':
            try:
                offerId = int(actionValue.strip())
            except ValueError:
                log.warn("Invalid offerID attribute: '%s' (should look like 'offerid=123')", action)
                return

            uicore.cmd.ShowVgsOffer(offerId)
        elif actionKey.strip() == 'target':
            try:
                url = self.bannerTargets[actionValue.strip()]
            except KeyError:
                log.warn("Invalid banner target attribute: '%s' (should look like 'target=[plex|aurum]')", action)
                return

            parsedUrl = urlparse.urlparse(url)
            if parsedUrl.hostname != 'secure.eveonline.com':
                log.warn("Invalid banner target attribute: '%s' (hostname must be secure.eveonline.com)", url)
                return
            if parsedUrl.scheme != 'https':
                log.warn("Invalid banner target attribute: '%s' (scheme must be https)", url)
                return
            blue.os.ShellExecute(url)
        else:
            log.warn("Unrecognised banner action: '%s'", action)


def GetBannerButtonComponent(bgParent, _):
    return Fill(name='buttonShape', bgParent=bgParent, width=BUTTON_WIDTH, height=BUTTON_HEIGHT, padding=(3, 3, 3, 3))


@Component(ButtonEffect(opacityIdle=0.4, opacityHover=0.8, opacityMouseDown=0.9, bgElementFunc=GetBannerButtonComponent, audioOnClick='store_selectpage'))

class BannerButton(Container):
    default_name = 'bannerButton'
    default_width = BUTTON_WIDTH
    default_height = BUTTON_HEIGHT
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.selectedSprite = Fill(parent=self, align=uiconst.CENTER, width=BUTTON_WIDTH, height=BUTTON_HEIGHT, state=uiconst.UI_DISABLED, opacity=0, padding=(3, 3, 3, 3))
        self.bannerReel = attributes.bannerReel
        self.bannerIndex = attributes.bannerIndex

    def SetSelected(self, selected):
        """ Change the button appearance to a selected/deselected state """
        if selected:
            uicore.animations.FadeIn(self.selectedSprite, duration=0.3)
        else:
            uicore.animations.FadeOut(self.selectedSprite, duration=0.3)

    def OnClick(self, *args):
        self.bannerReel._SetBanner(self.bannerIndex, TRANSITION_DELAY_MANUAL)
