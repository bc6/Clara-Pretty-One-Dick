#Embedded file name: industry\team.py
import industry

class Team(industry.Base):
    """
    A team is a specialized workforce assigned to a job, they just contain modifiers which
    adjust the properties of a job.
    """

    def __init__(self, teamID, activityID = None, solarSystemID = None, modifiers = None, isInAuction = False):
        self.teamID = teamID
        self.activityID = activityID
        self.solarSystemID = solarSystemID
        self.modifiers = modifiers or []
        self.isInAuction = isInAuction
