#Embedded file name: dogma/effects\modifiers.py


class BaseModifier(object):

    def __init__(self, operator, domain, modifiedAttributeID, modifyingAttributeID):
        self.operator = operator
        self.domain = domain
        self.modifiedAttributeID = modifiedAttributeID
        self.modifyingAttributeID = modifyingAttributeID
        self.isShipModifier = domain == 'shipID'
        self.isCharModifier = domain == 'charID'

    def _GetDomainID(self, env):
        if self.domain is None:
            return env.itemID
        return getattr(env, self.domain)

    def Start(self, env, dogmaLM, itemID, shipID, charID, otherID, targetID):
        self._GetStartFunc(dogmaLM)(*self._GetArgs(env, itemID))

    def Stop(self, env, dogmaLM, itemID, shipID, charID, otherID, targetID):
        self._GetStopFunc(dogmaLM)(*self._GetArgs(env, itemID))

    def IsShipModifier(self):
        return self.isShipModifier

    def IsCharModifier(self):
        return self.isCharModifier


class ItemModifier(BaseModifier):

    def _GetArgs(self, env, itemID):
        return (self.operator,
         self._GetDomainID(env),
         self.modifiedAttributeID,
         itemID,
         self.modifyingAttributeID)

    def _GetStartFunc(self, dogmaLM):
        return dogmaLM.AddModifier

    def _GetStopFunc(self, dogmaLM):
        return dogmaLM.RemoveModifier


class LocationModifier(ItemModifier):

    def _GetStartFunc(self, dogmaLM):
        return dogmaLM.AddLocationModifier

    def _GetStopFunc(self, dogmaLM):
        return dogmaLM.RemoveLocationModifier


class RequiredSkillModifier(BaseModifier):

    def __init__(self, operator, domain, modifiedAttributeID, modifyingAttributeID, skillTypeID):
        super(RequiredSkillModifier, self).__init__(operator, domain, modifiedAttributeID, modifyingAttributeID)
        self.skillTypeID = skillTypeID

    def _GetArgs(self, env, itemID):
        return (self.operator,
         self._GetDomainID(env),
         self.skillTypeID,
         self.modifiedAttributeID,
         itemID,
         self.modifyingAttributeID)


class LocationRequiredSkillModifier(RequiredSkillModifier):

    def _GetStartFunc(self, dogmaLM):
        return dogmaLM.AddLocationRequiredSkillModifier

    def _GetStopFunc(self, dogmaLM):
        return dogmaLM.RemoveLocationRequiredSkillModifier


class OwnerRequiredSkillModifier(RequiredSkillModifier):

    def _GetStartFunc(self, dogmaLM):
        return dogmaLM.AddOwnerRequiredSkillModifier

    def _GetStopFunc(self, dogmaLM):
        return dogmaLM.RemoveOwnerRequiredSkillModifier

    def IsShipModifier(self):
        return True

    def IsCharModifier(self):
        return True


class LocationGroupModifier(BaseModifier):

    def __init__(self, operator, domain, modifiedAttributeID, modifyingAttributeID, groupID):
        super(LocationGroupModifier, self).__init__(operator, domain, modifiedAttributeID, modifyingAttributeID)
        self.groupID = groupID

    def _GetArgs(self, env, itemID):
        return (self.operator,
         self._GetDomainID(env),
         self.groupID,
         self.modifiedAttributeID,
         itemID,
         self.modifyingAttributeID)

    def _GetStartFunc(self, dogmaLM):
        return dogmaLM.AddLocationGroupModifier

    def _GetStopFunc(self, dogmaLM):
        return dogmaLM.RemoveLocationGroupModifier


class GangItemModifier(ItemModifier):

    def _GetArgs(self, env, itemID):
        return (self._GetDomainID(env),
         self.operator,
         self.modifiedAttributeID,
         itemID,
         self.modifyingAttributeID)

    def _GetStartFunc(self, dogmaLM):
        return dogmaLM.AddGangShipModifier

    def _GetStopFunc(self, dogmaLM):
        return dogmaLM.RemoveGangShipModifier


class GangRequiredSkillModifier(RequiredSkillModifier):

    def _GetArgs(self, env, itemID):
        return (self._GetDomainID(env),
         self.operator,
         self.skillTypeID,
         self.modifiedAttributeID,
         itemID,
         self.modifyingAttributeID)

    def _GetStartFunc(self, dogmaLM):
        return dogmaLM.AddGangRequiredSkillModifier

    def _GetStopFunc(self, dogmaLM):
        return dogmaLM.RemoveGangRequiredSkillModifier
