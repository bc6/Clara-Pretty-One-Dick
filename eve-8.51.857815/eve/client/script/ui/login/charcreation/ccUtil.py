#Embedded file name: eve/client/script/ui/login/charcreation\ccUtil.py
"""
This file contains utility methods for character creation
"""
import paperDoll
import ccConst
import telemetry
import blue
import yaml
import trinity

@telemetry.ZONE_FUNCTION
def GenderIDToPaperDollGender(genderID):
    """
    Returns the paperDoll gender for a given genderID
    """
    if genderID == ccConst.GENDERID_FEMALE:
        return paperDoll.GENDER.FEMALE
    if genderID == ccConst.GENDERID_MALE:
        return paperDoll.GENDER.MALE
    raise RuntimeError('GenderIDToPaperDollGender: Invalid genderID!')


@telemetry.ZONE_FUNCTION
def PaperDollGenderToGenderID(gender):
    """
    Returns the genderID for a given paperDoll gender.
    """
    if gender == paperDoll.GENDER.MALE:
        return ccConst.GENDERID_MALE
    if gender == paperDoll.GENDER.FEMALE:
        return ccConst.GENDERID_FEMALE
    raise RuntimeError('PaperDollGenderToGenderID: Invalid gender!')


@telemetry.ZONE_FUNCTION
def SetupLighting(scene, lightScene, lightColorScene, lightIntensity = 0.5):
    """
    Sets the lights in a scene
    """
    intensityMultiplier = 0.75 + lightIntensity / 2.0
    if scene is not None:
        lightList = []
        for l in scene.lights:
            lightList.append(l)

        for l in lightList:
            scene.RemoveLightSource(l)

        for index in range(len(lightScene.lights)):
            light = lightScene.lights[index]
            for l in lightColorScene.lights:
                if l.name == light.name:
                    light.color = l.color

            light.color = (light.color[0] * intensityMultiplier,
             light.color[1] * intensityMultiplier,
             light.color[2] * intensityMultiplier,
             1.0)
            scene.AddLightSource(light)

        if paperDoll.SkinSpotLightShadows.instance is not None:
            paperDoll.SkinSpotLightShadows.instance.RefreshLights()


@telemetry.ZONE_FUNCTION
def LoadFromYaml(path):
    return paperDoll.LoadYamlFileNicely(path)


def HasUserDefinedWeight(category):
    """
        Returns whether there is a slider controlling weights
        on this modifier
    """
    return ccConst.COLORMAPPING.get(category, (0, 0))[0]


def HasUserDefinedSpecularity(category):
    """
        Returns whether there is a slider controlling specularity
        (glossiness) on this modifier
    """
    return ccConst.COLORMAPPING.get(category, (0, 0))[1]


def SupportsHigherShaderModel():
    shaderModel = trinity.GetShaderModel()
    maxSupported = trinity.GetMaxShaderModelSupported()
    if shaderModel == 'SM_2_0_LO' and maxSupported.startswith('SM_3'):
        return True
    return False


def CreateCategoryFolderIfNeeded(outputroot, folderName):
    import os
    folderName = os.path.normpath(folderName)
    if os.path.isdir(outputroot + folderName):
        return
    os.mkdir(outputroot + folderName)


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('ccUtil', globals())
