#Embedded file name: eve/client/script/ui/station/fitting\fittingTooltipUtils.py
"""
Helps functions for the tooltips for the fitting window
"""
from carbon.common.script.util.logUtil import LogError
from eve.client.script.ui.tooltips.tooltipUtil import SetTooltipHeaderAndDescription
import localization
tooltipLabelPathDict = {'ActiveDefenses': ('Tooltips/FittingWindow/ActiveDefenses', 'Tooltips/FittingWindow/ActiveDefenses_description'),
 'BrowseSavedFittings': ('Tooltips/FittingWindow/BrowseSavedFittings', None),
 'Calibration': ('Tooltips/FittingWindow/Calibration', 'Tooltips/FittingWindow/Calibration_description'),
 'CargoHold': ('Tooltips/FittingWindow/CargoHold', 'Tooltips/FittingWindow/CargoHold_description'),
 'CollapseSidePane': ('Tooltips/FittingWindow/CollapseSidePane', None),
 'ExpandSidePane': ('Tooltips/FittingWindow/ExpandSidePane', None),
 'CPU': ('Tooltips/FittingWindow/CPU', 'Tooltips/FittingWindow/CPU_description'),
 'DamagePerSecond': ('Tooltips/FittingWindow/DamagePerSecond', 'Tooltips/FittingWindow/DamagePerSecond_description'),
 'DroneBay': ('Tooltips/FittingWindow/DroneBay', 'Tooltips/FittingWindow/DroneBay_description'),
 'EffectiveHitPoints': ('Tooltips/FittingWindow/EffectiveHitPoints', 'Tooltips/FittingWindow/EffectiveHitPoints_description'),
 'InertiaModifier': ('Tooltips/FittingWindow/InertiaModifier', 'Tooltips/FittingWindow/InertiaModifier_description'),
 'LauncherHardPointBubbles': ('Tooltips/FittingWindow/LauncherHardPointBubbles', 'Tooltips/FittingWindow/LauncherHardPointBubbles_description'),
 'LauncherIcon': ('Tooltips/FittingWindow/LauncherIcon', None),
 'MaximumVelocity': ('Tooltips/FittingWindow/MaximumVelocity', 'Tooltips/FittingWindow/MaximumVelocity_description'),
 'MaxLockedTargets': ('Tooltips/FittingWindow/MaxLockedTargets', 'Tooltips/FittingWindow/MaxLockedTargets_description'),
 'MaxTargetingRange': ('Tooltips/FittingWindow/MaxTargetingRange', 'Tooltips/FittingWindow/MaxTargetingRange_description'),
 'PowerGrid': ('Tooltips/FittingWindow/PowerGrid', 'Tooltips/FittingWindow/PowerGrid_description'),
 'SaveFitting': ('Tooltips/FittingWindow/SaveFitting', None),
 'ScanResolution': ('Tooltips/FittingWindow/ScanResolution', 'Tooltips/FittingWindow/ScanResolution_description'),
 'SensorStrength': ('Tooltips/FittingWindow/SensorStrength', 'Tooltips/FittingWindow/SensorStrength_description'),
 'SignatureRadius': ('Tooltips/FittingWindow/SignatureRadius', 'Tooltips/FittingWindow/SignatureRadius_description'),
 'StripFitting': ('Tooltips/FittingWindow/StripFitting', None),
 'TurretHardPointBubbles': ('Tooltips/FittingWindow/TurretHardPointBubbles', 'Tooltips/FittingWindow/TurretHardPointBubbles_description'),
 'TurretIcon': ('Tooltips/FittingWindow/TurretIcon', None),
 'EmptyHighSlot': ('Tooltips/FittingWindow/EmptyHighSlot', None),
 'EmptyMidSlot': ('Tooltips/FittingWindow/EmptyMidSlot', None),
 'EmptyLowSlot': ('Tooltips/FittingWindow/EmptyLowSlot', None),
 'ResistanceHeaderEM': ('Tooltips/FittingWindow/ResistanceHeaderEM', 'Tooltips/FittingWindow/ResistanceHeaderEM_description'),
 'ResistanceHeaderThermal': ('Tooltips/FittingWindow/ResistanceHeaderThermal', 'Tooltips/FittingWindow/ResistanceHeaderThermal_description'),
 'ResistanceHeaderExplosive': ('Tooltips/FittingWindow/ResistanceHeaderExplosive', 'Tooltips/FittingWindow/ResistanceHeaderExplosive_description'),
 'ResistanceHeaderKinetic': ('Tooltips/FittingWindow/ResistanceHeaderKinetic', 'Tooltips/FittingWindow/ResistanceHeaderKinetic_description'),
 'DamagePerSecondTurrets': ('Tooltips/FittingWindow/DamagePerSecondTurrets', 'Tooltips/FittingWindow/DamagePerSecondTurrets_description'),
 'DamagePerSecondDrones': ('Tooltips/FittingWindow/DamagePerSecondDrones', 'Tooltips/FittingWindow/DamagePerSecondDrones_description'),
 'DamagePerSecondMissiles': ('Tooltips/FittingWindow/DamagePerSecondMissiles', 'Tooltips/FittingWindow/DamagePerSecondMissiles_description')}

def SetFittingTooltipInfo(targetObject, tooltipName, includeDesc = True):
    labelPaths = tooltipLabelPathDict.get(tooltipName, None)
    if not labelPaths:
        LogError('no valid labelpath for tooltipName=', tooltipName)
        return
    headerLabelPath, descriptionLabelPath = labelPaths
    if includeDesc and descriptionLabelPath:
        descriptionText = localization.GetByLabel(descriptionLabelPath)
    else:
        descriptionText = ''
    headerText = localization.GetByLabel(headerLabelPath)
    return SetTooltipHeaderAndDescription(targetObject, headerText, descriptionText)
