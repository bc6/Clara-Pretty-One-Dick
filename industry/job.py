#Embedded file name: industry\job.py
import math
import copy
import random
import fsdlite
import industry
import datetime
import operator

class JobBase(industry.Base):
    """
    Defines the common data properties for a Job and JobData class.
    """

    def __new__(cls, blueprint, activityID, *args, **kwargs):
        obj = industry.Base.__new__(cls)
        obj._blueprint = blueprint
        obj._activityID = activityID
        if obj.activity is None:
            raise RuntimeError('Invalid Activity for Blueprint')
        obj.jobID = None
        obj.characterID = None
        obj.corporationID = None
        obj.status = industry.STATUS_UNSUBMITTED
        obj.installerID = None
        obj.startDate = None
        obj.endDate = None
        obj._materials = copy.deepcopy(obj.activity.materials)
        obj._modifiers = []
        obj._skills = {}
        obj._slots = {}
        obj._distance = None
        obj._materialEfficiency = None
        obj._timeEfficiency = None
        obj._random = None
        obj.request = {}
        obj.prices = {}
        obj._modifiers_cache = None
        obj.on_validate = fsdlite.Signal()
        obj.on_updated = fsdlite.Signal()
        obj.on_errors = fsdlite.Signal()
        obj.on_delete = fsdlite.Signal()
        obj.on_facility = fsdlite.Signal()
        obj.on_input_location = fsdlite.Signal()
        obj.on_output_location = fsdlite.Signal()
        obj.on_dirty = fsdlite.Signal()
        obj.on_dirty.connect(obj.update)
        return obj

    def __repr__(self):
        return industry.repr(self, exclude=['_blueprint',
         '_facility',
         '_team',
         '_inputLocation',
         '_outputLocation',
         'on_delete',
         'on_validate',
         'on_dirty',
         'on_updated',
         'on_errors',
         'on_facility',
         'on_input_location',
         'on_output_location',
         '_materials',
         '_extras',
         '_locations',
         '_errors',
         '_request',
         'prices',
         'skills'])

    def update(self, job):
        self._modifiers_cache = None
        self.on_updated(self)

    modifiers = industry.Property('_modifiers', 'on_dirty')
    skills = industry.Property('_skills', 'on_dirty')
    slots = industry.Property('_slots', 'on_dirty')
    completed = property(lambda self: bool(self.status >= industry.STATUS_COMPLETED))

    def _get_random(self):
        """
        A cached random roll for things like job success or product selection.
        """
        if self._random is None:
            self._random = random.random()
        return self._random

    random = property(_get_random)

    def _get_blueprint(self):
        return self._blueprint

    blueprint = property(_get_blueprint)

    def _get_activityID(self):
        return self._activityID

    activityID = property(_get_activityID)

    def _get_activity(self):
        if self.activityID in self.blueprint._activities:
            return self.blueprint._activities[self.activityID]

    activity = property(_get_activity)

    def _get_runs_max(self):
        return self.activity.job_max_runs(self)

    maxRuns = property(_get_runs_max)

    def _get_licensed_runs_max(self):
        return self.blueprint.maxProductionLimit

    maxLicensedRuns = property(_get_licensed_runs_max)

    def _get_successful_runs(self):
        if self.completed:
            if self._successfulRuns is not None:
                return self._successfulRuns
            else:
                rand = random.Random()
                rand.seed(self.random)
                probabilities = [ rand.random() for i in range(self.runs) ]
                return len([ p for p in probabilities if p <= self.probability ])
        else:
            return self.runs

    successfulRuns = industry.Property('_successfulRuns', 'on_dirty', _get_successful_runs)

    def _get_base_cost(self):
        """
        Return the cost excluding any modifiers.
        """
        modifiers = [ modifier.amount for modifier in self.input_modifiers if isinstance(modifier, industry.CostModifier) and modifier.activity in (None, self.activityID) ]
        return int(round(self.cost / reduce(operator.mul, modifiers, 1.0)))

    base_cost = property(_get_base_cost)

    def _get_total_cost(self):
        """
        Returns the amount of tax required to pay to the facility owner.
        """
        return (self.cost or 0) + (self.tax or 0)

    total_cost = property(_get_total_cost)

    def _get_output(self):
        """
        Returns a list of the blueprints / materials that need constructing or modifying, including the
        final product provided it has been selected.
        """
        output = []
        if self.product:
            output.append(self.product)
        output += self.activity.job_output_extras(self)
        return output

    output = property(_get_output)

    def _get_products(self):
        """
        It is possible to have multiple possible outcomes for a job, this returns all the possibilities.
        """
        return self.activity.job_output_products(self)

    products = property(_get_products)

    def _get_product(self):
        """
        Returns the actual product to produce, in the case of multiple items it will pick
        the one selected if selectable, or a random one.
        """
        products = self.products
        if products:
            if len(products) == 1:
                return products[0]
            for product in products:
                if product.typeID == self.productTypeID:
                    return product

    def _set_product(self, value):
        """
        Sets the desired output product, if multiple are available.
        """
        products = self.products
        if not len(products):
            raise KeyError('Product is not selectable')
        if value is None:
            self.productTypeID = None
            return
        for product in products:
            if value in (product, product.typeID):
                self.productTypeID = product.typeID
                return

        raise KeyError('Invalid product option')

    product = property(_get_product, _set_product)

    def _get_materials(self):
        """
        Returns the materials required, not modified by runs or any other modifiers.
        """
        return self._materials + self.extras

    materials = property(_get_materials)

    def _get_optional_materials(self):
        """
        Returns the materials with optional selection.
        """
        return [ material for material in self.materials if len(material.options) ]

    optional_materials = property(_get_optional_materials)

    def _get_required_skills(self):
        """
        Returns the skills required for this jobs activity.
        """
        return self.activity.skills

    required_skills = property(_get_required_skills)

    def _get_all_skills(self):
        """
        Returns the list of skills that can affect this job.
        """
        return self.required_skills + [ industry.Skill(typeID=skill) for skill in industry.SKILLS ]

    all_skills = property(_get_all_skills)

    def _get_all_modifiers(self):
        """
        Modifiers can be applied to the job, the facility or the materials themselves.
        """
        if self._modifiers_cache is None:
            modifiers = []
            modifiers += self.modifiers
            modifiers += self.activity.job_modifiers(self)
            if self.facility:
                modifiers += self.facility.modifiers
            if self.team:
                modifiers += self.team.modifiers
            for material in JobBase._get_materials(self):
                modifiers += material.modifiers

            self._modifiers_cache = []
            for modifier in modifiers:
                if modifier.activity not in (None, self.activityID):
                    continue
                if modifier.blueprints and self.blueprint.blueprintTypeID not in modifier.blueprints:
                    continue
                self._modifiers_cache.append(modifier)

        return self._modifiers_cache

    all_modifiers = property(_get_all_modifiers)

    def _get_max_slots(self):
        """
        Return the maximum number of slots for this jobs activity.
        """
        count = 0
        for modifier in self.all_modifiers:
            if isinstance(modifier, industry.SlotModifier) and modifier.activity in (None, self.activityID):
                count += int(modifier.amount)

        return count

    max_slots = property(_get_max_slots)

    def _get_max_distance(self):
        """
        Return the maximum distance we can operate facilities from.
        """
        return industry.DISTANCE_PER_LEVEL.get(self.skills.get(industry.DISTANCE_SKILL_FOR_ACTIVITY.get(self.activityID), 0))

    max_distance = property(_get_max_distance)

    def _get_distance(self):
        """
        Returns the distance from the installer to the facility, as either defined
        on the facility or overridden on the job itself.
        """
        if self._distance is not None:
            return self._distance
        if self.facility and self.facility.distance is not None:
            return self.facility.distance

    distance = industry.Property('_distance', 'on_dirty', _get_distance)

    def _get_material_efficiency(self):
        """
        Returns either the overriden material efficiency of this job, or defaults to the blueprints ME
        """
        if self._materialEfficiency is not None:
            return self._materialEfficiency
        else:
            return self.blueprint.materialEfficiency

    materialEfficiency = industry.Property('_materialEfficiency', 'on_dirty', _get_material_efficiency)

    def _get_time_efficiency(self):
        """
        Returns either the overriden time efficiency of this job, or defaults to the blueprints TE
        """
        if self._timeEfficiency is not None:
            return self._timeEfficiency
        else:
            return self.blueprint.timeEfficiency

    timeEfficiency = industry.Property('_timeEfficiency', 'on_dirty', _get_time_efficiency)

    def _get_used_slots(self):
        """
        Returns the number of slots in use for the current activity.
        """
        return self.slots.get(self.activityID, 0)

    used_slots = property(_get_used_slots)

    def _get_input_modifiers(self):
        """
        Filters all the modifiers by whether they affect input.
        """
        return [ modifier for modifier in self.all_modifiers if modifier.output is False ]

    input_modifiers = property(_get_input_modifiers)

    def _get_output_modifiers(self):
        """
        Filters all the modifiers by whether they affect the output product.
        """
        return [ modifier for modifier in self.all_modifiers if modifier.output is True ]

    output_modifiers = property(_get_output_modifiers)


class JobData(JobBase):
    """
    A plain old python object which defines the interface for a job. We can use
    this as a basic data storage class, minus all of the dynamically calculated
    stuff a normal industry.Job class has.
    """

    def __new__(cls, blueprint, activity, *args, **kwargs):
        obj = JobBase.__new__(cls, blueprint, activity, *args, **kwargs)
        obj.ownerID = None
        obj.facility = None
        obj.facilityID = None
        obj.team = None
        obj.teamID = None
        obj.inputLocation = None
        obj.outputLocation = None
        obj.runs = 1
        obj.licensedRuns = 1
        obj.productTypeID = 1
        obj.probability = None
        obj.cost = None
        obj.tax = None
        obj.time = None
        obj.account = None
        obj.accounts = None
        obj.roles = 0
        obj.extras = []
        obj.locations = []
        obj.errors = []
        return obj


class Job(JobBase):
    """
    A job describes performing an Activity on a Blueprint at a Facility. We subclass the
    basic JobData class and then replace some of the static values with computed properties
    for setting up new jobs.
    """
    facility = industry.Property('_facility', 'on_facility')
    team = industry.Property('_team', 'on_dirty')
    account = industry.Property('_account', 'on_dirty')
    accounts = industry.Property('_accounts', 'on_dirty')
    roles = industry.Property('_roles', 'on_dirty')
    extras = industry.Property('_extras', 'on_dirty')
    available = industry.Property('_available', 'on_dirty')
    locations = industry.Property('_locations', 'on_dirty')
    inputLocation = industry.Property('_inputLocation', 'on_input_location')
    outputLocation = industry.Property('_outputLocation', 'on_output_location')

    def __new__(cls, blueprint, activity, *args, **kwargs):
        obj = JobBase.__new__(cls, blueprint, activity, *args, **kwargs)
        obj._ownerID = None
        obj._facility = None
        obj._team = None
        obj._inputLocation = None
        obj._outputLocation = None
        obj._runs = 1
        obj._licensedRuns = 1
        obj._productTypeID = None
        obj._cost = None
        obj._tax = None
        obj._time = None
        obj._account = None
        obj._accounts = {}
        obj._roles = 0
        obj._extras = []
        obj._available = {}
        obj._locations = []
        obj._errors = []
        obj.on_facility.connect(obj.on_dirty)
        obj.on_input_location.connect(obj.on_dirty)
        obj.on_output_location.connect(obj.on_dirty)
        return obj

    def __del__(self):
        """
        Emit a signal when we are garbage collected, be very careful with this.
        """
        if hasattr(self, 'on_delete'):
            self.on_delete(self)

    def update(self, job):
        """
        Forces a reload of materials and errors for this job. We do this to make sure
        signals are emitted whenever dependent attributes change.
        """
        self._modifiers_cache = None
        self.materials
        self.errors
        self.on_updated(self)

    def _get_runs(self):
        return max(min(self._runs or 1, self.maxRuns), 1)

    runs = industry.Property('_runs', 'on_dirty', _get_runs)

    def _get_licensed_runs(self):
        return max(min(self._licensedRuns or 1, self.maxLicensedRuns), 1)

    licensedRuns = industry.Property('_licensedRuns', 'on_dirty', _get_licensed_runs)

    def _get_productTypeID(self):
        return self._productTypeID

    productTypeID = industry.Property('_productTypeID', 'on_dirty', _get_productTypeID)

    def _get_probability(self):
        return self.activity.job_probability(self)

    probability = property(_get_probability)

    def _get_ownerID(self):
        return self.blueprint.ownerID

    ownerID = property(_get_ownerID)

    def _get_facilityID(self):
        if self.facility:
            return self.facility.facilityID

    facilityID = property(_get_facilityID)

    def _get_blueprintID(self):
        if self.blueprint:
            return self.blueprint.blueprintID

    blueprintID = property(_get_blueprintID)

    def _get_blueprint_location(self):
        blueprintLocation = self.blueprint.location
        for location in self.locations:
            if location == blueprintLocation:
                return location

    blueprint_location = property(_get_blueprint_location)

    def _get_teamID(self):
        if self.team:
            return self.team.teamID

    teamID = property(_get_teamID)

    def _get_cost(self):
        """
        Recalculates the ISK cost for this job.
        """
        cost = self.activity.job_cost(self) or 0
        for modifier in self.input_modifiers:
            if isinstance(modifier, industry.CostModifier) and modifier.activity in (None, self.activityID):
                cost *= modifier.amount

        return int(round(cost))

    cost = property(_get_cost)

    def _get_tax(self):
        """
        Returns the amount of tax required to pay to the facility owner.
        """
        if self.facility and self.facility.tax:
            return int(round(self.cost * self.facility.tax))
        else:
            return 0

    tax = property(_get_tax)

    def _get_time(self):
        """
        Returns the estimated production time for this job.
        """
        seconds = self.activity.job_time(self)
        for modifier in self.input_modifiers:
            if isinstance(modifier, industry.TimeModifier) and modifier.activity in (None, self.activityID):
                seconds *= modifier.amount

        return datetime.timedelta(seconds=long(round(seconds)))

    time = property(_get_time)

    def _get_materials(self):
        """
        Recalculates and returns the required materials for this job. This will automatically emit
        signals on the existing material objects if we are just changing modifiers or runs for example.
        """
        materials = JobBase._get_materials(self)
        for material in materials:
            quantity = float(material.base)
            for modifier in self.input_modifiers:
                if isinstance(modifier, industry.MaterialModifier) and modifier.activity in (None, self.activityID):
                    quantity *= modifier.amount

            quantity *= self.activity.job_material_runs(self)
            material.quantity = max(int(math.ceil(round(quantity, industry.MATERIAL_ROUND_PRECISION))), self.runs)
            material.on_select.connect(self._material_selected)
            material.update_available(self.available)

        return materials

    materials = property(_get_materials)

    def _material_selected(self, material):
        """
        Callback for whenever an optional material is selected.
        """
        self.on_dirty(self)

    def add_error(self, error, *args):
        """
        Pushes a new validation error onto this job for displaying. Used by validation
        callbacks. Errors should look like: (industry.Error.MY_ERROR, (arg1, arg2))
        """
        self._errors.append((error, args))

    def _get_errors(self):
        """
        Run job validation logic and return all the errors.
        """
        self._errors, existing = [], self._errors
        if self.activityID not in industry.ACTIVITY_CLASSES:
            self.add_error(industry.Error.INVALID_ACTIVITY)
        if self.blueprint.blueprintID is None:
            self.add_error(industry.Error.MISSING_BLUEPRINT)
        if self.facility is None:
            self.add_error(industry.Error.MISSING_FACILITY)
        elif not isinstance(self.facility, industry.Facility):
            self.add_error(industry.Error.INVALID_FACILITY)
        else:
            if not self.facility.online:
                self.add_error(industry.Error.FACILITY_OFFLINE)
            if self.facility.tax is None:
                self.add_error(industry.Error.FACILITY_DENIED)
            if self.distance is None or self.distance > self.max_distance:
                self.add_error(industry.Error.FACILITY_DISTANCE, self.distance, self.max_distance)
            if self.activityID not in self.facility.activities:
                self.add_error(industry.Error.FACILITY_ACTIVITY, self.activityID)
            elif self.facility.activities[self.activityID]['blueprints']:
                if self.blueprint.blueprintTypeID not in self.facility.activities[self.activityID]['blueprints']:
                    self.add_error(industry.Error.FACILITY_TYPE, self.blueprint.blueprintTypeID)
        if self.inputLocation is None:
            self.add_error(industry.Error.MISSING_INPUT_LOCATION)
        if self.outputLocation is None:
            self.add_error(industry.Error.MISSING_OUTPUT_LOCATION)
        if self.ownerID not in (self.characterID, self.corporationID):
            self.add_error(industry.Error.INVALID_OWNER)
        if self.ownerID and self.ownerID == self.corporationID:
            if not self.roles & industry.ROLE_FACTORY_MANAGER:
                self.add_error(industry.Error.MISSING_ROLE, industry.ROLE_FACTORY_MANAGER)
            if self.activityID == industry.MANUFACTURING:
                if not self.roles & industry.ROLE_FACTORY_MANUFACTURING:
                    self.add_error(industry.Error.MISSING_ROLE, industry.ROLE_FACTORY_MANUFACTURING)
            elif not self.roles & industry.ROLE_FACTORY_SCIENCE:
                self.add_error(industry.Error.MISSING_ROLE, industry.ROLE_FACTORY_SCIENCE)
        if self.blueprint.jobID is not None:
            self.add_error(industry.Error.BLUEPRINT_INSTALLED)
        if self.facility and self.blueprint.facilityID != self.facility.facilityID:
            self.add_error(industry.Error.BLUEPRINT_WRONG_FACILITY)
        if self.activityID not in self.blueprint.activities:
            self.add_error(industry.Error.INCOMPATIBLE_ACTIVITY)
        if self.timeEfficiency != self.blueprint.timeEfficiency:
            self.add_error(industry.Error.INVALID_TIME_EFFICIENCY)
        if self.materialEfficiency != self.blueprint.materialEfficiency:
            self.add_error(industry.Error.INVALID_MATERIAL_EFFICIENCY)
        if self.team:
            if not isinstance(self.team, industry.Team) or not self.team.teamID:
                self.add_error(industry.Error.INVALID_TEAM)
            else:
                if self.team.activityID != self.activityID:
                    self.add_error(industry.Error.TEAM_ACTIVITY)
                if self.team.solarSystemID is None or self.facility and self.team.solarSystemID != self.facility.solarSystemID:
                    self.add_error(industry.Error.TEAM_SOLARSYSTEM)
                if self.team.isInAuction:
                    self.add_error(industry.Error.TEAM_INAUCTION)
        if self.activityID == industry.MANUFACTURING and self.runs <= 0 or self.runs > self.blueprint.runsRemaining and self.blueprint.runsRemaining != -1:
            self.add_error(industry.Error.INVALID_RUNS, self.blueprint.runsRemaining)
        elif self.activityID == industry.INVENTION and self.blueprint.runsRemaining <= 0:
            self.add_error(industry.Error.INVALID_RUNS, self.blueprint.runsRemaining)
        if self.activityID == industry.COPYING and (not self.licensedRuns or self.licensedRuns <= 0 or self.licensedRuns > self.blueprint.maxProductionLimit):
            self.add_error(industry.Error.INVALID_LICENSED_RUNS, self.licensedRuns)
        if not self.product:
            self.add_error(industry.Error.INVALID_PRODUCT)
        if self.account is None or self.accounts is None:
            self.add_error(industry.Error.ACCOUNT_INVALID)
        elif self.account not in self.accounts:
            self.add_error(industry.Error.ACCOUNT_ACCESS, self.account, self.accounts.keys())
        elif (self.accounts[self.account] or 0) < self.total_cost:
            self.add_error(industry.Error.ACCOUNT_FUNDS, self.accounts[self.account], self.total_cost)
        if not self.blueprint_location:
            self.add_error(industry.Error.INVALID_BLUEPRINT_LOCATION, self.blueprint.location)
        elif not self.blueprint_location.canView:
            self.add_error(industry.Error.BLUEPRINT_ACCESS, self.blueprint.location)
        if len(JobBase._get_materials(self)):
            materialErrors = sum([ material.errors for material in JobBase._get_materials(self) ], [])
            if self.inputLocation not in self.locations:
                self.add_error(industry.Error.INVALID_INPUT_LOCATION, self.inputLocation)
            elif not self.inputLocation.canTake:
                self.add_error(industry.Error.INPUT_ACCESS, self.inputLocation)
            else:
                self._errors += materialErrors
        if self.outputLocation not in self.locations:
            self.add_error(industry.Error.INVALID_OUTPUT_LOCATION, self.outputLocation)
        for skill in self.required_skills:
            actual = self.skills.get(skill.typeID, 0)
            if actual < skill.level:
                self.add_error(industry.Error.MISSING_SKILL, skill.typeID, skill.level, actual)

        if self.used_slots >= self.max_slots:
            self.add_error(industry.Error.SLOTS_FULL, self.max_slots, self.used_slots)
        time = self.time.total_seconds()
        time_previous = time - time / float(self.runs)
        if time_previous > industry.MAX_RUN_LENGTH:
            self.add_error(industry.Error.RUN_LENGTH, time_previous, industry.MAX_RUN_LENGTH)
        if self.request:
            if self.request['cost'] and self.request['cost'] != self.cost:
                self.add_error(industry.Error.MISMATCH_COST, self.request['cost'], self.cost)
            if self.request['tax'] and self.request['tax'] != self.tax:
                self.add_error(industry.Error.MISMATCH_TAX, self.request['tax'], self.tax)
            if self.request['time'] and self.request['time'] != self.time.total_seconds():
                self.add_error(industry.Error.MISMATCH_TIME, self.request['time'], self.time.total_seconds())
            materials = {material.typeID:material.quantity for material in JobBase._get_materials(self)}
            if self.request['materials'] and self.request['materials'] != materials:
                self.add_error(industry.Error.MISMATCH_MATERIAL, self.request['materials'], materials)
        self.activity.job_validate(self)
        self.on_validate(self)
        if existing != self._errors:
            self.on_errors(self, self._errors)
        return self._errors

    errors = property(_get_errors)

    def _get_error_codes(self):
        """
        Returns a set of just the error codes.
        """
        return set([ error for error, args in self.errors ])

    error_codes = property(_get_error_codes)

    def validate(self):
        """
        Checks the errors and raises an exception.
        """
        errors = self.errors
        if len(errors):
            raise industry.ValidationError(errors)

    def dump(self):
        """
        Creates a slim item for this job, summarizing the dynamic elements as well as the final
        calculated values. We can use this for sending a copy of a job over the wire and validating
        the state of it afterwards.
        """
        return {'blueprintID': self.blueprint.blueprintID,
         'blueprintTypeID': self.blueprint.blueprintTypeID,
         'activityID': self.activityID,
         'facilityID': self.facility.facilityID if self.facility else None,
         'solarSystemID': self.facility.solarSystemID if self.facility else None,
         'teamID': self.team.teamID if self.team else None,
         'characterID': self.characterID,
         'corporationID': self.corporationID,
         'account': self.account,
         'runs': self.runs,
         'cost': self.cost,
         'tax': self.tax,
         'time': self.time.total_seconds(),
         'materials': {material.typeID:material.quantity for material in self.materials},
         'inputLocation': self.inputLocation,
         'outputLocation': self.outputLocation,
         'licensedRuns': self.licensedRuns,
         'productTypeID': self.productTypeID}

    @classmethod
    def create(cls, request, blueprint):
        """
        The reverse of the dump method, takes a slim dictionary summary of a job and reconstructs
        it into the current object. We need to be provided a few load methods responsible for fetching
        the related objects.
        """
        required = {'blueprintID',
         'blueprintTypeID',
         'activityID',
         'facilityID',
         'teamID',
         'characterID',
         'corporationID',
         'account',
         'runs',
         'inputLocation',
         'outputLocation',
         'licensedRuns',
         'productTypeID'}
        if len(required.difference(set(request))):
            raise RuntimeError('Invalid Request: ', required.difference(set(request)))
        job = Job(blueprint, request['activityID'])
        job.characterID = request['characterID']
        job.corporationID = request['corporationID']
        job.account = request['account']
        job.runs = request['runs']
        job.inputLocation = request['inputLocation']
        job.outputLocation = request['outputLocation']
        job.licensedRuns = request['licensedRuns']
        job.productTypeID = request['productTypeID']
        job.request = request
        return job


class ValidationError(Exception):
    """
    Container for job validation errors.
    """

    def __init__(self, errors):
        self.errors = errors

    def __reduce__(self):
        return (self.__class__, (self.errors,))


class Location(industry.Base):
    """
    A location holds reference to where blueprints and materials live. This is used
    for defining the input and output for jobs, and holding a cache of available
    materials to be used during validation.
    """

    def __init__(self, **kwargs):
        self.itemID = None
        self.typeID = None
        self.ownerID = None
        self.flagID = None
        self.canView = None
        self.canTake = None
        industry.Base.__init__(self, **kwargs)

    def __eq__(self, location):
        return isinstance(location, Location) and self.itemID == location.itemID and self.typeID == location.typeID and self.ownerID == location.ownerID and self.flagID == location.flagID

    def __repr__(self):
        return industry.repr(self)
