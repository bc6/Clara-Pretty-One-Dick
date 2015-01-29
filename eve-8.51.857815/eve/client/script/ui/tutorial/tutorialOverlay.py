#Embedded file name: eve/client/script/ui/tutorial\tutorialOverlay.py
from carbonui.control.layer import LayerCore
from carbonui.control.scrollContainer import ScrollContainer
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
from carbonui.primitives.sprite import Sprite
import carbonui.const as uiconst
import blue
import form
import uthread
OVERLAYROOT = 'res:/UI/Texture/Classes/Tutorial/\\OverlayAssets/'

class TutorialOverlay(LayerCore):
    __notifyevents__ = ['OnUIScalingChange',
     'OnUIRefresh',
     'OnSetDevice',
     'OnSessionChanged']

    def OnUIScalingChange(self, change, *args):
        self.Reload()

    def OnUIRefresh(self):
        self.Reload()

    def OnSetDevice(self):
        pass

    def Reload(self):
        self.CloseView()
        if session.solarsystemid:
            uthread.new(uicore.layer.tutorialOverlay.OpenView)

    def OnSessionChanged(self, isRemote, sess, change):
        if uicore.layer.tutorialOverlay.isopen and change.has_key('solarsystemid'):
            if not session.solarsystemid:
                uicore.layer.tutorialOverlay.CloseView()

    def OnOpenView(self):
        self.opacity = 0.0
        welcomeSprite = self.CreateSpriteObject(parent=self, texturePath=OVERLAYROOT + 'section_Welcome.png', align=uiconst.CENTERTOP)
        mainCenter = self.CreateSpriteObject(parent=self, texturePath=OVERLAYROOT + 'section_CameraControls.png', align=uiconst.CENTERBOTTOM, top=200)
        mainLeft = self.CreateSpriteObject(parent=self, texturePath=OVERLAYROOT + 'section_Interaction.png', align=uiconst.CENTERLEFT, left=100, top=-50)
        mainRight = self.CreateSpriteObject(parent=self, texturePath=OVERLAYROOT + 'section_Tooltips.png', align=uiconst.CENTERRIGHT, left=100, top=-50)
        uthread.new(self.TryShowShipModuleHint)
        uthread.new(self.TryShowChannelHint)
        uthread.new(self.TryShowOverviewHint)
        uthread.new(self.TryShowLocationHint)
        uthread.new(self.TryShowShipHudHint)
        uicore.animations.FadeTo(self, startVal=0.0, endVal=1.5, duration=0.125, loops=1, curveType=2, callback=self.ResetOpacity, sleep=True, curveSet=None, timeOffset=0.0)
        sm.RegisterNotify(self)

    def ResetOpacity(self, *args):
        shade = Fill(bgParent=self, color=(0, 0, 0, 0.0))
        uicore.animations.FadeTo(shade, startVal=0.0, endVal=0.5, duration=1.0)
        uicore.animations.FadeTo(self, startVal=self.opacity, endVal=1.0, duration=0.5)

    def TryShowChannelHint(self):
        sprite = self.CreateSpriteObject(parent=self, texturePath=OVERLAYROOT + 'section_Chat.png', align=uiconst.ABSOLUTE)
        while (self.isopen or self.isopening) and not self.destroyed:
            window = form.LSCChannel.GetIfOpen(windowID='chatchannel_solarsystemid2')
            if window and window.IsVisible():
                absL, absT, absW, absH = window.GetAbsolute()
                sprite.left = absL + 100
                sprite.top = absT - 100
                sprite.display = True
            else:
                sprite.display = False
            blue.pyos.synchro.Sleep(1)

    def TryShowOverviewHint(self):
        sprite = self.CreateSpriteObject(parent=self, texturePath=OVERLAYROOT + 'section_ItemsInSpace.png', align=uiconst.ABSOLUTE)
        while (self.isopen or self.isopening) and not self.destroyed:
            window = form.OverView.GetIfOpen()
            if window and window.IsVisible():
                absL, absT, absW, absH = window.GetAbsolute()
                sprite.left = absL - sprite.width
                sprite.top = absT
                sprite.display = True
            else:
                sprite.display = False
            blue.pyos.synchro.Sleep(1)

    def TryShowLocationHint(self):
        window = uicore.layer.sidepanels.GetChild('InfoPanelLocationInfo', 'header')
        if window and window.IsVisible():
            sprite = self.CreateSpriteObject(parent=self, texturePath=OVERLAYROOT + 'section_YouAreHere.png', align=uiconst.ABSOLUTE)
            absL, absT, absW, absH = window.GetAbsolute()
            sprite.left = absL + absW
            sprite.top = absT - 14

    def TryShowShipHudHint(self):
        sprite = self.CreateSpriteObject(parent=self, texturePath=OVERLAYROOT + 'section_ShipInfo.png', align=uiconst.ABSOLUTE)
        while (self.isopen or self.isopening) and not self.destroyed:
            window = uicore.layer.shipui.GetChild('shipuiMainShape')
            if window and window.IsVisible():
                absL, absT, absW, absH = window.GetAbsolute()
                sprite.left = absL + absW / 2 - 428
                sprite.top = absT + absH / 2 - 120
                sprite.display = True
            else:
                sprite.display = False
            blue.pyos.synchro.Sleep(1)

    def TryShowShipModuleHint(self):
        sprite = self.CreateSpriteObject(parent=self, texturePath=OVERLAYROOT + 'section_ShipModules.png', align=uiconst.ABSOLUTE)
        while (self.isopen or self.isopening) and not self.destroyed:
            for i in xrange(1, 9):
                slot = uicore.layer.shipui.sr.slotsContainer.FindChild('inFlightHighSlot' + str(i))
                if not slot or slot.sr.module is None:
                    continue
                absL, absT, absW, absH = slot.GetAbsolute()
                sprite.left = absL + 50
                sprite.top = absT - sprite.height + 50
                sprite.display = True
                blue.pyos.synchro.Sleep(1)
                break
            else:
                sprite.display = False

            blue.pyos.synchro.Sleep(1)

    def OnCloseView(self):
        sm.UnregisterNotify(self)

    def Setup(self):
        pass

    def CreateSpriteObject(self, *args, **kwds):
        kwds['state'] = uiconst.UI_DISABLED
        sprite = Sprite(*args, **kwds)
        while not sprite.texture.atlasTexture or sprite.texture.atlasTexture.isLoading:
            blue.pyos.synchro.Sleep(1)

        sprite.width = sprite.texture.atlasTexture.width
        sprite.height = sprite.texture.atlasTexture.height
        return sprite
