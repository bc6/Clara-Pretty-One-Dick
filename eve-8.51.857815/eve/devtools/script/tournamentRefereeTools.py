#Embedded file name: eve/devtools/script\tournamentRefereeTools.py
import uicontrols
import const
import carbonui.const as uiconst
import uix
import blue
import util
import service
import uthread
from eve.client.script.ui.control import entries as listentry
import uiutil
import form
import base
import uiprimitives
from collections import namedtuple
EntryRow = namedtuple('EntryRow', 'character groupName typeName maxDistance distance')
EntryRow.__guid__ = 'at.EntryRow'
STATE_BANNING = 0
STATE_PREGAME = 1
STATE_WARPIN = 2
STATE_COUNTDOWN = 3
STATE_STARTING = 4
STATE_INPROGRESS = 5
STATE_COMPLETE = 6
STATE_CLOSED = 7
shipPointsGroups = {25: 2,
 28: 3,
 420: 3,
 541: 4,
 831: 3,
 324: 4,
 830: 4,
 893: 6,
 834: 4,
 26: 6,
 419: 13,
 1201: 13,
 894: 11,
 358: 12,
 832: 13,
 906: 14,
 833: 14,
 963: 16,
 540: 16,
 27: 17,
 898: 17,
 900: 26}
shipPointsTypes = {32207: 4,
 3516: 4,
 2834: 4,
 17619: 4,
 17926: 4,
 17928: 4,
 17932: 4,
 17841: 4,
 11940: 4,
 17703: 4,
 17812: 4,
 11942: 4,
 17924: 4,
 17930: 4,
 32788: 4,
 33468: 4,
 33816: 4,
 33677: 4,
 32848: 3,
 32844: 3,
 32842: 3,
 32840: 3,
 33099: 3,
 32846: 3,
 2863: 3,
 32811: 3,
 4363: 3,
 4388: 3,
 32985: 2,
 32987: 2,
 32983: 2,
 33190: 2,
 32989: 2,
 617: 2,
 33079: 2,
 615: 2,
 33081: 2,
 33083: 2,
 2161: 4,
 584: 4,
 609: 4,
 3766: 4,
 625: 10,
 634: 10,
 620: 10,
 631: 10,
 29337: 12,
 17634: 12,
 29344: 12,
 11011: 12,
 17709: 12,
 29340: 12,
 29336: 12,
 17713: 12,
 17843: 12,
 17922: 12,
 17720: 12,
 17718: 12,
 17715: 12,
 17722: 12,
 33470: 12,
 33818: 12,
 2836: 12,
 32209: 12,
 3518: 12,
 32790: 13,
 17738: 20,
 17736: 20,
 17920: 20,
 17918: 20,
 17740: 20,
 33820: 20,
 11936: 19,
 17726: 19,
 11938: 19,
 32305: 19,
 32307: 19,
 17728: 19,
 13202: 19,
 17636: 19,
 26840: 19,
 32309: 19,
 17732: 19,
 26842: 19,
 32311: 19,
 33151: 14,
 33153: 14,
 33155: 14,
 33157: 14,
 645: 20,
 12005: 14}
skinEquivalents = {33623: 24692,
 33625: 24692,
 33627: 24688,
 33629: 24688,
 33631: 24694,
 33633: 24694,
 33635: 24690,
 33637: 24690,
 4005: 640,
 33869: 16229,
 33871: 33871,
 33873: 33873,
 33875: 33875,
 33639: 2006,
 33641: 2006,
 33643: 621,
 33645: 621,
 33647: 622,
 33649: 622,
 33651: 627,
 33653: 627,
 33877: 16240,
 33879: 16236,
 33881: 16238,
 33883: 16242,
 32848: 16240,
 32844: 16240,
 32842: 16240,
 32840: 16240,
 32846: 16240,
 33655: 597,
 33657: 597,
 33659: 603,
 33661: 603,
 33663: 587,
 33665: 587,
 33667: 594,
 33669: 594,
 32811: 656,
 33689: 657,
 33691: 649,
 33693: 652,
 33695: 1944,
 4363: 656,
 4388: 656}

class AtCompetitorEntry(listentry.ColumnLine):
    __guid__ = 'listentry.AtCompetitorEntry'

    def Startup(self, args):
        listentry.ColumnLine.Startup(self, args)
        self.warn = uiprimitives.Fill(name='warn', parent=self, padTop=1, color=(1.0, 0.0, 0.0, 0.125), state=uiconst.UI_HIDDEN)


class TournamentRefereeTool(uicontrols.Window):
    __guid__ = 'form.TournamentRefereeTool'
    __notifyevents__ = ['OnCompetitorTrackingUpdate', 'OnCompetitorTrackingStart']
    default_arenaRadius = 125
    default_windowID = 'TournamentRefereeTool'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.SetCaption('Tournament Referee Tool')
        self.SetMinSize((525, 550))
        self.SetTopparentHeight(0)
        self.centerItemID = None
        self.arenaRadius = 125000
        self.isToggling = False
        self.playersCanLock = True
        self.playersCanWarp = True
        self.ConstructLayout()
        self.matchDetails = [None,
         None,
         None,
         None]
        sm.RegisterForNotifyEvent(self, 'ProcessTournamentMatchUpdate')
        self.solarsystemID = None
        self.pregameRangeTimer = None
        self.countdownTimer = None

    def ConstructLayout(self):
        svc = sm.GetService('allianceTournamentSvc')
        tourneyMgr = sm.RemoteSvc('tourneyMgr')
        tournaments, tourneySystems = tourneyMgr.GetTourneySetup()
        locations = []
        for systemID, (redBeacons, blueBeacons, combatBeacons, warpBubbles) in tourneySystems.iteritems():
            locations.append(systemID)
            locations.extend(redBeacons)
            locations.extend(blueBeacons)

        cfg.evelocations.Prime(locations)
        self.beaconOptions = {}
        for systemID, (redBeacons, blueBeacons, combatBeacons, warpBubbles) in tourneySystems.iteritems():
            self.beaconOptions[systemID] = ([ (cfg.evelocations.Get(id).locationName, idx) for idx, id in enumerate(redBeacons) ], [ (cfg.evelocations.Get(id).locationName, idx) for idx, id in enumerate(blueBeacons) ])

        self.resetButton = uicontrols.Button(label='Reset Match', parent=self.sr.main, align=uiconst.TOBOTTOM, func=self.ResetMatch, state=uiconst.UI_HIDDEN, padding=(5, 5, 5, 5))
        tourneyOptions = [ (name, tourneyID) for tourneyID, name in tournaments.iteritems() ]
        systemOptions = [ (cfg.evelocations.Get(id).locationName, id) for id in tourneySystems ]
        self.allianceSelections = uiprimitives.Container(name='aliSelect', parent=self.sr.main, align=uiconst.TOTOP, height=190)
        self.startButton = uicontrols.Button(label='Start Match', parent=self.allianceSelections, align=uiconst.TOBOTTOM, pos=(0, 0, 100, 28), padding=(5, 5, 5, 5), func=self.StartMatch)
        self.solSystemSelect = uicontrols.Combo(label='Select Solar System', parent=self.allianceSelections, align=uiconst.TOBOTTOM, options=systemOptions, pos=(0, 0, 100, 40), padding=(5, 15, 5, 5))
        self.sr.pointsSelect = uicontrols.Combo(label='PointsAllowed', parent=self.allianceSelections, align=uiconst.TOBOTTOM, name='pointSel', options=(('100', 100),), select='100', padding=(5, 15, 5, 5))

        def TourneySelChanged(combo, tName, tourneyID):
            if tourneyID is None:
                self.sr.matchSelect.options = []
            else:
                possibleMatches = tourneyMgr.GetPotentialMatches(tourneyID)
                self.sr.matchSelect.LoadOptions([ ('%s vs %s' % (redTeam, blueTeam), (seriesID, redTeam, blueTeam)) for seriesID, redTeam, blueTeam in possibleMatches ])

        self.sr.tourneySelect = uicontrols.Combo(label='Select Tournament:', parent=self.allianceSelections, align=uiconst.TOTOP, padding=(5, 15, 5, 5), name='tourneySel', options=[('Select Tourney', None)] + tourneyOptions, callback=TourneySelChanged)
        self.sr.matchSelect = uicontrols.Combo(label='Select Match:', parent=self.allianceSelections, align=uiconst.TOTOP, padding=(5, 15, 5, 5), name='matchSel', options=[('Pick Tourney First', None)])
        banOptions = sorted([ (x.typeName, x.typeID) for x in cfg.invtypes if not x.typeName.startswith('[no messageID:') and (x.typeID in shipPointsTypes or x.groupID in shipPointsGroups) and x.typeID not in skinEquivalents ])
        self.banningScreen = uiprimitives.Container(name='banningScreen', parent=self.sr.main, state=uiconst.UI_HIDDEN, align=uiconst.TOALL, left=5, width=5)
        self.redTeamBanningHeader = uicontrols.EveLabelLarge(text='RedTeam', parent=self.banningScreen, align=uiconst.TOTOP, top=10, color=(1, 0.3, 0.3, 1))
        self.redBanBox = uiprimitives.Container(name='redBanBox', parent=self.banningScreen, align=uiconst.TOTOP, height=70, top=4)
        self.redBans = {}
        redBanChoice = uicontrols.Combo(label='Red Team Ban:', parent=self.banningScreen, options=banOptions, top=20, align=uiconst.TOTOP)
        uicontrols.Button(label="Perform Red's Ban", parent=self.banningScreen, func=self.SendBan, args=(0, redBanChoice), align=uiconst.TOTOP)
        self.blueTeamBanningHeader = uicontrols.EveLabelLarge(text='BlueTeam', parent=self.banningScreen, align=uiconst.TOTOP, top=30, color=(0.5, 0.5, 1, 1))
        self.blueBanBox = uiprimitives.Container(name='blueBanBox', parent=self.banningScreen, align=uiconst.TOTOP, height=70, top=4)
        self.blueBans = {}
        blueBanChoice = uicontrols.Combo(label='Blue Team Ban:', parent=self.banningScreen, options=banOptions, top=20, align=uiconst.TOTOP)
        uicontrols.Button(label="Perform Blue's Ban", parent=self.banningScreen, func=self.SendBan, args=(1, blueBanChoice), align=uiconst.TOTOP)
        autoBanBox = uiprimitives.Container(name='autoBanBox', parent=self.banningScreen, align=uiconst.TOTOP, height=115, top=10)
        autoBanOverrides = uiprimitives.Container(name='autoBanOverrides', parent=autoBanBox, align=uiconst.TOLEFT, width=150)
        autoBanOutput = uiprimitives.Container(name='autoBanOutput', parent=autoBanBox)
        autoBanRedCapt = uiprimitives.Container(name='redCapt', parent=autoBanOverrides, align=uiconst.TOTOP, top=4, height=44)
        uicontrols.Label(text='Red Captain:', parent=autoBanRedCapt, top=4)
        self.autoBanRedCharName = uicontrols.Label(text='?', parent=autoBanRedCapt, top=4, left=100)
        self.autoBanRedCharID = uicontrols.SinglelineEdit(name='redCaptID', setvalue='', OnFocusLost=self.LookupBanChars, align=uiconst.TOBOTTOM, parent=autoBanRedCapt, top=4)
        autoBanBlueCapt = uiprimitives.Container(name='blueCapt', parent=autoBanOverrides, align=uiconst.TOTOP, top=4, height=44)
        uicontrols.Label(text='Blue Captain:', parent=autoBanBlueCapt, top=4)
        self.autoBanBlueCharName = uicontrols.Label(text='?', parent=autoBanBlueCapt, top=4, left=100)
        self.autoBanBlueCharID = uicontrols.SinglelineEdit(name='blueCaptID', setvalue='', OnFocusLost=self.LookupBanChars, align=uiconst.TOBOTTOM, parent=autoBanBlueCapt, top=4)
        uicontrols.Button(label='Initiate Autobans', parent=autoBanOverrides, func=self.Autobans, align=uiconst.TOTOP, top=4)
        uicontrols.Label(text='Auto Ban Output:', parent=autoBanOutput, align=uiconst.TOTOP, top=4, padLeft=125)
        self.autoBanText = uicontrols.Label(text='', parent=autoBanOutput, align=uiconst.TOTOP, height=100, top=4, padLeft=125)
        uicontrols.Button(label='Finalize Bans', parent=self.banningScreen, func=self.FinalizeBans, top=40, align=uiconst.TOTOP)
        self.shipPilotCheck = uiprimitives.Container(name='shipPilotCheck', parent=self.sr.main, state=uiconst.UI_HIDDEN, align=uiconst.TOALL)
        uicontrols.Button(label="LET'S DO THIS", parent=self.shipPilotCheck, align=uiconst.TORIGHT, width=90, padLeft=5, padRight=5, func=self.CompleteShipPilotCheck)
        boxes = uiprimitives.Container(name='boxContainer', parent=self.shipPilotCheck, align=uiconst.TOALL)
        blueTeamBox = uiprimitives.Container(name='blueTeamBox', parent=boxes, align=uiconst.TOTOP_PROP, height=0.5)
        redTeamBox = uiprimitives.Container(name='redTeamBox', parent=boxes, align=uiconst.TOTOP_PROP, height=0.5)
        blueButtons = uiprimitives.Container(name='shipPilotCheckButtons', parent=blueTeamBox, align=uiconst.TOBOTTOM, height=25, padding=(4, 15, 4, 4))
        redButtons = uiprimitives.Container(name='shipPilotCheckButtons', parent=redTeamBox, align=uiconst.TOBOTTOM, height=25, padding=(4, 15, 4, 4))
        uicontrols.Button(label='Refresh Info', parent=blueButtons, align=uiconst.TOLEFT, func=self.RefreshShipPilotCheck, args=(1,))
        self.blueLockBtn = uicontrols.Button(label='Lock Member List', parent=blueButtons, align=uiconst.TOLEFT, func=self.LockMemberList, args=(1,))
        self.blueUnlockBtn = uicontrols.Button(label='Unlock Member List', parent=blueButtons, align=uiconst.TOLEFT, func=self.UnlockMemberList, args=(1,), state=uiconst.UI_HIDDEN)
        self.blueTeleportBtn = uicontrols.Button(label='Teleport Players', parent=blueButtons, align=uiconst.TOLEFT, func=self.TeleportPlayers, args=(1,), state=uiconst.UI_HIDDEN)
        self.blueTeleportBeacon = uicontrols.Combo(label='Beacon select', parent=blueButtons, align=uiconst.TOLEFT, state=uiconst.UI_HIDDEN, options=[])
        self.blueOverFleetBtn = uicontrols.Button(label='Override FleetID', parent=blueButtons, align=uiconst.TOLEFT, func=self.OverrideFleetID, args=(1,))
        self.blueAddPlayerBtn = uicontrols.Button(label='Add Player', parent=blueButtons, align=uiconst.TOLEFT, func=self.AddPlayer, args=(1,), state=uiconst.UI_HIDDEN)
        uicontrols.Button(label='Refresh Info', parent=redButtons, align=uiconst.TOLEFT, func=self.RefreshShipPilotCheck, args=(0,))
        self.redLockBtn = uicontrols.Button(label='Lock Member List', parent=redButtons, align=uiconst.TOLEFT, func=self.LockMemberList, args=(0,))
        self.redUnlockBtn = uicontrols.Button(label='Unlock Member List', parent=redButtons, align=uiconst.TOLEFT, func=self.UnlockMemberList, args=(0,), state=uiconst.UI_HIDDEN)
        self.redTeleportBtn = uicontrols.Button(label='Teleport Players', parent=redButtons, align=uiconst.TOLEFT, func=self.TeleportPlayers, args=(0,), state=uiconst.UI_HIDDEN)
        self.redTeleportBeacon = uicontrols.Combo(label='Beacon select', parent=redButtons, align=uiconst.TOLEFT, state=uiconst.UI_HIDDEN, options=[])
        self.redOverFleetBtn = uicontrols.Button(label='Override FleetID', parent=redButtons, align=uiconst.TOLEFT, func=self.OverrideFleetID, args=(0,))
        self.redAddPlayerBtn = uicontrols.Button(label='Add Player', parent=redButtons, align=uiconst.TOLEFT, func=self.AddPlayer, args=(0,), state=uiconst.UI_HIDDEN)
        self.shipcheckBlueTeamLabel = uicontrols.Label(text='Blue Team', parent=blueTeamBox, color=(0.5, 0.5, 1, 1), align=uiconst.TOTOP)
        self.shipcheckRedTeamLabel = uicontrols.Label(text='Red Team', parent=redTeamBox, color=(1, 0.3, 0.3, 1), align=uiconst.TOTOP)
        self.shipcheckRedScroll = uicontrols.Scroll(parent=redTeamBox, id='atRedTeamScroll')
        self.shipcheckBlueScroll = uicontrols.Scroll(parent=blueTeamBox, id='atBlueTeamScroll')
        self.pregameList = uiprimitives.Container(name='pregameList', parent=self.sr.main, state=uiconst.UI_HIDDEN, align=uiconst.TOALL)
        pregameRangeContainer = uiprimitives.Container(name='rangeCont', parent=self.pregameList, align=uiconst.TORIGHT, width=200)
        for idx in xrange(26):
            label = uicontrols.Label(text='', parent=pregameRangeContainer, align=uiconst.TOTOP, padTop=5, maxLines=1)
            setattr(self, 'pregameDistance%d' % (idx,), label)

        lockCont = uiprimitives.Container(name='locks', parent=self.pregameList, align=uiconst.TOBOTTOM, height=50)
        self.pregameLockStatus = uicontrols.EveLabelLarge(text="Player locking: <color='green'>Allowed</color>", parent=lockCont, align=uiconst.TOLEFT_PROP, width=0.75, padTop=10)
        tempContainer = uiprimitives.Container(parent=lockCont, align=uiconst.TORIGHT_PROP, width=0.2)
        uicontrols.Button(label='Toggle Locking', parent=tempContainer, func=self.ToggleLocks, align=uiconst.TOLEFT, padTop=5, padBottom=5)
        warpCont = uiprimitives.Container(name='warps', parent=self.pregameList, align=uiconst.TOBOTTOM, height=50)
        self.pregameWarpStatus = uicontrols.EveLabelLarge(text="Player warping: <color='red'>Disallowed</color>", parent=warpCont, align=uiconst.TOLEFT_PROP, width=0.75, padTop=10)
        tempContainer = uiprimitives.Container(parent=warpCont, align=uiconst.TORIGHT_PROP, width=0.2)
        uicontrols.Button(label='Toggle Warping', parent=tempContainer, func=self.ToggleWarping, align=uiconst.TOLEFT, padTop=5, padBottom=5)
        moveCont = uiprimitives.Container(name='move', parent=self.pregameList, align=uiconst.TOBOTTOM, height=50)
        self.pregameMoveStatus = uicontrols.EveLabelLarge(text="Player movement: <color='red'>Disallowed</color>", parent=moveCont, align=uiconst.TOLEFT_PROP, width=0.75, padTop=10)
        tempContainer = uiprimitives.Container(parent=moveCont, align=uiconst.TORIGHT_PROP, width=0.2)
        uicontrols.Button(label='Toggle Movement', parent=tempContainer, func=self.ToggleMovement, align=uiconst.TOLEFT, padTop=5, padBottom=5)
        stepOne = uiprimitives.Container(name='stepOne', parent=self.pregameList, align=uiconst.TOTOP, height=50)
        self.pregameStepOneText = uicontrols.EveLabelLarge(text="Step 1 - Let them warp, don't let them lock", parent=stepOne, align=uiconst.TOLEFT_PROP, width=0.75, padTop=10)
        tempContainer = uiprimitives.Container(parent=stepOne, align=uiconst.TORIGHT_PROP, width=0.2)
        uicontrols.Button(label='Do Step 1', parent=tempContainer, func=self.PreGameStepOne, align=uiconst.TOLEFT, padTop=5, padBottom=5)
        stepThree = uiprimitives.Container(name='stepThree', parent=self.pregameList, align=uiconst.TOTOP, height=50)
        self.pregameStepThreeText = uicontrols.EveLabelLarge(text='Step 2 - Lock warping again', parent=stepThree, align=uiconst.TOLEFT_PROP, width=0.75, padTop=10)
        tempContainer = uiprimitives.Container(parent=stepThree, align=uiconst.TORIGHT_PROP, width=0.2)
        uicontrols.Button(label='Do Step 2', parent=tempContainer, func=self.PreGameStepThree, align=uiconst.TOLEFT, padTop=5, padBottom=5)
        stepFour = uiprimitives.Container(name='stepFour', parent=self.pregameList, align=uiconst.TOTOP, height=50)
        self.pregameStepFourText = uicontrols.EveLabelLarge(text='Step 3 - Start Countdown', parent=stepFour, align=uiconst.TOLEFT_PROP, width=0.75, padTop=10)
        tempContainer = uiprimitives.Container(parent=stepFour, align=uiconst.TORIGHT_PROP, width=0.2)
        uicontrols.Button(label='Do Step 3', parent=tempContainer, func=self.PreGameStepFour, align=uiconst.TOLEFT, padTop=5, padBottom=5)
        self.countdownCont = uiprimitives.Container(name='Countdown', parent=self.pregameList, align=uiconst.TOALL, state=uiconst.UI_HIDDEN)
        self.countdownText = uicontrols.Label(parent=self.countdownCont, align=uiconst.CENTERTOP, fontsize=48, color=(1, 0, 0, 1))
        self.countdownAbort = uicontrols.Button(label='Abort!', parent=self.countdownCont, align=uiconst.TOALL, func=self.AbortCountdown, padTop=65, padBottom=28)
        self.countdownAbort.width = self.countdownAbort.height = 0
        self.countdownAbort.sr.label.fontsize = 32
        self.rangeCheck = uiprimitives.Container(name='range check', parent=self.sr.main, state=uiconst.UI_HIDDEN, align=uiconst.TOALL)
        uicontrols.Label(text='Center Item ID', parent=self.rangeCheck, left=const.defaultPadding, top=const.defaultPadding, fontsize=12)
        uicontrols.Label(text='Arena Radius km', parent=self.rangeCheck, left=const.defaultPadding, top=const.defaultPadding + 20, fontsize=12)
        self.centerItemIDEdit = uicontrols.SinglelineEdit(name='centerItemIDEdit', setvalue=str(session.shipid), parent=self.rangeCheck, left=100, width=120, top=const.defaultPadding)
        self.arenaRadiusEdit = uicontrols.SinglelineEdit(name='arenaRadiusEdit', setvalue=self.default_arenaRadius, parent=self.rangeCheck, left=100, top=const.defaultPadding + 20, ints=(1, 250))
        uicontrols.Button(label='Match Completed', parent=self.rangeCheck, left=300, top=const.defaultPadding + 20, func=self.MatchCompleted)
        startButtonText = 'Stop' if svc.isCompetitorsTrackingActive else 'Start'
        self.startButton = uicontrols.Button(label=startButtonText, parent=self.rangeCheck, left=const.defaultPadding, top=const.defaultPadding + 40)
        self.startButton.OnClick = self.OnToggleStart
        self.scroll = uicontrols.Scroll(name='competitorsList', parent=self.rangeCheck, align=uiconst.TOALL, top=70)
        self.postgameList = uiprimitives.Container(name='postgameList', parent=self.sr.main, state=uiconst.UI_HIDDEN, align=uiconst.TOALL)
        stepOne = uiprimitives.Container(name='stepOne', parent=self.postgameList, align=uiconst.TOTOP, height=50)
        self.postgameStepOneText = uicontrols.EveLabelLarge(text='Step 1 - Send everyone back home', parent=stepOne, align=uiconst.TOLEFT_PROP, width=0.75, padTop=10)
        tempContainer = uiprimitives.Container(parent=stepOne, align=uiconst.TORIGHT_PROP, width=0.2)
        uicontrols.Button(label='Do Step 1', parent=tempContainer, func=self.PostGameStepOne, align=uiconst.TOLEFT, padTop=5, padBottom=5)
        stepTwo = uiprimitives.Container(name='stepTwo', parent=self.postgameList, align=uiconst.TOTOP, height=50)
        self.postgameStepTwoText = uicontrols.EveLabelLarge(text='Step 2 - Clean up the grid', parent=stepTwo, align=uiconst.TOLEFT_PROP, width=0.75, padTop=10)
        tempContainer = uiprimitives.Container(parent=stepTwo, align=uiconst.TORIGHT_PROP, width=0.2)
        uicontrols.Button(label='Do Step 2', parent=tempContainer, func=self.PostGameStepTwo, align=uiconst.TOLEFT, padTop=5, padBottom=5)
        self.OnCompetitorTrackingStart(svc.competitorsByShipID)

    def StartMatch(self, *args):
        selectedMatch = self.sr.matchSelect.GetValue()
        self.redTeam = selectedMatch[1]
        self.blueTeam = selectedMatch[2]
        self.matchMoniker = util.Moniker('tourneyMgr', self.solSystemSelect.GetValue())
        self.matchDetails = [-1,
         None,
         None,
         None]
        matchID, beaconIDs, captainIDs = self.matchMoniker.CreateMatch(self.sr.tourneySelect.GetValue(), selectedMatch[0], self.sr.pointsSelect.GetValue())
        self.matchDetails[0] = matchID
        self.matchDetails[3] = beaconIDs
        self.autoBanRedCharID.SetValue(str(captainIDs[0]))
        self.redTeamBanningHeader.text = 'Red Team - %s' % (self.redTeam,)
        self.autoBanBlueCharID.SetValue(str(captainIDs[1]))
        self.blueTeamBanningHeader.text = 'Blue Team - %s' % (self.blueTeam,)
        self.LookupBanChars()

    def ProcessTournamentMatchUpdate(self, matchState):
        myMatchID = self.matchDetails[0]
        if matchState['matchID'] != myMatchID:
            if myMatchID != -1:
                return
        uiScreenPerState = {STATE_BANNING: [self.banningScreen],
         STATE_PREGAME: [self.shipPilotCheck],
         STATE_WARPIN: [self.pregameList],
         STATE_COUNTDOWN: [self.pregameList, self.countdownCont, self.countdownAbort],
         STATE_STARTING: [self.pregameList, self.countdownCont],
         STATE_INPROGRESS: [self.rangeCheck],
         STATE_COMPLETE: [self.postgameList],
         STATE_CLOSED: [self.allianceSelections]}
        allScreens = (self.allianceSelections,
         self.banningScreen,
         self.shipPilotCheck,
         self.pregameList,
         self.rangeCheck,
         self.postgameList,
         self.countdownCont,
         self.countdownAbort)
        for screen in allScreens:
            if screen in uiScreenPerState[matchState['state']]:
                screen.state = uiconst.UI_NORMAL
            else:
                screen.state = uiconst.UI_HIDDEN

        if matchState['state'] == STATE_WARPIN:
            if self.pregameRangeTimer is None:
                self.pregameRangeTimer = base.AutoTimer(1000, self.UpdatePregameRanges)
        else:
            self.pregameRangeTimer = None
        if 'matchStartTime' in matchState:
            self.matchStartTime = matchState['matchStartTime']
        if matchState['state'] in (STATE_COUNTDOWN, STATE_STARTING):
            if self.countdownTimer is None:
                self.UpdateTimer()
                self.countdownTimer = base.AutoTimer(100, self.UpdateTimer)
        else:
            self.countdownTimer = None
        if matchState['state'] == STATE_INPROGRESS:
            if self.centerItemID is None:
                self.startButton.SetLabel('Stop')
                closestBeacon = None
                ballpark = sm.GetService('michelle').GetBallpark()
                for beaconID in self.matchDetails[3]:
                    distance = ballpark.DistanceBetween(session.shipid, beaconID)
                    if not closestBeacon or distance < closestBeacon[1]:
                        closestBeacon = (beaconID, distance)

                self.centerItemIDEdit.SetValue(str(closestBeacon[0]))
                self.centerItemID = closestBeacon[0]
                self.arenaRadius = 125000
                self.arenaRadiusEdit.SetValue('125')
                svc = sm.GetService('allianceTournamentSvc')
                svc.StartTracking(self.centerItemID, self.arenaRadius)
        elif self.centerItemID is not None:
            svc = sm.GetService('allianceTournamentSvc')
            svc.StopTracking()
            self.centerItemID = None
        if 'solarsystemID' in matchState:
            if self.solarsystemID != matchState['solarsystemID']:
                self.solarsystemID = matchState['solarsystemID']
                self.redTeleportBeacon.LoadOptions(self.beaconOptions[self.solarsystemID][0])
                self.blueTeleportBeacon.LoadOptions(self.beaconOptions[self.solarsystemID][1])

        def CreateBanElement(typeID, parent, teamIdx):

            def RemoveBan(*args):
                self.matchMoniker.UnBanShipType(self.matchDetails[0], typeID, teamIdx)

            banContainer = uiprimitives.Container(name='banEle', parent=parent, align=uiconst.TOTOP, height=16)
            uicontrols.Button(label='X', parent=banContainer, func=RemoveBan, align=uiconst.TOLEFT)
            uicontrols.Label(text=cfg.invtypes[typeID].typeName, parent=banContainer, align=uiconst.TOLEFT)
            return banContainer

        if 'redTeamBans' in matchState:
            redBans = matchState['redTeamBans']
            keysToRemove = set(self.redBans.keys())
            for typeID in redBans:
                if typeID in keysToRemove:
                    keysToRemove.remove(typeID)
                if typeID not in self.redBans:
                    self.redBans[typeID] = CreateBanElement(typeID, self.redBanBox, 0)

            for typeID in keysToRemove:
                self.redBans[typeID].Close()
                del self.redBans[typeID]

        if 'blueTeamBans' in matchState:
            blueBans = matchState['blueTeamBans']
            keysToRemove = set(self.blueBans.keys())
            for typeID in blueBans:
                if typeID in keysToRemove:
                    keysToRemove.remove(typeID)
                if typeID not in self.blueBans:
                    self.blueBans[typeID] = CreateBanElement(typeID, self.blueBanBox, 1)

            for typeID in keysToRemove:
                self.blueBans[typeID].Close()
                del self.blueBans[typeID]

        if 'autoBanText' in matchState:
            autoBanText = matchState['autoBanText']
            self.autoBanText.text = autoBanText
        updatePilotDisplay = False
        if 'redTeamDetails' in matchState:
            self.matchDetails[1] = matchState['redTeamDetails']
            updatePilotDisplay = True
        if 'blueTeamDetails' in matchState:
            self.matchDetails[2] = matchState['blueTeamDetails']
            updatePilotDisplay = True
        if updatePilotDisplay:
            self.UpdateShipPilotDisplay()
        if 'redTeamLocked' in matchState:
            if matchState['redTeamLocked']:
                self.redLockBtn.state = uiconst.UI_HIDDEN
                self.redUnlockBtn.state = uiconst.UI_NORMAL
                self.redOverFleetBtn.state = uiconst.UI_HIDDEN
                self.redAddPlayerBtn.state = uiconst.UI_NORMAL
                self.redTeleportBtn.state = uiconst.UI_NORMAL
                self.redTeleportBeacon.state = uiconst.UI_NORMAL
            else:
                self.redLockBtn.state = uiconst.UI_NORMAL
                self.redUnlockBtn.state = uiconst.UI_HIDDEN
                self.redOverFleetBtn.state = uiconst.UI_NORMAL
                self.redAddPlayerBtn.state = uiconst.UI_HIDDEN
                self.redTeleportBtn.state = uiconst.UI_HIDDEN
                self.redTeleportBeacon.state = uiconst.UI_HIDDEN
        if 'blueTeamLocked' in matchState:
            if matchState['blueTeamLocked']:
                self.blueLockBtn.state = uiconst.UI_HIDDEN
                self.blueUnlockBtn.state = uiconst.UI_NORMAL
                self.blueOverFleetBtn.state = uiconst.UI_HIDDEN
                self.blueAddPlayerBtn.state = uiconst.UI_NORMAL
                self.blueTeleportBtn.state = uiconst.UI_NORMAL
                self.blueTeleportBeacon.state = uiconst.UI_NORMAL
            else:
                self.blueLockBtn.state = uiconst.UI_NORMAL
                self.blueUnlockBtn.state = uiconst.UI_HIDDEN
                self.blueOverFleetBtn.state = uiconst.UI_NORMAL
                self.blueAddPlayerBtn.state = uiconst.UI_HIDDEN
                self.blueTeleportBtn.state = uiconst.UI_HIDDEN
                self.blueTeleportBeacon.state = uiconst.UI_HIDDEN
        if 'warpRestrict' in matchState:
            self.playersCanWarp = not matchState['warpRestrict']
            if self.playersCanWarp:
                self.pregameWarpStatus.text = "Player warping: <color='green'>Allowed</color>"
            else:
                self.pregameWarpStatus.text = "Player warping: <color='red'>Disallowed</color>"
        if 'moveRestrict' in matchState:
            self.playersCanMove = not matchState['moveRestrict']
            if self.playersCanMove:
                self.pregameMoveStatus.text = "Player movement: <color='green'>Allowed</color>"
            else:
                self.pregameMoveStatus.text = "Player movement: <color='red'>Disallowed</color>"
        if 'lockRestrict' in matchState:
            self.playersCanLock = not matchState['lockRestrict']
            if self.playersCanLock:
                self.pregameLockStatus.text = "Player locking: <color='green'>Allowed</color>"
            else:
                self.pregameLockStatus.text = "Player locking: <color='red'>Disallowed</color>"
        if matchState['state'] in (STATE_PREGAME, STATE_WARPIN):
            self.resetButton.state = uiconst.UI_NORMAL
        else:
            self.resetButton.state = uiconst.UI_HIDDEN

    def LookupBanChars(self, *args):
        try:
            self.autoBanRedCharName.text = cfg.eveowners.Get(int(self.autoBanRedCharID.GetValue())).ownerName
        except Exception:
            self.autoBanRedCharName.text = '?'

        try:
            self.autoBanBlueCharName.text = cfg.eveowners.Get(int(self.autoBanBlueCharID.GetValue())).ownerName
        except Exception:
            self.autoBanRedCharName.text = '?'

    def Autobans(self, *args):
        self.matchMoniker.StartAutobanning(self.matchDetails[0], redCharID=int(self.autoBanRedCharID.GetValue()), blueCharID=int(self.autoBanBlueCharID.GetValue()))

    def FinalizeBans(self, *args):
        self.matchMoniker.FinalizeBans(self.matchDetails[0])

    def SendBan(self, teamIdx, comboBox, *args):
        curBans = self.matchMoniker.BanShipType(self.matchDetails[0], comboBox.GetValue(), teamIdx)

    def ToggleLocks(self, *args):
        self.matchMoniker.OverrideLockRestrict(self.matchDetails[0], self.playersCanLock)

    def ToggleWarping(self, *args):
        self.matchMoniker.OverrideWarpRestrict(self.matchDetails[0], self.playersCanWarp)

    def ToggleMovement(self, *args):
        self.matchMoniker.OverrideMoveRestrict(self.matchDetails[0], self.playersCanMove)

    def CompleteShipPilotCheck(self, *args):
        problems = []
        tharWereErrors = False
        if self.redLockBtn.state != uiconst.UI_HIDDEN:
            problems.append('Red team membership not locked')
        if self.blueLockBtn.state != uiconst.UI_HIDDEN:
            problems.append('Blue team membership not locked')
        for teamIdx in (1, 2):
            for charID, shipType, shipID, locationID, pointVal, errors in self.matchDetails[teamIdx]:
                if errors:
                    tharWereErrors = True
                if locationID != self.solarsystemID:
                    problems.append("%s doesn't look like they're here" % (cfg.eveowners[charID].ownerName,))

        if tharWereErrors:
            problems.append('Errors remain')
        if problems:
            ret = eve.Message('CustomQuestion', {'header': "This doesn't seem right",
             'question': 'The following problems remain:<br><br>' + '<br>'.join(problems) + '<br><br>Ignore and get this party started?'}, uiconst.YESNO)
            if ret != uiconst.ID_YES:
                return
        self.pregameStepOneText.text = "Step 1 - Let them warp, don't let them lock"
        self.pregameStepThreeText.text = 'Step 2 - Lock warping again'
        self.pregameStepFourText.text = 'Step 3 - Start Countdown'
        self.matchMoniker.CompletePregameChecks(self.matchDetails[0])

    def UpdatePregameRanges(self):
        bp = sm.GetService('michelle').GetBallpark()
        myBallID = session.shipid
        lines = []
        lines.append("<color='red'>" + self.redTeam)
        for charID, shipType, shipID, locationID, pointVal, errors in self.matchDetails[1]:
            try:
                dist = bp.DistanceBetween(myBallID, shipID)
                lines.append("<color='red'> %.1fkm %s" % (dist / 1000.0, cfg.eveowners.Get(charID).ownerName))
            except:
                lines.append("<color='red'> -- %s" % (cfg.eveowners.Get(charID).ownerName,))

        lines.append("<color='blue'>" + self.blueTeam)
        for charID, shipType, shipID, locationID, pointVal, errors in self.matchDetails[2]:
            try:
                dist = bp.DistanceBetween(myBallID, shipID)
                lines.append("<color='blue'> %.1fkm %s" % (dist / 1000.0, cfg.eveowners.Get(charID).ownerName))
            except:
                lines.append("<color='blue'> -- %s" % (cfg.eveowners.Get(charID).ownerName,))

        lines += [''] * (26 - len(lines))
        for idx, line in enumerate(lines):
            getattr(self, 'pregameDistance%d' % (idx,)).text = line

    def PreGameStepOne(self, *args):
        self.matchMoniker.OverrideLockRestrict(self.matchDetails[0], True)
        self.matchMoniker.OverrideWarpRestrict(self.matchDetails[0], False)
        self.pregameStepOneText.text = "<color='green'>%s</color>" % (self.pregameStepOneText.text,)

    def PreGameStepThree(self, *args):
        self.matchMoniker.OverrideWarpRestrict(self.matchDetails[0], True)
        self.pregameStepThreeText.text = "<color='green'>%s</color>" % (self.pregameStepThreeText.text,)

    def PreGameStepFour(self, *args):
        self.matchMoniker.StartCountdown(self.matchDetails[0])
        self.pregameStepFourText.text = "<color='green'>%s</color>" % (self.pregameStepFourText.text,)

    def UpdateTimer(self):
        timeDiffMS = max(0, -blue.os.TimeDiffInMs(self.matchStartTime, blue.os.GetWallclockTime()))
        self.countdownText.text = '%.1f' % (float(timeDiffMS) / 1000.0,)

    def AbortCountdown(self, *args):
        stopped = self.matchMoniker.AbortCountdown(self.matchDetails[0])
        if stopped:
            self.pregameStepFourText.text = 'Step 4 - Start Countdown'

    def MatchCompleted(self, *args):
        ret = eve.Message('CustomQuestion', {'header': 'Is it really over?',
         'question': 'Are you certain you want to prematurely end the match?'}, uiconst.YESNO)
        if ret != uiconst.ID_YES:
            return
        self.matchMoniker.MatchCompleted(self.matchDetails[0])
        self.postgameStepOneText.text = 'Step 1 - Send everyone back home'
        self.postgameStepTwoText.text = 'Step 2 - Clean up the grid'

    def PostGameStepOne(self, *args):
        self.matchMoniker.ReturnPlayers(self.matchDetails[0])
        self.postgameStepOneText.text = "<color='green'>%s</color>" % (self.postgameStepOneText.text,)

    def PostGameStepTwo(self, *args):
        self.matchMoniker.CleanupGrid(self.matchDetails[0])
        self.postgameStepTwoText.text = "<color='green'>%s</color>" % (self.postgameStepTwoText.text,)

    def OverrideFleetID(self, teamIdx, *args):
        format = [{'type': 'edit',
          'key': 'fleetid',
          'setfocus': True,
          'label': u'New FleetID'}]
        retVal = uix.HybridWnd(format, u'Specify new fleetID', minW=250, minH=100)
        if retVal:
            newFleetID = int(retVal['fleetid'])
            if newFleetID:
                self.matchMoniker.OverrideFleetID(self.matchDetails[0], teamIdx, newFleetID)

    def OverrideError(self, teamIdx, charID, errorString):
        ret = eve.Message('CustomQuestion', {'header': 'YOU FUCKING SURE DUDE?!?',
         'question': 'Override<br>%s<br>for pilot %s?' % (errorString, cfg.eveowners.Get(charID).ownerName)}, uiconst.YESNO)
        if ret != uiconst.ID_YES:
            return
        self.matchMoniker.OverrideError(self.matchDetails[0], charID, errorString)

    def RemovePlayer(self, teamIdx, charID):
        ret = eve.Message('CustomQuestion', {'header': "JUST CHECKIN'",
         'question': 'Remove %s from their team?' % cfg.eveowners.Get(charID).ownerName}, uiconst.YESNO)
        if ret != uiconst.ID_YES:
            return
        self.matchMoniker.RemovePlayer(self.matchDetails[0], teamIdx, charID)

    def GetPrematchPilotMenu(self, node):
        basePilotMenu = sm.GetService('menu').GetMenuFormItemIDTypeID(node.sr.node.id[1], const.typeCharacterAmarr)
        errorMenu = []
        for error in node.sr.node.errors:
            errorMenu.append(('Override: %s' % (error,), self.OverrideError, (node.sr.node.id[0], node.sr.node.id[1], error)))

        if errorMenu:
            errorMenu.append(None)
        errorMenu.append(('Remove Player', self.RemovePlayer, (node.sr.node.id[0], node.sr.node.id[1])))
        errorMenu.append(None)
        return errorMenu + basePilotMenu

    def UpdateShipPilotDisplay(self):
        redTeam = []
        pointTotal = 0
        for charID, shipType, shipID, locationID, pointVal, errors in self.matchDetails[1]:
            data = util.KeyVal(id=(0, charID), errors=errors, label='%s<t>%s<t>%s<t>%s<t><color=red>%s</color>' % (cfg.eveowners.Get(charID).ownerName,
             cfg.invtypes.Get(shipType).typeName,
             cfg.evelocations.Get(locationID).locationName,
             pointVal,
             ' - '.join(errors)), GetMenu=self.GetPrematchPilotMenu, hint='\n'.join(errors) if errors else 'No errors')
            listEntry = listentry.Get('Generic', data=data)
            redTeam.append(listEntry)
            pointTotal += pointVal

        self.shipcheckRedScroll.Load(contentList=redTeam, headers=['Name',
         'Ship Type',
         'Location',
         'Point Value',
         'Errors'], noContentHint='No pilots found')
        self.shipcheckRedTeamLabel.text = 'Red Team - %s - %d points' % (self.redTeam, pointTotal)
        blueTeam = []
        pointTotal = 0
        for charID, shipType, shipID, locationID, pointVal, errors in self.matchDetails[2]:
            data = util.KeyVal(id=(1, charID), errors=errors, label='%s<t>%s<t>%s<t>%s<t><color=red>%s</color>' % (cfg.eveowners.Get(charID).ownerName,
             cfg.invtypes.Get(shipType).typeName,
             cfg.evelocations.Get(locationID).locationName,
             pointVal,
             ' - '.join(errors)), GetMenu=self.GetPrematchPilotMenu, hint='\n'.join(errors) if errors else 'No errors')
            listEntry = listentry.Get('Generic', data=data)
            blueTeam.append(listEntry)
            pointTotal += pointVal

        self.shipcheckBlueScroll.Load(contentList=blueTeam, headers=['Name',
         'Ship Type',
         'Location',
         'Point Value',
         'Errors'], noContentHint='No pilots found')
        self.shipcheckBlueTeamLabel.text = 'Blue Team - %s - %d points' % (self.blueTeam, pointTotal)

    def RefreshShipPilotCheck(self, whichTeam, *args):
        self.matchMoniker.UpdateFleetDetails(self.matchDetails[0], whichTeam)

    def LockMemberList(self, whichTeam, *args):
        memberList = [ x[0] for x in self.matchDetails[whichTeam + 1] ]
        self.matchMoniker.LockMemberList(self.matchDetails[0], whichTeam, memberList)

    def UnlockMemberList(self, whichTeam, *args):
        self.matchMoniker.UnlockMemberList(self.matchDetails[0], whichTeam)

    def AddPlayer(self, whichTeam):
        format = [{'type': 'edit',
          'key': 'charid',
          'setfocus': True,
          'label': u'Char ID to add'}]
        retVal = uix.HybridWnd(format, u'Gimme a dude', minW=250, minH=100)
        if retVal:
            newCharID = int(retVal['charid'])
            if newCharID:
                self.matchMoniker.AddPlayer(self.matchDetails[0], whichTeam, newCharID)

    def TeleportPlayers(self, whichTeam, *args):
        if whichTeam == 0:
            beaconIdx = self.redTeleportBeacon.GetValue()
        else:
            beaconIdx = self.blueTeleportBeacon.GetValue()
        self.matchMoniker.TeleportPlayers(self.matchDetails[0], whichTeam, beaconIdx)

    def ResetMatch(self, *args):
        ret = eve.Message('CustomQuestion', {'header': 'Mildly Annoying',
         'question': 'Reseting is a moderate inconveniance, you sure you want that?'}, uiconst.YESNO)
        if ret != uiconst.ID_YES:
            return
        self.matchMoniker.ResetMatch(self.matchDetails[0])

    def OnToggleStart(self, *args):
        if self.isToggling:
            return
        try:
            self.isToggling = True
            self.centerItemID = int(self.centerItemIDEdit.GetValue())
            self.arenaRadius = int(self.arenaRadiusEdit.GetValue()) * 1000
            svc = sm.GetService('allianceTournamentSvc')
            if svc.isCompetitorsTrackingActive:
                svc.StopTracking()
                self.startButton.SetLabel('Start')
            else:
                svc.StartTracking(self.centerItemID, self.arenaRadius)
                self.startButton.SetLabel('Stop')
        finally:
            self.isToggling = False

    def UpdateColumnSort(self, scroll, entries, columnID):
        if not entries:
            return
        startIdx = entries[0].idx
        endIdx = entries[-1].idx
        entries = listentry.SortColumnEntries(entries, columnID)
        scroll.sr.nodes = scroll.sr.nodes[:startIdx] + entries + scroll.sr.nodes[endIdx + 1:]
        idx = 0
        for entry in scroll.GetNodes()[startIdx:]:
            if entry.panel:
                uiutil.SetOrder(entry.panel, -1)
            entry.idx = startIdx + idx
            if entry.Get('needReload', 0) and entry.panel:
                entry.panel.LoadLite(entry)
            idx += 1

    def OnCompetitorTrackingUpdate(self, competitorsByShipID):
        scrolllist = []
        for node in self.scroll.GetNodes():
            data = competitorsByShipID.get(node.shipID, None)
            if data:
                distance = '%0.1f km' % (data.distance * 0.001)
                maxDistance = '%0.1f km' % (data.maxDistance * 0.001)
                if distance != node.texts.distance:
                    node.needReload = True
                    node.texts = node.texts._replace(distance=distance, maxDistance=maxDistance)
                    node.sortData = node.sortData._replace(distance=data.distance, maxDistance=data.maxDistance)
                if data.maxDistance > self.arenaRadius:
                    node.panel.warn.state = uiconst.UI_DISABLED
                    if data.shipLost:
                        node.overlay.state = uiconst.UI_HIDDEN
                    else:
                        node.overlay.state = uiconst.UI_PICKCHILDREN
                scrolllist.append(node)

        self.UpdateColumnSort(self.scroll, scrolllist, 'AtCompetitorsScroll')

    def OnCompetitorTrackingStart(self, competitorsByShipID):
        scrolllist = []
        for shipData in competitorsByShipID.values():
            data = util.KeyVal()
            data.shipID = shipData.shipID
            data.texts = EntryRow(character=shipData.ownerName, groupName=shipData.groupName, typeName=shipData.typeName, maxDistance='%.1f km' % (shipData.maxDistance * 0.001), distance='%.1f km' % (shipData.distance * 0.001))
            data.sortData = EntryRow(character=shipData.ownerName, groupName=shipData.groupName, typeName=shipData.typeName, maxDistance=shipData.maxDistance, distance=shipData.distance)
            data.columnID = 'AtCompetitorsScroll'
            data.isSelected = False
            data.GetMenu = lambda x: sm.GetService('menu').GetMenuFormItemIDTypeID(shipData.shipID, shipData.typeID)
            iconPar = uiprimitives.Container(name='iconParent', parent=None, align=uiconst.TOPLEFT, width=16, height=16, state=uiconst.UI_HIDDEN)
            icon = uicontrols.Icon(parent=iconPar, icon='ui_38_16_182', pos=(0, 0, 16, 16), align=uiconst.RELATIVE)
            icon.hint = 'Destroy Ship'
            icon.shipID = shipData.shipID
            icon.OnClick = (self.DestroyShip, icon)
            data.overlay = iconPar
            entry = listentry.Get('AtCompetitorEntry', data=data)
            scrolllist.append(entry)

        scrolllist = listentry.SortColumnEntries(scrolllist, 'AtCompetitorsScroll')
        data = util.KeyVal()
        data.texts = ('Character', 'Group', 'Type', 'Max Distance', 'Distance')
        data.columnID = 'AtCompetitorsScroll'
        data.editable = True
        data.showBottomLine = True
        data.selectable = False
        data.hilightable = False
        scrolllist.insert(0, listentry.Get('AtCompetitorEntry', data=data))
        if scrolllist:
            listentry.InitCustomTabstops('AtCompetitorsScroll', scrolllist)
            self.scroll.LoadContent(contentList=scrolllist)

    def DestroyShip(self, button):
        svc = sm.GetService('allianceTournamentSvc')
        shipData = svc.competitorsByShipID[button.shipID]
        header = 'Destroy Ship'
        warning = 'Are you sure you want to destroy this ship?<br /><br />Character: <b>%s</b><br />Type: <b>%s</b>' % (shipData.ownerName, shipData.typeName)
        if eve.Message('CustomWarning', {'header': header,
         'warning': warning}, uiconst.YESNO) == uiconst.ID_YES:
            sm.GetService('slash').SlashCmd('/heal %d 0' % button.shipID)
            channelID = (('solarsystemid2', session.solarsystemid2),)
            message = u'<url=showinfo:%d>%s</url> piloted by <url=showinfo:1377//%s>%s</url> has been disqualified for boundary violations.' % (shipData.typeID,
             shipData.typeName,
             shipData.charID,
             shipData.ownerName)
            c = sm.StartService('LSC').GetChannelWindow(channelID[0])
            c.Speak(message, eve.session.charid, localEcho=True)
            sm.StartService('LSC').SendMessage(channelID, message)


class RefWindowSpawningWindow(uicontrols.Window):
    __guid__ = 'form.RefWindowSpawningWindow'
    __neocommenuitem__ = (('Referee Tool Root', 'tournament'), True, service.ROLE_GML)
    default_windowID = 'tournament'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.height = 90
        self.width = 150
        self.SetScope('all')
        self.SetWndIcon(None)
        self.SetCaption('Match Starter')
        self.SetTopparentHeight(0)
        self.SetMinSize([self.width, self.height])
        self.MakeUnResizeable()
        self.ConstructLayout()
        self.nextWndIDNum = 0

    def ConstructLayout(self):
        uicontrols.Button(label='Create New Match', parent=self.sr.main, padding=(5, 5, 5, 5), func=self.NewMatch, align=uiconst.TOTOP)

    def NewMatch(self, *args):
        form.TournamentRefereeTool.Open(windowID='TournamentRefereeTool%d' % (self.nextWndIDNum,))
        self.nextWndIDNum += 1


class AllianceTournamentSvc(service.Service):
    __guid__ = 'svc.allianceTournamentSvc'
    __neocommenuitem__ = (('Tournament Refree Tool', None), 'Show', service.ROLE_GML)
    __dependencies__ = ['michelle']

    def Run(self, *args):
        self.isCompetitorsTrackingActive = False
        self.competitorsByShipID = {}

    def Show(self):
        form.RefWindowSpawningWindow.Open()

    def StartTracking(self, centerItemID, arenaRadius):
        self.LogInfo('Start tracking arena center item', centerItemID, 'using a radius of', arenaRadius, 'meters')
        self.centerItemID = centerItemID
        self.arenaRadius = arenaRadius
        uthread.new(self.MonitorCompetitorsTask).context = 'at::competitortracking'

    def StopTracking(self):
        self.LogInfo('Stop tracking competitors')
        self.isCompetitorsTrackingActive = False
        self.competitorsByShipID = {}
        sm.ScatterEvent('OnCompetitorTrackingStart', {})

    def RegisterCompetitors(self):
        self.competitorsByShipID = {}
        ballpark = self.michelle.GetBallpark()
        for ball, slim in ballpark.GetBallsAndItems():
            if ball.id != session.shipid and slim.categoryID == const.categoryShip and slim.groupID != const.groupCapsule and slim.charID:
                distance = ballpark.DistanceBetween(self.centerItemID, ball.id)
                if distance is None or distance >= self.arenaRadius:
                    continue
                data = util.KeyVal(charID=slim.ownerID, shipID=ball.id, typeID=slim.typeID, groupID=slim.groupID, ownerName=cfg.eveowners.Get(slim.ownerID).ownerName, typeName=cfg.invtypes.Get(slim.typeID).typeName, groupName=cfg.invgroups.Get(slim.groupID).groupName, distance=distance, maxDistance=distance, shipLost=False)
                self.competitorsByShipID[ball.id] = data

        sm.ScatterEvent('OnCompetitorTrackingStart', self.competitorsByShipID)

    def MonitorCompetitorsTask(self):
        if self.isCompetitorsTrackingActive:
            return
        try:
            self.RegisterCompetitors()
            self.isCompetitorsTrackingActive = True
            self.LogInfo('Starting monitoring task')
            while self.isCompetitorsTrackingActive:
                blue.pyos.synchro.SleepWallclock(500)
                ballpark = sm.GetService('michelle').GetBallpark()
                ball = ballpark.GetBall(self.centerItemID)
                if not ball:
                    self.LogInfo('We lost the center ball.  Must abort tracking')
                    self.StopTracking()
                for shipID, data in self.competitorsByShipID.iteritems():
                    ball = ballpark.GetBall(shipID)
                    if ball:
                        data.distance = ballpark.DistanceBetween(self.centerItemID, shipID)
                        data.maxDistance = max(data.maxDistance, data.distance)
                    else:
                        data.shipLost = True

                sm.ScatterEvent('OnCompetitorTrackingUpdate', self.competitorsByShipID)

        finally:
            self.isCompetitorsTrackingActive = False
            self.LogInfo('Stopping monitoring task')
