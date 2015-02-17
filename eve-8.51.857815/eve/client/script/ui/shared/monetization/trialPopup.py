#Embedded file name: eve/client/script/ui/shared/monetization\trialPopup.py
import carbonui.const as uiconst
import localization
import math
import trinity
import uthread
import util
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.flowcontainer import FlowContainer
from carbonui.primitives.gradientSprite import GradientConst, GradientSprite
from carbonui.primitives.sprite import Sprite
from carbonui.uianimations import animations
from eve.client.script.ui.control.buttons import Button
from eve.client.script.ui.control.eveWindow import Window
from eve.client.script.ui.control.eveWindowUnderlay import LineUnderlay
from eve.client.script.ui.control.eveLabel import EveCaptionMedium, EveLabelLarge
GRID_HEIGHT_OFFSET = 18
ORIGIN_CERTIFICATES = 'certificates'
ORIGIN_CHARACTERSELECTION = 'characterSelection'
ORIGIN_CHARACTERSHEET = 'charactersheet'
ORIGIN_CONTRACTS = 'contracts'
ORIGIN_CORPORATIONAPPLICATIONS = 'corporationApplications'
ORIGIN_INDUSTRY = 'industry'
ORIGIN_ISIS = 'isis'
ORIGIN_MARKET = 'market'
ORIGIN_SHOWINFO = 'showinfo'
ORIGIN_SKILLREQUIREMENT = 'skills'
ORIGIN_UNKNOWN = 'unknown'
ORIGINS = [ORIGIN_CERTIFICATES,
 ORIGIN_CHARACTERSELECTION,
 ORIGIN_CHARACTERSHEET,
 ORIGIN_CONTRACTS,
 ORIGIN_CORPORATIONAPPLICATIONS,
 ORIGIN_INDUSTRY,
 ORIGIN_ISIS,
 ORIGIN_MARKET,
 ORIGIN_SHOWINFO,
 ORIGIN_SKILLREQUIREMENT,
 ORIGIN_UNKNOWN]

class TrialPopup(Window):
    """
    Dialog shown to trial users when they try to do actions that require a subscription
    """
    __guid__ = 'form.TrialPopup'
    default_width = 460
    default_height = 100
    default_windowID = 'TrialPopup'
    default_topParentHeight = 0
    default_clipChildren = True
    default_isPinable = False

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.origin = attributes.get('origin', None)
        self.reason = attributes.get('reason', None)
        self.message = attributes.get('message', None)
        if self.origin not in ORIGINS:
            raise RuntimeError('Origin Not defined for upsell')
        self._LogWindowOpened()
        self.Layout()

    def Layout(self):
        """
        Setup UI controls for this window.
        """
        self.HideHeader()
        self.MakeUnResizeable()
        self.container = ContainerAutoSize(parent=self.GetMainArea(), align=uiconst.TOTOP, alignMode=uiconst.TOTOP, state=uiconst.UI_PICKCHILDREN, callback=self.OnContainerResized)
        headerCont = ContainerAutoSize(parent=self.container, align=uiconst.TOTOP)
        EveCaptionMedium(parent=headerCont, align=uiconst.CENTERTOP, text=localization.GetByLabel('UI/TrialUpsell/Header'), padding=(0, 8, 0, 4))
        LineUnderlay(parent=self.container, align=uiconst.TOTOP, padding=(2, 0, 2, 0))
        bodyCont = ContainerAutoSize(parent=self.container, align=uiconst.TOTOP, alignMode=uiconst.TOTOP)
        mainCont = ContainerAutoSize(parent=bodyCont, align=uiconst.TOTOP, alignMode=uiconst.TOTOP)
        GradientSprite(bgParent=bodyCont, rgbData=[(0, (0.138, 0.138, 0.08)), (0.6, (0.06, 0.06, 0.06)), (1.0, (0.1, 0.1, 0.1))], alphaData=[(0.0, 0.8), (1.0, 0.2)], alphaInterp=GradientConst.INTERP_LINEAR, colorInterp=GradientConst.INTERP_LINEAR, rotation=-math.pi / 2, padding=(2, 0, 2, 2))
        EveLabelLarge(parent=mainCont, align=uiconst.TOTOP, text=localization.GetByLabel('UI/TrialUpsell/Greeting'), padding=(160, 18, 20, 8))
        EveLabelLarge(parent=mainCont, align=uiconst.TOTOP, text=self.message or localization.GetByLabel('UI/TrialUpsell/DefaultBody'), padding=(160, 0, 20, 8))
        EveLabelLarge(parent=mainCont, align=uiconst.TOTOP, text=localization.GetByLabel('UI/TrialUpsell/Footer'), padding=(160, 0, 20, 16))
        trialDays = sm.RemoteSvc('userSvc').GetTrialDaysRemaining()
        EveLabelLarge(parent=mainCont, align=uiconst.TOTOP, text=localization.GetByLabel('UI/TrialUpsell/TrialTimeLeft', daysLeft=trialDays.daysLeft, daysTotal=trialDays.trialLen), color=(0.8, 0.6, 0.2, 0.8), padding=(160, 0, 20, 8))
        self.iconGlow = Sprite(parent=mainCont, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/Monetization/Trial_Icon_Glow_256.png', left=-20, width=200, height=200)
        Sprite(parent=mainCont, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/Monetization/Trial_Icon_NoGlow_256.png', left=-20, width=200, height=200)
        self.iconGlare1 = Sprite(parent=mainCont, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/Monetization/glare_256_1.png', textureSecondaryPath='res:/UI/Texture/classes/Monetization/Trial_Icon_NoGlow_256.png', spriteEffect=trinity.TR2_SFX_MODULATE, blendMode=trinity.TR2_SBM_ADDX2, left=-20, width=200, height=200, tileX=True, tileY=True)
        self.iconGlare2 = Sprite(parent=mainCont, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/Monetization/glare_256_2.png', textureSecondaryPath='res:/UI/Texture/classes/Monetization/Trial_Icon_NoGlow_256.png', spriteEffect=trinity.TR2_SFX_MODULATE, left=-20, width=200, height=200, tileX=True, tileY=True)
        buttonCont = FlowContainer(parent=bodyCont, align=uiconst.TOTOP, centerContent=True, contentSpacing=(4, 4), padding=(8, 16, 8, 16))
        closeButton = Button(parent=buttonCont, align=uiconst.NOALIGN, fixedheight=26, label=localization.GetByLabel('UI/TrialUpsell/ButtonClose'), fontsize=12, func=lambda _: self.Close(), color=(0.2, 0.2, 0.2, 1.0))
        closeButton.sr.activeframe.SetFixedColor((0.6, 0.6, 0.6, 1.0))
        moreButton = Button(parent=buttonCont, align=uiconst.NOALIGN, fixedheight=26, label=localization.GetByLabel('UI/TrialUpsell/ButtonSubscribe'), fontsize=14, func=lambda _: self.OpenSubscriptionPage(), color=(0.8, 0.6, 0.2, 0.6))
        moreButton.sr.activeframe.SetFixedColor((0.9, 0.9, 0.9, 1.0))
        self.Animate()

    def Animate(self):
        animations.FadeTo(self.iconGlow, startVal=1.0, endVal=0.4, duration=1.0, timeOffset=0.4, curveType=uiconst.ANIM_WAVE)
        animations.MorphScalar(self.iconGlare1, 'rectLeft', startVal=-150, endVal=200, duration=0.8, timeOffset=0.4)
        animations.MorphScalar(self.iconGlare2, 'rectTop', startVal=100, endVal=50, duration=1.2)
        animations.MorphScalar(self.iconGlare2, 'rectLeft', startVal=-60, endVal=20, duration=1.2)

    def OpenSubscriptionPage(self):
        uicore.cmd.OpenSubscriptionPage(self.origin, self.reason)
        self.Close()

    def OnContainerResized(self):
        """
        Callback for the parent auto resized container, we set the overall window height
        to fit the contents of the resizeable container here. This allows localized text
        to wrap around and push out the height of this window.
        """
        self.height = self.container.height
        self.width = self.default_width

    def _LogWindowOpened(self):
        with util.ExceptionEater('eventLog'):
            uthread.new(sm.ProxySvc('eventLog').LogClientEvent, 'trial', ['origin', 'reason'], 'ShowUpsellWindow', self.origin, self.reason)
