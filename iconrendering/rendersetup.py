#Embedded file name: iconrendering\rendersetup.py
import os
import shutil
import site
import sys
_PKGSPATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
site.addsitedir(_PKGSPATH)
_ROOTPATH = os.path.abspath(os.path.join(_PKGSPATH, '..'))
if _ROOTPATH not in sys.path:
    sys.path.append(_ROOTPATH)
import osutils
try:
    import blue
except ImportError:
    blue = None

import devenv.libconst as const
import inventorycommon.const as invconst
import iconrendering.photo as photo
from iconrendering import USAGE_IEC_ICON, USAGE_INGAME_ICON, USAGE_IEC_RENDER
from iconrendering import BLUEPRINT_NONE, BLUEPRINT_NORMAL, BLUEPRINT_COPY, BLUEPRINT_RELIC, BLUEPRINT_DUST
from iconrendering import ICON_GROUPS_IEC, NON_ICON_GROUPS, NON_ICON_CATEGORIES
from evegraphics.utils import CombineSOFDNA
FALLBACK_ICON = 'res:/UI/Texture/notavailable.dds'
ICON_BLUEPRINT_BACKGROUND = 'res:/UI/Texture/Icons/BPO.png'
ICON_BLUEPRINT_OVERLAY = 'res:/UI/Texture/Icons/bpo_overlay.png'
ICON_BLUEPRINT_COPY_BACKGROUND = 'res:/UI/Texture/Icons/BPC.png'
ICON_BLUEPRINT_COPY_OVERLAY = 'res:/UI/Texture/Icons/bpc_overlay.png'
ICON_BLUEPRINT_RELIC_BACKGROUND = 'res:/UI/Texture/Icons/relic.png'
ICON_BLUEPRINT_RELIC_OVERLAY = 'res:/UI/Texture/Icons/relic_overlay.png'
ICON_BLUEPRINT_DUSTBACKGROUND = 'res:/UI/Texture/Icons/BPD.png'
BLUEPRINT_STRING = 'BP'
BLUEPRINT_STRING_COPY = 'BPC'
SCENE_BLUEPRINT = 'res:/dx9/scene/blueprint/original.red'
DIR_ICONS = 'res:/UI/Texture/Icons'
DIR_CORPS = 'res:/UI/Texture/Corps'
RENDER_METHOD_NONE = 'none'
RENDER_METHOD_ICON = 'icon'
RENDER_METHOD_SPACEOBJECT = 'spaceobject'
RENDER_METHOD_TURRET = 'turret'
RENDER_METHOD_PIN = 'pin'
RENDER_METHOD_SUN = 'sun'
RENDER_METHOD_APPAREL = 'apparel'
GROUP_MISSILE_BLUEPRINT = 166
_APPAREL_RENDERS_CACHEDIR = os.path.join(os.path.dirname(__file__), '_apparelcache')
SKIP_TYPES = (4044, 4045, 4049, 22691, 28610, 16132, 3964)
RENDER_CATEGORIES = (const.categoryDrone,
 const.categoryShip,
 const.categoryStation,
 const.categoryStructure,
 const.categoryDeployable,
 const.categorySovereigntyStructure,
 const.categoryPlanetaryInteraction,
 const.categoryOrbital,
 const.categoryApparel)
RENDER_GROUPS = (const.groupPlanetaryCustomsOffices,)
ICON_CATEGORIES = (const.categoryModule,
 const.categoryApparel,
 const.categoryCharge,
 const.categoryCommodity,
 const.categoryAccessories,
 const.categorySubSystem,
 invconst.categoryInfantry)
TECH_LEVEL_ICON = {2: 'res:/UI/Texture/Icons/73_16_242.png',
 3: 'res:/UI/Texture/Icons/73_16_243.png'}
META_LEVEL_ICON_BY_ID = {const.metaGroupStoryline: 'res:/UI/Texture/Icons/73_16_245.png',
 const.metaGroupFaction: 'res:/UI/Texture/Icons/73_16_246.png',
 const.metaGroupDeadspace: 'res:/UI/Texture/Icons/73_16_247.png',
 const.metaGroupOfficer: 'res:/UI/Texture/Icons/73_16_248.png'}

def GetRenderFunctionType(groupID, categoryID):
    if groupID == const.groupSun:
        return RENDER_METHOD_SUN
    if categoryID == const.categoryPlanetaryInteraction:
        return RENDER_METHOD_PIN
    if categoryID == const.categoryApparel:
        return RENDER_METHOD_APPAREL
    if categoryID == const.categoryModule:
        if groupID in const.turretModuleGroups:
            return RENDER_METHOD_TURRET
    return RENDER_METHOD_SPACEOBJECT


def GetOutputPath(outputFolder, typeID, graphicID, size, blueprint = BLUEPRINT_NONE, usage = None, raceID = None, blueprintID = None):
    if not os.path.exists(outputFolder):
        os.makedirs(outputFolder)
    if usage == USAGE_INGAME_ICON:
        if not raceID:
            raceID = 0
        if blueprint == BLUEPRINT_NONE:
            fileName = '%s_%s_%s.png' % (graphicID, size, raceID)
        else:
            if blueprint == BLUEPRINT_NORMAL:
                blueprintString = BLUEPRINT_STRING
            else:
                blueprintString = BLUEPRINT_STRING_COPY
            fileName = '%s_%s_%s_%s.png' % (graphicID,
             size,
             0,
             blueprintString)
    elif usage == USAGE_IEC_RENDER:
        fileName = str(typeID) + '.png'
    elif blueprint == BLUEPRINT_NORMAL:
        fileName = '%s_%s.png' % (blueprintID, size)
    else:
        fileName = '%s_%s.png' % (typeID, size)
    return os.path.join(outputFolder, fileName)


def GetTechIcon(inventoryMapper, typeID):
    """Return the tech icon path for a given typeID"""
    metaGroupID = inventoryMapper.GetDogmaAttributeForTypeID(const.attributeMetaGroupID, typeID)
    if metaGroupID:
        metaGroupID = int(metaGroupID)
        if metaGroupID in META_LEVEL_ICON_BY_ID:
            return META_LEVEL_ICON_BY_ID[metaGroupID]
    techLevel = inventoryMapper.GetDogmaAttributeForTypeID(const.attributeTechLevel, typeID)
    if techLevel in TECH_LEVEL_ICON:
        return TECH_LEVEL_ICON[techLevel]


def UseIcon(typeID, groupID, categoryID):
    if typeID == const.typePlanetaryLaunchContainer:
        return False
    if groupID in ICON_GROUPS_IEC:
        return True
    if groupID in NON_ICON_GROUPS or categoryID in NON_ICON_CATEGORIES:
        return False
    return True


def GetCachedApparelRenderPath(typeID):
    cachedSrcPath = os.path.join(_APPAREL_RENDERS_CACHEDIR, '%s.png' % typeID)
    if os.path.exists(cachedSrcPath):
        return cachedSrcPath


def GetNPCStationRenderFuncAndArgs(resourceMapper, typeID, graphicID, raceID, size, outputFolder):
    graphicFile = resourceMapper.GetGraphicFileForGraphicID(graphicID)
    scenePath = photo.GetScenePathByRaceID(raceID)
    outPath = GetOutputPath(outputFolder, typeID, graphicID, size, blueprint=BLUEPRINT_NONE, usage=USAGE_INGAME_ICON, raceID=raceID)
    return (photo.RenderSpaceObject, [outPath,
      scenePath,
      graphicFile,
      None,
      size,
      None,
      False,
      None,
      None,
      None])


def GetRenderFunctionAndArgs(resourceMapper, inventoryMapper, typeID, groupID, categoryID, raceID, size, outputFolder, usage, renderType = None, blueprint = BLUEPRINT_NONE, blueprintID = None):
    """Return the function and arguments required to render the type supplied.
    
    :param resourceMapper: Instance of py:func:`fsdauthoringutils.GraphicsCache`
    :param inventoryMapper: Instance of py:func:`iconrendering.inventory_map.InventoryMapper`
    :param typeID: The type ID of the item.
    :param groupID: The group ID of the item.
    :param categoryID: The category ID of the item.
    :param raceID: The race ID of the item.
    :param size: Integer defining the render size.
    :param outputFolder: The folder to store the output
    :param usage: One of the iconrendering.USAGE_* constants.
    :param renderType: Optional parameter. One of the RENDER_METHOD_* values.
      When not passed uses py:func:`GetRenderFunctionType`.
    :param blueprint: Enum flagging the render for special blueprint treatment.
    :param blueprintID: The id of the original blueprint.
    """
    iconFile = resourceMapper.GetIconFileForTypeID(typeID)
    iconPath = photo.GetIconFileFromSheet(iconFile)
    graphicID = resourceMapper.GetGraphicIDForTypeID(typeID)
    graphicFile = resourceMapper.GetGraphicFileForGraphicID(graphicID)
    sofDNA = None
    sofData = resourceMapper.GetSOFDataForGraphicID(graphicID)
    if all(sofData):
        sofDataForType = resourceMapper.GetSOFDataForTypeID(typeID)
        sofDNA = CombineSOFDNA(sofAddition=sofDataForType[0], *sofData)
    if usage == USAGE_INGAME_ICON and not (graphicFile or sofDNA):
        return
    backgroundPath = None
    overlayPath = None
    if blueprint == BLUEPRINT_NORMAL:
        backgroundPath = ICON_BLUEPRINT_BACKGROUND
        overlayPath = ICON_BLUEPRINT_OVERLAY
    elif blueprint == BLUEPRINT_COPY:
        backgroundPath = ICON_BLUEPRINT_COPY_BACKGROUND
        overlayPath = ICON_BLUEPRINT_COPY_OVERLAY
    elif blueprint == BLUEPRINT_RELIC:
        backgroundPath = ICON_BLUEPRINT_RELIC_BACKGROUND
        overlayPath = ICON_BLUEPRINT_RELIC_OVERLAY
    elif blueprint == BLUEPRINT_DUST:
        backgroundPath = ICON_BLUEPRINT_DUSTBACKGROUND
    outPath = GetOutputPath(outputFolder, typeID, graphicID, size, blueprint, usage, raceID, blueprintID)
    if renderType is None:
        renderType = GetRenderFunctionType(groupID, categoryID)
    if renderType == RENDER_METHOD_APPAREL:
        srcpath = iconFile
        if usage == USAGE_IEC_RENDER:
            srcpath = GetCachedApparelRenderPath(typeID) or srcpath
        return (photo.RenderApparel, [outPath, srcpath, size], {})
    if usage == USAGE_IEC_ICON:
        if UseIcon(typeID, groupID, categoryID):
            renderType = RENDER_METHOD_ICON
    elif not (graphicFile or sofDNA):
        return
    if not (graphicFile or iconPath or sofDNA) and usage != USAGE_IEC_RENDER:
        return (photo.RenderIcon, [outPath,
          size,
          None,
          None,
          None,
          FALLBACK_ICON], {})
    if usage == USAGE_IEC_RENDER:
        iconPath = None
        techPath = None
        backgroundPath = None
        overlayPath = None
    elif usage == USAGE_INGAME_ICON:
        techPath = None
    else:
        techPath = GetTechIcon(inventoryMapper, typeID)
    if renderType == RENDER_METHOD_PIN:
        return (photo.RenderPin, [outPath, graphicFile, size], {})
    if renderType == RENDER_METHOD_SPACEOBJECT:
        if blueprint != BLUEPRINT_NONE:
            scenePath = SCENE_BLUEPRINT
        else:
            scenePath = photo.GetScenePathByRaceID(raceID)
        animationStates = resourceMapper.GetGraphicStateFilesFromGraphicID(graphicID)
        return (photo.RenderSpaceObject, [outPath], {'scenePath': scenePath,
          'objectPath': graphicFile,
          'sofDNA': sofDNA,
          'size': size,
          'backgroundPath': backgroundPath,
          'overlayPath': overlayPath,
          'techPath': techPath,
          'animationStates': animationStates})
    if renderType == RENDER_METHOD_TURRET:
        if usage == USAGE_IEC_ICON:
            return (photo.RenderIcon, [outPath,
              size,
              backgroundPath,
              overlayPath,
              techPath,
              iconPath], {})
        else:
            sofDataForType = resourceMapper.GetSOFDataForTypeID(typeID)
            return (photo.RenderTurret, [outPath,
              graphicFile,
              sofDataForType[1],
              size], {})
    if renderType == RENDER_METHOD_SUN:
        scenePath = photo.DEFAULT_SCENE_PATH
        return (photo.RenderSun, [outPath,
          graphicFile,
          scenePath,
          size], {})
    if renderType == RENDER_METHOD_ICON:
        return (photo.RenderIcon, [outPath,
          size,
          backgroundPath,
          overlayPath,
          techPath,
          iconPath], {})


def YieldAllRenderFuncsAndArgs(resourceMapper, inventoryMapper, outputFolder, size, logger, filterFunc = None, typeDatas = None, **kwargs):
    """Returns a generator yielding callable,
    arguments tuple for rendering for all types that pass ``filterFunc``.
    
    :type resourceMapper: fsdauthoringutils.GraphicsCache
    :type inventoryMapper: iconrendering.inventory_map.InventoryMapper
    :param outputFolder: A folder path defining where the renders
      will be placed. See py:func:`GetOutputPath` for usage
    :param size: Integer defining the render size
    :param logger: A python logger
    :param filterFunc: A callable that takes
      ``typeID, groupID, categoryID, raceID`` that filters which types,
      groups and categories we will render
    :param typeDatas: An optional list of type data to process
    """
    if typeDatas:
        typeGenerator = lambda : typeDatas
    else:
        typeGenerator = inventoryMapper.GetAllTypesData
    for typeData in typeGenerator():
        typeID, groupID, categoryID, raceID = typeData
        blueprint = BLUEPRINT_NONE
        blueprintID = None
        if categoryID == const.categoryBlueprint:
            blueprint = BLUEPRINT_NORMAL
            blueprintID = typeID
            typeID = inventoryMapper.GetBlueprintProductType(typeID)
            if typeID is None:
                continue
            result = inventoryMapper.GetGroupAndCategoryByType(typeID)
            if result:
                groupID, categoryID = result
            else:
                logger.warning('The blueprint %s with product %s is invalid' % (blueprintID, typeID))
                continue
        elif categoryID == invconst.categoryAncientRelic:
            blueprint = BLUEPRINT_RELIC
        elif categoryID == invconst.categoryInfantry:
            blueprint = BLUEPRINT_DUST
        if filterFunc and filterFunc(typeID, groupID, categoryID, raceID, blueprint=blueprint):
            usage = kwargs.get('usage')
            yield GetRenderFunctionAndArgs(resourceMapper, inventoryMapper, typeID, groupID, categoryID, raceID, size, outputFolder, usage, blueprint=blueprint, blueprintID=blueprintID)
            if blueprint == BLUEPRINT_NORMAL and usage == USAGE_INGAME_ICON:
                yield GetRenderFunctionAndArgs(resourceMapper, inventoryMapper, typeID, groupID, categoryID, raceID, size, outputFolder, usage, blueprint=BLUEPRINT_COPY, blueprintID=blueprintID)


def FilterForTypes(typeID, groupID, categoryID, raceID, **kwargs):
    return True


def FilterForRenders(typeID, groupID, categoryID, raceID, **kwargs):
    if kwargs.get('blueprint', BLUEPRINT_NONE) != BLUEPRINT_NONE:
        return False
    if typeID in SKIP_TYPES:
        return False
    if categoryID in RENDER_CATEGORIES:
        return True
    if groupID in const.turretModuleGroups or groupID in RENDER_GROUPS:
        return True
    return False


def FilterForIngameIcons(typeID, groupID, categoryID, raceID, **kwargs):
    if groupID in ICON_GROUPS_IEC or categoryID in ICON_CATEGORIES:
        return False
    if groupID in NON_ICON_GROUPS or categoryID in NON_ICON_CATEGORIES:
        return True
    return False


def FilterForIngameIconsNoBluePrints(typeID, groupID, categoryID, raceID, **kwargs):
    if kwargs.get('blueprint', False) != BLUEPRINT_NONE:
        return False
    if groupID in ICON_GROUPS_IEC or categoryID in ICON_CATEGORIES:
        return False
    if groupID in NON_ICON_GROUPS or categoryID in NON_ICON_CATEGORIES:
        return True
    return False


def CopyIconDirs(outroot):
    """Copies the icon directories into the output folder
    (will copy into 'Icons' subdir)."""
    outroot = os.path.join(outroot, 'Icons')
    if not os.path.exists(outroot):
        os.makedirs(outroot)
    iconoutdir = os.path.join(outroot, 'items')
    corpsoutdir = os.path.join(outroot, 'corporations')
    for src, tgt in ((DIR_ICONS, iconoutdir), (DIR_CORPS, corpsoutdir)):
        realsrc = blue.paths.ResolvePath(src)
        shutil.copytree(realsrc, tgt)
        map(lambda p: osutils.SetReadonly(p, False), osutils.FindFiles(tgt))


def FileWriter(outPath, *args, **kwargs):
    """Creates a file in ``outPath``, with content of arguments passed in.
    For testing rendering logic."""
    with open(outPath, 'w') as f:
        f.write('Args: %s\nKwargs: %s' % (args, kwargs))
