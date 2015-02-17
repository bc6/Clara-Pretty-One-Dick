#Embedded file name: industry\blueprint.py
import os
import fsdlite
import industry

class Blueprint(industry.Base):
    """
    A blueprint defines the inputs and outputs of manufacturing jobs. They themselves can
    also be the output of an industry jobs.
    """
    __metaclass__ = fsdlite.Immutable

    def __new__(cls, *args, **kwargs):
        obj = industry.Base.__new__(cls)
        obj.blueprintTypeID = None
        obj.maxProductionLimit = None
        obj.blueprintID = None
        obj.timeEfficiency = 0
        obj.materialEfficiency = 0
        obj.runsRemaining = -1
        obj.quantity = 1
        obj.original = True
        obj.facilityID = None
        obj.locationID = None
        obj.locationTypeID = None
        obj.locationFlagID = None
        obj.flagID = None
        obj.ownerID = None
        obj.jobID = None
        obj._activities = {}
        return obj

    def __repr__(self):
        return industry.repr(self, exclude=['_activities'])

    def _get_activities(self):
        return {activityID:activity for activityID, activity in self._activities.iteritems() if activity.is_compatible(self)}

    def _set_activities(self, value):
        if isinstance(value, list):
            value = {int(activity.activityID):activity for activity in value}
        self._activities = {int(industry.ACTIVITY_NAME_IDS.get(activityID, activityID)):activity for activityID, activity in (value or {}).iteritems()}

    activities = property(_get_activities, _set_activities)

    def _get_all_activities(self):
        return self._activities

    all_activities = property(_get_all_activities)

    def _get_typeID(self):
        return self.blueprintTypeID

    typeID = property(_get_typeID)

    def _get_itemID(self):
        return self.blueprintID

    itemID = property(_get_itemID)

    def _get_product(self):
        """
        The product on a blueprint is just the first product listed on the manufacturing activity.
        """
        try:
            return self.activities[industry.MANUFACTURING].products[0].typeID
        except (KeyError, IndexError):
            return None

    productTypeID = property(_get_product)

    def _get_location(self):
        """
        Returns a location object for comparison.
        """
        return industry.Location(itemID=self.locationID, flagID=self.locationFlagID, ownerID=self.ownerID, typeID=self.locationTypeID)

    location = property(_get_location)


def BlueprintStorage():
    """
    Returns a storage object for the autobuilt blueprint cache. Useful for utilities that
    just need access to the blueprint data from their branch.
    """
    data = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../eve/staticData/blueprints/*.staticdata'))
    cache = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../eve/autobuild/staticData/server/blueprints.db'))
    return fsdlite.Storage(data=data, cache=cache, mapping=industry.MAPPING, indexes=industry.INDEXES, monitor=True)
