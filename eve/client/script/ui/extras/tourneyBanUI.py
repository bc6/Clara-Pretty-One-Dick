#Embedded file name: eve/client/script/ui/extras\tourneyBanUI.py
import service
import uiprimitives
import uicontrols
import carbonui.const as uiconst
import blue
import base
shipGroups = {25,
 28,
 420,
 541,
 831,
 324,
 893,
 834,
 26,
 419,
 1201,
 894,
 358,
 832,
 906,
 833,
 963,
 540,
 27,
 898,
 900}
shipTypes = {32207,
 3516,
 2834,
 17619,
 17926,
 17928,
 17932,
 17841,
 11940,
 17703,
 17812,
 11942,
 17924,
 17930,
 625,
 634,
 620,
 631,
 29337,
 17634,
 29344,
 11011,
 17709,
 29340,
 29336,
 17713,
 17843,
 17922,
 17720,
 17718,
 17715,
 17722,
 2836,
 32209,
 3518,
 32790,
 11936,
 17726,
 11938,
 32305,
 32307,
 17728,
 17636,
 32309,
 17732,
 32311,
 17738,
 17736,
 17920,
 17918,
 17740,
 617,
 33079,
 615,
 33081,
 33083}
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
 33643: 17634,
 33645: 17634,
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

class TourneyBanUISvc(service.Service):
    __guid__ = 'svc.tourneyBanUI'
    __notifyevents__ = ['OnTournamentPerformBan']

    def OnTournamentPerformBan(self, banID, numBans, curBans, deadline, respondToNodeID):
        self.LogInfo('OnTourneyBan recv', banID, numBans, curBans, deadline, respondToNodeID)
        TourneyBanUI.CloseIfOpen()
        banBox = TourneyBanUI.Open()
        banBox.Execute(banID, numBans, curBans, deadline, respondToNodeID)
        banBox.ShowModal()


class TourneyBanUI(uicontrols.Window):
    __guid__ = 'form.TourneyBanUI'
    default_alwaysLoadDefaults = True

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.SetCaption('Tournament Ban Prompt')
        self.SetMinSize((300, 375))
        self.SetTopparentHeight(0)

    def SetModalResult(self, result, caller = None):
        if result == uiconst.ID_OK:
            return
        super(TourneyBanUI, self).SetModalResult(result, caller)

    def Execute(self, banID, numBans, curBans, deadline, respondToNodeID):
        self.banID = banID
        self.deadline = deadline
        self.respondToNodeID = respondToNodeID
        self.resetButton = uicontrols.Button(label='Submit Ban' if numBans > 0 else 'Okay', parent=self.sr.main, align=uiconst.TOBOTTOM, func=self.Submit, state=uiconst.UI_NORMAL, padding=5)
        uicontrols.EveLabelLarge(text="Let's ban some ships!" if numBans > 0 else "Here's the bans:", parent=self.sr.main, align=uiconst.TOTOP, top=10, padding=5, color=(0.5, 0.5, 1, 1))
        uicontrols.Label(text='You have banned:', parent=self.sr.main, align=uiconst.TOTOP, top=5, padding=5)
        uicontrols.Label(text='<br>'.join([ cfg.invtypes[typeID].typeName for typeID in curBans[0] ]), padding=5, parent=self.sr.main, align=uiconst.TOTOP)
        uicontrols.Label(text='They have banned:', parent=self.sr.main, align=uiconst.TOTOP, top=5, padding=5)
        uicontrols.Label(text='<br>'.join([ cfg.invtypes[typeID].typeName for typeID in curBans[1] ]), padding=5, parent=self.sr.main, align=uiconst.TOTOP)
        banOptions = [('Pass', -1)] + sorted([ (x.typeName, x.typeID) for x in cfg.invtypes if (x.typeID in shipTypes or x.groupID in shipGroups) and not x.typeName.startswith('[no messageID:') and x.typeID not in skinEquivalents ])
        self.banChoices = []
        for banNum in xrange(numBans):
            self.banChoices.append(uicontrols.Combo(label='Ban: ', parent=self.sr.main, options=banOptions, top=20, padding=5, align=uiconst.TOTOP))

        if numBans > 0:
            banCont = uiprimitives.Container(name='banTimer', parent=self.sr.main, align=uiconst.TOTOP, height=50)
            self.countdownText = uicontrols.Label(parent=banCont, align=uiconst.CENTER, fontsize=36, color=(1, 0, 0, 1))
            self.countdownTimer = base.AutoTimer(100, self.UpdateTimer)
        uicore.registry.SetFocus(self)
        self.MakeUnKillable()

    def Submit(self, *args):
        machoNet = sm.GetService('machoNet')
        remoteTourneyMgr = machoNet.ConnectToRemoteService('tourneyMgr', self.respondToNodeID)
        banTypes = []
        for choice in self.banChoices:
            shipTypeToBan = choice.GetValue()
            if shipTypeToBan != -1:
                banTypes.append(shipTypeToBan)

        remoteTourneyMgr.BanShip(self.banID, banTypes)
        self.Close()

    def UpdateTimer(self):
        timeDiffMS = max(0, blue.os.TimeDiffInMs(blue.os.GetWallclockTime(), self.deadline))
        self.countdownText.text = '%.1f' % (float(timeDiffMS) / 1000.0,)
        if timeDiffMS == 0:
            self.MakeKillable()
            self.countdownTimer = None
