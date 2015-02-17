#Embedded file name: eve/client/script/ui/station\worldspaceCustomization.py
"""
A namespace with function ApplyWorldspaceCustomization that when provided a list of shader parameter 
changes plus changes to light colors and some other stuff, is able to determine in which station the 
player is in and who owns that station and applies specific shader changes to the objects in the scene 
if a theme definition is found for the race-owner combination
"""
import worldspaceCustomizationDefinitions

def ApplyWorldspaceCustomization():
    if not eve.stationItem or session.worldspaceid != session.stationid2:
        return
    stationTypeID = eve.stationItem.stationTypeID
    stationType = cfg.invtypes.Get(stationTypeID)
    stationRace = stationType.raceID
    if stationRace not in worldspaceCustomizationDefinitions.themeSettings:
        return
    if eve.stationItem.ownerID not in worldspaceCustomizationDefinitions.themeSettings[stationRace]:
        return
    changes = worldspaceCustomizationDefinitions.themeSettings[stationRace][eve.stationItem.ownerID]
    UpdateShaderParameters(changes.shaderParameters)
    if changes.flares:
        UpdateFlares(*changes.flares)
    if changes.pointLights:
        UpdateSpotPointLights(*changes.pointLights)
    if changes.cylendricalLights:
        UpdateCylendricalLights(*changes.cylendricalLights)
    UpdateEnlightenTexture()


def UpdateFlares(r = 1, g = 1, b = 1, a = 1):
    """
    Find all Tr2InteriorFlares in the scene and adjusts their color
    """
    MultiplyColorValue('trinity.Tr2InteriorFlare', r, g, b, a)


def UpdateSpotPointLights(r = 1, g = 1, b = 1, a = 1):
    """ 
    Find all Tr2InteriorLightSources in the scene and adjust their color.
    These are SpotLights and PointLights.
    """
    MultiplyColorValue('trinity.Tr2InteriorLightSource', r, g, b, a)


def UpdateCylendricalLights(r = 1, g = 1, b = 1, a = 1):
    """
    Find all Tr2InteriorCylinderLights in the scene and adjust their color.
    """
    MultiplyColorValue('trinity.Tr2InteriorCylinderLight', r, g, b, a)


def MultiplyColorValue(trinityObjectName, r = 1, g = 1, b = 1, a = 1):
    """ 
    Find trinityObjectName instances in the scene and modify RGBA color
    """
    scene = sm.GetService('sceneManager').incarnaRenderJob.scene.object
    for effect in scene.Find(trinityObjectName):
        currentColor = effect.color
        effect.color = (currentColor[0] * r,
         currentColor[1] * g,
         currentColor[2] * b,
         currentColor[3] * a)


def UpdateShaderParameters(params):
    """
    Collects all Tr2MeshAreas from the scene (including the static ones such as walls and floors that live in
    scene.objects). Then iterates over them, searching first for a specific shader provided in the params keyval,
    if found, searches for the shader parameter provided in params, and if that is found, applies the changes
    stored in params to that parameter.
    """
    meshAreas = []
    scene = sm.GetService('sceneManager').incarnaRenderJob.scene.object
    meshAreas.extend(scene.Find('trinity.Tr2MeshArea'))
    for interiorStatic, system in scene.objects.iteritems():
        staticMesh = interiorStatic.Find('trinity.Tr2MeshArea')
        meshAreas.extend(staticMesh)

    for each in meshAreas:
        if not hasattr(each, 'effect'):
            continue
        if not hasattr(each.effect, 'highLevelShaderName'):
            continue
        for entry in params:
            if entry.highLevelShader != each.effect.highLevelShaderName:
                continue
            resourcePath = ''
            if entry.textureName != 'NoTexture' and entry.parameter in each.effect.parameters and hasattr(each.effect.parameters[entry.parameter], 'resourcePath'):
                resourcePath = each.effect.parameters[entry.parameter].resourcePath.lower()
            if entry.textureName.lower() in resourcePath or entry.textureName == 'NoTexture':
                SetShaderMaterialValue(each.effect.parameters, entry.parameter, entry.value, entry.hdr)


def SetShaderMaterialValue(parameter, effectEntry, value, modifier = 1.0):
    """
    Given a parameter (a shader parameter), modifies the parameter's effectEntry
    (such as "MaterialDiffuseColor") to value provided. Value can be a string (swapping
    out textures) a float (e.g. intensity ) or a tuple (e.g. color).
    """
    if isinstance(value, basestring):
        parameter[effectEntry].resourcePath = value
    elif isinstance(value, float):
        parameter[effectEntry].value = value * modifier
    else:
        parameter[effectEntry].value = [ x * modifier for x in value ]


def UpdateEnlightenTexture():
    """
    Find and push update for enlighten textures
    """
    scene = sm.GetService('sceneManager').incarnaRenderJob.scene.object
    for entry in scene.Find('trinity.Tr2InteriorEnlightenSystem'):
        entry.UpdateEnlightenMaterialTextures()


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('worldspaceCustomization', locals())
