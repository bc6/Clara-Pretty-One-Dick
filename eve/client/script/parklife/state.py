#Embedded file name: eve/client/script/parklife\state.py
from localization import GetByLabel
import service
import states as state
import base
import log
import util
import telemetry
from collections import namedtuple
import facwarCommon
import crimewatchConst
CRIMINAL_RED = crimewatchConst.Colors.Criminal.GetRGBA()
SUSPECT_YELLOW = crimewatchConst.Colors.Suspect.GetRGBA()
TURQUOISE = (0.0,
 0.63,
 0.57,
 1.0)
NORELATIONSHIP_SENTINEL = "Just a string which will be used as a sentinel value.  We use 'is' to compare it so it doesn't matter that it's hella long."
STATE_COLORS = {'purple': ((0.6,
             0.15,
             0.9,
             1.0), 'UI/Common/Colors/Purple'),
 'green': ((0.1,
            0.6,
            0.1,
            1.0), 'UI/Common/Colors/Green'),
 'red': ((0.75,
          0.0,
          0.0,
          1.0), 'UI/Common/Colors/Red'),
 'darkBlue': ((0.0,
               0.15,
               0.6,
               1.0), 'UI/Common/Colors/DarkBlue'),
 'blue': ((0.2,
           0.5,
           1.0,
           1.0), 'UI/Common/Colors/Blue'),
 'darkTurquoise': ((0.0,
                    0.34,
                    0.33,
                    1.0), 'UI/Common/Colors/DarkTurquoise'),
 'turquoise': (TURQUOISE, 'UI/Common/Colors/Turquoise'),
 'orange': ((1.0,
             0.35,
             0.0,
             1.0), 'UI/Common/Colors/Orange'),
 'black': ((0.0,
            0.0,
            0.0,
            1.0), 'UI/Common/Colors/Black'),
 'yellow': ((1.0,
             0.7,
             0.0,
             1.0), 'UI/Common/Colors/Yellow'),
 'white': ((0.7,
            0.7,
            0.7,
            1.0), 'UI/Common/Colors/White'),
 'indigo': ((0.3,
             0.0,
             0.5,
             1.0), 'UI/Common/Colors/Indigo')}
StateProperty = namedtuple('StateProperty', 'text label defaultColor hint iconIndex iconColor defaultBackgroundColor')
colorToNameMap = {color[0]:colorKey for colorKey, color in STATE_COLORS.iteritems()}

def FindColorName(colorValue):
    return colorToNameMap.get(colorValue, None)


def IsHighStanding(relationship):
    """
    Takes in a relationship (e.g. corporation -> alliance).
    Returns a check to see if it matches a defined criteria.
    """
    return relationship > const.contactGoodStanding


def IsGoodStanding(relationship):
    """
    Takes in a relationship (e.g. corporation -> alliance).
    Returns a check to see if it matches a defined criteria.
    """
    return const.contactGoodStanding >= relationship > const.contactNeutralStanding


def IsNeutralStanding(relationship):
    """
    Takes in a relationship (e.g. corporation -> alliance).
    Returns a check to see if it matches a defined criteria.
    """
    return relationship == const.contactNeutralStanding


def IsBadStanding(relationship):
    """
    Takes in a relationship (e.g. corporation -> alliance).
    Returns a check to see if it matches a defined criteria.
    """
    return const.contactBadStanding <= relationship < const.contactNeutralStanding


def IsHorribleStanding(relationship):
    """
    Takes in a relationship (e.g. corporation -> alliance).
    Returns a check to see if it matches a defined criteria.
    """
    return relationship < const.contactBadStanding


class StateSvc(service.Service):
    __guid__ = 'svc.state'
    __exportedcalls__ = {'GetExclState': [],
     'GetStates': [],
     'SetState': [],
     'RemoveWarOwners': []}
    __notifyevents__ = ['DoBallClear',
     'DoBallRemove',
     'OnSessionChanged',
     'DoBallsRemove']
    __update_on_reload__ = 0
    __startupdependencies__ = ['settings']
    __dependencies__ = ['bountySvc']

    def Run(self, *etc):
        service.Service.Run(self, *etc)
        self.logme = 0
        self.exclusive = [state.mouseOver,
         state.selected,
         state.activeTarget,
         state.lookingAt]
        self.exclusives = {}
        self.states = {}
        self.stateColors = {}
        self.stateBlinks = {}
        self.atWar = {}
        self.alliesAtWar = {}
        self.cachedStateSettings = {}
        self.stateColorsInited = 0
        self.props = None
        self.smartFilterProps = None
        self.defaultBackgroundOrder = [state.flagAtWarCanFight,
         state.flagAtWarMilitia,
         state.flagLimitedEngagement,
         state.flagSameFleet,
         state.flagCriminal,
         state.flagSuspect,
         state.flagOutlaw,
         state.flagSameCorp,
         state.flagSameAlliance,
         state.flagDangerous,
         state.flagSameMilitia,
         state.flagStandingHigh,
         state.flagStandingGood,
         state.flagStandingHorrible,
         state.flagStandingBad,
         state.flagIsWanted,
         state.flagHasKillRight,
         state.flagAgentInteractable,
         state.flagStandingNeutral,
         state.flagNoStanding,
         state.flagAlliesAtWar]
        self.defaultBackgroundStates = [state.flagCriminal,
         state.flagSuspect,
         state.flagOutlaw,
         state.flagSameFleet,
         state.flagSameCorp,
         state.flagSameAlliance,
         state.flagAtWarCanFight,
         state.flagAtWarMilitia,
         state.flagSameMilitia,
         state.flagLimitedEngagement]
        self.defaultFlagOrder = [state.flagAtWarCanFight,
         state.flagAtWarMilitia,
         state.flagLimitedEngagement,
         state.flagSameFleet,
         state.flagCriminal,
         state.flagSuspect,
         state.flagOutlaw,
         state.flagSameCorp,
         state.flagSameAlliance,
         state.flagDangerous,
         state.flagSameMilitia,
         state.flagStandingHigh,
         state.flagStandingGood,
         state.flagStandingHorrible,
         state.flagStandingBad,
         state.flagIsWanted,
         state.flagHasKillRight,
         state.flagAgentInteractable,
         state.flagStandingNeutral,
         state.flagNoStanding,
         state.flagAlliesAtWar]
        self.defaultFlagStates = [state.flagSameFleet,
         state.flagSameCorp,
         state.flagSameAlliance,
         state.flagAtWarCanFight,
         state.flagSameMilitia,
         state.flagAtWarMilitia,
         state.flagStandingHigh,
         state.flagStandingGood,
         state.flagStandingBad,
         state.flagStandingHorrible,
         state.flagCriminal,
         state.flagSuspect,
         state.flagOutlaw,
         state.flagAgentInteractable,
         state.flagStandingNeutral,
         state.flagAlliesAtWar,
         state.flagLimitedEngagement]
        self.defaultBlinkStates = {('flag', state.flagSuspect): True,
         ('flag', state.flagCriminal): True,
         ('flag', state.flagLimitedEngagement): True,
         ('background', state.flagAtWarCanFight): True,
         ('background', state.flagAtWarMilitia): True}
        self.ewarStates = {'warpScramblerMWD': (state.flagWarpScrambledMWD, const.iconModuleWarpScramblerMWD),
         'warpScrambler': (state.flagWarpScrambled, const.iconModuleWarpScrambler),
         'webify': (state.flagWebified, const.iconModuleStasisWeb),
         'electronic': (state.flagECMd, const.iconModuleECM),
         'ewRemoteSensorDamp': (state.flagSensorDampened, const.iconModuleSensorDamper),
         'ewTrackingDisrupt': (state.flagTrackingDisrupted, const.iconModuleTrackingDisruptor),
         'ewTargetPaint': (state.flagTargetPainted, const.iconModuleTargetPainter),
         'ewEnergyVampire': (state.flagEnergyLeeched, const.iconModuleNosferatu),
         'ewEnergyNeut': (state.flagEnergyNeut, const.iconModuleEnergyNeutralizer)}
        self.ewarStateItems = self.ewarStates.items()
        self.shouldLogError = True
        self.InitFilter()

    def OnSessionChanged(self, isRemote, session, change):
        if 'corpid' in change or 'allianceid' in change:
            self.atWar = {}
            self.alliesAtWar = {}

    def RemoveWarOwners(self, ownerIDs):
        if not self.atWar:
            return
        for ownerID in ownerIDs:
            if ownerID in self.atWar:
                del self.atWar[ownerID]
            if ownerID in self.alliesAtWar:
                del self.alliesAtWar[ownerID]

    def GetProps(self):
        if self.props is None:
            criminalLabelAndHint = (GetByLabel('UI/Services/State/Standing/Criminal'), GetByLabel('UI/Services/State/Standing/CriminalHint'))
            suspectLabelAndHint = (GetByLabel('UI/Services/State/Standing/Suspect'), GetByLabel('UI/Services/State/Standing/SuspectHint'))
            outlawLabelAndHint = (GetByLabel('UI/Services/State/Standing/Outlaw'), GetByLabel('UI/Services/State/Standing/OutlawHint'))
            dangerousLabelAndHint = (GetByLabel('UI/Services/State/Standing/Dangerous'), GetByLabel('UI/Services/State/Standing/DangerousHint'))
            sameFleetLabelAndHint = (GetByLabel('UI/Services/State/Standing/SameFleet'), GetByLabel('UI/Services/State/Standing/SameFleetHint'))
            sameCorpLabelAndHint = (GetByLabel('UI/Services/State/Standing/SameCorporation'), GetByLabel('UI/Services/State/Standing/SameCorporationHint'))
            sameAllianceLabelAndHint = (GetByLabel('UI/Services/State/Standing/SameAlliance'), GetByLabel('UI/Services/State/Standing/SameAllianceHint'))
            sameMilitiaLabelAndHint = (GetByLabel('UI/Services/State/Standing/SameMilitia'), GetByLabel('UI/Services/State/Standing/SameMilitiaHint'))
            atWarWithCorpLabelAndHint = (GetByLabel('UI/Services/State/Standing/AtWarWithCorporationOrAlliance'), GetByLabel('UI/Services/State/Standing/AtWarWithCorporationOrAllianceHint'))
            atWarWithMilitiaLabelAndHint = (GetByLabel('UI/Services/State/Standing/AtWarWithMilitia'), GetByLabel('UI/Services/State/Standing/AtWarWithMilitiaHint'))
            excellentLabelAndHint = (GetByLabel('UI/Services/State/Standing/Excellent'), GetByLabel('UI/Services/State/Standing/ExcellentHint'))
            goodLabelAndHint = (GetByLabel('UI/Services/State/Standing/Good'), GetByLabel('UI/Services/State/Standing/GoodHint'))
            neutralLabelAndHint = (GetByLabel('UI/Services/State/Standing/Neutral'), GetByLabel('UI/Services/State/Standing/NeutralHint'))
            badLabelAndHint = (GetByLabel('UI/Services/State/Standing/Bad'), GetByLabel('UI/Services/State/Standing/BadHint'))
            terribleLabelAndHint = (GetByLabel('UI/Services/State/Standing/Terrible'), GetByLabel('UI/Services/State/Standing/TerribleHint'))
            isWantedLabelAndHint = (GetByLabel('UI/Services/State/Standing/IsWanted'), GetByLabel('UI/Services/State/Standing/IsWantedHint'))
            hasKillRightLabelAndHint = (GetByLabel('UI/Services/State/Standing/HasKillRight'), GetByLabel('UI/Services/State/Standing/HasKillRightHint'))
            agentInteractableLabelAndHint = (GetByLabel('UI/Services/State/Standing/AgentIsInteractable'), GetByLabel('UI/Services/State/Standing/AgentIsInteractableHint'))
            wreckIsViewedLabelAndHint = (GetByLabel('UI/Services/State/Standing/WreckIsViewed'), GetByLabel('UI/Services/State/Standing/WreckIsViewedHint'))
            wreckIsEmptyLabelAndHint = (GetByLabel('UI/Services/State/Standing/WreckIsEmpty'), GetByLabel('UI/Services/State/Standing/WreckIsEmptyHint'))
            noStandingLabelAndHint = (GetByLabel('UI/Services/State/Standing/NoStanding'), GetByLabel('UI/Services/State/Standing/NoStandingHint'))
            alliesAtWar = (GetByLabel('UI/Services/State/Standing/AlliesAtWar'), GetByLabel('UI/Services/State/Standing/AlliesAtWarHint'))
            limitedEngagementLabelAndHint = (GetByLabel('UI/Services/State/Standing/LimitedEngagement'), GetByLabel('UI/Services/State/Standing/LimitedEngagementHint'))
            self.props = {state.flagCriminal: StateProperty(criminalLabelAndHint[0], 'Criminal', 'black', criminalLabelAndHint[1], 5, CRIMINAL_RED, 'red'),
             state.flagSuspect: StateProperty(suspectLabelAndHint[0], 'Suspect', 'black', suspectLabelAndHint[1], 5, SUSPECT_YELLOW, 'yellow'),
             state.flagOutlaw: StateProperty(outlawLabelAndHint[0], 'Outlaw', 'red', outlawLabelAndHint[1], 5, util.Color.WHITE, None),
             state.flagDangerous: StateProperty(dangerousLabelAndHint[0], 'Dangerous', 'yellow', dangerousLabelAndHint[1], 5, util.Color.WHITE, None),
             state.flagSameFleet: StateProperty(sameFleetLabelAndHint[0], 'SameFleet', 'purple', sameFleetLabelAndHint[1], 0, util.Color.WHITE, None),
             state.flagSameCorp: StateProperty(sameCorpLabelAndHint[0], 'SameCorp', 'green', sameCorpLabelAndHint[1], 1, util.Color.WHITE, None),
             state.flagSameAlliance: StateProperty(sameAllianceLabelAndHint[0], 'SameAlliance', 'darkBlue', sameAllianceLabelAndHint[1], 1, util.Color.WHITE, None),
             state.flagSameMilitia: StateProperty(sameMilitiaLabelAndHint[0], 'SameMilitia', 'indigo', sameMilitiaLabelAndHint[1], 1, util.Color.WHITE, None),
             state.flagAtWarCanFight: StateProperty(atWarWithCorpLabelAndHint[0], 'AtWarCanFight', 'red', atWarWithCorpLabelAndHint[1], 1, util.Color.WHITE, None),
             state.flagAtWarMilitia: StateProperty(atWarWithMilitiaLabelAndHint[0], 'AtWarMilitia', 'orange', atWarWithMilitiaLabelAndHint[1], 1, util.Color.WHITE, None),
             state.flagStandingHigh: StateProperty(excellentLabelAndHint[0], 'StandingHigh', 'darkBlue', excellentLabelAndHint[1], 2, util.Color.WHITE, None),
             state.flagStandingGood: StateProperty(goodLabelAndHint[0], 'StandingGood', 'blue', goodLabelAndHint[1], 2, util.Color.WHITE, None),
             state.flagStandingNeutral: StateProperty(neutralLabelAndHint[0], 'StandingNeutral', 'white', neutralLabelAndHint[1], 4, util.Color.WHITE, None),
             state.flagStandingBad: StateProperty(badLabelAndHint[0], 'StandingBad', 'orange', badLabelAndHint[1], 3, util.Color.WHITE, None),
             state.flagStandingHorrible: StateProperty(terribleLabelAndHint[0], 'StandingHorrible', 'red', terribleLabelAndHint[1], 3, util.Color.WHITE, None),
             state.flagIsWanted: StateProperty(isWantedLabelAndHint[0], 'IsWanted', 'black', isWantedLabelAndHint[1], 5, util.Color.WHITE, None),
             state.flagHasKillRight: StateProperty(hasKillRightLabelAndHint[0], 'HasKillRight', 'orange', hasKillRightLabelAndHint[1], 7, util.Color.WHITE, None),
             state.flagAgentInteractable: StateProperty(agentInteractableLabelAndHint[0], 'AgentInteractable', 'blue', agentInteractableLabelAndHint[1], 6, util.Color.WHITE, None),
             state.flagWreckAlreadyOpened: StateProperty(wreckIsViewedLabelAndHint[0], 'WreckViewed', 'white', wreckIsViewedLabelAndHint[1], 1, util.Color.WHITE, None),
             state.flagWreckEmpty: StateProperty(wreckIsEmptyLabelAndHint[0], 'WreckEmpty', 'white', wreckIsEmptyLabelAndHint[1], 1, util.Color.WHITE, None),
             state.flagNoStanding: StateProperty(noStandingLabelAndHint[0], 'NoStanding', 'white', noStandingLabelAndHint[1], 4, util.Color.WHITE, None),
             state.flagAlliesAtWar: StateProperty(alliesAtWar[0], 'AlliesAtWar', 'darkBlue', alliesAtWar[1], 1, util.Color.WHITE, None),
             state.flagLimitedEngagement: StateProperty(limitedEngagementLabelAndHint[0], 'LimitedEngagement', 'black', limitedEngagementLabelAndHint[1], 5, TURQUOISE, 'turquoise')}
            self.defaultProp = StateProperty('', '', 'white', '', 6, util.Color.WHITE, None)
        return self.props

    def GetSmartFilterProps(self):
        if self.smartFilterProps is None:
            self.smartFilterProps = {state.flagWarpScrambledMWD: StateProperty(GetByLabel('UI/Services/State/InflightState/WarpScramblingMWD'), '', '', GetByLabel('UI/Services/State/InflightState/WarpScramblingMWDHint'), 0, None, None),
             state.flagWarpScrambled: StateProperty(GetByLabel('UI/Services/State/InflightState/WarpScrambling'), '', '', GetByLabel('UI/Services/State/InflightState/WarpScramblingHint'), 0, None, None),
             state.flagWebified: StateProperty(GetByLabel('UI/Services/State/InflightState/Webified'), '', '', GetByLabel('UI/Services/State/InflightState/WebifiedHint'), 0, None, None),
             state.flagECMd: StateProperty(GetByLabel('UI/Services/State/InflightState/Jamming'), '', '', GetByLabel('UI/Services/State/InflightState/JammingHint'), 0, None, None),
             state.flagSensorDampened: StateProperty(GetByLabel('UI/Services/State/InflightState/SensorDamping'), '', '', GetByLabel('UI/Services/State/InflightState/SensorDampingHint'), 0, None, None),
             state.flagTrackingDisrupted: StateProperty(GetByLabel('UI/Services/State/InflightState/TrackingDisrupting'), '', '', GetByLabel('UI/Services/State/InflightState/TrackingDisruptingHint'), 0, None, None),
             state.flagTargetPainted: StateProperty(GetByLabel('UI/Services/State/InflightState/Painting'), '', '', GetByLabel('UI/Services/State/InflightState/PaintingHint'), 0, None, None),
             state.flagEnergyLeeched: StateProperty(GetByLabel('UI/Services/State/InflightState/EnergyLeeched'), '', '', GetByLabel('UI/Services/State/InflightState/EnergyLeechedHint'), 0, None, None),
             state.flagEnergyNeut: StateProperty(GetByLabel('UI/Services/State/InflightState/EnergyNeutralizing'), '', '', GetByLabel('UI/Services/State/InflightState/EnergyNeutralizingHint'), 0, None, None)}
        return self.smartFilterProps

    @telemetry.ZONE_METHOD
    def GetStateProps(self, st = None):
        props = self.GetProps()
        if st is not None:
            if st in props:
                return props[st]
            else:
                if self.shouldLogError:
                    log.LogTraceback('Bad state flag: %s' % st)
                    self.shouldLogError = False
                return self.defaultProp
        else:
            return props

    @telemetry.ZONE_METHOD
    def GetActiveStateOrder(self, where):
        cacheKey = 'ActiveStateOrder_' + where
        if cacheKey in self.cachedStateSettings:
            return self.cachedStateSettings[cacheKey]
        return self.cachedStateSettings.setdefault(cacheKey, [ flag for flag in self.GetStateOrder(where) if self.GetStateState(where, flag) ])

    @telemetry.ZONE_METHOD
    def GetActiveStateOrderFunctionNames(self, where):
        cacheKey = 'ActiveStateOrderFunctionNames_' + where
        if cacheKey in self.cachedStateSettings:
            return self.cachedStateSettings[cacheKey]
        return self.cachedStateSettings.setdefault(cacheKey, [ self.GetStateProps(flag).label for flag in self.GetActiveStateOrder(where) ])

    @telemetry.ZONE_METHOD
    def GetStateOrder(self, where):
        default = getattr(self, 'default' + where.capitalize() + 'Order', [])
        ret = settings.user.overview.Get(where.lower() + 'Order', default)
        if ret is None:
            return default
        ret.extend([ flag for flag in default if flag not in ret ])
        return ret

    @telemetry.ZONE_METHOD
    def GetStateState(self, where, flag):
        return flag in self.GetStateStates(where)

    @telemetry.ZONE_METHOD
    def GetStateStates(self, where):
        """get the active overview states 'flag' or 'background'"""
        if where == 'background':
            ret = settings.user.overview.Get('backgroundStates')
            if ret is None:
                ret = self.defaultBackgroundStates
        else:
            ret = settings.user.overview.Get('flagStates')
            if ret is None:
                ret = self.defaultFlagStates
        return ret

    @telemetry.ZONE_METHOD
    def GetStateColors(self):
        return STATE_COLORS

    @telemetry.ZONE_METHOD
    def GetStateColor(self, flag, where = 'flag'):
        self.InitColors()
        color = self.stateColors.get((where, flag))
        if color:
            return color
        else:
            color = self._GetDefaultColor(flag, where)
            return color

    def _GetDefaultColor(self, flag, where):
        colors = self.GetStateColors()
        defColor = None
        if where == 'background':
            defColor = self.GetStateProps(flag).defaultBackgroundColor
        if defColor is None:
            defColor = self.GetStateProps(flag).defaultColor
        color = colors[defColor][0]
        return color

    def GetStateFlagColor(self, flagCode):
        return self.GetStateColor(flagCode, 'flag')

    def GetStateBackgroundColor(self, flagCode):
        return self.GetStateColor(flagCode, 'background')

    def GetStatePropsColorAndBlink(self, flagCode):
        if not flagCode:
            return None
        return util.KeyVal(flagCode=flagCode, flagProperties=self.GetStateProps(flagCode), flagColor=self.GetStateFlagColor(flagCode), flagBlink=self.GetStateFlagBlink(flagCode))

    @telemetry.ZONE_METHOD
    def GetStateBlink(self, where, flag):
        defBlink = self.defaultBlinkStates.get((where, flag), 0)
        return settings.user.overview.Get('stateBlinks', {}).get((where, flag), defBlink)

    def GetStateFlagBlink(self, flagCode):
        return self.GetStateBlink('flag', flagCode)

    def GetStateBackgroundBlink(self, flagCode):
        return self.GetStateBlink('background', flagCode)

    @telemetry.ZONE_METHOD
    def GetEwarGraphicID(self, ewarType):
        flag, gid = self.ewarStates[ewarType]
        return gid

    def GetEwarTypes(self):
        return self.ewarStateItems

    def GetEwarFlag(self, ewarType):
        flag, gid = self.ewarStates[ewarType]
        return flag

    def GetEwarTypeByEwarState(self, flag = None):
        if not getattr(self, 'ewartypebystate', {}):
            ret = {}
            for ewarType, (f, gid) in self.ewarStateItems:
                ret[f] = ewarType

            self.ewartypebystate = ret
        if flag:
            return self.ewartypebystate[flag]
        return self.ewartypebystate

    def GetEwarHint(self, ewarType):
        flag, gid = self.ewarStates[ewarType]
        return self.GetSmartFilterProps()[flag].text

    def GetFixedColorSettings(self):
        """
        For some obscure reason the cache has been stored as a single value per flag
        rather than a color for both flag and background.  Which is weird since that is what the UI is offering
        So this is basically making sure the setting keys are tuples of ("flag", flag) or ("background", flag)
        """
        stateColors = settings.user.overview.Get('stateColors', {})
        newStatesColors = {}
        for flag, color in stateColors.iteritems():
            if isinstance(flag, tuple):
                newStatesColors[flag] = color
            else:
                newStatesColors['flag', flag] = color
                newStatesColors['background', flag] = color

        settings.user.overview.Set('stateColors', newStatesColors)
        return newStatesColors

    def SetStateColor(self, where, flag, color):
        self.InitColors()
        self.stateColors[where, flag] = color
        settings.user.overview.Set('stateColors', self.stateColors.copy())
        self.cachedStateSettings = {}
        self.NotifyOnStateSetupChance('stateColor')

    def SetStateBlink(self, where, flag, blink):
        stateBlinks = settings.user.overview.Get('stateBlinks', {})
        stateBlinks[where, flag] = blink
        settings.user.overview.Set('stateBlinks', stateBlinks)
        self.cachedStateSettings = {}
        self.NotifyOnStateSetupChance('stateBlink')

    def InitColors(self, reset = 0):
        if reset:
            self.cachedStateSettings = {}
        if not self.stateColorsInited or reset:
            self.stateColors = self.GetFixedColorSettings()
            self.stateColorsInited = 1

    def ResetColors(self):
        settings.user.overview.Set('stateColors', {})
        self.cachedStateSettings = {}
        self.InitColors(reset=True)
        self.NotifyOnStateSetupChance('stateColor')

    def InitFilter(self):
        """
        certain npc's are grouped together, when new NPC's are added and the
        supergroup is checked, then make sure that all the NPC's that reside
        under that supergroup get checked as well.
        """
        self.filterCategs = {const.categoryShip, const.categoryEntity, const.categoryDrone}
        self.updateCategs = self.filterCategs.copy()
        self.filterGroups = {const.groupCargoContainer,
         const.groupSecureCargoContainer,
         const.groupStargate,
         const.groupWarpGate,
         const.groupAgentsinSpace,
         const.groupCosmicSignature,
         const.groupHarvestableCloud,
         const.groupForceField,
         const.groupWreck}
        applyOnlyToShips = sm.GetService('overviewPresetSvc').GetSettingValueOrDefaultFromName('applyOnlyToShips', True)
        if applyOnlyToShips:
            self.updateGroups = set()
        else:
            self.updateCategs.add(const.categoryStructure)
            self.updateCategs.add(const.categorySovereigntyStructure)
            self.updateGroups = self.filterGroups.copy()
        settings.user.ui.Set('linkedWeapons_groupsDict', {})

    def ChangeStateOrder(self, where, flag, idx):
        current = self.GetStateOrder(where)[:]
        while flag in current:
            current.remove(flag)

        if idx == -1:
            idx = len(current)
        current.insert(idx, flag)
        settings.user.overview.Set(where.lower() + 'Order', current)
        self.cachedStateSettings = {}
        self.NotifyOnStateSetupChance('flagOrder')

    def ChangeStateState(self, where, flag, true):
        current = self.GetStateStates(where)[:]
        while flag in current:
            current.remove(flag)

        if true:
            current.append(flag)
        settings.user.overview.Set(where.lower() + 'States', current)
        self.cachedStateSettings = {}
        self.NotifyOnStateSetupChance('flagState')

    def ChangeLabelOrder(self, oldidx, idx):
        labels = self.GetShipLabels()
        label = labels.pop(oldidx)
        if idx == -1:
            idx = len(labels)
        labels.insert(idx, label)
        settings.user.overview.Set('shipLabels', labels)
        self.cachedStateSettings = {}
        sm.GetService('bracket').UpdateLabels()

    def ChangeShipLabels(self, flag, true):
        labels = self.GetShipLabels()
        type = flag['type']
        flag['state'] = true
        for i in xrange(len(labels)):
            if labels[i]['type'] == type:
                labels[i] = flag
                break

        settings.user.overview.Set('shipLabels', labels)
        self.cachedStateSettings = {}
        sm.GetService('bracket').UpdateLabels()
        sm.GetService('tactical').RefreshOverview()

    def SetDefaultShipLabel(self, setting):
        hideCorpTickerDefault = sm.GetService('overviewPresetSvc').GetDefaultSettingValueFromName('hideCorpTicker', False)
        defaults = {'default': (hideCorpTickerDefault, [{'state': 1,
                       'pre': '',
                       'type': 'pilot name',
                       'post': ' '},
                      {'state': 1,
                       'pre': '[',
                       'type': 'corporation',
                       'post': ']'},
                      {'state': 1,
                       'pre': '&lt;',
                       'type': 'alliance',
                       'post': '&gt;'},
                      {'state': 0,
                       'pre': "'",
                       'type': 'ship name',
                       'post': "'"},
                      {'state': 1,
                       'pre': '(',
                       'type': 'ship type',
                       'post': ')'},
                      {'state': 0,
                       'pre': '[',
                       'type': None,
                       'post': ''}]),
         'ally': (hideCorpTickerDefault, [{'state': 1,
                    'pre': '',
                    'type': 'pilot name',
                    'post': ''},
                   {'state': 1,
                    'pre': ' [',
                    'type': 'corporation',
                    'post': ''},
                   {'state': 1,
                    'pre': ',',
                    'type': 'alliance',
                    'post': ''},
                   {'state': 1,
                    'pre': ']',
                    'type': None,
                    'post': ''},
                   {'state': 0,
                    'pre': "'",
                    'type': 'ship name',
                    'post': "'"},
                   {'state': 0,
                    'pre': '(',
                    'type': 'ship type',
                    'post': ')'}]),
         'corpally': (hideCorpTickerDefault, [{'state': 1,
                        'pre': '[',
                        'type': 'corporation',
                        'post': '] '},
                       {'state': 1,
                        'pre': '',
                        'type': 'pilot name',
                        'post': ''},
                       {'state': 1,
                        'pre': ' &lt;',
                        'type': 'alliance',
                        'post': '&gt;'},
                       {'state': 0,
                        'pre': "'",
                        'type': 'ship name',
                        'post': "'"},
                       {'state': 0,
                        'pre': '(',
                        'type': 'ship type',
                        'post': ')'},
                       {'state': 0,
                        'pre': '[',
                        'type': None,
                        'post': ''}])}
        settings.user.overview.Set('hideCorpTicker', defaults.get(setting, 'default')[0])
        self.shipLabels = defaults.get(setting, 'default')[1]
        settings.user.overview.Set('shipLabels', self.shipLabels)
        self.cachedStateSettings = {}
        sm.GetService('bracket').UpdateLabels()

    def NotifyOnStateSetupChance(self, reason):
        self.notifyStateChangeTimer = base.AutoTimer(1000, self._NotifyOnStateSetupChance, reason)

    def _NotifyOnStateSetupChance(self, reason):
        self.notifyStateChangeTimer = None
        sm.ScatterEvent('OnStateSetupChance', reason)

    @telemetry.ZONE_METHOD
    def CheckIfUpdateItem(self, slimItem):
        return getattr(slimItem, 'categoryID', None) in self.updateCategs or getattr(slimItem, 'groupID', None) in self.updateGroups

    @telemetry.ZONE_METHOD
    def CheckIfFilterItem(self, slimItem):
        return getattr(slimItem, 'categoryID', None) in self.filterCategs or getattr(slimItem, 'groupID', None) in self.filterGroups

    @telemetry.ZONE_METHOD
    def GetStates(self, itemID, flags):
        ret = []
        for flag in flags:
            if flag in self.exclusive:
                ret.append(itemID == self.exclusives.get(flag, 0))
                continue
            ret.append(self.states.get(flag, {}).get(itemID, 0))

        return ret

    @telemetry.ZONE_METHOD
    def GetExclState(self, flag):
        return self.exclusives.get(flag, None)

    @telemetry.ZONE_METHOD
    def DoExclusive(self, itemID, flag, true, *args):
        excl = self.exclusives.get(flag, None)
        if true:
            if excl and excl != itemID:
                sm.ScatterEvent('OnStateChange', excl, flag, 0, *args)
            sm.ScatterEvent('OnStateChange', itemID, flag, 1, *args)
            self.exclusives[flag] = itemID
        else:
            sm.ScatterEvent('OnStateChange', itemID, flag, 0, *args)
            self.exclusives[flag] = None

    @telemetry.ZONE_METHOD
    def SetState(self, itemID, flag, state, *args):
        self.LogInfo('SetState', itemID, flag, state, *args)
        if flag in self.exclusive:
            self.DoExclusive(itemID, flag, state, *args)
            return
        states = self.states.get(flag, {})
        if state:
            states[itemID] = state
        elif itemID in states:
            del states[itemID]
        if states:
            self.states[flag] = states
        elif flag in self.states:
            del self.states[flag]
        self.LogInfo('Before OnStateChange', itemID, flag, state, *args)
        sm.ScatterEvent('OnStateChange', itemID, flag, state, *args)

    def DoBallClear(self, *etc):
        self.states = {}

    @telemetry.ZONE_METHOD
    def DoBallsRemove(self, pythonBalls, isRelease):
        for ball, slimItem, terminal in pythonBalls:
            self.DoBallRemove(ball, slimItem, terminal)

    def DoBallRemove(self, ball, slimItem, terminal):
        if ball is None:
            return
        self.LogInfo('DoBallRemove::state', ball.id)
        if ball.id in self.exclusives.itervalues():
            for state in self.exclusive:
                if self.GetExclState(state) == ball.id:
                    self.SetState(ball.id, state, 0)

        if ball.id == session.shipid:
            return
        for stateDict in self.states.values():
            if ball.id in stateDict:
                del stateDict[ball.id]

    def GetAllShipLabels(self):
        return [{'state': 1,
          'pre': '',
          'type': 'pilot name',
          'post': ' '},
         {'state': 1,
          'pre': '[',
          'type': 'corporation',
          'post': ']'},
         {'state': 1,
          'pre': '&lt;',
          'type': 'alliance',
          'post': '&gt;'},
         {'state': 0,
          'pre': "'",
          'type': 'ship name',
          'post': "'"},
         {'state': 1,
          'pre': '(',
          'type': 'ship type',
          'post': ')'},
         {'state': 0,
          'pre': '[',
          'type': None,
          'post': ''}]

    def GetShipLabels(self):
        if not getattr(self, 'shipLabels', None):
            self.shipLabels = settings.user.overview.Get('shipLabels', None) or self.GetAllShipLabels()
        return self.shipLabels

    @telemetry.ZONE_METHOD
    def GetIconAndBackgroundFlags(self, slimItem):
        if slimItem is None:
            return (0, 0)
        flag = self.CheckStates(slimItem, 'flag')
        background = self.CheckStates(slimItem, 'background')
        return (flag or 0, background or 0)

    @telemetry.ZONE_METHOD
    def CheckStates(self, slimItem, what):
        if slimItem is None:
            return
        if not (slimItem.ownerID in [None, const.ownerSystem] or util.IsNPC(slimItem.ownerID)):
            relationships = self._GetRelationship(slimItem)
        else:
            relationships = None
        for functionName in self.GetActiveStateOrderFunctionNames(what):
            fullFunctionName = 'Check' + functionName
            checkFunction = getattr(self, fullFunctionName, None)
            if checkFunction:
                if checkFunction(slimItem, relationships):
                    return getattr(state, 'flag' + functionName, None)

    @telemetry.ZONE_METHOD
    def CheckFilteredFlagState(self, slimItem, excludedFlags = ()):
        """
        A specialized version of CheckStates where we can query for overview settings and ignoring some flag StateSvc
        this version is less optimized than the CheckStates and should not be used as a replacement outright
        
        slimItem: the slimItem of a player/ship to test
        excludedFlags: a collection of flag states we want to ignore (as if they where not selected in overview settings)
        return the flag code if found or else 0
        """
        if slimItem is None:
            return 0
        if not (slimItem.ownerID in [None, const.ownerSystem] or util.IsNPC(slimItem.ownerID)):
            relationships = self._GetRelationship(slimItem)
        else:
            relationships = None
        for flag in self.GetActiveStateOrder('flag'):
            if flag in excludedFlags:
                continue
            flagName = self.GetStateProps(flag).label
            fullFunctionName = 'Check' + flagName
            checkFunction = getattr(self, fullFunctionName, None)
            if checkFunction:
                if checkFunction(slimItem, relationships):
                    return getattr(state, 'flag' + flagName, 0)

        return 0

    @telemetry.ZONE_METHOD
    def _GetRelationship(self, item):
        allianceID = getattr(item, 'allianceID', None)
        ownerID = getattr(item, 'ownerID', None)
        corpID = getattr(item, 'corpID', None)
        return sm.GetService('addressbook').GetRelationship(ownerID, corpID, allianceID)

    @telemetry.ZONE_METHOD
    def IsStandingRelevant(self, slimItem):
        ownerID = slimItem.ownerID
        if ownerID is None or ownerID == const.ownerSystem or util.IsNPC(ownerID):
            return False
        return True

    @telemetry.ZONE_METHOD
    def CheckStandingHigh(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        if not self.IsStandingRelevant(slimItem):
            return False
        if relationships is NORELATIONSHIP_SENTINEL:
            relationships = self._GetRelationship(slimItem)
        if not relationships:
            return False
        if getattr(slimItem, 'categoryID', None) not in const.stateFilteredCategories:
            return False
        if self.IfAnyRelations(IsHighStanding, self.GetAllRelationshipGroups(relationships)):
            return True
        return False

    @telemetry.ZONE_METHOD
    def CheckStandingGood(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        if not self.IsStandingRelevant(slimItem):
            return False
        if relationships is NORELATIONSHIP_SENTINEL:
            relationships = self._GetRelationship(slimItem)
        if not relationships:
            return False
        if getattr(slimItem, 'categoryID', None) not in const.stateFilteredCategories:
            return False
        if self.IfAnyRelations(IsGoodStanding, self.GetAllRelationshipGroups(relationships)):
            return True
        return False

    @telemetry.ZONE_METHOD
    def CheckStandingNeutral(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        if not self.IsStandingRelevant(slimItem):
            return False
        if relationships is NORELATIONSHIP_SENTINEL:
            relationships = self._GetRelationship(slimItem)
        if not relationships:
            return False
        if getattr(slimItem, 'categoryID', None) not in const.stateFilteredCategories:
            return False
        if relationships.hasRelationship:
            isNeutral = IsNeutralStanding
            if getattr(slimItem, 'allianceID', None) is None or self.IfAllRelations(isNeutral, self.GetAllianceRelationshipGroups(relationships)):
                if not self.IfAllRelations(isNeutral, self.GetCorpRelationshipGroups(relationships)):
                    return False
                if not self.IfAllRelations(isNeutral, self.GetPersonalRelationshipGroups(relationships)):
                    return False
                if not self.CheckSameCorp(slimItem) and not self.CheckSameAlliance(slimItem):
                    return True
        return False

    @telemetry.ZONE_METHOD
    def CheckStandingBad(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        if not self.IsStandingRelevant(slimItem):
            return False
        if relationships is NORELATIONSHIP_SENTINEL:
            relationships = self._GetRelationship(slimItem)
        if not relationships:
            return False
        if getattr(slimItem, 'categoryID', None) not in const.stateFilteredCategories:
            return False
        if self.IfAnyRelations(IsBadStanding, self.GetAllRelationshipGroups(relationships)):
            return True
        return False

    @telemetry.ZONE_METHOD
    def CheckStandingHorrible(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        if not self.IsStandingRelevant(slimItem):
            return False
        if relationships is NORELATIONSHIP_SENTINEL:
            relationships = self._GetRelationship(slimItem)
        if not relationships:
            return False
        if getattr(slimItem, 'categoryID', None) not in const.stateFilteredCategories:
            return False
        if self.IfAnyRelations(IsHorribleStanding, self.GetAllRelationshipGroups(relationships)):
            return True
        return False

    def GetAllRelationshipGroups(self, relationships):
        """
        Gets all relationshipgroups for a slimitem.
        """
        ret = []
        ret.extend(self.GetAllianceRelationshipGroups(relationships))
        ret.extend(self.GetCorpRelationshipGroups(relationships))
        ret.extend(self.GetPersonalRelationshipGroups(relationships))
        return ret

    def GetAllianceRelationshipGroups(self, relationships):
        """
        Gets relationships for an alliance.
        """
        return (relationships.allianceToPers, relationships.allianceToCorp, relationships.allianceToAlliance)

    def GetCorpRelationshipGroups(self, relationships):
        """
        Gets relationships for a corporation.
        """
        return (relationships.corpToPers, relationships.corpToCorp, relationships.corpToAlliance)

    def GetPersonalRelationshipGroups(self, relationships):
        """
        Gets relationships for a person.
        """
        return (relationships.persToPers, relationships.persToCorp, relationships.persToAlliance)

    def IfAnyRelations(self, standingCheck, relationshipGroup):
        """
        Takes in a lambda expression and the relationships of the slim item.
        Returns a check for if ANY relation matches the condition.
        """
        return any((standingCheck(relationship) for relationship in relationshipGroup))

    def IfAllRelations(self, standingCheck, relationshipGroup):
        """
        Takes in a lambda expression and group of relationships for a slim item.
        Returns a check for if ALL relations match the condition.
        """
        return all((standingCheck(relationship) for relationship in relationshipGroup))

    @telemetry.ZONE_METHOD
    def CheckSameCorp(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        if self.logme:
            self.LogInfo('Tactical::CheckSameCorp', slimItem)
        return getattr(slimItem, 'corpID', None) == session.corpid and getattr(slimItem, 'categoryID', None) in const.stateFilteredCategories

    @telemetry.ZONE_METHOD
    def CheckSameAlliance(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        if self.logme:
            self.LogInfo('Tactical::CheckSameAlliance', slimItem)
        return session.allianceid and getattr(slimItem, 'allianceID', None) == session.allianceid and getattr(slimItem, 'categoryID', None) in const.stateFilteredCategories

    @telemetry.ZONE_METHOD
    def CheckSameFleet(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        if self.logme:
            self.LogInfo('Tactical::CheckSameFleet', slimItem)
        if session.fleetid:
            charID = getattr(slimItem, 'charID', None)
            if charID or getattr(slimItem, 'categoryID', None) == const.categoryDrone:
                if charID is None:
                    charID = slimItem.ownerID
                return sm.GetService('fleet').IsMember(charID)
        return 0

    @telemetry.ZONE_METHOD
    def CheckSameMilitia(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        if self.logme:
            self.LogInfo('Tactical::CheckSameMilitia', slimItem)
        if session.warfactionid:
            if (getattr(slimItem, 'charID', None) or getattr(slimItem, 'categoryID', None) == const.categoryDrone) and getattr(slimItem, 'corpID', None):
                slimItemWarFactionID = getattr(slimItem, 'warFactionID', None)
                if slimItemWarFactionID is not None:
                    return facwarCommon.IsFriendlyFaction(slimItemWarFactionID, session.warfactionid)
        return 0

    @telemetry.ZONE_METHOD
    def CheckAgentInteractable(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        if self.logme:
            self.LogInfo('Tactical::CheckAgentInteractable', slimItem)
        return getattr(slimItem, 'groupID', None) == const.groupAgentsinSpace

    @telemetry.ZONE_METHOD
    def CheckIsWanted(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        if self.logme:
            self.LogInfo('Tactical::CheckIsWanted', slimItem)
        return self.bountySvc.QuickHasBounty(slimItem)

    @telemetry.ZONE_METHOD
    def CheckHasKillRight(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        if self.logme:
            self.LogInfo('Tactical::CheckIsWanted', slimItem)
        return self.bountySvc.QuickHasKillRight(slimItem)

    @telemetry.ZONE_METHOD
    def CheckAtWarCanFight(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        if self.logme:
            self.LogInfo('Tactical::CheckAtWarCanFight', slimItem)
        id = getattr(slimItem, 'allianceID', None) or getattr(slimItem, 'corpID', None)
        if id:
            if id not in self.atWar:
                self.atWar[id] = sm.StartService('war').GetRelationship(id)
            return self.atWar[id] == const.warRelationshipAtWarCanFight
        else:
            return 0

    @telemetry.ZONE_METHOD
    def CheckAlliesAtWar(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        if self.logme:
            self.LogInfo('Tactical::CheckAlliesAtWar', slimItem)
        ownerID = getattr(slimItem, 'allianceID', None) or getattr(slimItem, 'corpID', None)
        if ownerID is not None:
            if ownerID not in self.alliesAtWar:
                self.alliesAtWar[ownerID] = sm.GetService('war').GetRelationship(ownerID)
            return self.alliesAtWar[ownerID] == const.warRelationshipAlliesAtWar
        return 0

    @telemetry.ZONE_METHOD
    def CheckAtWarMilitia(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        if self.logme:
            self.LogInfo('Tactical::CheckAtWarMilitia', slimItem)
        if session.warfactionid and getattr(slimItem, 'warFactionID', None):
            id = (slimItem.warFactionID, session.warfactionid)
            if id not in self.atWar:
                self.atWar[id] = facwarCommon.IsEnemyFaction(slimItem.warFactionID, session.warfactionid)
            return self.atWar[id] == True
        return 0

    @telemetry.ZONE_METHOD
    def CheckDangerous(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        if self.logme:
            self.LogInfo('Tactical::CheckDangerous', slimItem)
        if getattr(slimItem, 'charID', None) and -0.1 > (getattr(slimItem, 'securityStatus', None) or 0) >= const.outlawSecurityStatus:
            return 1
        return 0

    @telemetry.ZONE_METHOD
    def CheckOutlaw(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        if self.logme:
            self.LogInfo('Tactical::CheckOutlaw', slimItem)
        if getattr(slimItem, 'charID', None) and util.IsOutlawStatus(getattr(slimItem, 'securityStatus', None) or 0):
            return 1
        return 0

    @telemetry.ZONE_METHOD
    def CheckWreckEmpty(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        return getattr(slimItem, 'groupID', None) == const.groupWreck and slimItem.isEmpty

    @telemetry.ZONE_METHOD
    def CheckNoStanding(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        if relationships is NORELATIONSHIP_SENTINEL:
            relationships = self._GetRelationship(slimItem)
        return (not relationships or not relationships.hasRelationship) and util.IsCharacter(getattr(slimItem, 'ownerID', None)) and getattr(slimItem, 'categoryID', None) in const.stateFilteredCategories

    @telemetry.ZONE_METHOD
    def CheckWreckViewed(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        return sm.GetService('wreck').IsViewedWreck(slimItem.itemID)

    @telemetry.ZONE_METHOD
    def CheckCriminal(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        charID = getattr(slimItem, 'charID', None)
        if charID is not None:
            return sm.GetService('crimewatchSvc').IsCriminal(charID)
        return False

    @telemetry.ZONE_METHOD
    def CheckSuspect(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        charID = getattr(slimItem, 'charID', None)
        if charID is not None:
            return sm.GetService('crimewatchSvc').IsSuspect(charID)
        return False

    def CheckLimitedEngagement(self, slimItem, relationships = NORELATIONSHIP_SENTINEL):
        charID = getattr(slimItem, 'charID', None)
        if charID is not None:
            return sm.GetService('crimewatchSvc').HasLimitedEngagmentWith(charID)
        return False


def GetNPCGroups():
    npcGroups = {GetByLabel('UI/Services/State/NonPlayerCharacter/Generic'): {GetByLabel('UI/Services/State/NonPlayerCharacter/Pirate'): [const.groupAsteroidAngelCartelBattleCruiser,
                                                                                                                              const.groupAsteroidAngelCartelBattleship,
                                                                                                                              const.groupAsteroidAngelCartelCruiser,
                                                                                                                              const.groupAsteroidAngelCartelDestroyer,
                                                                                                                              const.groupAsteroidAngelCartelFrigate,
                                                                                                                              const.groupAsteroidAngelCartelHauler,
                                                                                                                              const.groupAsteroidAngelCartelOfficer,
                                                                                                                              const.groupAsteroidBloodRaidersBattleCruiser,
                                                                                                                              const.groupAsteroidBloodRaidersBattleship,
                                                                                                                              const.groupAsteroidBloodRaidersCruiser,
                                                                                                                              const.groupAsteroidBloodRaidersDestroyer,
                                                                                                                              const.groupAsteroidBloodRaidersFrigate,
                                                                                                                              const.groupAsteroidBloodRaidersHauler,
                                                                                                                              const.groupAsteroidBloodRaidersOfficer,
                                                                                                                              const.groupAsteroidGuristasBattleCruiser,
                                                                                                                              const.groupAsteroidGuristasBattleship,
                                                                                                                              const.groupAsteroidGuristasCruiser,
                                                                                                                              const.groupAsteroidGuristasDestroyer,
                                                                                                                              const.groupAsteroidGuristasFrigate,
                                                                                                                              const.groupAsteroidGuristasHauler,
                                                                                                                              const.groupAsteroidGuristasOfficer,
                                                                                                                              const.groupAsteroidSanshasNationBattleCruiser,
                                                                                                                              const.groupAsteroidSanshasNationBattleship,
                                                                                                                              const.groupAsteroidSanshasNationCruiser,
                                                                                                                              const.groupAsteroidSanshasNationDestroyer,
                                                                                                                              const.groupAsteroidSanshasNationFrigate,
                                                                                                                              const.groupAsteroidSanshasNationHauler,
                                                                                                                              const.groupAsteroidSanshasNationOfficer,
                                                                                                                              const.groupAsteroidSerpentisBattleCruiser,
                                                                                                                              const.groupAsteroidSerpentisBattleship,
                                                                                                                              const.groupAsteroidSerpentisCruiser,
                                                                                                                              const.groupAsteroidSerpentisDestroyer,
                                                                                                                              const.groupAsteroidSerpentisFrigate,
                                                                                                                              const.groupAsteroidSerpentisHauler,
                                                                                                                              const.groupAsteroidSerpentisOfficer,
                                                                                                                              const.groupDeadspaceAngelCartelBattleCruiser,
                                                                                                                              const.groupDeadspaceAngelCartelBattleship,
                                                                                                                              const.groupDeadspaceAngelCartelCruiser,
                                                                                                                              const.groupDeadspaceAngelCartelDestroyer,
                                                                                                                              const.groupDeadspaceAngelCartelFrigate,
                                                                                                                              const.groupDeadspaceBloodRaidersBattleCruiser,
                                                                                                                              const.groupDeadspaceBloodRaidersBattleship,
                                                                                                                              const.groupDeadspaceBloodRaidersCruiser,
                                                                                                                              const.groupDeadspaceBloodRaidersDestroyer,
                                                                                                                              const.groupDeadspaceBloodRaidersFrigate,
                                                                                                                              const.groupDeadspaceGuristasBattleCruiser,
                                                                                                                              const.groupDeadspaceGuristasBattleship,
                                                                                                                              const.groupDeadspaceGuristasCruiser,
                                                                                                                              const.groupDeadspaceGuristasDestroyer,
                                                                                                                              const.groupDeadspaceGuristasFrigate,
                                                                                                                              const.groupDeadspaceSanshasNationBattleCruiser,
                                                                                                                              const.groupDeadspaceSanshasNationBattleship,
                                                                                                                              const.groupDeadspaceSanshasNationCruiser,
                                                                                                                              const.groupDeadspaceSanshasNationDestroyer,
                                                                                                                              const.groupDeadspaceSanshasNationFrigate,
                                                                                                                              const.groupDeadspaceSerpentisBattleCruiser,
                                                                                                                              const.groupDeadspaceSerpentisBattleship,
                                                                                                                              const.groupDeadspaceSerpentisCruiser,
                                                                                                                              const.groupDeadspaceSerpentisDestroyer,
                                                                                                                              const.groupDeadspaceSerpentisFrigate,
                                                                                                                              const.groupDeadspaceSleeperSleeplessPatroller,
                                                                                                                              const.groupDeadspaceSleeperSleeplessSentinel,
                                                                                                                              const.groupDeadspaceSleeperSleeplessDefender,
                                                                                                                              const.groupDeadspaceSleeperAwakenedPatroller,
                                                                                                                              const.groupDeadspaceSleeperAwakenedSentinel,
                                                                                                                              const.groupDeadspaceSleeperAwakenedDefender,
                                                                                                                              const.groupDeadspaceSleeperEmergentPatroller,
                                                                                                                              const.groupDeadspaceSleeperEmergentSentinel,
                                                                                                                              const.groupDeadspaceSleeperEmergentDefender,
                                                                                                                              const.groupAsteroidAngelCartelCommanderBattleCruiser,
                                                                                                                              const.groupAsteroidAngelCartelCommanderCruiser,
                                                                                                                              const.groupAsteroidAngelCartelCommanderDestroyer,
                                                                                                                              const.groupAsteroidAngelCartelCommanderFrigate,
                                                                                                                              const.groupAsteroidBloodRaidersCommanderBattleCruiser,
                                                                                                                              const.groupAsteroidBloodRaidersCommanderCruiser,
                                                                                                                              const.groupAsteroidBloodRaidersCommanderDestroyer,
                                                                                                                              const.groupAsteroidBloodRaidersCommanderFrigate,
                                                                                                                              const.groupAsteroidGuristasCommanderBattleCruiser,
                                                                                                                              const.groupAsteroidGuristasCommanderCruiser,
                                                                                                                              const.groupAsteroidGuristasCommanderDestroyer,
                                                                                                                              const.groupAsteroidGuristasCommanderFrigate,
                                                                                                                              const.groupAsteroidRogueDroneBattleCruiser,
                                                                                                                              const.groupAsteroidRogueDroneBattleship,
                                                                                                                              const.groupAsteroidRogueDroneCruiser,
                                                                                                                              const.groupAsteroidRogueDroneDestroyer,
                                                                                                                              const.groupAsteroidRogueDroneFrigate,
                                                                                                                              const.groupAsteroidRogueDroneHauler,
                                                                                                                              const.groupAsteroidRogueDroneSwarm,
                                                                                                                              const.groupAsteroidRogueDroneOfficer,
                                                                                                                              const.groupAsteroidSanshasNationCommanderBattleCruiser,
                                                                                                                              const.groupAsteroidSanshasNationCommanderCruiser,
                                                                                                                              const.groupAsteroidSanshasNationCommanderDestroyer,
                                                                                                                              const.groupAsteroidSanshasNationCommanderFrigate,
                                                                                                                              const.groupAsteroidSerpentisCommanderBattleCruiser,
                                                                                                                              const.groupAsteroidSerpentisCommanderCruiser,
                                                                                                                              const.groupAsteroidSerpentisCommanderDestroyer,
                                                                                                                              const.groupAsteroidSerpentisCommanderFrigate,
                                                                                                                              const.groupDeadspaceRogueDroneBattleCruiser,
                                                                                                                              const.groupDeadspaceRogueDroneBattleship,
                                                                                                                              const.groupDeadspaceRogueDroneCruiser,
                                                                                                                              const.groupDeadspaceRogueDroneDestroyer,
                                                                                                                              const.groupDeadspaceRogueDroneFrigate,
                                                                                                                              const.groupDeadspaceRogueDroneSwarm,
                                                                                                                              const.groupDeadspaceOverseerFrigate,
                                                                                                                              const.groupDeadspaceOverseerCruiser,
                                                                                                                              const.groupDeadspaceOverseerBattleship,
                                                                                                                              const.groupAsteroidRogueDroneCommanderFrigate,
                                                                                                                              const.groupAsteroidRogueDroneCommanderDestroyer,
                                                                                                                              const.groupAsteroidRogueDroneCommanderCruiser,
                                                                                                                              const.groupAsteroidRogueDroneCommanderBattleCruiser,
                                                                                                                              const.groupAsteroidRogueDroneCommanderBattleship,
                                                                                                                              const.groupAsteroidAngelCartelCommanderBattleship,
                                                                                                                              const.groupAsteroidBloodRaidersCommanderBattleship,
                                                                                                                              const.groupAsteroidGuristasCommanderBattleship,
                                                                                                                              const.groupAsteroidSanshasNationCommanderBattleship,
                                                                                                                              const.groupAsteroidSerpentisCommanderBattleship,
                                                                                                                              const.groupMissionAmarrEmpireCarrier,
                                                                                                                              const.groupMissionCaldariStateCarrier,
                                                                                                                              const.groupMissionGallenteFederationCarrier,
                                                                                                                              const.groupMissionMinmatarRepublicCarrier,
                                                                                                                              const.groupMissionFighterDrone,
                                                                                                                              const.groupMissionGenericFreighters,
                                                                                                                              const.groupInvasionSanshaNationBattleship,
                                                                                                                              const.groupInvasionSanshaNationCapital,
                                                                                                                              const.groupInvasionSanshaNationCruiser,
                                                                                                                              const.groupInvasionSanshaNationFrigate,
                                                                                                                              const.groupInvasionSanshaNationIndustrial,
                                                                                                                              const.groupGhostSitesAngelCartelCruiser,
                                                                                                                              const.groupGhostSitesBloodRaidersCruiser,
                                                                                                                              const.groupGhostSitesGuristasCruiser,
                                                                                                                              const.groupGhostSitesSanshasCruiser,
                                                                                                                              const.groupGhostSitesSerpentisCruiser,
                                                                                                                              const.groupGhostSitesMordusLegion],
                                                                  GetByLabel('UI/Services/State/NonPlayerCharacter/Mission'): [const.groupMissionDrone,
                                                                                                                               const.groupStorylineBattleship,
                                                                                                                               const.groupStorylineFrigate,
                                                                                                                               const.groupStorylineCruiser,
                                                                                                                               const.groupStorylineMissionBattleship,
                                                                                                                               const.groupStorylineMissionFrigate,
                                                                                                                               const.groupStorylineMissionCruiser,
                                                                                                                               const.groupMissionGenericBattleships,
                                                                                                                               const.groupMissionGenericCruisers,
                                                                                                                               const.groupMissionGenericFrigates,
                                                                                                                               const.groupMissionThukkerBattlecruiser,
                                                                                                                               const.groupMissionThukkerBattleship,
                                                                                                                               const.groupMissionThukkerCruiser,
                                                                                                                               const.groupMissionThukkerDestroyer,
                                                                                                                               const.groupMissionThukkerFrigate,
                                                                                                                               const.groupMissionThukkerOther,
                                                                                                                               const.groupMissionGenericBattleCruisers,
                                                                                                                               const.groupMissionGenericDestroyers],
                                                                  GetByLabel('UI/Services/State/NonPlayerCharacter/Police'): [const.groupPoliceDrone],
                                                                  GetByLabel('UI/Services/State/NonPlayerCharacter/Concord'): [const.groupConcordDrone],
                                                                  GetByLabel('UI/Services/State/NonPlayerCharacter/Customs'): [const.groupCustomsOfficial],
                                                                  GetByLabel('UI/Services/State/NonPlayerCharacter/FactionNavy'): [const.groupFactionDrone]}}
    return npcGroups


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('util', {'GetNPCGroups': GetNPCGroups})
