#Embedded file name: workers\teamLoader.py
from operator import attrgetter
from workers import TEAM_EXPIRY_TIME
from workers.qualityEffects import TIME_EFFICIENCY, MATERIAL_EFFICIENCY
from workers.teams import Team, Worker
from workers.util import GetSpecialization

def RegisterNames(nameGenerator, teamInfo):
    for teamRow in teamInfo:
        nameGenerator.RegisterName(teamRow.corporationID, teamRow.activity, teamRow.identifier[:3], int(teamRow.identifier[3:]))


def LoadTeamsFromDB(nameGenerator, persister, timer, teams, teamsInAuction, auction):
    teamInfo, workerInfo, bidInfo, bidTimeInfo = persister.GetAllTeamsInfo(TEAM_EXPIRY_TIME)
    auctionTeamRows = []
    teamRows = []
    for row in teamInfo:
        if row.inAuction:
            auctionTeamRows.append(row)
        else:
            teamRows.append(row)

    LoadTeams(teamRows, workerInfo, teams)
    LoadTeams(auctionTeamRows, workerInfo, teamsInAuction)
    LoadTeamsToAuction(auctionTeamRows, auction, timer)
    LoadBids(bidInfo, bidTimeInfo, auction)
    RegisterNames(nameGenerator, teamInfo)


def LoadTeams(teamInfo, workerInfo, teams):
    for row in _SortByTeamID(teamInfo):
        typeIdentifier = row.identifier[:3]
        uniqueId = row.identifier[3:]
        workers = [ Worker(w.specializationID, w.quality, MATERIAL_EFFICIENCY if w.isMaterialModifier else TIME_EFFICIENCY, row.activity) for w in workerInfo.get(row.teamID, []) ]
        team = Team(row.teamID, row.activity, GetSpecialization(row.speciality), workers, row.solarSystemID, row.creationTime, (row.corporationID, typeIdentifier, uniqueId))
        teams.AddTeam(team)


def LoadTeamsToAuction(teamInfo, auction, timer):
    for row in _SortByTeamID(teamInfo):
        auction.AddTeam(row.teamID, row.auctionID, row.auctionExpiryTime)


def _SortByTeamID(teamInfo):
    return sorted(teamInfo, key=attrgetter('teamID'))


def LoadBids(bidInfo, bidTimeInfo, auction):
    auction.LoadBids(bidInfo)
    auction.SetBidTimes(bidTimeInfo)
