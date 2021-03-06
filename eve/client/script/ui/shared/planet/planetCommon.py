#Embedded file name: eve/client/script/ui/shared/planet\planetCommon.py
import util
import trinity
import uix
import math
import mathUtil
import uiutil
import eve.common.script.util.planetCommon as planetCommon
import log
import blue
import localization
from eve.common.script.planet.surfacePoint import SurfacePoint
PLANET_ZOOM_MAX = 4000.0
PLANET_ZOOM_MIN = 1150.0
PLANET_SCALE = 1000.0
PLANET_TEXTURE_SIZE = 2048
PLANET_RESOURCE_TEX_WIDTH = 2048
PLANET_RESOURCE_TEX_HEIGHT = 1024
PLANET_HEATMAP_COLORS = ((0, 0, 0.5, 0.5),
 (0, 0, 1, 1),
 (0, 0.5, 1, 1),
 (0, 1, 1, 1),
 (0, 1, 0.5, 1),
 (0, 1, 0, 1),
 (0.5, 1, 0, 1),
 (1, 1, 0, 1),
 (1, 0.5, 0, 1),
 (1, 0, 0, 1))
PANEL_STATS = 1
PANEL_LINKS = 2
PANEL_DECOMMISSION = 3
PANEL_STORAGE = 4
PANEL_INCOMING = 5
PANEL_OUTGOING = 6
PANEL_LAUNCH = 7
PANEL_PRODUCTS = 8
PANEL_SURVEYFORDEPOSITS = 9
PANEL_SCHEMATICS = 10
PANEL_UPGRADELINK = 11
PANEL_UPGRADE = 12
PANEL_ROUTES = 13
PANELDATA = {PANEL_STATS: ('ui_44_32_24', 'UI/PI/Common/Stats'),
 PANEL_LINKS: ('ui_77_32_31', 'UI/PI/Common/Links'),
 PANEL_DECOMMISSION: ('ui_77_32_22', 'UI/PI/Common/Decommission'),
 PANEL_STORAGE: ('ui_77_32_18', 'UI/PI/Common/Storage'),
 PANEL_INCOMING: ('ui_77_32_21', 'UI/PI/Common/Incoming'),
 PANEL_OUTGOING: ('ui_77_32_20', 'UI/PI/Common/Outgoing'),
 PANEL_LAUNCH: ('ui_77_32_19', 'UI/PI/Common/Launch'),
 PANEL_PRODUCTS: ('ui_77_32_24', 'UI/PI/Common/Products'),
 PANEL_SURVEYFORDEPOSITS: ('ui_77_32_23', 'UI/PI/Common/SurveyForDeposits'),
 PANEL_SCHEMATICS: ('ui_77_32_17', 'UI/PI/Common/Schematics'),
 PANEL_UPGRADELINK: ('ui_77_32_36', 'UI/PI/Common/UpgradeLink'),
 PANEL_UPGRADE: ('ui_77_32_37', 'UI/PI/Common/Upgrade'),
 PANEL_ROUTES: ('ui_77_32_32', 'UI/PI/Common/Routes')}
PLANET_COLOR_POWER = (236 / 255.0, 28 / 255.0, 36 / 255.0)
PLANET_COLOR_CPU = (0.0, 255 / 255.0, 212 / 255.0)
PLANET_COLOR_CYCLE = (1.0, 1.0, 1.0)
PLANET_COLOR_BANDWIDTH = (1.0, 1.0, 1.0)
PLANET_COLOR_LINKEDITMODE = (255 / 255.0,
 205 / 255.0,
 0.0,
 1.0)
PLANET_COLOR_PINEDITMODE = (255 / 255.0, 205 / 255.0, 0.0)
PLANET_COLOR_STORAGE = (10 / 255.0,
 67 / 255.0,
 102 / 255.0,
 1.0)
PLANET_COLOR_EXTRACTOR = (0 / 255.0,
 153 / 255.0,
 153 / 255.0,
 1.0)
PLANET_COLOR_PROCESSOR = (178 / 255.0,
 98 / 255.0,
 45 / 255.0,
 1.0)
PLANET_COLOR_CURRLEVEL = (0.247, 0.745, 0.165, 1.0)
PLANET_COLOR_UPGRADELEVEL = (0.271, 0.494, 0.137, 1.0)
PLANET_COLOR_POWERUPGRADE = (0.671, 0.047, 0.071, 1.0)
PLANET_COLOR_CPUUPGRADE = (0.278, 0.655, 0.592, 1.0)
PLANET_COLOR_EXTRACTIONLINK = (0.4, 1.0, 1.0, 1.0)
PLANET_COLOR_USED_STORAGE = (0 / 255.0, 169 / 255.0, 244 / 255.0)
PLANET_COLOR_USED_PROCESSOR = (237 / 255.0, 153 / 255.0, 53 / 255.0)
PLANET_COLOR_ICON_COMMANDCENTER = (171 / 255.0, 243 / 255.0, 255 / 255.0)
PLANET_COLOR_ICON_STORAGE = (2 / 255.0, 106 / 255.0, 147 / 255.0)
PLANET_COLOR_ICON_SPACEPORT = (3 / 255.0, 178 / 255.0, 239 / 255.0)
PLANET_COLOR_ICON_EXTRACTOR = (48 / 255.0, 239 / 255.0, 216 / 255.0)
PLANET_COLOR_ICON_PROCESSOR = (237 / 255.0, 153 / 255.0, 53 / 255.0)
PINTYPE_NOPICK = 0
PINTYPE_NORMAL = 1
PINTYPE_NORMALEDIT = 2
PINTYPE_EXTRACTIONHEAD = 3
PINTYPE_OTHERS = 4
PINTYPE_DEPLETION = 5
PLANET_2PI = math.pi * 2
PLANET_PI_DIV_2 = math.pi / 2
PLANET_COMMANDCENTERMAXLEVEL = 5
DARKPLANETS = (const.typePlanetPlasma, const.typePlanetLava, const.typePlanetSandstorm)
AMBIENT_SOUNDS = {const.typePlanetEarthlike: util.KeyVal(start='wise:/terrestrial_play', stop='wise:/terrestrial_stop'),
 const.typePlanetGas: util.KeyVal(start='wise:/gas_play', stop='wise:/gas_stop'),
 const.typePlanetIce: util.KeyVal(start='wise:/ice_play', stop='wise:/ice_stop'),
 const.typePlanetLava: util.KeyVal(start='wise:/lava_play', stop='wise:/lava_stop'),
 const.typePlanetOcean: util.KeyVal(start='wise:/oceanic_play', stop='wise:/oceanic_stop'),
 const.typePlanetSandstorm: util.KeyVal(start='wise:/barren_play', stop='wise:/barren_stop'),
 const.typePlanetThunderstorm: util.KeyVal(start='wise:/storm_play', stop='wise:/storm_stop'),
 const.typePlanetPlasma: util.KeyVal(start='wise:/plasma_play', stop='wise:/plasma_stop'),
 const.typePlanetShattered: util.KeyVal(start='wise:/plasma_play', stop='wise:/plasma_stop')}

def GetContrastColorForCurrPlanet():
    if not sm.GetService('viewState').IsViewActive('planet'):
        return None
    else:
        planetTypeID = sm.GetService('planetUI').planet.planetTypeID
        if planetTypeID in DARKPLANETS:
            return util.Color.WHITE
        return util.Color.BLACK


def GetPickIntersectionPoint(x = None, y = None):
    """
    Returns the point on the planet at (x, y) screen coordinates. This is done
    by casting a ray based on the screen coordinates (x, y) and the viewport
    and then finally calculating the intersection of that ray and a sphere (the planet).
    Method defaults to the current mouse coordinates if x and y arguments are None
    Returns None if the planet was not clicked.
    Arguments:
    x - the x coordinates in screen space
    y - the y coordinares in screen space
    """
    if None in (x, y):
        x, y = int(uicore.uilib.x * uicore.desktop.dpiScaling), int(uicore.uilib.y * uicore.desktop.dpiScaling)
    device = trinity.device
    proj, view, vp = uix.GetFullscreenProjectionViewAndViewport()
    ray, start = device.GetPickRayFromViewport(x, y, vp, view.transform, proj.transform)
    lineVec = trinity.TriVector(*ray)
    lineP0 = trinity.TriVector(*start)
    sphereP0 = trinity.TriVector(0.0, 0.0, 0.0)
    sphereRad = 1000.0
    pInt = GetSphereLineIntersectionPoint(lineP0, lineVec, sphereP0, sphereRad)
    if not pInt:
        return
    ret = SurfacePoint(pInt.x, pInt.y, pInt.z)
    ret.SetRadius(1.0)
    return ret


def GetSphereLineIntersectionPoint(lineP0, lineVec, sphereP0, sphereRad):
    """
    Returns the intersection point of a line and a sphere. lineP0, lineVec, sphereP0
    and the return value are all trinity.TriVector instances, while sphereRad is a
    float  
    """
    a = 1
    b = (lineVec * 2).DotProduct(lineP0 - sphereP0)
    c = (lineP0 - sphereP0).Length() ** 2 - sphereRad ** 2
    d = b ** 2.0 - 4.0 * a * c
    if d < 0:
        return None
    elif d == 0:
        t = -b / (2 * a)
        return lineP0 + lineVec * t / lineVec.Length()
    d = math.sqrt(d)
    t1 = (-b + d) / (2 * a)
    t2 = (-b - d) / (2 * a)
    lineLength = lineVec.Length()
    P1 = lineP0 + lineVec * t1 / lineLength
    P2 = lineP0 + lineVec * t2 / lineLength
    l1 = (lineP0 - P1).LengthSq()
    l2 = (lineP0 - P2).LengthSq()
    if l1 < l2:
        return P1
    else:
        return P2


def NormalizeLatitude(angle):
    """normalize angle to [-pi/2..pi/2]"""
    while angle < -PLANET_PI_DIV_2:
        angle += math.pi

    while angle > PLANET_PI_DIV_2:
        angle -= math.pi

    return angle


def NormalizeLongitude(angle):
    """normalize angle to [-pi/2..pi/2]"""
    while angle <= -math.pi:
        angle += PLANET_2PI

    while angle > math.pi:
        angle -= PLANET_2PI

    return angle


def FmtGeoCoordinates(latitude, longitude):
    latitude = mathUtil.RadToDeg(NormalizeLatitude(latitude))
    longitude = mathUtil.RadToDeg(NormalizeLongitude(longitude))
    d1, m1, s1 = ConvertToDMS(latitude)
    d2, m2, s2 = ConvertToDMS(longitude)
    dir1 = 'N' if d1 >= 0 else 'S'
    dir2 = 'E' if d2 >= 0 else 'W'
    return "%d\xb0 %d' %d'' %s, %d\xb0 %d' %d'' %s" % (d1,
     m1,
     s1,
     dir1,
     d2,
     m2,
     s2,
     dir2)


def ConvertToDMS(value):
    """splits a angle value into a DMS (degrees, minutes, secods) formatted geo coordinte value"""
    degrees = int(value)
    minPart = abs(value - degrees)
    secPart = minPart - int(minPart)
    return (degrees, int(minPart * 60), int(round(secPart * 60)))


def GetPinCycleInfo(pin, cycleTime = None):
    if cycleTime is None:
        cycleTime = pin.GetCycleTime()
    if pin.IsActive() and not pin.IsInEditMode():
        currCycle = min(blue.os.GetWallclockTime() - pin.lastRunTime, cycleTime)
        currCycleProportion = currCycle / float(cycleTime)
    else:
        currCycle = currCycleProportion = 0
    if cycleTime is None:
        cycleText = localization.GetByLabel('UI/PI/Common/InactivePin')
    else:
        cycleText = '%s / %s' % (util.FmtTime(currCycle), util.FmtTime(cycleTime))
    return (cycleText, currCycleProportion)


def GetSchematicData(processorTypeID):
    """
    Returns an alphabetically sorted list of all schematics that the specified processor pin type can produce
    RETURN: a list of util.KeyVal(
        name [string]
        schematicID [int]
        cycleTime [int] (in seconds)
        outputs [list of util.KeyVal(name, typeID, quantity)]
        inputs [list of util.KeyVal(name, typeID, quantity)]
    ) 
    """
    schematicsData = cfg.schematicsByPin[processorTypeID]
    if len(schematicsData) == 0:
        log.LogTraceback('Authoring error: No schematics found for processor pin with typeID %s' % processorTypeID)
    schematics = []
    for s in schematicsData:
        try:
            schematic = cfg.schematics.Get(s.schematicID)
        except:
            log.LogTraceback('Authoring error: No schematic found with id=%s' % s.schematicID)
            raise

        inputs, outputs = _GetSchematicInputsAndOutputs(schematic.schematicID)
        outputsDict = {}
        for o in outputs:
            outputsDict[o.typeID] = o.quantity

        volumePerCycle = planetCommon.GetCommodityTotalVolume(outputsDict)
        volumePerHour = planetCommon.GetBandwidth(volumePerCycle, schematic.cycleTime * const.SEC)
        sData = util.KeyVal(name=schematic.schematicName, schematicID=schematic.schematicID, cycleTime=schematic.cycleTime, outputs=outputs, inputs=inputs, outputVolume=volumePerHour)
        schematics.append((sData.name, sData))

    return uiutil.SortListOfTuples(schematics)


def _GetSchematicInputsAndOutputs(schematicID):
    inputs = []
    outputs = []
    schematicstypemap = cfg.schematicstypemap[schematicID]
    if len(schematicstypemap) == 0:
        log.LogTraceback('Authoring error: No inputs/outputs defined for schematic with id=%s' % schematicID)
    for typeInfo in schematicstypemap:
        data = util.KeyVal(name=cfg.invtypes.Get(typeInfo.typeID).typeName, typeID=typeInfo.typeID, quantity=typeInfo.quantity)
        if typeInfo.isInput:
            inputs.append(data)
        else:
            outputs.append(data)

    return (inputs, outputs)


def GetSchematicDataByGroupID():
    schematics = GetSchematicData()
    ret = {}
    for schematic in schematics:
        groupID = cfg.invtypes.Get(schematic.output.typeID).groupID
        if groupID not in ret:
            ret[groupID] = []
        ret[groupID].append(schematic)

    return ret


def PinHasBeenBuilt(pinID):
    if isinstance(pinID, tuple):
        return False
    return True


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('planetCommon', locals())
