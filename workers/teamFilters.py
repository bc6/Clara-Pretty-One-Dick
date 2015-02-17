#Embedded file name: workers\teamFilters.py
from workers.const import RANGE_SOLAR_SYSTEM, RANGE_REGION, RANGE_WORLD
FILTER_RANGE = 0
FILTER_SPECIALIZATION = 1
FILTER_GROUP = 2
FILTER_ACTIVITY = 3

class MultiFilter(object):

    def __init__(self, *filters):
        self.filters = filters

    def __call__(self, *args):
        return all((f(*args) for f in self.filters))


class RangeFilter(object):

    def __init__(self, rangeValue, solarSystemID, getRegion):
        self.rangeValue = rangeValue
        self.solarSystemID = solarSystemID
        self.getRegion = getRegion

    def __call__(self, team):
        return self.IsValid(team)

    def IsValid(self, team):
        if self.rangeValue == RANGE_SOLAR_SYSTEM:
            return team.solarSystemID == self.solarSystemID
        if self.rangeValue == RANGE_REGION:
            return self.getRegion(team.solarSystemID) == self.getRegion(self.solarSystemID)
        if self.rangeValue == RANGE_WORLD:
            return True
        raise RuntimeError('rangeValue for filter is incorrect')


class SpecializationFilter(object):

    def __init__(self, specializationID):
        self.specializationID = specializationID

    def __call__(self, team):
        return team.specializationID == self.specializationID


class GroupFilter(object):

    def __init__(self, groupID):
        self.groupID = groupID

    def __call__(self, team):
        return team.IsValidForGroup(self.groupID)


class ActivityFilter(object):

    def __init__(self, activityID):
        self.activityID = activityID

    def __call__(self, team):
        return team.activity == self.activityID


class FilterGenerator(object):

    def __init__(self, getRegion):
        self.getRegion = getRegion

    def Filter(self, filterArgs, teams):
        filters = []
        for filterType, args in filterArgs:
            if filterType == FILTER_RANGE:
                rangeType, solarSystemID = args
                filters.append(RangeFilter(rangeType, solarSystemID, self.getRegion))
            elif filterType == FILTER_SPECIALIZATION:
                filters.append(SpecializationFilter(*args))
            elif filterType == FILTER_GROUP:
                filters.append(GroupFilter(*args))
            elif filterType == FILTER_ACTIVITY:
                filters.append(ActivityFilter(*args))

        return filter(MultiFilter(*filters), teams.GetTeams())
