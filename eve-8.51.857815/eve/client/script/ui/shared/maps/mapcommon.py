#Embedded file name: eve/client/script/ui/shared/maps\mapcommon.py
"""
This file contains declarations for constants used by various map-related files
"""
import trinity
import utillib as util
MODE_SOLARSYSTEM = 1
MODE_CONSTELLATION = 2
MODE_REGION = 3
MODE_UNIVERSE = 4
MODE_HIDE = 5
MODE_NOLINES = 6
COLORMODE_UNIFORM = 1
COLORMODE_REGION = 2
COLORMODE_FACTION = 3
COLORMODE_CONSTELLATION = 4
COLORMODE_POPULATION = 5
COLORMODE_STANDINGS = 6
DISPLAYMODE_SINGLE = 0
DISPLAYMODE_NEIGHBORS = 1
DISPLAYMODE_NEIGHBORS2X = 2
DISPLAYMODE_ALL = 3
STARMODE_REAL = 0
STARMODE_SECURITY = 1
STARMODE_FACTION = 2
STARMODE_REGION = 3
STARMODE_JUMPS1HR = 4
STARMODE_SHIPKILLS1HR = 5
STARMODE_PODKILLS1HR = 6
STARMODE_PLAYERCOUNT = 7
STARMODE_VISITED = 8
STARMODE_BOOKMARKED = 9
STARMODE_STATIONCOUNT = 10
STARMODE_FACTIONKILLS1HR = 11
STARMODE_PLAYERDOCKED = 12
STARMODE_FRIENDS_CORP = 13
STARMODE_FRIENDS_FLEET = 14
STARMODE_FRIENDS_AGENT = 15
STARMODE_ASSETS = 16
STARMODE_SHIPKILLS24HR = 17
STARMODE_PODKILLS24HR = 18
STARMODE_DUNGEONS = 19
STARMODE_CARGOILLEGALITY = 20
STARMODE_CYNOSURALFIELDS = 22
STARMODE_CORPOFFICES = 24
STARMODE_CORPIMPOUNDED = 25
STARMODE_CORPPROPERTY = 26
STARMODE_CORPDELIVERIES = 27
STARMODE_CONSTSOVEREIGNTY = 28
STARMODE_DUNGEONSAGENTS = 29
STARMODE_MILITIA = 30
STARMODE_MILITIAKILLS1HR = 31
STARMODE_MILITIAKILLS24HR = 32
STARMODE_AVOIDANCE = 35
STARMODE_FACTIONEMPIRE = 36
STARMODE_INDEX_STRATEGIC = 37
STARMODE_INDEX_MILITARY = 38
STARMODE_INDEX_INDUSTRY = 39
STARMODE_SOV_CHANGE = 40
STARMODE_SOV_GAIN = 41
STARMODE_SOV_LOSS = 42
STARMODE_OUTPOST_GAIN = 43
STARMODE_OUTPOST_LOSS = 44
STARMODE_SOV_STANDINGS = 45
STARMODE_SERVICE = 46
STARMODE_PISCANRANGE = 47
STARMODE_PLANETTYPE = 48
STARMODE_MYCOLONIES = 49
STARMODE_INCURSION = 50
STARMODE_INCURSIONGM = 51
STARMODE_FRIENDS_CONTACTS = 52
STARMODE_JOBS24HOUR = 53
STARMODE_MANUFACTURING_JOBS24HOUR = 54
STARMODE_RESEARCHTIME_JOBS24HOUR = 55
STARMODE_RESEARCHMATERIAL_JOBS24HOUR = 56
STARMODE_COPY_JOBS24HOUR = 57
STARMODE_INVENTION_JOBS24HOUR = 59
STARMODE_INDUSTRY_MANUFACTURING_COST_INDEX = 60
STARMODE_INDUSTRY_RESEARCHTIME_COST_INDEX = 61
STARMODE_INDUSTRY_RESEARCHMATERIAL_COST_INDEX = 62
STARMODE_INDUSTRY_COPY_COST_INDEX = 63
STARMODE_INDUSTRY_INVENTION_COST_INDEX = 65
STARMODE_SERVICE_AssassinationMissions = (STARMODE_SERVICE, const.stationServiceAssassinationMissions)
STARMODE_SERVICE_BlackMarket = (STARMODE_SERVICE, const.stationServiceBlackMarket)
STARMODE_SERVICE_Cloning = (STARMODE_SERVICE, const.stationServiceCloning)
STARMODE_SERVICE_CourierMissions = (STARMODE_SERVICE, const.stationServiceCourierMission)
STARMODE_SERVICE_DNATherapy = (STARMODE_SERVICE, const.stationServiceDNATherapy)
STARMODE_SERVICE_Factory = (STARMODE_SERVICE, const.stationServiceFactory)
STARMODE_SERVICE_Fitting = (STARMODE_SERVICE, const.stationServiceFitting)
STARMODE_SERVICE_Gambling = (STARMODE_SERVICE, const.stationServiceGambling)
STARMODE_SERVICE_Insurance = (STARMODE_SERVICE, const.stationServiceInsurance)
STARMODE_SERVICE_Interbus = (STARMODE_SERVICE, const.stationServiceInterbus)
STARMODE_SERVICE_Laboratory = (STARMODE_SERVICE, const.stationServiceLaboratory)
STARMODE_SERVICE_Market = (STARMODE_SERVICE, const.stationServiceMarket)
STARMODE_SERVICE_News = (STARMODE_SERVICE, const.stationServiceNews)
STARMODE_SERVICE_Paintshop = (STARMODE_SERVICE, 131072)
STARMODE_SERVICE_Refinery = (STARMODE_SERVICE, const.stationServiceRefinery)
STARMODE_SERVICE_RepairFacilities = (STARMODE_SERVICE, const.stationServiceRepairFacilities)
STARMODE_SERVICE_ReprocessingPlant = (STARMODE_SERVICE, const.stationServiceReprocessingPlant)
STARMODE_SERVICE_StockExchange = (STARMODE_SERVICE, const.stationServiceStockExchange)
STARMODE_SERVICE_Storage = (STARMODE_SERVICE, const.stationServiceStorage)
STARMODE_SERVICE_NavyOffices = (STARMODE_SERVICE, const.stationServiceNavyOffices)
STARMODE_SERVICE_Surgery = (STARMODE_SERVICE, const.stationServiceSurgery)
STARMODE_SERVICE_SecurityOffice = (STARMODE_SERVICE, const.stationServiceSecurityOffice)
STARMODE_FILTER_FACWAR_ENEMY = -1
STARMODE_FILTER_FACWAR_MINE = -2
STARMODE_FILTER_EMPIRE = -3
STARMAP_SCALE = 1e-13
SYSTEMMAP_SCALE = 1e-10
ZOOM_MAX_STARMAP = 200000.0
ZOOM_MIN_STARMAP = 4000.0
ZOOM_FAR_SYSTEMMAP = 8000.0
ZOOM_NEAR_SYSTEMMAP = 1.0
LINESET_EFFECT = 'res:/Graphics/Effect/Managed/Space/SpecialFX/LinesAdditive.fx'
LINESET_EFFECT_STARMAP = 'res:/Graphics/Effect/Managed/Space/SpecialFX/LinesAdditiveStarMap.fx'
LINESET_3D_EFFECT_STARMAP = 'res:/Graphics/Effect/Managed/Space/SpecialFX/Lines3DStarMap.fx'
COLORCURVE_SECURITY = [trinity.TriColor(1.0, 0.0, 0.0, 1.0),
 trinity.TriColor(0.9, 0.2, 0.0, 1.0),
 trinity.TriColor(1.0, 0.3, 0.0, 1.0),
 trinity.TriColor(1.0, 0.4, 0.0, 1.0),
 trinity.TriColor(0.9, 0.5, 0.0, 1.0),
 trinity.TriColor(1.0, 1.0, 0.0, 1.0),
 trinity.TriColor(0.6, 1.0, 0.2, 1.0),
 trinity.TriColor(0.0, 1.0, 0.0, 1.0),
 trinity.TriColor(0.0, 1.0, 0.3, 1.0),
 trinity.TriColor(0.3, 1.0, 0.8, 1.0),
 trinity.TriColor(0.2, 1.0, 1.0, 1.0)]
COLOR_STANDINGS_NEUTRAL = (0.25, 0.25, 0.25)
COLOR_STANDINGS_GOOD = (0.0, 1.0, 0.0)
COLOR_STANDINGS_BAD = (1.0, 0.0, 0.0)
NEUTRAL_COLOR = trinity.TriColor(0.25, 0.25, 0.25)
ACTUAL_COLOR_OVERGLOWFACTOR = 0.4
TILE_MODE_SOVEREIGNTY = 0
TILE_MODE_STANDIGS = 1
SOV_CHANGES_SOV_GAIN = 1
SOV_CHANGES_SOV_LOST = 2
SOV_CHANGES_OUTPOST_GAIN = 4
SOV_CHANGES_OUTPOST_LOST = 8
SOV_CHANGES_OUTPOST_CONQUERED = SOV_CHANGES_OUTPOST_GAIN + SOV_CHANGES_OUTPOST_LOST
SOV_CHANGES_ALL = 15
SUN_WHITE = (1.0, 1.0, 1.0, 1.0)
SUN_BLUE = (0.6, 0.95, 1.0, 1.0)
SUN_BLUE_BRIGHT = (0.8, 0.98, 1.0, 1.0)
SUN_ORANGE = (1.0, 0.8, 0.6, 1.0)
SUN_ORANGE_BRIGHT = (1.0, 0.75, 0.65, 1.0)
SUN_RED = (1.0, 0.6, 0.6, 1.0)
SUN_YELLOW = (1.0, 1.0, 0.5, 1.0)
SUN_PINK = (1.0, 0.85, 0.9, 1.0)
SUN_SIZE_DWARF = 3
SUN_SIZE_SMALL = 3
SUN_SIZE_MEDIUM = 4
SUN_SIZE_LARGE = 5
SUN_SIZE_GIANT = 6
SUN_DATA = {3801: util.KeyVal(__doc__='Sun A0 (Blue Small)', color=SUN_BLUE, size=SUN_SIZE_SMALL),
 9: util.KeyVal(__doc__='Sun B0 (Blue)', color=SUN_BLUE, size=SUN_SIZE_MEDIUM),
 3803: util.KeyVal(__doc__='Sun B5 (White Dwarf)', color=SUN_WHITE, size=SUN_SIZE_DWARF),
 10: util.KeyVal(__doc__='Sun F0 (White)', color=SUN_WHITE, size=SUN_SIZE_SMALL),
 3799: util.KeyVal(__doc__='Sun G3 ( Pink Small ', color=SUN_PINK, size=SUN_SIZE_SMALL),
 3797: util.KeyVal(__doc__='Sun G5 (Pink)', color=SUN_PINK, size=SUN_SIZE_MEDIUM),
 6: util.KeyVal(__doc__='Sun G5 (Yellow)', color=SUN_YELLOW, size=SUN_SIZE_MEDIUM),
 3802: util.KeyVal(__doc__='Sun K3 (Yellow Small)', color=SUN_YELLOW, size=SUN_SIZE_SMALL),
 3798: util.KeyVal(__doc__='Sun K5 (Orange Bright)', color=SUN_ORANGE_BRIGHT, size=SUN_SIZE_MEDIUM),
 8: util.KeyVal(__doc__='Sun K5 (Red Giant)', color=SUN_RED, size=SUN_SIZE_GIANT),
 7: util.KeyVal(__doc__='Sun K7 (Orange)', color=SUN_ORANGE, size=SUN_SIZE_MEDIUM),
 3800: util.KeyVal(__doc__='Sun M0 (Orange radiant)', color=SUN_ORANGE, size=SUN_SIZE_LARGE),
 3796: util.KeyVal(__doc__='Sun O1 (Blue Bright)', color=SUN_BLUE_BRIGHT, size=SUN_SIZE_MEDIUM)}
REGION_JUMP = 2
CONSTELLATION_JUMP = 1
SOLARSYSTEM_JUMP = 0
JUMP_TYPES = (SOLARSYSTEM_JUMP, CONSTELLATION_JUMP, REGION_JUMP)
COLOR_REGION = (0.5, 0.0, 0.5, 1.0)
COLOR_CONSTELLATION = (0.5, 0.0, 0.0, 1.0)
COLOR_SOLARSYSTEM = (0.0, 0.0, 1.0, 1.0)
JUMP_COLORS = (COLOR_SOLARSYSTEM, COLOR_CONSTELLATION, COLOR_REGION)
JUMPBRIDGE_CURVE_SCALE = 0.75
JUMPBRIDGE_COLOR = (0.0, 1.0, 0.0, 1.0)
JUMPBRIDGE_COLOR_SCALE = 0.25
JUMPBRIDGE_ANIMATION_SPEED = 1.0

class LegendItem(object):
    """
    Wrapping legend item entries in a fuzzy warm cloak before this tuple stuff gets out of hand
    We wants it to sort correctly and to fit into sets for easy duplication removal
    """

    def __init__(self, order, caption, color, data = None, highlight = True):
        """
        caption: this is the text that is displayed in the legend list
        color: this is the color that is in the color box on the legend entry
        data: arbitrary data item, usualy factionID/allianceID/regionID etc.
        highlight: this enables or disables highlighting
        order: this is used to sort the legend entries can be text or numbers, defaults to caption if None
        """
        self.order = order
        self.caption = caption
        self.color = color
        self.data = data
        self.highlight = highlight

    def __cmp__(self, other):
        """for some proper sorting"""
        return cmp((self.order, self.caption), (other.order, self.caption))

    def __hash__(self):
        """for set compatability, duplicate removal"""
        return hash(self.caption)


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('mapcommon', locals())
