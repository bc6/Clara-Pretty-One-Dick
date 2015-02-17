#Embedded file name: iconrendering\__init__.py
"""
Package with functionality for the following:

- Rendering of icons and 2D images for the EVE client.
  This includes blueprints, icons, spaceobject renders, apparel renders,
  planets, pins, etc.
  Most of this is in `photo`.
- The IEC (Image Export Collection), which includes:
  - High-level orchestration (`rendermanagement`).
  - Mapping data setup and design choices into actual rendering code
    setup (`rendersetup.py`).
  - Packaging of IEC renders into zip files (`packaging`)
  - User interfaces for running the IEC (`iec_cli`, `iec_gui`)
"""
import inventorycommon.const as const
APPNAME = 'iconrendering'
TIMESTAMP_FORMAT = '%Y_%m_%d_%H_%M_%S'
USAGE_INGAME_ICON = 'ingame'
USAGE_IEC_ICON = 'icon'
USAGE_IEC_RENDER = 'render'
BLUEPRINT_NONE = 'none'
BLUEPRINT_NORMAL = 'normal'
BLUEPRINT_COPY = 'copy'
BLUEPRINT_DUST = 'dust'
BLUEPRINT_RELIC = 'relic'
ICON_GROUPS_INGAME = (const.groupCargoContainer,
 const.groupSecureCargoContainer,
 const.groupAuditLogSecureContainer,
 const.groupFreightContainer,
 const.groupHarvestableCloud,
 const.groupAsteroidBelt,
 const.groupTemporaryCloud,
 const.groupPlanetaryLinks,
 const.groupSolarSystem)
ICON_GROUPS_IEC = ICON_GROUPS_INGAME + (const.groupPlanet, const.groupMoon)
NON_ICON_GROUPS = (const.groupCharacter,
 const.groupStation,
 const.groupStargate,
 const.groupWreck)
NON_ICON_CATEGORIES = (const.categoryCelestial,
 const.categoryShip,
 const.categoryStation,
 const.categoryEntity,
 const.categoryDrone,
 const.categoryDeployable,
 const.categoryStructure,
 const.categorySovereigntyStructure,
 const.categoryPlanetaryInteraction,
 const.categoryOrbital)

class IconRenderingException(Exception):
    pass
