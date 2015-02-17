#Embedded file name: workers\constructor.py
import random
from workers import TEAM_EXPIRY_TIME
from workers.auction import Auction
from workers.auctionNotifier import AuctionNotifier
from workers.eventLogger import EventLogger
from workers.iskMover import IskMover
from workers.namegenerator import NameGenerator
from workers.restricted.regionWeights import regionWeights
from workers.restricted.persister import Persister
from workers.restricted.spawner import Spawner, TeamKiller
from workers.restricted.systemPicker import SystemPicker
from workers.restricted.teamCreator import TeamManager
from workers.teamLoader import LoadTeamsFromDB
from workers.teams import Teams

def SetupTeamObjects(dbindustry, eventLog, account, notificationMgr, regionCache, timer):
    teams = Teams()
    teamsInAuction = Teams()
    persister = Persister(dbindustry)
    eventLogger = EventLogger(eventLog)
    auction = Auction(timer, persister, teamsInAuction, teams, IskMover(account), AuctionNotifier(notificationMgr, teams), eventLogger)
    nameGenerator = NameGenerator()
    teamCreator = TeamManager(random.randint, SystemPicker(regionWeights, regionCache), timer, teamsInAuction, nameGenerator, persister, auction)
    LoadTeamsFromDB(nameGenerator, persister, timer, teams, teamsInAuction, auction)
    teamSpawner = Spawner(teamCreator, timer)
    teamSpawner.StartWorker()
    teamKiller = TeamKiller(TEAM_EXPIRY_TIME, teams, timer, eventLogger)
    teamKiller.Start()
    return (teams,
     teamsInAuction,
     auction,
     teamSpawner,
     teamCreator,
     teamKiller)
