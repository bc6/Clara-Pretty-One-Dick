#Embedded file name: planetCommon.py
"""This is an autogenerated file to mimic the nasty namespace."""
from eve.common.script.util.planetCommon import CanPutTypeInCustomsOffice
from eve.common.script.util.planetCommon import ECU_MAX_HEADS
from eve.common.script.util.planetCommon import GetBandwidth
from eve.common.script.util.planetCommon import GetCPUAndPowerForPinType
from eve.common.script.util.planetCommon import GetCPUOutput
from eve.common.script.util.planetCommon import GetCommodityTotalVolume
from eve.common.script.util.planetCommon import GetCpuUsageForLink
from eve.common.script.util.planetCommon import GetCycleTimeFromProgramLength
from eve.common.script.util.planetCommon import GetDistanceBetweenPins
from eve.common.script.util.planetCommon import GetExpeditedTransferTime
from eve.common.script.util.planetCommon import GetGenericPinName
from eve.common.script.util.planetCommon import GetMaxCommandUpgradeLevel
from eve.common.script.util.planetCommon import GetPinEntityType
from eve.common.script.util.planetCommon import GetPowerOutput
from eve.common.script.util.planetCommon import GetPowerUsageForLink
from eve.common.script.util.planetCommon import GetProgramLengthFromHeadRadius
from eve.common.script.util.planetCommon import GetRouteValidationInfo
from eve.common.script.util.planetCommon import GetUpgradeCost
from eve.common.script.util.planetCommon import GetUsageParametersForLinkType
from eve.common.script.util.planetCommon import ItemIDToPinDesignator
from eve.common.script.util.planetCommon import LINK_MAX_UPGRADE
from eve.common.script.util.planetCommon import LINK_UPGRADE_BASECOST
from eve.common.script.util.planetCommon import MAX_WAYPOINTS
from eve.common.script.util.planetCommon import NETWORK_UPDATE_DELAY
from eve.common.script.util.planetCommon import PLANET_CACHE_TIMEOUT
from eve.common.script.util.planetCommon import RADIUS_DRILLAREADIFF
from eve.common.script.util.planetCommon import RADIUS_DRILLAREAMAX
from eve.common.script.util.planetCommon import RADIUS_DRILLAREAMIN
from eve.common.script.util.planetCommon import RESOURCE_CACHE_TIMEOUT
from eve.common.script.util.planetCommon import importExportThrottleTimer
from eve.common.script.util.planetCommon import priority_dict
from eve.client.script.ui.shared.planet.planetCommon import AMBIENT_SOUNDS
from eve.client.script.ui.shared.planet.planetCommon import ConvertToDMS
from eve.client.script.ui.shared.planet.planetCommon import DARKPLANETS
from eve.client.script.ui.shared.planet.planetCommon import FmtGeoCoordinates
from eve.client.script.ui.shared.planet.planetCommon import GetContrastColorForCurrPlanet
from eve.client.script.ui.shared.planet.planetCommon import GetPickIntersectionPoint
from eve.client.script.ui.shared.planet.planetCommon import GetPinCycleInfo
from eve.client.script.ui.shared.planet.planetCommon import GetSchematicData
from eve.client.script.ui.shared.planet.planetCommon import GetSchematicDataByGroupID
from eve.client.script.ui.shared.planet.planetCommon import GetSphereLineIntersectionPoint
from eve.client.script.ui.shared.planet.planetCommon import NormalizeLatitude
from eve.client.script.ui.shared.planet.planetCommon import NormalizeLongitude
from eve.client.script.ui.shared.planet.planetCommon import PANELDATA
from eve.client.script.ui.shared.planet.planetCommon import PANEL_DECOMMISSION
from eve.client.script.ui.shared.planet.planetCommon import PANEL_INCOMING
from eve.client.script.ui.shared.planet.planetCommon import PANEL_LAUNCH
from eve.client.script.ui.shared.planet.planetCommon import PANEL_LINKS
from eve.client.script.ui.shared.planet.planetCommon import PANEL_OUTGOING
from eve.client.script.ui.shared.planet.planetCommon import PANEL_PRODUCTS
from eve.client.script.ui.shared.planet.planetCommon import PANEL_ROUTES
from eve.client.script.ui.shared.planet.planetCommon import PANEL_SCHEMATICS
from eve.client.script.ui.shared.planet.planetCommon import PANEL_STATS
from eve.client.script.ui.shared.planet.planetCommon import PANEL_STORAGE
from eve.client.script.ui.shared.planet.planetCommon import PANEL_SURVEYFORDEPOSITS
from eve.client.script.ui.shared.planet.planetCommon import PANEL_UPGRADE
from eve.client.script.ui.shared.planet.planetCommon import PANEL_UPGRADELINK
from eve.client.script.ui.shared.planet.planetCommon import PINTYPE_DEPLETION
from eve.client.script.ui.shared.planet.planetCommon import PINTYPE_EXTRACTIONHEAD
from eve.client.script.ui.shared.planet.planetCommon import PINTYPE_NOPICK
from eve.client.script.ui.shared.planet.planetCommon import PINTYPE_NORMAL
from eve.client.script.ui.shared.planet.planetCommon import PINTYPE_NORMALEDIT
from eve.client.script.ui.shared.planet.planetCommon import PINTYPE_OTHERS
from eve.client.script.ui.shared.planet.planetCommon import PLANET_2PI
from eve.client.script.ui.shared.planet.planetCommon import PLANET_COLOR_BANDWIDTH
from eve.client.script.ui.shared.planet.planetCommon import PLANET_COLOR_CPU
from eve.client.script.ui.shared.planet.planetCommon import PLANET_COLOR_CPUUPGRADE
from eve.client.script.ui.shared.planet.planetCommon import PLANET_COLOR_CURRLEVEL
from eve.client.script.ui.shared.planet.planetCommon import PLANET_COLOR_CYCLE
from eve.client.script.ui.shared.planet.planetCommon import PLANET_COLOR_EXTRACTIONLINK
from eve.client.script.ui.shared.planet.planetCommon import PLANET_COLOR_EXTRACTOR
from eve.client.script.ui.shared.planet.planetCommon import PLANET_COLOR_ICON_COMMANDCENTER
from eve.client.script.ui.shared.planet.planetCommon import PLANET_COLOR_ICON_EXTRACTOR
from eve.client.script.ui.shared.planet.planetCommon import PLANET_COLOR_ICON_PROCESSOR
from eve.client.script.ui.shared.planet.planetCommon import PLANET_COLOR_ICON_SPACEPORT
from eve.client.script.ui.shared.planet.planetCommon import PLANET_COLOR_ICON_STORAGE
from eve.client.script.ui.shared.planet.planetCommon import PLANET_COLOR_LINKEDITMODE
from eve.client.script.ui.shared.planet.planetCommon import PLANET_COLOR_PINEDITMODE
from eve.client.script.ui.shared.planet.planetCommon import PLANET_COLOR_POWER
from eve.client.script.ui.shared.planet.planetCommon import PLANET_COLOR_POWERUPGRADE
from eve.client.script.ui.shared.planet.planetCommon import PLANET_COLOR_PROCESSOR
from eve.client.script.ui.shared.planet.planetCommon import PLANET_COLOR_STORAGE
from eve.client.script.ui.shared.planet.planetCommon import PLANET_COLOR_UPGRADELEVEL
from eve.client.script.ui.shared.planet.planetCommon import PLANET_COLOR_USED_PROCESSOR
from eve.client.script.ui.shared.planet.planetCommon import PLANET_COLOR_USED_STORAGE
from eve.client.script.ui.shared.planet.planetCommon import PLANET_COMMANDCENTERMAXLEVEL
from eve.client.script.ui.shared.planet.planetCommon import PLANET_HEATMAP_COLORS
from eve.client.script.ui.shared.planet.planetCommon import PLANET_PI_DIV_2
from eve.client.script.ui.shared.planet.planetCommon import PLANET_RESOURCE_TEX_HEIGHT
from eve.client.script.ui.shared.planet.planetCommon import PLANET_RESOURCE_TEX_WIDTH
from eve.client.script.ui.shared.planet.planetCommon import PLANET_SCALE
from eve.client.script.ui.shared.planet.planetCommon import PLANET_TEXTURE_SIZE
from eve.client.script.ui.shared.planet.planetCommon import PLANET_ZOOM_MAX
from eve.client.script.ui.shared.planet.planetCommon import PLANET_ZOOM_MIN
from eve.client.script.ui.shared.planet.planetCommon import PinHasBeenBuilt
