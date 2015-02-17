#Embedded file name: workers\specialization.py


class Specialization(object):

    def __init__(self, specializationID, specializationType, tier, subSpecializationIDs, label, groupIDs):
        self.specializationID = specializationID
        self.specializationType = specializationType
        self.tier = tier
        self.groupIDs = groupIDs
        self.subSpecializations = subSpecializationIDs

    def AddSubSpecialization(self, specialization):
        self.subSpecializations.append(specialization)
