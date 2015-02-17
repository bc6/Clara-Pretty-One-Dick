#Embedded file name: gatekeeper\gatekeeperClass.py
from eveexceptions.exceptionEater import ExceptionEater
import functoolsext
CACHE_SIZE = 4096

class Gatekeeper:

    def __init__(self, ignoreMultipleTeardowns = False, allowMultipleInits = False):
        self.GetCohortFunction = None
        self.tolerantTearDown = ignoreMultipleTeardowns
        self.allowMultipleInits = allowMultipleInits

    def IsInitialized(self):
        return self.GetCohortFunction is not None

    def Initialize(self, getCohortFunction):
        """
            Initializes the gatekeeper modules method of resolving the proper service
            to use. Function must return a list of cohorts or an empty list
        
            :params getCohortFunction: A function that will fetch cohorts for an
            entity(user or a character at the time of writing) based on a id
        """
        self.__raiseRuntimeErrorIfNone(getCohortFunction)
        if not self.IsInitialized() or self.allowMultipleInits:
            self.GetCohortFunction = getCohortFunction
        else:
            raise RuntimeError('Gatekeeper has already been initialized!')

    def __raiseRuntimeErrorIfNone(self, function):
        if function is None:
            raise RuntimeError('Gatekeeper cohort Function cannot be None')

    def Teardown(self):
        """
            Teardown method used by unit tests to avoid repeated initializations.
        """
        if self.IsInitialized():
            self.GetCohortFunction = None
        elif not self.tolerantTearDown:
            raise RuntimeError('Gatekeeper has not been initialized!')
        self.IsInCohort.cache_clear()
        self.GetCohorts.cache_clear()

    @functoolsext.lru_cache(CACHE_SIZE)
    def IsInCohort(self, cohortID, *args):
        """
            A simple utility function that returns if an entity(user or character) belongs to a cohort
            It is cached until cache size runs out or TearDown is called
        
            :param cohort: The cohorts unique identifier
            :param *args: any arguments required to resolve the bound GetCohortFunction call.
        """
        if self.IsInitialized():
            isInCohort = False
            with ExceptionEater('Failed to query the gatekeeper. Returning False for querying entity.'):
                CohortFunction = self.GetCohortFunction(args)
                isInCohort = cohortID in self._GetCohortsForEntityFromService(CohortFunction)
            return isInCohort
        raise RuntimeError('Gatekeeper not initialized')

    def _GetCohortsForEntityFromService(self, CohortFunction):
        return CohortFunction()

    @functoolsext.lru_cache(CACHE_SIZE)
    def GetCohorts(self, *args):
        """
            Simply returns the cohorts the entity belongs to
        
            :param args: any arguments required to resolve the bound GetCohortFunction call
            :return: lists of cohorts an entity belongs to
        """
        self._RaiseErrorIfNotInitialized()
        CohortFunction = self.GetCohortFunction(args)
        return self._GetCohortsForEntityFromService(CohortFunction)

    def _RaiseErrorIfNotInitialized(self):
        if not self.IsInitialized():
            raise RuntimeError('Gatekeeper has not been initialized')
