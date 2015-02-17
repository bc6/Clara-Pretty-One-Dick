#Embedded file name: eve/client/script/ui/view\fadeToCQTransition.py
import uiprimitives
import uicontrols
import viewstate
import blue
import uicls
import carbonui.const as uiconst
import util
import localization
import evegraphics.settings as gfxsettings
PAPERDOLL_TIMEOUT = const.SEC * 120

class FadeToCQTransition(viewstate.Transition):
    """
    Fade to background image and back state transition.
    This version will allow all windows and overlays to stay visible.
    It is placed in the view_overlays layer temporarily while transitioning
    """
    __guid__ = 'viewstate.FadeToCQTransition'

    def __init__(self, fadeTimeMS = 1000, fadeInTimeMS = None, fadeOutTimeMS = None, **kwargs):
        viewstate.Transition.__init__(self, **kwargs)
        self.fadeInTimeMS = fadeInTimeMS or fadeTimeMS
        self.fadeOutTimeMS = fadeOutTimeMS or fadeTimeMS
        self.fadeLayer = None
        self.racialLoadingBackgrounds = {const.raceAmarr: 'res:/UI/Texture/Classes/CQLoadingScreen/loadingScreen_Amarr.png',
         const.raceCaldari: 'res:/UI/Texture/Classes/CQLoadingScreen/loadingScreen_Caldari.png',
         const.raceGallente: 'res:/UI/Texture/Classes/CQLoadingScreen/loadingScreen_Gallente.png',
         const.raceMinmatar: 'res:/UI/Texture/Classes/CQLoadingScreen/loadingScreen_Minmatar.png',
         const.raceJove: 'res:/UI/Texture/Classes/CQLoadingScreen/loadingScreen.png'}

    def StartTransition(self, fromView, toView):
        viewstate.Transition.StartTransition(self, fromView, toView)
        viewState = sm.GetService('viewState')
        self.fadeLayer = uiprimitives.Container(name='transition_overlay', parent=viewState.overlayLayerParent, pickState=uiconst.TR2_SPS_OFF, bgColor=util.Color.BLACK, opacity=0.0)
        self.loadStationEnv = gfxsettings.Get(gfxsettings.MISC_LOAD_STATION_ENV)
        height = uicore.desktop.height
        width = uicore.desktop.width
        self.loadingText = uicontrols.Label(parent=self.fadeLayer, text=localization.GetByLabel('UI/Worldspaces/Common/Loading'), fontsize=50, align=uiconst.CENTER, top=100, color=util.Color.WHITE, glowFactor=1.0, glowColor=(1.0, 1.0, 1.0, 0.1), uppercase=uiconst.WINHEADERUPPERCASE)
        stationTypeID = eve.stationItem.stationTypeID
        stationType = cfg.invtypes.Get(stationTypeID)
        stationRace = stationType['raceID']
        backgroundToUse = self.racialLoadingBackgrounds[stationRace]
        uiprimitives.Sprite(name='aura', parent=self.fadeLayer, texturePath=backgroundToUse, align=uiconst.CENTER, width=width, height=height)
        if fromView is not None:
            if getattr(fromView, 'cachedPlayerPos', None) is not None and getattr(fromView, 'cachedPlayerRot', None) is not None:
                toView.cachedPlayerPos = fromView.cachedPlayerPos
                toView.cachedPlayerRot = fromView.cachedPlayerRot
            if getattr(fromView, 'cachedCameraYaw', None) is not None and getattr(fromView, 'cachedCameraPitch', None) is not None and getattr(fromView, 'cachedCameraZoom', None) is not None:
                toView.cachedCameraYaw = fromView.cachedCameraYaw
                toView.cachedCameraPitch = fromView.cachedCameraPitch
                toView.cachedCameraZoom = fromView.cachedCameraZoom
        uicore.animations.FadeIn(self.fadeLayer, duration=self.fadeInTimeMS / 1000.0, sleep=True)

    def EndTransition(self, fromView, toView):
        uicore.animations.MorphScalar(self.loadingText, 'glowExpand', startVal=0.0, endVal=2.0, duration=3.0, curveType=uiconst.ANIM_WAVE, loops=uiconst.ANIM_REPEAT)
        uicore.animations.MorphScalar(self.loadingText, 'opacity', startVal=0.0, endVal=1.0, duration=3.0, curveType=uiconst.ANIM_WAVE, loops=uiconst.ANIM_REPEAT)
        playerEntity = sm.GetService('entityClient').GetPlayerEntity(canBlock=True)
        paperdoll = playerEntity.GetComponent('paperdoll')
        timeOutEnd = blue.os.GetWallclockTime() + PAPERDOLL_TIMEOUT
        loadingFailed = False
        while paperdoll.doll.doll.busyUpdating:
            if blue.os.GetWallclockTime() > timeOutEnd:
                loadingFailed = True
                break
            blue.synchro.Yield()

        if not loadingFailed:
            if self.loadStationEnv:
                sm.GetService('sceneManager').EnableIncarnaRendering()
            sm.GetService('cameraClient').EnterWorldspace()
            charControlLayer = sm.GetService('viewState').GetView('station').layer
            uicore.registry.SetFocus(charControlLayer)
            sm.GetService('loading').FadeOut(self.fadeOutTimeMS, opacityStart=1.0)
        self.loadingText.StopAnimations()
        uicore.animations.BlinkOut(self.loadingText, sleep=True)
        blue.statistics.SetTimelineSectionName('done loading')
        uicore.animations.FadeOut(self.fadeLayer, duration=self.fadeOutTimeMS / 1000.0, sleep=True)
        self.fadeLayer.Hide()
        self.fadeLayer.Flush()
        self.fadeLayer.Close()
        del self.fadeLayer
        viewstate.Transition.EndTransition(self, fromView, toView)
        return loadingFailed
