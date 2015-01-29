#Embedded file name: workers\teams.py
from collections import OrderedDict
from carbon.common.lib.const import DAY
from workers.specializationGroups import SPECIALIZATION_GROUPS
from workers import SPECIALIZATION_TREE, TEAM_EXPIRY_TIME, ACT_MANUFACTURING, ACT_TIMERESEARCH, ACT_MATERIALRESEARCH, ACT_COPYING
from workers.qualityEffects import QUALITY_MATERIAL_EFFECTS, QUALITY_TIME_EFFECTS, TIME_EFFICIENCY, MATERIAL_EFFICIENCY, RESEARCH_TIME_EFFECTS

class Worker(object):

    def __init__(self, specializationID, quality, bonusType, activity):
        self.tier = SPECIALIZATION_TREE[specializationID].tier
        self.specializationID = specializationID
        self.quality = quality
        self.bonusType = bonusType
        if activity == ACT_MANUFACTURING:
            if bonusType == MATERIAL_EFFICIENCY:
                self.qualityEffects = QUALITY_MATERIAL_EFFECTS
            elif bonusType == TIME_EFFICIENCY:
                self.qualityEffects = QUALITY_TIME_EFFECTS
        elif activity in (ACT_TIMERESEARCH, ACT_MATERIALRESEARCH, ACT_COPYING):
            self.qualityEffects = RESEARCH_TIME_EFFECTS

    def GetBonusType(self):
        return (('TE', 'ME')[self.bonusType], self.GetBonus())

    def GetBonus(self):
        return self.qualityEffects[self.quality, self.tier]

    def GetSpecializationBonus(self, groupID):
        if groupID in SPECIALIZATION_GROUPS[self.specializationID]:
            return (self.bonusType, self.specializationID, self.GetBonus())
        return (None, 0)

    def IsMaterialModifier(self):
        return self.bonusType == MATERIAL_EFFICIENCY


class Team(object):

    def __str__(self):
        return 'TEAM: %s, members: %s, systemID: %s, spec1: %s(%s), spec2: %s(%s), spec3: %s(%s), spec4: %s(%s)' % (self.teamID,
         len(self.teamMembers),
         self.solarSystemID,
         self.teamMembers[0].specializationID,
         self.teamMembers[0].quality,
         self.teamMembers[1].specializationID,
         self.teamMembers[1].quality,
         self.teamMembers[2].specializationID,
         self.teamMembers[2].quality,
         self.teamMembers[3].specializationID,
         self.teamMembers[3].quality)

    def __init__(self, teamID, activity, specialization, members, systemID, creationTime, nameInfo):
        self.teamID = teamID
        self.activity = activity
        self.solarSystemID = systemID
        self.teamMembers = members
        self.creationTime = creationTime
        self.nameInfo = nameInfo
        self.specialization = specialization
        self.specializationID = specialization.specializationID

    def GetBonusList(self, groupID):
        bonuses = []
        for worker in self.teamMembers:
            bonus = worker.GetSpecializationBonus(groupID)
            if bonus[1] > 0:
                bonuses.append(bonus)

        return bonuses

    def GetBonus(self, bonusType, groupID):
        bonus = 0
        for worker in self.teamMembers:
            b = worker.GetSpecializationBonus(groupID)
            if b[0] == bonusType:
                bonus += b[2]

        return bonus

    def GetAllBonuses(self):
        bonuses = []
        for worker in self.teamMembers:
            bonuses.append((worker.bonusType, worker.qualityEffects[worker.quality, worker.tier], SPECIALIZATION_GROUPS[worker.specializationID]))

        return bonuses

    def GetMaterialBonus(self, groupID):
        return self.GetBonus(MATERIAL_EFFICIENCY, groupID)

    def GetTimeBonus(self, groupID):
        return self.GetBonus(TIME_EFFICIENCY, groupID)

    def UpdateSolarSystemID(self, solarSystemID):
        self.solarSystemID = solarSystemID

    def GetSpecialization(self):
        return self.specialization

    def GetCostModifier(self):
        q = 0
        for worker in self.teamMembers:
            q += worker.quality

        return q - 2

    def GetNameInfo(self):
        return self.nameInfo

    def GetExpiryTime(self):
        return self.creationTime + TEAM_EXPIRY_TIME * DAY

    def IsValidForGroup(self, groupID):
        for worker in self.teamMembers:
            if groupID in SPECIALIZATION_GROUPS[worker.specializationID]:
                return True

        return False


class Teams(object):

    def __init__(self):
        self.teamsByTeamID = OrderedDict()

    def GetLastTeamCreationTime(self):
        if len(self.teamsByTeamID.values()) > 0:
            return self.teamsByTeamID.values()[-1].creationTime

    def AddTeam(self, team):
        self.teamsByTeamID[team.teamID] = team

    def RemoveTeams(self, teamIDs):
        for teamID in teamIDs:
            del self.teamsByTeamID[teamID]

    def GetNumberOfTeams(self):
        return len(self.teamsByTeamID)

    def GetTeamByID(self, teamID):
        return self.teamsByTeamID[teamID]

    def GetTeams(self):
        return self.teamsByTeamID.values()

    def UpdateTeamSolarSystemID(self, teamID, solarSystemID):
        self.teamsByTeamID[teamID].UpdateSolarSystemID(solarSystemID)

    def GetTeamNameInfo(self, teamID):
        return self.teamsByTeamID[teamID].GetNameInfo()

    def GetSolarSystemIDByTeamID(self, teamID):
        return self.teamsByTeamID[teamID].solarSystemID

    def GetTeamsMoreRecentThan(self, time):
        teams = []
        for teamID, team in reversed(self.teamsByTeamID.items()):
            if team.creationTime > time:
                teams.append(team)

        return teams

    def GetMostRecentlyAddedTeam(self):
        return self.teamsByTeamID.values()[0]

    def HasTeam(self, teamID):
        return teamID in self.teamsByTeamID
