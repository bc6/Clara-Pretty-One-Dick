#Embedded file name: notifications/client/development\notificationDevUI.py
from notifications.common.notification import SimpleNotification
from eve.client.script.ui.control.eveWindow import Window
from eve.client.script.ui.control.buttons import Button
from carbonui.primitives.container import Container
from notifications.client.generator.notificationGenerator import NotificationGenerator
from notifications.client.controls.notificationSettingsWindow import NotificationSettingsWindow
from notifications.client.development.skillHistoryProvider import SkillHistoryProvider
import carbonui.const as uiconst

class NotificationDevWindow(Window):
    default_caption = 'Notification Debug window'
    default_windowID = 'NotificationDevWindow2'
    default_width = 300
    default_height = 300
    default_topParentHeight = 0

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.mainContainer = NotificationDevMainContainer(name='mainContainer', align=uiconst.TOALL, parent=self.GetMainArea())


class NotificationDevMainContainer(Container):

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes=attributes)
        self.generateButton = Button(name='generationStartButton', align=uiconst.TOTOP, label='start Generating', func=self.OnGenerateButtonClicked, pos=(0, 20, 100, 20), parent=self)
        self.fillSkillHistoryBtn = Button(name='fillSkillHistory', align=uiconst.TOTOP, label='skillHistory()', func=self.OnSkillDevClick, pos=(0, 5, 100, 20), parent=self)
        self.makeAllNotificationsBtn = Button(name='MakeAllNotifications', align=uiconst.TOTOP, label='MakeAllNotifications()', func=self.OnMakeAllNotificationClick, pos=(0, 5, 100, 20), parent=self)
        self.displayNotificationSettingBtn = Button(name='NotificationSettingsWindowButton', align=uiconst.TOTOP, label='Notification Settings window', func=self.OnDisplayNotificationSettingClick, pos=(0, 5, 100, 20), parent=self)
        self.toggleEnabledFlagBtn = Button(name='NotificationSettingsWindowButton', align=uiconst.TOTOP, label='Toggle enabled', func=self.OnToggleEnabledClick, pos=(0, 5, 100, 20), parent=self)
        self.toggleEnabledDevModeFlagBtn = Button(name='DevToggleButton', align=uiconst.TOTOP, label='Toggle developermode', func=self.OnDevToggleButtonClick, pos=(0, 5, 100, 20), parent=self)
        self.isGenerating = False
        self.MakeNewGenerator()

    def OnDevToggleButtonClick(self, *args):
        sm.GetService('notificationUIService').ToggleDeveloperMode()

    def OnToggleEnabledClick(self, *args):
        service = sm.GetService('notificationUIService')
        service.ToggleEnabledFlag()

    def OnDisplayNotificationSettingClick(self, *args):
        NotificationSettingsWindow.ToggleOpenClose()

    def OnMakeAllNotificationClick(self, *args):
        notificationMaker = FakeNotificationMaker()
        notificationMaker.MakeAndScatterAllClassicNotifications()

    def fakeNotification(self, typeID):
        newNotification = Notification(notificationID=1345)

    def OnSkillDevClick(self, *args):
        provider = SkillHistoryProvider()
        provider.provide()

    def OnMakeNewGeneratorClicked(self, *args):
        if self.notificationGenerator:
            self.notificationGenerator.Stop()
        self.MakeNewGenerator()

    def adjustLabel(self):
        if self.isGenerating:
            self.generateButton.SetLabel('Stop generating')
        else:
            self.generateButton.SetLabel('Start generating')

    def MakeNewGenerator(self):
        self.notificationGenerator = NotificationGenerator()

    def OnGenerateButtonClicked(self, *args):
        self.isGenerating = not self.isGenerating
        if self.isGenerating:
            sm.GetService('notificationUIService').SpawnFakeNotifications()
        else:
            sm.GetService('notificationUIService').notificationGenerator.Stop()
        self.adjustLabel()


import eve.common.script.util.notificationUtil as notificationUtil
import eve.common.script.util.notificationconst as notificationConst
import blue
import sys
from eve.client.script.ui.services.mail.notificationSvc import Notification

class FakeNotificationMaker:

    def MakeFakeData(self, senderID = 98000002):
        data = {}
        data['addCloneInfo'] = 1
        data['againstID'] = 98000002
        data['agentLocation'] = {3: 10000037,
         4: 20000443,
         5: 30003029,
         15: 60011125}
        data['aggressorCorpID'] = 98000002
        data['aggressorID'] = 98000001
        data['allianceID'] = 99000002
        data['allyID'] = 98000001
        data['amount'] = 6666
        data['armorValue'] = 0.2
        data['attackerID'] = 90000002
        data['billTypeID'] = 1
        data['body'] = 'This Is a body'
        data['bounty'] = 666
        data['bountyPlacerID'] = 98000001
        data['celestialIndex'] = 1
        data['characterID'] = 90000001
        data['charID'] = 90000001
        data['charRefID'] = 90000001
        data['charsInCorpID'] = [90000001]
        data['cloneStationID'] = 60012415
        data['corpID'] = senderID
        data['corporationID'] = senderID
        data['corpsPresent'] = ''
        data['corpStationID'] = 60012415
        data['cost'] = 12456
        data['creditorID'] = 98000001
        data['debtorID'] = 90000003
        data['declaredByID'] = senderID
        data['defenderID'] = 98000001
        data['disqualificationType'] = 9
        data['districtIndex'] = 1
        data['enemyID'] = 90000001
        data['entityID'] = 90000001
        data['errorText'] = 'THIS IS AN ERROR TEXT'
        data['event'] = 373
        data['factionID'] = 3
        data['header'] = 'THIS IS A BULLSHIT HEADER'
        data['hours'] = 667
        data['iskValue'] = 666
        data['itemRefID'] = 1
        data['level'] = 5
        data['locationID'] = 60012415
        data['locationOwnerID'] = 30005031
        data['lostList'] = None
        data['medalID'] = 132919
        data['mercID'] = 90000001
        data['messageIndex'] = 1
        data['myIsk'] = 668
        data['newOwnerID'] = 90000004
        data['newRank'] = 'Your New rank'
        data['offeredID'] = 90000001
        data['offeringID'] = 90000001
        data['oldOwnerID'] = 90000001
        data['ownerID'] = 90000001
        data['ownerID1'] = 90000001
        data['parameter'] = 98000001
        data['password'] = 'thisIsPassword'
        data['payout'] = 1231313
        data['planetID'] = 40318731
        data['planetTypeID'] = 1
        data['price'] = 45646456
        data['reason'] = 'This is a bullshit reason'
        data['reinforceExitTime'] = blue.os.GetWallclockTime() + 100000
        data['security'] = 3
        data['shieldValue'] = 0.8
        data['skillPointsLost'] = 669
        data['solarSystemID'] = 30005031
        data['standingsChange'] = 0.2
        data['startDate'] = blue.os.GetWallclockTime()
        data['startTime'] = blue.os.GetWallclockTime()
        data['state'] = 1
        data['stationID'] = 60012415
        data['subject'] = 'This is a subject'
        data['systemBids'] = (90000001, 1234)
        data['teamNameInfo'] = (1000144, 17740, 3767636)
        data['time'] = blue.os.GetWallclockTime()
        data['timeFinished'] = blue.os.GetWallclockTime()
        data['toEntityID'] = 90000001
        data['topTen'] = None
        data['totalIsk'] = 45646
        data['typeID'] = 17740
        data['typeIDs'] = None
        data['victimID'] = 90000001
        data['voteType'] = 1
        data['wants'] = None
        data['yourAmount'] = 6667
        data['hullValue'] = 0.9
        data['aggressorAllianceID'] = 99000002
        data['delayHours'] = 24
        data['hostileState'] = 1
        data['targetLocation'] = {3: 10000037,
         4: 20000443,
         5: 30003029,
         15: 60011125}
        return data

    def ScatterSingleNotification(self, counter, notificationId, senderID, someAgentID, someCorp):
        data = self.MakeFakeData(someCorp)
        aNotification = Notification(notificationID=counter + 10000000, typeID=notificationId, senderID=senderID, receiverID=90000001, processed=False, created=blue.os.GetWallclockTime() - counter * 10000, data=data)
        fsubject, fbody = notificationUtil.Format(aNotification)
        try:
            characterID = None
            corporationId = None
            if notificationId in notificationConst.groupTypes[notificationConst.groupAgents]:
                senderID = someAgentID
            if notificationId in notificationConst.groupTypes[notificationConst.groupCorp]:
                senderID = someCorp
            newNotification = SimpleNotification(subject=fsubject, created=blue.os.GetWallclockTime() - counter * 10000, notificationID=counter + 1000000, notificationTypeID=notificationId, senderID=senderID, body=fbody)
            sm.ScatterEvent('OnNewNotificationReceived', newNotification)
        except:
            print 'exception'
            print sys.exc_info()[0]

    def MakeAndScatterAllClassicNotifications(self):
        counter = 0
        onlyOneGroup = False
        whitelistedGroups = [notificationConst.groupAgents, notificationConst.groupCorp]
        useWhiteLists = False
        for notificationId, dict in notificationUtil.formatters.iteritems():
            if useWhiteLists:
                foundSomething = False
                for group in whitelistedGroups:
                    if notificationId in notificationConst.groupTypes[group]:
                        foundSomething = True

                if not foundSomething:
                    continue
            agentStartID = 3008416
            someAgentID = agentStartID + counter
            senderID = 98000001
            corpStartID = 1000089
            someCorp = corpStartID + counter
            self.ScatterSingleNotification(counter, notificationId, senderID, someAgentID, someCorp)
            counter = counter + 1
            blue.synchro.Yield()
