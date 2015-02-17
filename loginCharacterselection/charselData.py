#Embedded file name: loginCharacterselection\charselData.py
"""
    This is a package for the character details you use in the character selection
"""
from itertoolsext import Bundle

class CharacterSelectionData:
    """
        class that keeps track of many characters' details
    """

    def __init__(self, charRemoteSvc, cfg, localization, uiutil):
        self.charRemoteSvc = charRemoteSvc
        self.cfg = cfg
        self.localization = localization
        self.uiutil = uiutil
        self.details = {}
        self.userDetails = None
        self.FetchCharacterInfoForUserID()

    def FetchCharacterInfoForUserID(self):
        if self.details:
            return None
        self.trainingDetails = (None, None)
        userDetails, self.trainingDetails, characterDetails = self.charRemoteSvc.GetCharacterSelectionData()
        self.userDetails = userDetails[0]
        for row in characterDetails:
            character = CharacterSelectionDataForCharacter(row.characterID, row, self.cfg, self.localization, self.uiutil)
            self.details[row.characterID] = character

    def GetCharInfo(self, charID):
        return self.details[charID]

    def GetNumCharacterSlots(self):
        return self.userDetails.characterSlots

    def GetUserName(self):
        return self.userDetails.userName

    def GetUserCreationDate(self):
        return self.userDetails.creationDate

    def GetChars(self):
        chars = [ data.charDetails for data in self.details.itervalues() ]
        chars.sort(key=lambda x: x.logoffDate, reverse=True)
        return chars

    def GetSubscriptionEndTime(self):
        return Bundle(subscriptionEndTime=self.userDetails.subscriptionEndTime, trainingEndTimes=self.trainingDetails)

    def GetMaxServerCharacters(self):
        return int(self.userDetails.maxCharacterSlots)


class CharacterSelectionDataForCharacter:
    """
        class that contains the details for each character
    """

    def __init__(self, charID, charDetails, cfg, localization, uiutil):
        self.charID = charID
        self.charDetails = charDetails
        self.cfg = cfg
        self.localization = localization
        self.uiutil = uiutil
        if charDetails.stationID:
            self.stationID = charDetails.stationID
            self.solarSystemID = self.cfg.stations.Get(self.stationID).solarSystemID
        elif charDetails.solarSystemID:
            self.stationID = None
            self.solarSystemID = charDetails.solarSystemID
        else:
            self.stationID = None
            self.solarSystemID = None
        if self.solarSystemID:
            self.securityStatus = self.cfg.mapSystemCache[self.solarSystemID].securityStatus
        else:
            self.securityStatus = 0.0

    def GetWalletBalance(self):
        balance = self.charDetails.balance
        return balance

    def GetSkillInfo(self):
        skillPoints = self.charDetails.skillPoints
        return skillPoints

    def GetCorporationInfo(self):
        return (self.charDetails.corporationID, self.charDetails.allianceID)

    def GetUnreaddMailCount(self):
        unreadMailCount = self.charDetails.unreadMailCount
        return unreadMailCount

    def GetUnreadNotificationCount(self):
        return self.charDetails.unprocessedNotifications

    def GetCurrentLocationInfo(self):
        if self.securityStatus > 0.0 and self.securityStatus < 0.05:
            securityStatus = 0.05
        else:
            securityStatus = self.securityStatus
        return (self.solarSystemID, securityStatus)

    def GetCurrentStation(self):
        return self.stationID

    def GetCurrentStationAndStationLocation(self):
        if self.stationID is None:
            return

        def CleanString(locationString):
            locationString = self.uiutil.StripTags(locationString, stripOnly=['localized'])
            locationString = locationString.replace(self.localization.HIGHLIGHT_IMPORTANT_MARKER, '')
            return locationString

        orbitID = self.cfg.stations.Get(self.stationID).orbitID
        orbitName = self.cfg.evelocations.Get(orbitID).name
        orbitName = CleanString(orbitName)
        solarsystemName = self.cfg.evelocations.Get(self.solarSystemID).name
        solarsystemName = CleanString(solarsystemName)
        shortOrbitName = orbitName.replace(solarsystemName, '').strip()
        moonText = self.localization.GetByLabel('UI/Locations/LocationMoonLong')
        shortOrbitName = shortOrbitName.replace(moonText, '').replace('  ', ' ')
        stationName = self.cfg.evelocations.Get(self.stationID).name
        stationName = CleanString(stationName)
        stationNameWithoutOrbit = stationName.replace(orbitName, '')
        stationNameWithoutOrbit = stationNameWithoutOrbit.strip(' - ')
        stationInfo = {'stationName': stationNameWithoutOrbit,
         'orbitName': orbitName,
         'shortOrbitName': shortOrbitName}
        return stationInfo

    def GetCurrentShip(self):
        return self.charDetails.shipTypeID

    def GetPaperDollState(self):
        return self.charDetails.paperdollState

    def GetPetitionMessage(self):
        return self.charDetails.petitionMessage

    def GetFinishedSkills(self):
        return self.charDetails.finishedSkills

    def GetWalletChanged(self):
        return self.charDetails.balanceChange

    def GetSkillInTrainingInfo(self):
        return {'currentSkill': self.charDetails.skillTypeID,
         'level': self.charDetails.toLevel,
         'trainingStartTime': self.charDetails.trainingStartTime,
         'trainingEndTime': self.charDetails.trainingEndTime,
         'queueEndTime': self.charDetails.queueEndTime,
         'finishSP': self.charDetails.finishSP,
         'trainedSP': self.charDetails.trainedSP,
         'fromSP': self.charDetails.fromSP}

    def GetDeletePrepareTime(self):
        return self.charDetails.deletePrepareDateTime

    def IsPreparingForDeletion(self):
        return bool(self.charDetails.deletePrepareDateTime)
