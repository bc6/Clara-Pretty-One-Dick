#Embedded file name: industry\facility.py
import industry
import collections

class Facility(industry.Base):
    """
    A facility is a location at which jobs can be installed. Each facility contains static
    modifies as well as values can be modified at runtime.
    """

    def __init__(self, facilityID = None, typeID = None, ownerID = None, solarSystemID = None, tax = None, distance = None, modifiers = None, online = True):
        self.facilityID = facilityID
        self.typeID = typeID
        self.ownerID = ownerID
        self.solarSystemID = solarSystemID
        self.tax = tax
        self.distance = distance if distance is not None else None
        self.activities = collections.defaultdict(lambda : {'blueprints': set(),
         'categories': set(),
         'groups': set()})
        self.modifiers = modifiers or []
        self.online = online

    def __repr__(self):
        return industry.repr(self, exclude=['activities'])

    def update_activity(self, activityID, blueprints = None, categories = None, groups = None):
        """
        Adds an activity to this facility. Blueprints is a set of typeIDs identifying the
        blueprints that we are allowing to be installed at this facility for this activity.
        Groups and categories summarize the types available but don't strictly define them.
        """
        self.activities[activityID]['blueprints'].update(blueprints or [])
        self.activities[activityID]['categories'].update(categories or [])
        self.activities[activityID]['groups'].update(groups or [])
