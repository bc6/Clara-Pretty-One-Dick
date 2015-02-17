#Embedded file name: eve/client/script/ui/login/charcreation\assetRenderer.py
from eve.client.script.ui.control.buttons import Button
from eve.client.script.ui.control.checkbox import Checkbox
from carbonui.control.layer import LayerCore
import carbonui.const as uiconst
import blue
import trinity
from eve.client.script.ui.camera.charCreationCamera import CharCreationCamera
import paperDoll
from eve.client.script.ui.control.eveCombo import Combo
from eve.client.script.ui.control.eveSinglelineEdit import SinglelineEdit
from eve.common.script.util.paperDollBloodLineAssets import bloodlineAssets
import ccUtil
import ccConst
import log
import types
from carbonui.primitives.container import Container
from carbonui.util.bunch import Bunch
from eve.client.script.ui.login.charcreation.assetRendererConst import DRESSCODE, SETUP, DRESSCODEINDEX, TUCKINDEX, EXAGGERATE, BLOODLINES, SCARGROUPS, SCARCAMERASETINGS, MALE_MANNEQUIN, FEMALE_MANNEQUIN, LIGHTLOCATION, PIERCINGCATEGORIES, PIERCINGRIGHTGROUPS, PIERCINGLEFTGROUPS, PIERCINGPAIRGROUPS, NORMAL_LIGHT_COLOR, NORMAL_LIGHT_SETTINGS, DRESSCODE_CUSTOM_BY_CATEGORY, DRESSCODE_FEMALE_DEFAULT, DRESSCODE_MALE_DEFAULT, DRESSCODE_CATEGORIES
from carbonui.primitives.line import Line
OUTPUT_ROOT = 'C:/Temp/Thumbnails/'
RGB_FOLDER = 'RGBs/'

def GetPaperDollResource(typeID, genderID):
    assets = []
    for each in cfg.paperdollResources:
        if each.typeID == typeID:
            assets.append(each)

    if len(assets) == 1:
        return assets[0]
    if len(assets) > 1:
        for asset in assets:
            if genderID == asset.resGender:
                return asset

    log.LogError('PreviewWnd::PreviewType - No asset matched the typeID: %d' % typeID)


class AssetRenderer(object):
    __guid__ = 'cc.AssetRenderer'
    __exportedcalls__ = {}

    def __init__(self, showUI = True):
        trinity.SetFpsEnabled(False)
        if uicore.layer.charactercreation.isopen:
            uicore.layer.charactercreation.TearDown()
            uicore.layer.charactercreation.Flush()
        uicore.layer.login.CloseView()
        uicore.layer.charsel.CloseView()
        for each in uicore.layer.main.children[:]:
            each.Close()

        uicore.device.ForceSize()
        self.resolution = ccConst.TEXTURE_RESOLUTIONS[1]
        self.oldNonRandomize = getattr(prefs, 'NoRandomize', False)
        prefs.NoRandomize = True
        self.characterSvc = sm.GetService('character')
        self.charID = 0
        self.factory = sm.GetService('character').factory
        self.factory.compressTextures = False
        self.SetupUI(showUI=showUI)

    def SetupUI(self, showUI = True):
        uicore.layer.main.Flush()
        col1 = Container(parent=uicore.layer.main, align=uiconst.TOLEFT, width=160, padLeft=20, padTop=10)
        self.femaleCB = self.AddCheckbox('female', col1)
        self.maleCB = self.AddCheckbox('male', col1)
        Line(parent=col1, align=uiconst.TOTOP)
        self.bloodlines = []
        for bloodlineID, each in BLOODLINES:
            cb = self.AddCheckbox(each, col1)
            cb.bloodlineID = bloodlineID
            self.bloodlines.append(cb)

        Line(parent=col1, align=uiconst.TOTOP)
        cb = self.AddCheckbox('mannequin', col1)
        cb.bloodlineID = -1
        cb.padTop = 5
        self.mannequinCB = cb
        Line(parent=col1, align=uiconst.TOTOP, padBottom=15)
        cb = self.AddCheckbox('render rgb', col1)
        cb.hint = 'to render images with 3 different background to make alpha (needs processing). You should be using this'
        self.rgbCB = cb
        Line(parent=col1, align=uiconst.TOTOP, padBottom=15)
        cb = self.AddCheckbox('render Types', col1)
        self.renderTypesCb = cb
        cb.hint = 'check this to only render typed Items. Leave field blank to render all types, else provide typeIDs.\n<br>Usually typed items should only be rendered on mannequins, but can be rendered on any doll (tattoos look bad on mannequin so they are rendered on bloodlines)'
        self.typeIDsEditField = SinglelineEdit(parent=col1, align=uiconst.TOTOP, padding=(15, -4, 20, 0))
        Line(parent=col1, align=uiconst.TOTOP, padBottom=15)
        cb = self.AddCheckbox('render sets', col1)
        self.renderSetsCb = cb
        cb.hint = 'check this to only render sets of typed items. Need to provide a list of sets of this format:\n<br>(typeID1, typeID2, typeID3), (typeID4, typeID5, typeID6)'
        self.setTypeIDsEditField = SinglelineEdit(parent=col1, align=uiconst.TOTOP, padding=(15, -4, 20, 0))
        col2 = Container(parent=uicore.layer.main, align=uiconst.TOLEFT, width=160, padTop=10)
        col3 = Container(parent=uicore.layer.main, align=uiconst.TOLEFT, width=140, padTop=10)
        self.checkboxes = []
        categs = SETUP.keys()
        categs.sort()
        for each in categs[:20]:
            if isinstance(each, types.StringTypes):
                cb = self.AddCheckbox(each, col2)
                self.checkboxes.append(cb)

        for each in categs[20:]:
            if isinstance(each, types.StringTypes):
                cb = self.AddCheckbox(each, col3)
                self.checkboxes.append(cb)

        Line(parent=col3, align=uiconst.TOTOP, padBottom=20)
        self.altCheckboxes = []
        for each in ('poses', 'lights'):
            cb = self.AddCheckbox(each, col3)
            self.altCheckboxes.append(cb)

        self.sizeCombo = Combo(label='Size', parent=col3, options=[('512', 512), ('128', 128)], name='sizeCombo', align=uiconst.TOTOP, padTop=40)
        self.sizeCombo.hint = 'use 512 for NES rendering, unless the 128 rendering has been fixed'
        resolutionOption = [('Best', ccConst.TEXTURE_RESOLUTIONS[0]), ('Good', ccConst.TEXTURE_RESOLUTIONS[1]), ('Low', ccConst.TEXTURE_RESOLUTIONS[2])]
        self.resolutionCombo = Combo(label='Resolution', parent=col3, options=resolutionOption, name='resolutionComb', align=uiconst.TOTOP, padTop=20)
        self.resolutionCombo.hint = "it's ok to use Good for character creator/types, use Best for NES rendering"
        b1 = Button(parent=uicore.layer.main, label='Render', align=uiconst.CENTERBOTTOM, func=self.RenderLoopAll, top=20)
        b2 = Button(parent=uicore.layer.main, label='Try one item', align=uiconst.BOTTOMLEFT, func=self.RenderLoopTry, top=20, left=20)
        if not showUI:
            for each in [col1,
             col2,
             col3,
             b1,
             b2]:
                each.display = False

    def AddCheckbox(self, cbName, parent, groupname = None):
        setting = Bunch(settings.user.ui.Get('assetRenderState', {}))
        cb = Checkbox(parent=parent, text=cbName, checked=bool(setting.Get(cbName, None)), callback=self.CBChange, groupname=groupname)
        cb.name = cbName
        return cb

    def CBChange(self, checkbox, *args):
        setting = settings.user.ui.Get('assetRenderState', {})
        setting[checkbox.name] = checkbox.GetValue()
        settings.user.ui.Set('assetRenderState', setting)
        if not getattr(self, 'spreadingValue', False):
            ctrl = uicore.uilib.Key(uiconst.VK_CONTROL)
            if ctrl:
                self.spreadingValue = True
                if checkbox in self.bloodlines:
                    for each in self.bloodlines:
                        each.SetValue(checkbox.GetValue())

                elif checkbox in self.checkboxes:
                    for each in self.checkboxes:
                        each.SetValue(checkbox.GetValue())

                self.spreadingValue = False

    def RenderLoopTry(self, *args):
        self.RenderLoop(tryout=True)

    def RenderLoopAll(self, *args):
        self.RenderLoop(tryout=False)

    def RenderLoop(self, tryout = False, fromWebtools = False):
        try:
            self._RenderLoop(tryout=tryout, fromWebtools=fromWebtools)
        finally:
            uicore.device.ForceSize(512, 512)
            uicore.layer.menu.display = True
            uicore.layer.hint.display = True
            uicore.layer.main.display = True
            print 'in finally'
            prefs.NoRandomize = self.oldNonRandomize

    def _RenderLoop(self, tryout = False, fromWebtools = False):
        self.FindWhatToRender()
        self.characterSvc.characters = {}
        self.characterSvc.TearDown()
        uicore.layer.charactercreation.OpenView()
        uicore.layer.charactercreation.Flush()
        for layerName, layer in uicore.layer.__dict__.iteritems():
            if isinstance(layer, LayerCore):
                layer.display = False

        renderSize = self.sizeCombo.GetValue()
        uicore.device.ForceSize(renderSize, renderSize)
        sm.GetService('sceneManager').SetSceneType(0)
        uicore.layer.charactercreation.SetupScene(ccConst.SCENE_PATH_CUSTOMIZATION)
        self.resolution = self.resolutionCombo.GetValue()
        scene = uicore.layer.charactercreation.scene
        lightScene = trinity.Load(NORMAL_LIGHT_SETTINGS)
        ccUtil.SetupLighting(scene, lightScene, lightScene)
        uicore.layer.charactercreation.cameraUpdateJob = None
        uicore.layer.charactercreation.camera = CharCreationCamera(None)
        uicore.layer.charactercreation.SetupCameraUpdateJob()
        camera = uicore.layer.charactercreation.camera
        self.SetupRenderJob()
        blue.pyos.synchro.SleepWallclock(2000)
        self.DoLightsAndPoses(camera, scene)
        self.DoAssets(camera, scene, tryout)

    def SetupRenderJob(self):
        for each in trinity.renderJobs.recurring:
            if each.name == 'cameraUpdate':
                trinity.renderJobs.recurring.remove(each)
            elif each.name == 'BaseSceneRenderJob':
                self.renderJob = each
                self.renderJob.RemoveStep('RENDER_BACKDROP')
                self.renderJob.SetClearColor((0.9, 0.9, 0.9, 0.0))

    def FindWhatToRender(self):
        self.doRenderFemale = self.femaleCB.GetValue()
        self.doRenderMale = self.maleCB.GetValue()
        self.bloodlineIDsToRender = [ bloodlineCB.bloodlineID for bloodlineCB in self.bloodlines if bloodlineCB.GetValue() ]
        self.altGroupsToRender = [ checkBox.name for checkBox in self.altCheckboxes if checkBox.GetValue() ]
        self.assetCategoriesToRender = [ checkBox.name for checkBox in self.checkboxes if checkBox.GetValue() ]

    def DoLightsAndPoses(self, camera, scene):
        for altCategory in self.altGroupsToRender:
            for genderID, shouldRender in [(0, self.doRenderFemale), (1, self.doRenderMale)]:
                if not shouldRender:
                    continue
                uicore.layer.charactercreation.genderID = genderID
                for bloodlineID in self.bloodlineIDsToRender:
                    self.PosesAndLightThumbnails(bloodlineID, altCategory, camera, genderID, scene)

    def DoAssets(self, camera, scene, tryout):
        for gender, genderID, shouldRender in [('Female', 0, self.doRenderFemale), ('Male', 1, self.doRenderMale)]:
            if not shouldRender:
                continue
            if getattr(self, 'mannequinCB', None) and self.mannequinCB.GetValue():
                avatar = self.RenderMannequinAssets(camera, genderID, scene, tryout)
            paperdollGender = ccUtil.GenderIDToPaperDollGender(genderID)
            for bloodlineID in self.bloodlineIDsToRender:
                character = self.PrepareBloodlineDoll(bloodlineID, paperdollGender, scene)
                self.RenderNormalAssets(bloodlineID, camera, character, genderID, scene, tryout)
                if tryout:
                    break

            if tryout:
                break

    def PosesAndLightThumbnails(self, bloodlineID, altCategory, camera, genderID, scene):
        self.characterSvc.RemoveCharacter(self.charID)
        uicore.layer.charactercreation.ResetDna()
        paperdollGender = ccUtil.GenderIDToPaperDollGender(genderID)
        self.SetupCharacter(bloodlineID, scene, paperdollGender)
        for dcCategory in DRESSCODE[ccConst.hair]:
            dcTypeData = self.characterSvc.GetAvailableTypesByCategory(dcCategory, genderID, bloodlineID)
            if dcTypeData:
                dcItemType = dcTypeData[0]
                dcModifier = self.characterSvc.ApplyTypeToDoll(self.charID, dcItemType)

        character = self.characterSvc.GetSingleCharacter(self.charID)
        self.WaitForDollAndScene(character.doll, scene)
        trinity.WaitForResourceLoads()
        camera.SetFieldOfView(0.3)
        if altCategory == 'poses':
            self.RenderPoseThumbnails(bloodlineID, camera, character, genderID)
        elif altCategory == 'lights':
            self.RenderLightThumbnails(bloodlineID, camera, genderID)

    def RenderPoseThumbnails(self, bloodlineID, camera, character, genderID):
        if genderID == 0:
            camera.SetPointOfInterest((0.0, 1.5, 0.0))
        else:
            camera.SetPointOfInterest((0.0, 1.6, 0.0))
        camera.distance = 2.0
        camera.Update()
        self.characterSvc.StartPosing(self.charID)
        character.avatar.animationUpdater.network.SetControlParameter('ControlParameters|NetworkMode', 2)
        renderRGB = self.rgbCB.GetValue()
        for i in xrange(ccConst.POSERANGE):
            self.characterSvc.ChangePose(i, self.charID)
            blue.pyos.synchro.SleepWallclock(100)
            outputPath = OUTPUT_ROOT + '%s_g%s_b%s.png' % ('pose_%s' % i, genderID, bloodlineID)
            self.SaveScreenShot(outputPath, rgb=renderRGB)

    def RenderLightThumbnails(self, bloodlineID, camera, genderID):
        if genderID == 0:
            camera.SetPointOfInterest((0.0, 1.6, 0.0))
        else:
            camera.SetPointOfInterest((0.0, 1.7, 0.0))
        camera.distance = 1.4
        camera.Update()
        lightingList = ccConst.LIGHT_SETTINGS_ID
        lightingColorList = ccConst.LIGHT_COLOR_SETTINGS_ID
        renderRGB = self.rgbCB.GetValue()
        for each in lightingList:
            for color in lightingColorList:
                uicore.layer.charactercreation.SetLightsAndColor(each, color)
                blue.synchro.Yield()
                blue.resMan.Wait()
                trinity.WaitForResourceLoads()
                for i in xrange(10):
                    blue.pyos.synchro.SleepWallclock(100)

                camera.Update()
                outputPath = OUTPUT_ROOT + '%s_g%s_b%s.png' % ('light_%s_%s' % (each, color), genderID, bloodlineID)
                self.SaveScreenShot(outputPath, rgb=renderRGB)

    def FreezeCharacter(self, avatar):
        avatar.animationUpdater.network.SetControlParameter('ControlParameters|isAlive', 0)
        avatar.animationUpdater.network.update = False
        blue.pyos.synchro.SleepWallclock(500)

    def RenderMannequinAssets(self, camera, genderID, scene, tryout):
        mannequin = paperDoll.PaperDollCharacter(self.factory)
        mannequin.doll = paperDoll.Doll('mannequin', gender=ccUtil.GenderIDToPaperDollGender(genderID))
        doll = mannequin.doll
        if genderID == ccConst.GENDERID_MALE:
            doll.Load(MALE_MANNEQUIN, self.factory)
        else:
            doll.Load(FEMALE_MANNEQUIN, self.factory)
        self.WaitForDoll(doll)
        doll.overrideLod = paperDoll.LOD_SKIN
        doll.textureResolution = self.resolution
        mannequin.Spawn(scene, usePrepass=False)
        avatar = mannequin.avatar
        networkPath = ccConst.CHARACTER_CREATION_NETWORK
        self.factory.CreateGWAnimation(avatar, networkPath)
        network = avatar.animationUpdater.network
        if network is not None:
            network.SetControlParameter('ControlParameters|BindPose', 1.0)
            if doll.gender == 'female':
                network.SetAnimationSetIndex(0)
            else:
                network.SetAnimationSetIndex(1)
        blue.pyos.synchro.SleepWallclock(500)
        self.FreezeCharacter(avatar)
        if self.renderSetsCb.GetValue():
            self.LoadMannequinAndCamera(mannequin, genderID, ccConst.outer, camera, scene)
            setText = self.setTypeIDsEditField.GetValue()
            setText = setText.strip()
            if not setText.endswith(','):
                setText += ','
            clothingSets = eval(setText)
            for eachSet in clothingSets:
                self.DoRenderMannequinAssetType(avatar, eachSet, genderID, mannequin, scene, 'set')

            return avatar
        for category in self.assetCategoriesToRender:
            self.LoadMannequinAndCamera(mannequin, genderID, category, camera, scene)
            typeData = self.characterSvc.GetAvailableTypesByCategory(category, genderID, -1)
            for itemType in typeData:
                wasRendered = self.RenderMannequinAssetType(avatar, genderID, mannequin, scene, itemType, category)
                if wasRendered and tryout:
                    break

        return avatar

    def LoadMannequinAndCamera(self, mannequin, genderID, category, camera, scene):
        doll = mannequin.doll
        if genderID == ccConst.GENDERID_MALE:
            doll.Load(MALE_MANNEQUIN, self.factory)
        else:
            doll.Load(FEMALE_MANNEQUIN, self.factory)
        self.WaitForDoll(doll)
        lightScene = trinity.Load(NORMAL_LIGHT_SETTINGS)
        ccUtil.SetupLighting(scene, lightScene, lightScene)
        cameraSetup = self.SetUpCamera(camera, category, mannequin, SETUP, scene, genderID)

    def GetTypeIDsFromField(self):
        typeIDsString = self.typeIDsEditField.GetValue()
        typeIDs = [ int(x) for x in typeIDsString.split(',') if x ]
        return typeIDs

    def RenderMannequinAssetType(self, avatar, genderID, mannequin, scene, itemType, category):
        typeID = itemType[2]
        if typeID in (None, -1):
            return False
        typeIDs = self.GetTypeIDsFromField()
        if typeIDs and typeID not in typeIDs:
            return False
        return self.DoRenderMannequinAssetType(avatar, [typeID], genderID, mannequin, scene, category)

    def DoRenderMannequinAssetType(self, avatar, typeIDs, genderID, mannequin, scene, category):
        if category == ccConst.bottommiddle:
            pantsModifiers = mannequin.doll.buildDataManager.GetModifiersByCategory(ccConst.bottomouter)
            for pm in pantsModifiers:
                mannequin.doll.RemoveResource(pm.GetResPath(), self.factory)

        modifierList = []
        for typeID in typeIDs:
            asset = GetPaperDollResource(typeID, genderID)
            doll = mannequin.doll
            path = asset.resPath
            modifier = doll.SetItemType(self.factory, path, weight=1.0)
            if modifier:
                modifierList.append(modifier)

        mannequin.Update()
        self.WaitForDoll(doll)
        if not modifierList:
            return False
        self.SetShadow(avatar, scene)
        blue.pyos.synchro.SleepWallclock(500)
        renderRGB = self.rgbCB.GetValue()
        if len(typeIDs) == 1:
            outputPath = self.GetOutputPath(assetPath=path, genderID=genderID, category=category, typeID=typeID)
        else:
            typeIDsString = str(typeIDs).replace(' ', '').replace('(', '').replace(')', '').replace(',', '_')
            outputPath = self.GetOutputPath(assetPath=typeIDsString, genderID=genderID, category=category)
        self.SaveScreenShot(outputPath, rgb=renderRGB)
        for modifier in modifierList:
            doll.RemoveResource(modifier.GetResPath(), self.factory)

        mannequin.Update()
        self.WaitForDoll(doll)
        return True

    def PrepareBloodlineDoll(self, bloodlineID, paperdollGender, scene):
        self.characterSvc.RemoveCharacter(self.charID)
        uicore.layer.charactercreation.ResetDna()
        self.SetupCharacter(bloodlineID, scene, paperdollGender)
        character = self.characterSvc.GetSingleCharacter(self.charID)
        character.avatar.translation = (0.0, 0.0, 0.0)
        self.WaitForDollAndScene(character.doll, scene)
        self.FreezeCharacter(character.avatar)
        trinity.WaitForResourceLoads()
        return character

    def SetupCharacter(self, bloodlineID, scene, paperdollGender):
        self.characterSvc.AddCharacterToScene(self.charID, scene, paperdollGender, bloodlineID=bloodlineID)
        doll = self.characterSvc.GetSingleCharactersDoll(self.charID)
        doll.overrideLod = paperDoll.LOD_SKIN
        doll.textureResolution = self.resolution
        self.characterSvc.SetDollBloodline(self.charID, bloodlineID)
        self.characterSvc.ApplyItemToDoll(self.charID, 'head', bloodlineAssets[bloodlineID], doUpdate=False)
        self.characterSvc.UpdateDoll(self.charID, fromWhere='RenderLoop')

    def RenderNormalAssets(self, bloodlineID, camera, character, genderID, scene, tryout):
        doll = character.doll
        for category in self.assetCategoriesToRender:
            typeData = self.characterSvc.GetAvailableTypesByCategory(category, genderID, bloodlineID)
            lightScene = trinity.Load(NORMAL_LIGHT_COLOR)
            ccUtil.SetupLighting(scene, lightScene, lightScene)
            cameraSetup = self.SetUpCamera(camera, category, character, SETUP, scene, genderID)
            log.LogNotice('before dresscode')
            if category in DRESSCODE:
                removeDcModifers = self.EnforceDresscode(bloodlineID, category, doll, genderID)
            else:
                removeDcModifers = []
            log.LogNotice('go render type')
            for itemType in typeData:
                wasRendered = self.RenderNormalType(bloodlineID, camera, category, character, genderID, itemType, scene)
                if tryout and wasRendered:
                    break

            log.LogNotice('remove the dresscode')
            for dcResPath in removeDcModifers:
                doll.RemoveResource(dcResPath, self.factory)

            log.LogNotice('done with category')

    def RenderNormalType(self, bloodlineID, camera, category, character, genderID, itemType, scene):
        typeID = itemType[2]
        if typeID is not None:
            if not self.renderTypesCb.GetValue():
                return False
            typeIDs = self.GetTypeIDsFromField()
            if typeIDs and typeID not in typeIDs:
                return False
        doll = character.doll
        modifer = self.characterSvc.ApplyTypeToDoll(self.charID, itemType)
        if not modifer:
            return False
        typeInfo = itemType[1]
        if typeInfo[0].startswith('scars'):
            self.SetCameraForScar(typeInfo, character, camera, scene)
        if typeInfo[0].startswith(PIERCINGCATEGORIES):
            self.SetCameraAndLightPiercings(category, typeInfo, character, camera, scene)
        self.ApplyTuckingIfNeeded(category)
        self.TrySetColor(bloodlineID, category, genderID, typeInfo)
        if (category, genderID) in EXAGGERATE:
            if getattr(modifer, 'weight', None) is not None:
                modifer.weight = 1.5 * modifer.weight
        self.characterSvc.UpdateDoll(self.charID, fromWhere='RenderLoop')
        self.SetShadow(character.avatar, scene)
        blue.pyos.synchro.SleepWallclock(500)
        self.WaitForDoll(doll)
        blue.resMan.Wait()
        trinity.WaitForResourceLoads()
        path = '_'.join(list(itemType[1]))
        outputPath = self.GetOutputPath(assetPath=path, genderID=genderID, category=category, bloodlineID=bloodlineID, typeID=typeID)
        renderRGB = self.rgbCB.GetValue()
        self.SaveScreenShot(outputPath, rgb=renderRGB)
        doll.RemoveResource(modifer.GetResPath(), self.factory)
        return True

    def ApplyTuckingIfNeeded(self, category):
        if category not in TUCKINDEX:
            return
        tuckPath, requiredModifier, subKey = ccConst.TUCKMAPPING[category]
        tuckModifier = sm.GetService('character').GetModifierByCategory(self.charID, tuckPath)
        if tuckModifier:
            tuckVariations = tuckModifier.GetVariations()
            tuckStyle = tuckModifier.GetResPath().split('/')[-1]
            self.characterSvc.ApplyItemToDoll(self.charID, category, tuckStyle, variation=tuckVariations[TUCKINDEX[category]])

    def TrySetColor(self, bloodlineID, category, genderID, typeInfo):
        if category in (ccConst.beard, ccConst.hair, ccConst.eyebrows):
            category = ccConst.hair
        try:
            if typeInfo[1] or typeInfo[2]:
                return
            categoryColors = self.characterSvc.GetAvailableColorsForCategory(category, genderID, bloodlineID)
            if not categoryColors:
                return
            primary, secondary = categoryColors
            primaryVal = (primary[1][0], primary[1][2])
            if primary and secondary:
                secondaryVal = (secondary[1][0], secondary[1][2])
                self.characterSvc.SetColorValueByCategory(self.charID, category, primaryVal, secondaryVal)
            else:
                self.characterSvc.SetColorValueByCategory(self.charID, category, primaryVal, None)
        except:
            pass
        finally:
            if category == ccConst.hair:
                sm.GetService('character').SetHairDarkness(0, 0.5)

    def ReformatAssetPath(self, path):
        assetResPath = path.replace('/', '_').replace('.type', '')
        return assetResPath

    def WaitForDollAndScene(self, doll, scene):
        while len(scene.dynamics) < 1:
            blue.synchro.Yield()

        blue.synchro.Yield()
        self.WaitForDoll(doll)

    def WaitForDoll(self, doll):
        while doll.busyUpdating:
            blue.synchro.Yield()

    def EnforceDresscode(self, bloodlineID, category, doll, genderID):
        if category in DRESSCODE_CUSTOM_BY_CATEGORY:
            dressCode = DRESSCODE_CUSTOM_BY_CATEGORY[category][genderID]
        elif genderID == ccConst.GENDERID_FEMALE:
            dressCode = DRESSCODE_FEMALE_DEFAULT
        else:
            dressCode = DRESSCODE_MALE_DEFAULT
        removeDcModifers = []
        for dcCategory in DRESSCODE_CATEGORIES:
            if dcCategory == category:
                continue
            dcTypeData = self.characterSvc.GetAvailableTypesByCategory(dcCategory, genderID, bloodlineID)
            if not dcTypeData:
                continue
            for itemType in dcTypeData:
                assetID = itemType[0]
                if assetID in dressCode:
                    if dcCategory == ccConst.hair:
                        var = self.GetHairColor(genderID, bloodlineID)
                    else:
                        var = None
                    dcModifier = self.characterSvc.ApplyTypeToDoll(self.charID, itemType, doUpdate=False, rawColorVariation=var)
                    if dcModifier:
                        removeDcModifers.append(dcModifier.GetResPath())
                    self.WaitForDoll(doll)
                    blue.resMan.Wait()
                    break

        return removeDcModifers

    def SetShadow(self, avatar, scene):
        if paperDoll.SkinSpotLightShadows.instance is not None:
            paperDoll.SkinSpotLightShadows.instance.Clear(killThread=True)
            del paperDoll.SkinSpotLightShadows.instance
            paperDoll.SkinSpotLightShadows.instance = None
        ss = paperDoll.SkinSpotLightShadows(scene, debugVisualize=False, size=2048)
        ss.SetupSkinnedObject(avatar)
        paperDoll.SkinSpotLightShadows.instance = ss

    def SetCameraAndLightPiercings(self, category, typeInfo, character, camera, scene):
        typeName, a, b = typeInfo
        if typeName.endswith('left', 0, -1):
            dictToUse = PIERCINGLEFTGROUPS
        elif typeName.endswith('right', 0, -1):
            dictToUse = PIERCINGRIGHTGROUPS
        else:
            dictToUse = PIERCINGPAIRGROUPS
        self.SetUpCamera(camera, category, character, dictToUse, scene)

    def SetCameraForScar(self, typeInfo, character, camera, scene):
        group = SCARGROUPS.get(typeInfo, None)
        if group is None:
            print 'couldnt find the group, return'
            return
        self.SetUpCamera(camera, group, character, SCARCAMERASETINGS, scene)

    def SetCamera(self, camera, poi, distance, yaw, pitch):
        camera.SetPointOfInterest(poi)
        camera.distance = distance
        camera.SetFieldOfView(0.3)
        camera.SetYaw(yaw)
        camera.SetPitch(pitch)
        camera.Update()

    def SetUpCamera(self, camera, category, character, categoryList = SETUP, scene = None, genderID = None):
        if (category, genderID) in categoryList:
            options = categoryList[category, genderID]
        else:
            options = categoryList.get(category, None)
        if options:
            log.LogNotice('+ category = %s' % category)
            boneName, offset, lightSetting = options
            if lightSetting:
                path = '%s%s.red' % (LIGHTLOCATION, lightSetting)
                lightScene = trinity.Load(path)
                ccUtil.SetupLighting(scene, lightScene, lightScene)
            log.LogNotice('before joint')
            joint = 4294967295L
            while joint == 4294967295L:
                log.LogNotice('joint = %s' % joint)
                log.LogNotice('boneName = %s' % boneName)
                joint = character.avatar.GetBoneIndex(boneName)
                log.LogNotice('j = %s' % joint)
                blue.synchro.Yield()
                log.LogNotice('done waiting')

            log.LogNotice('-- joint = %s' % joint)
            poi = character.avatar.GetBonePosition(joint)
            distance, yOffset, xOffset, yaw, pitch = offset
            x, y, z = poi
            if yOffset:
                y += yOffset
            if xOffset:
                x += xOffset
            poi = (x, y, z)
            log.LogNotice('before poi')
            if category in (ccConst.bottomouter, ccConst.feet):
                poi = (0.0, y, z)
            log.LogNotice('before setting camera')
            self.SetCamera(camera, poi, distance, yaw, pitch)
            log.LogNotice('after setting camera')
            return (distance,
             yaw,
             pitch,
             poi)
        else:
            return

    def GetHairColor(self, genderID, bloodlineID):
        colorsA, colorsB = sm.GetService('character').GetAvailableColorsForCategory(ccConst.hair, genderID, bloodlineID)
        colorA = []
        colorB = []
        var = None
        color1Value, color1Name, color2Name, variation = (None, None, None, None)
        if len(colorsA) > 0:
            indexA = int(len(colorsA) * 0.3)
            colorA = colorsA[indexA]
            colorB = None
            if len(colorsB) > 0:
                colorB = colorsB[0]
            color1Value, color1Name, color2Name, variation = sm.GetService('character').GetColorsToUse(colorA, colorB)
        if color1Value:
            return var
        if colorB:
            var = variation
        elif len(colorA) > 0:
            var = colorA[1]
        return var

    def GetOutputPath(self, assetPath, genderID, category = None, bloodlineID = -1, typeID = None):
        assetResPath = self.ReformatAssetPath(assetPath)
        renderRGB = self.rgbCB.GetValue()
        categoryPath = self.ReformatAssetPath(category)
        if renderRGB:
            subFolder = RGB_FOLDER
        else:
            subFolder = categoryPath + '/'
        ccUtil.CreateCategoryFolderIfNeeded(OUTPUT_ROOT, subFolder)
        outputPath = OUTPUT_ROOT + subFolder
        if renderRGB:
            outputPath = outputPath + '%s~' % categoryPath
        if typeID:
            if genderID == ccConst.GENDERID_MALE:
                gender = 'male'
            else:
                gender = 'female'
            outputPath = outputPath + '%s_%s_%s.png' % (typeID, gender, assetResPath)
        elif bloodlineID < 0:
            outputPath = outputPath + '%s_g%s.png' % (assetResPath, genderID)
        else:
            outputPath = outputPath + '%s_g%s_b%s.png' % (assetResPath, genderID, bloodlineID)
        return outputPath

    def SaveScreenShot(self, outputPath, rgb = False):
        if rgb:
            clearColors = (('R', (1.0, 0.0, 0.0, 0.0)), ('G', (0.0, 1.0, 0.0, 0.0)), ('B', (0.0, 0.0, 1.0, 0.0)))
        else:
            clearColors = ((None, None),)
        print 'SaveScreenShot', outputPath
        for channel, color in clearColors:
            if color:
                self.renderJob.SetClearColor(color)
            blue.synchro.Yield()
            backBuffer = trinity.device.GetRenderContext().GetDefaultBackBuffer()
            if not backBuffer.isReadable:
                tempRT = trinity.Tr2RenderTarget(backBuffer.width, backBuffer.height, 1, backBuffer.format)
                backBuffer.Resolve(tempRT)
                bmp = trinity.Tr2HostBitmap(tempRT)
            else:
                bmp = trinity.Tr2HostBitmap(backBuffer)
            if bmp.format == trinity.PIXEL_FORMAT.B8G8R8A8_UNORM:
                bmp.ChangeFormat(trinity.PIXEL_FORMAT.B8G8R8X8_UNORM)
            if rgb:
                bmp.Save(outputPath[:-4] + '_' + channel + outputPath[-4:])
            else:
                bmp.Save(outputPath)
