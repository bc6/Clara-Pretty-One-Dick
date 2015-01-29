#Embedded file name: gatekeeper\__init__.py
"""
    Common functionality for A/B/n testing
"""
__author__ = 'unnar'
import functoolsext
from eveexceptions.exceptionEater import ExceptionEater
CACHE_SIZE = 4096
GetCohortFunction = None

def Initialize(getCohortFunction):
    """
        Initializes the gatekeeper modules method of resolving the proper service
        to use. Service must implement GetCohortsForCharacter.
    
        :params getCohortFunction: A function that will fetch cohorts for user base on
        a characterID
    """
    global GetCohortFunction
    with ExceptionEater('Gatekeeper has already been initialized!'):
        if not GetCohortFunction:
            GetCohortFunction = getCohortFunction
        else:
            raise RuntimeError('Gatekeeper has already been initialized!')


def Teardown():
    """
        Teardown method used by unit tests to avoid repeated initializations.
    """
    global GetCohortFunction
    with ExceptionEater('Gatekeeper has not been initialized!'):
        if GetCohortFunction:
            GetCohortFunction = None
        else:
            raise RuntimeError('Gatekeeper has not been initialized!')
    CharacterIsInCohort.cache_clear()
    GetCharacterCohorts.cache_clear()


@functoolsext.lru_cache(CACHE_SIZE)
def CharacterIsInCohort(cohort, *args):
    """
        A simple utility function to keep code clean.
        This should be the only function you ever need to call.
    
        :param cohort: The cohorts unique identifier
        :param *args: any arguments required to resolve the bound GetCohortFunction call.
    """
    isInCohort = False
    with ExceptionEater('Failed to query the gatekeeper. Returning False for querying entity.'):
        CohortFunction = GetCohortFunction(args)
        isInCohort = cohort in _GetCohortsForCharacterFromService(CohortFunction)
    return isInCohort


@functoolsext.lru_cache(CACHE_SIZE)
def GetCharacterCohorts(*args):
    with ExceptionEater('Failed to query the gatekeeper. Returning [] for querying entity.'):
        CohortFunction = GetCohortFunction(args)
        return _GetCohortsForCharacterFromService(CohortFunction)
    return []


def _GetCohortsForCharacterFromService(CohortFunction):
    """
        Please refrain from calling this from outside of the package.
        CharacterIsInCohort is cached, this is not.
    
        :params CohortFunction: Bound function for cohort resolution
    """
    return CohortFunction()
