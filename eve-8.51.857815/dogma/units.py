#Embedded file name: dogma\units.py


def _GetDogmaUnits():
    return cfg.dgmunits


def GetUnit(unitID):
    return _GetDogmaUnits().Get(unitID)


def HasUnit(unitID):
    return unitID in _GetDogmaUnits()


def GetDisplayName(unitID):
    return GetUnit(unitID).displayName
