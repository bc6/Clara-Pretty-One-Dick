#Embedded file name: sensorsuite/overlay\anomalies.py
from carbonui.control.menuLabel import MenuLabel
from eve.client.script.ui.shared.radialMenu.radialMenuUtils import SimpleRadialMenuAction
from eve.client.script.ui.shared.radialMenu.spaceRadialMenuFunctions import bookMarkOption
from inventorycommon.const import groupCosmicAnomaly
import localization
from probescanning.const import probeScanGroupAnomalies
from sensorsuite.overlay.brackets import SensorSuiteBracket, INNER_ICON_COLOR
from sensorsuite.overlay.siteconst import SITE_COLOR_ANOMALY
from sensorsuite.overlay.sitedata import SiteData
from sensorsuite.overlay.sitehandler import SiteHandler
from sensorsuite.overlay.sitetype import ANOMALY

class BaseScannableSiteData(SiteData):
    scanGroupID = None
    groupID = None

    def __init__(self, siteID, position, targetID, difficulty, dungeonNameID, factionID, scanStrengthAttribute):
        SiteData.__init__(self, siteID, position)
        self.targetID = targetID
        self.difficulty = difficulty
        self.dungeonNameID = dungeonNameID
        self.factionID = factionID
        self.scanStrengthAttribute = scanStrengthAttribute

    def GetName(self):
        return self.targetID

    def WarpToAction(self, _, distance, *args):
        sm.GetService('menu').WarpToScanResult(self.targetID, minRange=distance)

    def GetMenu(self):
        scanSvc = sm.GetService('scanSvc')
        menu = [(MenuLabel(uicore.cmd.OpenScanner.nameLabelPath), uicore.cmd.OpenScanner, [])]
        menu.extend(scanSvc.GetScanResultMenuWithIgnore(self, self.scanGroupID))
        return menu

    def GetSiteActions(self):
        return [SimpleRadialMenuAction(option1=uicore.cmd.OpenScanner.nameLabelPath)]

    def GetSecondaryActions(self):
        return [bookMarkOption, SimpleRadialMenuAction(option1='UI/Inflight/Scanner/IngoreResult'), SimpleRadialMenuAction(option1='UI/Inflight/Scanner/IgnoreOtherResults')]


class AnomalySiteData(BaseScannableSiteData):
    """
    This is a data construct holding data we know about sites in a system for the sensor overlay
    """
    siteType = ANOMALY
    baseColor = SITE_COLOR_ANOMALY
    hoverSoundEvent = 'ui_scanner_state_anomaly'
    scanGroupID = probeScanGroupAnomalies
    groupID = groupCosmicAnomaly

    def __init__(self, siteID, position, targetID, difficulty, dungeonNameID, factionID, scanStrengthAttribute):
        BaseScannableSiteData.__init__(self, siteID, position, targetID, difficulty, dungeonNameID, factionID, scanStrengthAttribute)
        self.deviation = 0.0
        self.signalStrength = 1.0

    def GetBracketClass(self):
        return AnomalyBracket


class AnomalyBracket(SensorSuiteBracket):
    outerColor = SITE_COLOR_ANOMALY.GetRGBA()
    innerColor = INNER_ICON_COLOR.GetRGBA()
    innerIconResPath = 'res:/UI/Texture/classes/SensorSuite/diamond2.png'
    outerTextures = ('res:/UI/Texture/classes/SensorSuite/bracket_anomaly_1.png', 'res:/UI/Texture/classes/SensorSuite/bracket_anomaly_2.png', 'res:/UI/Texture/classes/SensorSuite/bracket_anomaly_3.png', 'res:/UI/Texture/classes/SensorSuite/bracket_anomaly_4.png')

    def ApplyAttributes(self, attributes):
        SensorSuiteBracket.ApplyAttributes(self, attributes)
        self.UpdateSiteName(localization.GetByMessageID(self.data.dungeonNameID))

    def GetMenu(self):
        return self.data.GetMenu()

    def GetBracketLabelText(self):
        return self.data.targetID


class AnomalyHandler(SiteHandler):
    siteType = ANOMALY
    filterIconPath = 'res:/UI/Texture/classes/SensorSuite/diamond2.png'
    filterLabel = 'UI/Inflight/Scanner/AnomalySiteFilterLabel'
    color = SITE_COLOR_ANOMALY

    def GetSiteData(self, siteID, position, targetID, difficulty, dungeonNameID, factionID, scanStrengthAttribute):
        return AnomalySiteData(siteID, position, targetID, difficulty, dungeonNameID, factionID, scanStrengthAttribute)

    def ProcessSiteUpdate(self, addedSites, removedSites):
        SiteHandler.ProcessSiteUpdate(self, addedSites, removedSites)
        sm.GetService('sensorSuite').InjectScannerResults(self.siteType)
