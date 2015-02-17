#Embedded file name: dogma/effects\__init__.py
EXPRESSIONS = {'LocationRequiredSkillModifier': 'on all items located in {domain} requiring skill {skillTypeID}',
 'LocationGroupModifier': 'on all items located in {domain} in group {groupID}',
 'OwnerRequiredSkillModifier': 'on all items owned by {domain} that require skill {skillTypeID}',
 'ItemModifier': '{domain}',
 'GangItemModifier': 'on ships in gang',
 'GangRequiredSkillModifier': 'on items fitted to ships in gang that require skill {skillTypeID}'}

def _GetModifierDict(realDict):
    ret = {}
    for key, value in realDict.iteritems():
        if key in ('modifiedAttributeID', 'modifyingAttributeID'):
            newValue = cfg.dgmattribs.Get(value).attributeName
        elif key == 'domain':
            if value is None:
                newValue = 'self'
            else:
                newValue = value.replace('ID', '')
        elif key == 'skillTypeID':
            newValue = cfg.invtypes.Get(value).typeName
        elif key == 'groupID':
            newValue = cfg.invgroups.Get(value).groupName
        else:
            newValue = value
        ret[key] = newValue

    ret['domainInfo'] = EXPRESSIONS.get(ret['func'], ' UNKNOWN {func}').format(**ret)
    return ret


def IterReadableModifierStrings(modifiers):
    for modifierDict in modifiers:
        yield 'modifies {modifiedAttributeID} on {domainInfo} with attribute {modifyingAttributeID}'.format(**_GetModifierDict(modifierDict))


def IsCloakingEffect(effectID):
    return effectID in [const.effectCloaking, const.effectCloakingWarpSafe, const.effectCloakingPrototype]


class Effect:
    __guid__ = 'dogmaXP.Effect'
    isPythonEffect = True
    __modifier_only__ = False
    __modifies_character__ = False
    __modifies_ship__ = False

    def RestrictedStop(self, *args):
        pass

    def PreStartChecks(self, *args):
        """
            These are the custom checks that have to be made before the toll for
            starting the effect is taken.
        """
        pass

    def StartChecks(self, *args):
        pass

    def Start(self, *args):
        pass

    def Stop(self, *args):
        pass


def GetName(effectID):
    return cfg.dgmeffects.Get(effectID).effectName


def IsDefault(typeID, effectID):
    for effectRow in cfg.dgmtypeeffects[typeID]:
        if effectID == effectRow.effectID:
            if effectRow.isDefault:
                return True
            else:
                return False

    raise KeyError()
