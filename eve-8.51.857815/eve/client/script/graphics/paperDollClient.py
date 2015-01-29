#Embedded file name: eve/client/script/graphics\paperDollClient.py
import paperDollUtil
import telemetry
import eve.common.script.paperDoll.paperDollConfiguration as pdCfg
import eve.client.script.paperDoll.paperDollImpl as pdImp
import evegraphics.settings as gfxsettings
from ccConst import TEXTURE_RESOLUTIONS
from carbon.client.script.graphics.paperDollClient import PaperDollClient

class EvePaperDollClient(PaperDollClient):
    __guid__ = 'svc.evePaperDollClient'
    __replaceservice__ = 'paperDollClient'
    __notifyevents__ = PaperDollClient.__notifyevents__ + ['OnGraphicSettingsChanged']
    __dependencies__ = PaperDollClient.__dependencies__ + ['info', 'character', 'device']

    def Run(self, *etc):
        PaperDollClient.Run(self, *etc)
        doKick = False
        try:
            self.LogInfo('Early loading of paperDoll asset data requested, station environments enabled')
            doKick = gfxsettings.Get(gfxsettings.MISC_LOAD_STATION_ENV)
        except NameError:
            doKick = True

        if doKick:
            kicker = self.dollFactory

    def _AppPerformanceOptions(self):
        pdCfg.PerformanceOptions.EnableEveOptimizations()

    @telemetry.ZONE_METHOD
    def GetDollDNA(self, scene, entity, dollGender, dollDnaInfo, typeID):
        bloodlineID = self.info.GetBloodlineByTypeID(typeID).bloodlineID
        return self.character.GetDNAFromDBRowsForEntity(entity.entityID, dollDnaInfo, dollGender, bloodlineID)

    def SetupComponent(self, entity, component):
        PaperDollClient.SetupComponent(self, entity, component)
        doll = component.doll.doll
        if session.charid == entity.entityID:
            cs = pdImp.CompressionSettings(compressTextures=True, generateMipmap=False)
            cs.compressNormalMap = False
            doll.compressionSettings = cs
        doll.usePrepassAlphaTestHair = gfxsettings.Get(gfxsettings.GFX_INTERIOR_SHADER_QUALITY) == 0
        self.SetBoneOffsets(entity, component)

        def UpdateDoneCallback():
            """ 
            The avatar is created with a curveset that references the avatar. This createsa a circular reference.
            We fix it by moving the curveset to the scene instead.
            """
            if component.doll and component.doll.avatar:
                for curveSet in component.doll.avatar.curveSets:
                    if curveSet.name == 'HeadMatrixCurves':
                        trinityScene = sm.GetService('graphicClient').GetScene(entity.scene.sceneID)
                        if trinityScene:
                            for each in trinityScene.curveSets:
                                if each.name == 'HeadMatrixCurves':
                                    trinityScene.curveSets.remove(each)

                            trinityScene.curveSets.append(curveSet)
                            component.doll.avatar.curveSets.remove(curveSet)

        component.doll.doll.AddUpdateDoneListener(UpdateDoneCallback)

    def SetBoneOffsets(self, entity, component):
        """ Sets the bloodline specific bone offsets for the character. """
        avatar = self.GetPaperDollByEntityID(entity.entityID).avatar
        gender = self.GetDBGenderToPaperDollGender(component.gender)
        bloodlineID = self.info.GetBloodlineByTypeID(component.typeID).bloodlineID
        bloodline = paperDollUtil.bloodlineAssets[bloodlineID]
        self.character.AdaptDollAnimationData(bloodline, avatar, gender)

    def GetInitialTextureResolution(self):
        textureQuality = gfxsettings.Get(gfxsettings.GFX_CHAR_TEXTURE_QUALITY)
        return TEXTURE_RESOLUTIONS[textureQuality]

    @telemetry.ZONE_METHOD
    def OnGraphicSettingsChanged(self, changes):
        if gfxsettings.GFX_CHAR_TEXTURE_QUALITY in changes:
            textureQuality = gfxsettings.Get(gfxsettings.GFX_CHAR_TEXTURE_QUALITY)
            resolution = TEXTURE_RESOLUTIONS[textureQuality]
            for character in self.paperDollManager:
                character.doll.SetTextureSize(resolution)
                character.doll.buildDataManager.SetAllAsDirty()
                character.Update()

        if gfxsettings.GFX_INTERIOR_SHADER_QUALITY in changes:
            for character in self.paperDollManager:
                character.doll.usePrepassAlphaTestHair = gfxsettings.Get(gfxsettings.GFX_INTERIOR_SHADER_QUALITY) == 0
                if character.doll.usePrepass:
                    character.doll.buildDataManager.SetAllAsDirty(True)
                    character.Update()
