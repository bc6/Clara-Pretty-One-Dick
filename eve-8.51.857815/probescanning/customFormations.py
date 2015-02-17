#Embedded file name: probescanning\customFormations.py
from probescanning.util import GetOffsetPositions

class EditFormations(object):

    def __init__(self):
        self.__formations = None

    def __enter__(self):
        self.__formations = _GetAllCustomFormations()
        return self.__formations

    def __exit__(self, *args):
        _PersistAllFormations(self.__formations)


def GetCustomFormation(formationID):
    formations = _GetAllCustomFormations()
    return formations[formationID]


def GetCustomFormationsInfo():
    formations = _GetAllCustomFormations()
    return tuple(((formationID, name, len(probeInfo)) for formationID, (name, probeInfo) in formations.iteritems()))


def PersistFormation(formationName, probeInfo):
    if not probeInfo:
        raise RuntimeError('Persisting Scan Formation but have no probeInfo')
    with EditFormations() as formations:
        key = _GetNewFormationID(formations)
        formations[key] = (formationName, _GetPositionsWithOffset(probeInfo))
    SelectFormation(key)
    return key


def DeleteFormation(formationID):
    with EditFormations() as formations:
        del formations[formationID]
    if formationID == GetSelectedFormationID():
        SelectFormation(None)


def SelectFormation(formationID):
    if formationID is not None:
        formations = _GetAllCustomFormations()
        if formationID not in formations:
            raise KeyError
    return settings.user.ui.Set('probescanning.selectedFormationID', formationID)


def GetSelectedFormationID():
    formationID = settings.user.ui.Get('probescanning.selectedFormationID', None)
    if formationID not in _GetAllCustomFormations():
        return
    return formationID


def GetSelectedFormationName():
    formationID = GetSelectedFormationID()
    if formationID is None:
        return ''
    return _GetAllCustomFormations()[formationID][0]


def GetActiveFormation():
    return GetCustomFormation(GetSelectedFormationID())


def _PersistAllFormations(formations):
    settings.user.ui.Set('probescanning.customFormations', formations)


def _GetAllCustomFormations():
    return settings.user.ui.Get('probescanning.customFormations', {})


def _GetPositionsWithOffset(probeInfo):
    positions, scanRanges = zip(*probeInfo)
    offsets = GetOffsetPositions(positions)
    return zip(offsets, scanRanges)


def _GetNewFormationID(formations):
    key = max(formations.iterkeys()) + 1 if formations else 0
    return key
