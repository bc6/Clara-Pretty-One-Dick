#Embedded file name: eve/client/script/industry\industrySvc.py
import industry
import service
import weakref
import uthread
import telemetry
import util
import blue
from eve.common.script.util import industryCommon

class IndustryService(service.Service):
    """
    The client side Industry code is broken into 3 distinct parts:
    
     * A standlone python module which loads static FSD data and provides an interface
       for getting blueprints, creating jobs and calculating the cost of activities etc.
       (packages/industry/*)
    
     * This client side services which act as a controllers between the static data, the
       user interface, the server side industry manager and other client side services
       such as skills and inventory.
       (eve/client/script/industry/*)
    
     * The user interface code.
       (eve/client/script/ui/industry/*)
    
    This particular service has a number of responsibilities:
    
     * Requesting character and inventory data for the industry module related to Jobs
     * Forwarding actions from the UI to the server and handling any errors
     * Listening to server notifications to trigger updates to the UI or cached data
    """
    __guid__ = 'svc.industrySvc'
    __servicename__ = 'Industry'
    __displayname__ = 'Industry Service'
    __dependencies__ = ['blueprintSvc', 'facilitySvc', 'clientPathfinderService']
    __notifyevents__ = ['OnCharacterAttributeChanged',
     'OnIndustryMaterials',
     'OnIndustryJob',
     'OnSessionChanged',
     'OnAccountChange',
     'OnSkillLevelChanged']

    def Run(self, *args, **kwargs):
        self.monitoring = weakref.ref(set())
        self.installed = weakref.WeakValueDictionary()
        uthread.new(self._PollJobCompletion)
        service.Service.Run(self, *args, **kwargs)

    def GetJobByID(self, jobID):
        """
        Returns a single job from the ID.
        """
        return self._JobInstance(sm.RemoteSvc('industryManager').GetJob(jobID), fetchBlueprint=True)

    @telemetry.ZONE_METHOD
    def GetOwnerJobs(self, ownerID, includeCompleted = False):
        """
        Returns a list of all jobs for a given ownerID.
        """
        jobs = []
        locations = set()
        for data in sm.RemoteSvc('industryManager').GetJobsByOwner(ownerID, includeCompleted):
            job = self._JobInstance(data, fetchBlueprint=False)
            jobs.append(job)
            if not job.completed:
                locations.add(job.facilityID)

        cfg.evelocations.Prime(locations)
        return jobs

    def GetCharacterJobs(self, includeCompleted = False):
        """
        Fetches our personal industry jobs.
        """
        return self.GetOwnerJobs(session.charid, includeCompleted)

    def GetCorporationJobs(self, includeCompleted = False):
        """
        Fetches our corporations industry jobs.
        """
        return self.GetOwnerJobs(session.corpid, includeCompleted)

    @telemetry.ZONE_METHOD
    def CreateJob(self, blueprint, activityID, facilityID, runs = 1):
        """
        Returns a new instance of industry.Job with the character skill data pre-populated.
        """
        job = industry.Job(blueprint, activityID)
        job.runs = runs
        job.status = industry.STATUS_UNSUBMITTED
        job.extras = industryCommon.GetOptionalMaterials(job)
        job.prices = industryCommon.JobPrices()
        industryCommon.AttachSessionToJob(job, session)
        self._UpdateSkills(job)
        self._UpdateSlots(job)
        self._UpdateModifiers(job)
        self._UpdateDistance(job)
        self._UpdateAccounts(job)
        job.on_facility.connect(self.LoadLocations)
        job.on_delete.connect(self.DisconnectJob)
        job.on_input_location.connect(self.ConnectJob)
        job.facility = self.facilitySvc.GetFacility(facilityID)
        self._ApplyJobSettings(job)
        return job

    def RecreateJob(self, existing):
        """
        Creates a new job using the setting from a previous job.
        """
        try:
            blueprint = self.blueprintSvc.GetBlueprintItem(existing.blueprintID)
            if blueprint.ownerID != existing.ownerID:
                raise UserError
        except UserError:
            blueprint = self.blueprintSvc.GetBlueprintType(existing.blueprintTypeID, not existing.blueprint.original)

        job = self.CreateJob(blueprint, existing.activityID, existing.facilityID)
        job.outputLocation = industryCommon.MatchLocation(job, existing.outputLocationID, existing.outputFlagID)
        job.productTypeID = existing.productTypeID
        job.runs = existing.runs
        job.licensedRuns = existing.licensedRuns
        for material in job.optional_materials:
            material.select(None)
            if getattr(existing, 'optionalTypeID', None) in material.all_types():
                material.select(existing.optionalTypeID)
            if getattr(existing, 'optionalTypeID2', None) in material.all_types():
                material.select(existing.optionalTypeID2)

        job.team = self._GetTeam(existing.teamID)
        return job

    def JobDataWithBlueprint(self, existing):
        """
        Given an existing JobData class, construct a new one but this time using a real blueprint.
        """
        job = self._JobInstance(existing.data, fetchBlueprint=True)
        job.extras = industryCommon.GetOptionalMaterials(job)
        return job

    def InstallJob(self, job):
        """
        Submits a job to the server. This remote call will raise UserErrors
        if anything went wrong that the client needs to know about.
        """
        sm.RemoteSvc('industryManager').InstallJob(job.dump())

    def CompleteJob(self, jobID):
        sm.RemoteSvc('industryManager').CompleteJob(int(jobID))

    def CompleteJobs(self, jobs):
        uthread.parallel([ (self.CompleteJob, (jobID,)) for jobID in jobs ])

    def CancelJob(self, jobID):
        sm.RemoteSvc('industryManager').CancelJob(int(jobID))

    def _PollJobCompletion(self):
        """
        Spawns a thread every second to monitor for job completion
        """
        while self.state == service.SERVICE_RUNNING:
            uthread.new(self._PollJobCompletionThreaded)
            blue.pyos.synchro.SleepWallclock(1000)

    def _PollJobCompletionThreaded(self):
        """
        Polls the weakref dictionary of loaded jobs to see if their end date has passed
        in which case the job is completed. Scatters an OnIndustryJob event if they change.
        """
        for job in self.installed.values():
            if job.status == industry.STATUS_INSTALLED and util.DateToBlue(job.endDate) < blue.os.GetWallclockTime():
                job.status = industry.STATUS_READY
                sm.ScatterEvent('OnIndustryJob', job.jobID, job.ownerID, job.blueprintID, job.installerID, job.status, None)

    def _JobInstance(self, data, fetchBlueprint = False):
        if fetchBlueprint:
            blueprint = self.blueprintSvc.GetBlueprint(data.blueprintID, data.blueprintTypeID)
        else:
            blueprint = self.blueprintSvc.GetBlueprintType(data.blueprintTypeID, data.blueprintCopy)
        job = industryCommon.JobData(data, blueprint)
        self._UpdateSkills(job)
        self._UpdateSlots(job)
        self._UpdateModifiers(job)
        self._UpdateDistance(job)
        if job.status == industry.STATUS_INSTALLED:
            self.installed[job.jobID] = job
        else:
            self.installed.pop(job.jobID, None)
        return job

    @telemetry.ZONE_METHOD
    def _UpdateModifiers(self, job):
        """
        Returns a list of character modifiers. We cache these on the client service and will
        update the bonuses in place if they are updated.
        """
        if job:
            modifiers = industryCommon.GetJobModifiers(job)
            dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
            for modifier, attribute, activity in industryCommon.ATTRIBUTE_MODIFIERS:
                if job.activityID == activity:
                    amount = dogmaLocation.GetAttributeValue(session.charid, attribute)
                    modifiers.append(modifier(amount=amount, activity=activity, reference=industry.Reference.SKILLS))

            job.modifiers = modifiers

    @telemetry.ZONE_METHOD
    def _UpdateDistance(self, job):
        """
        Manually sets the distance on this job if its a JobData class.
        """
        if job and isinstance(job, industry.JobData):
            job._distance = self.clientPathfinderService.GetJumpCountFromCurrent(job.solarSystemID)

    @telemetry.ZONE_METHOD
    def _UpdateSkills(self, job):
        """
        Returns the list of relevant industry skill levels for the current character.
        """
        if job:
            skills = {}
            skillsByTypeID = sm.GetService('skills').MySkills(byTypeID=True)
            for typeID in [ skill.typeID for skill in job.all_skills ]:
                skill = skillsByTypeID.get(typeID, None)
                skills[typeID] = skill.skillLevel if skill else 0

            job.skills = skills

    @telemetry.ZONE_METHOD
    def _UpdateSlots(self, job = None, force = False):
        """
        Returns the number of currently running job slots consumed for this character.
        """
        if not hasattr(self, 'slots'):
            self.slots = {}
        if not len(self.slots) or force:
            self.slots = sm.RemoteSvc('industryManager').GetJobCounts(session.charid)
        if job:
            job.slots = self.slots

    def _GetTeam(self, teamID):
        """
        Returns a team by ID or None if not found.
        """
        try:
            team = sm.GetService('industryTeamSvc').GetTeam(teamID)
            return industryCommon.JobTeam(util.KeyVal(team=team, isInAuction=False))
        except KeyError:
            return None

    @telemetry.ZONE_METHOD
    def _UpdateAccounts(self, job, ownerID = None, account = None, balance = None):
        """
        Returns the account balance for the wallet used in this job.
        """
        if job:
            accounts = {(session.charid, const.accountingKeyCash): sm.GetService('wallet').GetWealth()}
            if session.corpAccountKey and sm.GetService('wallet').HaveAccessToCorpWalletDivision(session.corpAccountKey):
                if ownerID and account and balance and session.corpid == ownerID and session.corpAccountKey == account:
                    accounts[session.corpid, session.corpAccountKey] = balance
                else:
                    accounts[session.corpid, session.corpAccountKey] = sm.GetService('wallet').GetCorpWealthCached1Min(session.corpAccountKey)
            job.accounts = accounts
            if job.account not in job.accounts:
                for accountOwner, accountKey in job.accounts.keys():
                    if job.ownerID == accountOwner:
                        job.account = (accountOwner, accountKey)
                        return

                job.account = job.accounts.keys()[0]

    def OnCharacterAttributeChanged(self, attributeID, oldValue, value):
        """
        If any character attributes change in dogma related to industry modifiers then force
        reload them in place to update any jobs.
        """
        if attributeID in [ attribute for _, attribute, _ in industryCommon.ATTRIBUTE_MODIFIERS ]:
            self._UpdateModifiers(self.monitoring())

    def OnSessionChanged(self, isRemote, session, change):
        """
        Listens to session changes and reattaches the session to our monitored job if there is one.
        """
        industryCommon.AttachSessionToJob(self.monitoring(), session)
        if 'corpAccountKey' in change:
            self._UpdateAccounts(self.monitoring())
        if 'corprole' in change:
            self._UpdateAccounts(self.monitoring())
            self.LoadLocations(self.monitoring())

    def OnAccountChange(self, accountKey, ownerID, balance):
        """
        Listens to session changes and reattaches the session to our monitored job if there is one.
        """
        self._UpdateAccounts(self.monitoring(), ownerID, sm.GetService('account').GetAccountKeyID(accountKey), balance)

    def OnSkillLevelChanged(self, typeID, oldValue, newValue):
        """
        If a skill is modified while a job is opened then we should update its skills.
        """
        self._UpdateSkills(self.monitoring())
        self._UpdateModifiers(self.monitoring())

    def OnIndustryJob(self, jobID, ownerID, blueprintID, installerID, status, successfulRuns):
        """
        Notification if a job is modified in anyway.
        """
        if installerID == session.charid:
            self._UpdateSlots(self.monitoring(), force=True)

    @telemetry.ZONE_METHOD
    def ConnectJob(self, job):
        """
        The server will allow us to monitor a single job for changes to inventory, even if
        it is a remote station inventory. This will replace which job we are currently
        monitoring.
        """
        self.monitoring = weakref.ref(job)
        job.monitorID, job.available = sm.RemoteSvc('industryMonitor').ConnectJob(job.dump())

    @telemetry.ZONE_METHOD
    def DisconnectJob(self, job):
        """
        Whenever a job is thrown away, check to see if its the one we are currently monitoring
        and notify the server we no longer need updates.
        """
        if self.monitoring() == job:
            sm.RemoteSvc('industryMonitor').DisconnectJob(job.monitorID)

    @telemetry.ZONE_METHOD
    def LoadLocations(self, job):
        """
        Whenever the facility is set we should refetch the list of valid locations for a job.
        """
        if job:
            job.locations = self.facilitySvc.GetFacilityLocations(job.facilityID, job.ownerID)
            if len(job.locations):
                self._ApplyJobSettings(job)

    def OnIndustryMaterials(self, jobID, materials):
        """
        This notification is raised on the client whenever materials related to a monikered
        industry job get updated. We should use this to refresh ourself.
        """
        job = self.monitoring()
        if job and job.monitorID == jobID:
            job.available = materials

    def _UpdateJobSettings(self, job):
        """
        Whenever a job changes we update our persisted job settings, so next time we use
        a blueprint of this type we remember the settings we used.
        """
        settings.char.ui.Set('industry_b:%s_a:%s_runs' % (job.blueprint.blueprintTypeID, job.activityID), job.runs)
        settings.char.ui.Set('industry_b:%s_a:%s_productTypeID' % (job.blueprint.blueprintTypeID, job.activityID), job.productTypeID)
        settings.char.ui.Set('industry_b:%s_a:%s_licensedRuns' % (job.blueprint.blueprintTypeID, job.activityID), job.licensedRuns)
        settings.char.ui.Set('industry_account:%s' % (job.ownerID,), job.account)
        if job.inputLocation is not None and job.facility is not None:
            settings.char.ui.Set('industry_b:%s_a:%s_f:%s_input' % (job.blueprint.blueprintTypeID, job.activityID, job.facility.facilityID), (job.inputLocation.itemID, job.inputLocation.flagID))
        if job.outputLocation is not None and job.facility is not None:
            settings.char.ui.Set('industry_b:%s_a:%s_f:%s_output' % (job.blueprint.blueprintTypeID, job.activityID, job.facility.facilityID), (job.outputLocation.itemID, job.outputLocation.flagID))
        if job.facility is not None:
            settings.char.ui.Set('industry_b:%s_a:%s_f:%s_teamID' % (job.blueprint.blueprintTypeID, job.activityID, job.facility.facilityID), job.teamID)
        if len(job.optional_materials):
            settings.char.ui.Set('industry_b:%s_a:%s_materials' % (job.blueprint.blueprintTypeID, job.activityID), list([ material.typeID for material in job.optional_materials if material.typeID ]))

    def _ApplyJobSettings(self, job):
        """
        After setting up a new job, try to select
        """
        job.runs = settings.char.ui.Get('industry_b:%s_a:%s_runs' % (job.blueprint.blueprintTypeID, job.activityID), 1)
        job.productTypeID = settings.char.ui.Get('industry_b:%s_a:%s_productTypeID' % (job.blueprint.blueprintTypeID, job.activityID), None)
        job.licensedRuns = min(job.maxLicensedRuns, settings.char.ui.Get('industry_b:%s_a:%s_licensedRuns' % (job.blueprint.blueprintTypeID, job.activityID), job.maxLicensedRuns))
        account = settings.char.ui.Get('industry_account:%s' % (job.ownerID,), job.account)
        job.account = account if account in job.accounts else job.account
        if job.facility:
            job.inputLocation = industryCommon.MatchLocation(job, *settings.char.ui.Get('industry_b:%s_a:%s_f:%s_input' % (job.blueprint.blueprintTypeID, job.activityID, job.facility.facilityID), (job.blueprint.location.itemID, job.blueprint.location.flagID)))
            job.outputLocation = industryCommon.MatchLocation(job, *settings.char.ui.Get('industry_b:%s_a:%s_f:%s_output' % (job.blueprint.blueprintTypeID, job.activityID, job.facility.facilityID), (job.blueprint.location.itemID, job.blueprint.location.flagID)))
            try:
                job.team = self._GetTeam(settings.char.ui.Get('industry_b:%s_a:%s_f:%s_teamID' % (job.blueprint.blueprintTypeID, job.activityID, job.facility.facilityID), None))
            except KeyError:
                pass

        materials = settings.char.ui.Get('industry_b:%s_a:%s_materials' % (job.blueprint.blueprintTypeID, job.activityID), [])
        for material in job.materials:
            for option in material.options:
                if option.typeID in materials:
                    material.select(option)

        job.on_updated.connect(self._UpdateJobSettings)
