#Embedded file name: crimewatch/corp_aggression\settings.py
import logging
from ccpProfile import TimedFunction
from eve.common.script.sys.idCheckers import IsNPCCorporation
DEFAULT_AGGRESSION_ENABLED = True
logger = logging.getLogger(__name__)

class AggressionSettings:
    __passbyvalue__ = True

    def __init__(self, enableAfter, disableAfter):
        self._enableAfter = enableAfter
        self._disableAfter = disableAfter

    def __repr__(self):
        return 'AggressionSettings(enableAfter=%r,disableAfter=%r)' % (self._enableAfter, self._disableAfter)

    def __eq__(self, other):
        return self._enableAfter == other._enableAfter and self._disableAfter == other._disableAfter

    def __ne__(self, other):
        return self._enableAfter != other._enableAfter or self._disableAfter != other._disableAfter

    def HasPendingChangeAtTime(self, time):
        return self._IsDisableTimeInFuture(time) or self._IsEnableTimeInFuture(time)

    @TimedFunction('AggressionSettings::IsFriendlyFireLegalAtTime')
    def IsFriendlyFireLegalAtTime(self, time):
        if self._IsDisableTimeInPast(time) and self._IsEnableTimeInPast(time):
            return self._disableAfter < self._enableAfter
        elif self._IsDisableTimeInPast(time):
            return False
        elif self._IsEnableTimeInPast(time):
            return True
        else:
            return DEFAULT_AGGRESSION_ENABLED

    def _IsDisableTimeInPast(self, now):
        return self._disableAfter is not None and self._disableAfter < now

    def _IsEnableTimeInPast(self, now):
        return self._enableAfter is not None and self._enableAfter < now

    def _IsDisableTimeInFuture(self, now):
        return self._disableAfter is not None and self._disableAfter >= now

    def _IsEnableTimeInFuture(self, now):
        return self._enableAfter is not None and self._enableAfter >= now

    def GetNextPendingChangeTime(self, now):
        if self._IsDisableTimeInFuture(now):
            return self._disableAfter
        if self._IsEnableTimeInFuture(now):
            return self._enableAfter

    @staticmethod
    def CreateDefaultForCorp(corpID):
        if not IsNPCCorporation(corpID):
            return ALWAYS_ENABLED
        else:
            return ALWAYS_DISABLED

    @staticmethod
    def CreateFromDBRows(rows):
        if len(rows) == 1:
            return AggressionSettings(rows[0].enableAfter, rows[0].disableAfter)


ALWAYS_ENABLED = AggressionSettings(0, None)
ALWAYS_DISABLED = AggressionSettings(None, 0)
