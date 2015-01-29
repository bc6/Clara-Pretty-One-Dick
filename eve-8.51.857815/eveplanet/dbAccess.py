#Embedded file name: eveplanet\dbAccess.py


class DBAccess(object):

    def __init__(self, dborbital):
        self.dborbital = dborbital

    def GetOrbitalsForCorpID(self, corpID):
        return self.dborbital.SelectByOwnerID(corpID)

    def DeleteOrbitalSettings(self, orbitalIDs):
        if orbitalIDs:
            return self.dborbital.Settings_DeleteMany(','.join((str(orbitalID) for orbitalID in orbitalIDs)))
