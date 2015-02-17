#Embedded file name: eve/client/script/environment/spaceObject\playerOwnedStructure.py
import trinity
import blue
import uthread
import eve.common.lib.appConst as const
import eve.client.script.environment.nodemanager as nodemanager
from eve.client.script.environment.spaceObject.LargeCollidableStructure import LargeCollidableStructure
CONSTRUCTION_MATERIAL = 'res:/Texture/MinmatarShared/Gradientbuild.dds'
ONLINE_GLOW_OFF = (0.0, 0.0, 0.0)
ONLINE_GLOW_MID = (0.004, 0.0, 0.0)

def FindCurves(tf, typename):
    if not tf:
        return []
    curves = tf.Find(('trinity.TriScalarCurve', 'trinity.TriVectorCurve', 'trinity.TriRotationCurve', 'trinity.TriColorCurve'), -1, 1)
    ret = []
    for curve in curves:
        if curve.name[:len(typename)] == typename:
            ret.append(curve)

    return ret


def ReverseTimeCurves(curves):
    for curve in curves:
        length = curve.length
        if length > 0.0:
            curve.Sort()
            curve.ScaleTime(-1.0)
            for key in curve.keys:
                key.time = key.time + length

            curve.Sort()


def ResetTimeCurves(curves):
    for curve in curves:
        curve.start = blue.os.GetSimTime()


class PlayerOwnedStructure(LargeCollidableStructure):

    def __init__(self):
        LargeCollidableStructure.__init__(self)
        self.savedShaders = {}
        self.buildAnim, self.onlineAnim = (None, None)

    def LoadModel(self, fileName = None, loadedModel = None):
        self.LogInfo('================ POS LoadModel ')
        if self.IsAnchored():
            self.LoadStationModel(True)
        else:
            LargeCollidableStructure.LoadModel(self, 'res:/dx9/Model/deployables/nanocontainer/nanocontainer.red')

    def LoadStationModel(self, builtAlready):
        LargeCollidableStructure.LoadModel(self)
        if hasattr(self.model, 'ChainAnimationEx'):
            self.model.ChainAnimationEx('NormalLoop', 0, 0, 1)
        if not self.IsOnline():
            self.buildAnim, self.onlineAnim = self.PrepareModelForConstruction(builtAlready, False)
            self.OfflineAnimation(0)
            if hasattr(self.model, 'EndAnimation'):
                self.model.EndAnimation()
        else:
            self.ResetAfterConstruction()

    def Assemble(self):
        slimItem = self.typeData.get('slimItem')
        if slimItem.groupID == const.groupMoonMining:
            direction = self.FindClosestMoonDir()
            self.AlignToDirection(direction)

    def DelayedRemove(self, model, delay):
        model.name = model.name + '_removing'
        blue.pyos.synchro.SleepSim(delay)
        model.display = False
        self.RemoveAndClearModel(model)

    def RemoveFloatAlphathreshold(self, effect):
        """ Some alpha chanels need to be converted to Vector4 params, so remove the float ones."""
        removes = nodemanager.FindNodes(effect.parameters, 'AlphaThreshold', 'trinity.Tr2FloatParameter')
        for each in removes:
            effect.parameters.fremove(each)

    def FindOrMakeAlphathreshold(self, effect, v1, v2, v3, v4):
        """ find a alpha threshold, or make one."""
        for i, each in enumerate(effect.constParameters):
            if each[0] == 'AlphaThreshold':
                del effect.constParameters[i]
                break

        nodes = nodemanager.FindNodes(effect.parameters, 'AlphaThreshold', 'trinity.Tr2Vector4Parameter')
        res = None
        if nodes:
            res = nodes[0]
        else:
            res = trinity.Tr2Vector4Parameter()
            res.name = 'AlphaThreshold'
        if res:
            res.v1 = v1
            res.v2 = v2
            res.v3 = v3
            res.v4 = v4
        return res

    def PrepareAreasForConstruction(self, areas, alphaParams, prefix):
        sovShaders = False
        slimItem = self.typeData.get('slimItem')
        if slimItem is not None:
            groupID = slimItem.groupID
            if groupID in [const.groupSovereigntyDisruptionStructures, const.groupInfrastructureHub]:
                sovShaders = True
        for each in areas:
            if 'alpha_' not in each.effect.effectFilePath and 'v3.fx' not in each.effect.effectFilePath.lower():
                effectFilePathInsertPos = each.effect.effectFilePath.rfind('/')
                if effectFilePathInsertPos != -1:
                    filePath = each.effect.effectFilePath
                    if prefix + each.effect.name not in self.savedShaders:
                        self.savedShaders[prefix + str(id(each))] = filePath
                    if sovShaders:
                        skp = filePath[effectFilePathInsertPos + 1:].lower().find('skinned_')
                        if skp >= 0:
                            each.effect.effectFilePath = filePath[:effectFilePathInsertPos + 1] + 'alpha_' + filePath[effectFilePathInsertPos + 9:]
                        else:
                            each.effect.effectFilePath = filePath[:effectFilePathInsertPos + 1] + 'alpha_' + filePath[effectFilePathInsertPos + 1:]
                    else:
                        each.effect.effectFilePath = filePath[:effectFilePathInsertPos + 1] + 'alpha_' + filePath[effectFilePathInsertPos + 1:]
                    alphaParam = self.FindOrMakeAlphathreshold(each.effect, 1.0, 0.0, 0.0, 0.0)
                    alphaParams.append(alphaParam)
                    each.effect.parameters.fremove(alphaParam)
                    each.effect.parameters.append(alphaParam)
                    alphaMap = trinity.TriTexture2DParameter()
                    alphaMap.name = 'AlphaThresholdMap'
                    alphaMap.resourcePath = CONSTRUCTION_MATERIAL
                    each.effect.resources.append(alphaMap)
                    each.effect.RebuildCachedData()

    def ResetAreasAfterConstruction(self, areas, prefix):
        if not len(self.savedShaders):
            return
        for each in areas:
            if prefix + str(id(each)) in self.savedShaders:
                each.effect.effectFilePath = self.savedShaders[prefix + str(id(each))]
                each.effect.RebuildCachedData()

    def ResetAfterConstruction(self):
        model = self.model
        if model.meshLod:
            self.ResetAreasAfterConstruction(model.meshLod.opaqueAreas, 'high_opaque')
            self.ResetAreasAfterConstruction(model.meshLod.decalAreas, 'high_decal')
            self.ResetAreasAfterConstruction(model.meshLod.transparentAreas, 'high_transparent')
        else:
            self.ResetAreasAfterConstruction(model.mesh.opaqueAreas, 'high_opaque')
            self.ResetAreasAfterConstruction(model.mesh.decalAreas, 'high_decal')
            self.ResetAreasAfterConstruction(model.mesh.transparentAreas, 'high_transparent')

    def PrepareModelForConstruction(self, builtAlready, onlineAlready):
        self.LogInfo('  PrepareModelForConstruction - Built:', builtAlready, ' Online:', onlineAlready)
        if not self.model:
            return (None, None)
        if not hasattr(self.model, 'curveSets'):
            return (None, None)
        model = self.model
        alphaParams = []
        if model.meshLod:
            self.PrepareAreasForConstruction(model.meshLod.opaqueAreas, alphaParams, 'high_opaque')
            self.PrepareAreasForConstruction(model.meshLod.decalAreas, alphaParams, 'high_decal')
            self.PrepareAreasForConstruction(model.meshLod.transparentAreas, alphaParams, 'high_transparent')
        else:
            self.PrepareAreasForConstruction(model.mesh.opaqueAreas, alphaParams, 'high_opaque')
            self.PrepareAreasForConstruction(model.mesh.decalAreas, alphaParams, 'high_decal')
            self.PrepareAreasForConstruction(model.mesh.transparentAreas, alphaParams, 'high_transparent')
        buildCurve = trinity.TriCurveSet()
        buildCurve.name = 'Build'
        buildCurve.playOnLoad = False
        buildCurve.Stop()
        buildCurve.scaledTime = 0.0
        model.curveSets.append(buildCurve)
        curve = trinity.TriScalarCurve()
        curve.value = 1.0
        curve.extrapolation = trinity.TRIEXT_CONSTANT
        buildCurve.curves.append(curve)
        curve.AddKey(0.0, 1.0, 0.0, 0.0, trinity.TRIINT_HERMITE)
        curve.AddKey(10.0, 0.0, 0.0, 0.0, trinity.TRIINT_HERMITE)
        curve.Sort()
        for alphaParam in alphaParams:
            binding = trinity.TriValueBinding()
            binding.sourceAttribute = 'value'
            binding.destinationAttribute = 'value.x'
            binding.scale = 1.0
            binding.sourceObject = curve
            binding.destinationObject = alphaParam
            buildCurve.bindings.append(binding)

        glows = nodemanager.FindNodes(model, 'GlowColor', 'trinity.Tr2Vector4Parameter')
        finalColor = (1.0, 1.0, 1.0)
        if glows:
            r, g, b, a = glows[0].value
            finalColor = (r, g, b)
        onlineCurve = trinity.TriCurveSet()
        onlineCurve.name = 'Online'
        onlineCurve.playOnLoad = False
        onlineCurve.Stop()
        onlineCurve.scaledTime = 0.0
        model.curveSets.append(onlineCurve)
        curve = trinity.TriVectorCurve()
        onlineCurve.curves.append(curve)
        curve.value = finalColor
        curve.extrapolation = trinity.TRIEXT_CONSTANT
        curve.AddKey(0.0, ONLINE_GLOW_OFF, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), trinity.TRIINT_HERMITE)
        curve.AddKey(1.9, ONLINE_GLOW_MID, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), trinity.TRIINT_LINEAR)
        curve.AddKey(2.0, finalColor, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), trinity.TRIINT_HERMITE)
        curve.Sort()
        for each in glows:
            binding = trinity.TriValueBinding()
            binding.sourceAttribute = 'value'
            binding.destinationAttribute = 'value'
            binding.scale = 1.0
            binding.sourceObject = curve
            binding.destinationObject = each
            onlineCurve.bindings.append(binding)

        if builtAlready:
            buildCurve.Stop()
            buildCurve.scale = 0.0
            buildCurve.scaledTime = buildCurve.GetMaxCurveDuration()
            buildCurve.PlayFrom(buildCurve.scaledTime)
            self.LogInfo('  PrepareModelForConstruction - Already Built, set curve to:', buildCurve.scaledTime)
        if onlineAlready:
            onlineCurve.Stop()
            onlineCurve.scale = 0.0
            onlineCurve.scaledTime = onlineCurve.GetMaxCurveDuration()
            onlineCurve.PlayFrom(onlineCurve.scaledTime)
            self.LogInfo('  PrepareModelForConstruction - Already Online, Set curve Time to:', onlineCurve.scaledTime)
        trinity.WaitForResourceLoads()
        if model.meshLod:
            for each in model.meshLod.opaqueAreas:
                each.effect.PopulateParameters()

        else:
            for each in model.mesh.opaqueAreas:
                each.effect.PopulateParameters()

        return (buildCurve, onlineCurve)

    def SetCapsuleGraphics(self, animate = 0):
        self.LogInfo('  SetCapsuleGraphics - Animate:', animate)
        safeModel = self.model
        LargeCollidableStructure.LoadModel(self, 'res:/dx9/Model/deployables/nanocontainer/nanocontainer.red')
        self.Assemble()
        self.Display(1)
        if animate == 1:
            if self.buildAnim:
                self.buildAnim.scale = -1.0
                self.buildAnim.PlayFrom(self.buildAnim.GetMaxCurveDuration())
                uthread.pool('PlayerOwnedStructure::DelayedRemove', self.DelayedRemove, safeModel, int(self.buildAnim.GetMaxCurveDuration() * 1000))
        else:
            self.DelayedRemove(safeModel, 0)
        if animate == 1:
            if self.IsControlTower():
                self.PlayGeneralAudioEvent('wise:/msg_ct_disassembly_play')
            else:
                self.PlayGeneralAudioEvent('wise:/msg_pos_disassembly_play')

    def IsControlTower(self):
        slimItem = self.typeData.get('slimItem')
        if slimItem is not None:
            groupID = self.typeData.get('groupID')
            return groupID == const.groupControlTower
        return False

    def SetBuiltStructureGraphics(self, animate = 0):
        safeModel = self.model
        self.LoadStationModel(False)
        cameraSvc = self.sm.GetService('camera')
        cameraSvc.ClearBoundingInfoForID(self.id)
        if cameraSvc.LookingAt() == self.id:
            cameraSvc.LookAt(self.id)
        if animate == 1:
            self.Assemble()
            self.buildAnim.scale = 1.0
            self.buildAnim.Play()
            self.Display(1)
        else:
            self.buildAnim.Stop()
            self.buildAnim.scale = 0.0
            self.buildAnim.scaledTime = self.buildAnim.GetMaxCurveDuration()
            self.buildAnim.PlayFrom(self.buildAnim.scaledTime)
            self.DelayedRemove(safeModel, 0)
        if animate == 1:
            if self.IsControlTower():
                self.PlayGeneralAudioEvent('wise:/msg_ct_assembly_play')
            else:
                self.PlayGeneralAudioEvent('wise:/msg_pos_assembly_play')
            uthread.pool('PlayerOwnedStructure::DelayedRemove', self.DelayedRemove, safeModel, 35000)

    def IsAnchored(self):
        self.LogInfo('Anchor State = ', not self.isFree)
        return not self.isFree

    def IsOnline(self):
        slimItem = self.typeData.get('slimItem')
        res = self.sm.GetService('pwn').GetStructureState(slimItem)[0] in ('online', 'invulnerable', 'vulnerable', 'reinforced')
        self.LogInfo('Online State = ', res)
        return res

    def OnlineAnimation(self, animate = 0):
        if animate:
            if getattr(self, 'graphicsOffline', 0):
                if not hasattr(self, 'onlineAnim'):
                    self.buildAnim, self.onlineAnim = self.PrepareModelForConstruction(True, True)
                self.onlineAnim.scale = 1.0
                self.onlineAnim.Play()
                if self.IsControlTower():
                    self.PlayGeneralAudioEvent('wise:/msg_ct_online_play')
                else:
                    self.PlayGeneralAudioEvent('wise:/msg_pos_online_play')
            self.graphicsOffline = False
        if hasattr(self.model, 'ChainAnimationEx'):
            self.ResetAfterConstruction()
            self.model.ChainAnimationEx('NormalLoop', 0, 0, 1)

    def OfflineAnimation(self, animate = 0):
        if hasattr(self.model, 'curveSets'):
            if not hasattr(self, 'onlineAnim') or not self.onlineAnim:
                self.buildAnim, self.onlineAnim = self.PrepareModelForConstruction(True, True)
            self.onlineAnim.scale = -1.0
            self.onlineAnim.PlayFrom(self.onlineAnim.GetMaxCurveDuration())
        else:
            onlineCurves = FindCurves(self.model, 'online')
            ReverseTimeCurves(onlineCurves)
        self.graphicsOffline = True
        if animate:
            if self.IsControlTower():
                self.PlayGeneralAudioEvent('wise:/msg_ct_online_play')
            else:
                self.PlayGeneralAudioEvent('wise:/msg_pos_offline_play')
        if hasattr(self.model, 'EndAnimation'):
            self.model.EndAnimation()
