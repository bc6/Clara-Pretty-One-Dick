#Embedded file name: localizationBSD\localizationTableToMessageUtil.py
"""
Message Utility used for ESP for Add/Update/Remove Groups and Messages
"""
from collections import namedtuple
import log
import blue
from wrappers.message import Message
from wrappers.messageGroup import MessageGroup
_NamedRule = namedtuple('_NamedRule', ['parentID',
 'pattern',
 'default',
 'lookup'])
_mappingRules = {'CATEGORY-NAME': [_NamedRule(24408, '{0}', False, False),
                   _NamedRule(24409, '{0}', False, False),
                   _NamedRule(170, None, True, False),
                   _NamedRule(264, '{0}', False, False)],
 'GROUP-NAME': [_NamedRule(24408, '{0}', False, True), _NamedRule(24409, '{0}', False, True), _NamedRule(264, None, True, True)],
 'TYPE-NAME': [_NamedRule(24408, None, True, True)],
 'TYPE-DESCRIPTION': [_NamedRule(24409, None, True, True)],
 'MARKETGROUP-NAME': [_NamedRule(174, None, True, True)],
 'MARKETGROUP-DESCRIPTION': [_NamedRule(270, None, True, True)],
 'RECRUITMENTTYPE-NAME': [_NamedRule(137, None, True, False)],
 'RECRUITMENTTYPE-DESCRIPTION': [_NamedRule(183, None, True, False)],
 'RACE-NAME': [_NamedRule(128, '{0}', False, False),
               _NamedRule(171, '{0}', False, False),
               _NamedRule(162, '{0}', False, False),
               _NamedRule(198, None, True, False)],
 'RACE-DESCRIPTION': [_NamedRule(139, None, True, False)],
 'BLOODLINE': [_NamedRule(128, None, True, True)],
 'ANCESTRY': [_NamedRule(162, None, True, True)],
 'SPECIALITY': [_NamedRule(171, None, True, True)],
 'DUNGEON-NAME': [_NamedRule(867, '{0} - {1}', True, False),
                  _NamedRule(151, '{0} - {1}', False, False),
                  _NamedRule(251, '{0} - {1}', False, False),
                  _NamedRule(178, '{0} - {1}', False, False),
                  _NamedRule(271, '{0} - {1}', False, False),
                  _NamedRule(166, '{0} - {1}', False, False)],
 'DUNGEON-DESCRIPTION': [_NamedRule(275, '{0} - {1}', True, False)],
 'DUNGEON-MISSIONBRIEFING': [_NamedRule(867, '{0} - {1}', True, False)],
 'DUNGEON-ROOMS': [_NamedRule(178, '{0} - {1}', True, False)],
 'DUNGEON-OBJECTS': [_NamedRule(271, '{0} - {1}', True, False)],
 'DUNGEON-PATHSTEPS': [_NamedRule(151, '{0} - {1}', True, False)],
 'DUNGEON-ENTITIES': [_NamedRule(251, '{0} - {1}', True, False)],
 'DUNGEON-EVENTS': [_NamedRule(166, '{0} - {1}', True, False)],
 'EPICARC-NAME': [_NamedRule(127, None, True, False)],
 'DOGMA-ATTRIBUTES': [_NamedRule(600, None, True, False)],
 'DOGMA-ATTRIBUTES-TOOLTIPS-TITLES': [_NamedRule(28204, None, True, False)],
 'DOGMA-ATTRIBUTES-TOOLTIPS-DESCRIPTIONS': [_NamedRule(28205, None, True, False)],
 'DOGMA-EFFECTS-NAME': [_NamedRule(190, None, True, False)],
 'DOGMA-EFFECTS-DESCRIPTION': [_NamedRule(215, None, True, False)],
 'TUTORIAL-PAGES': [_NamedRule(276, '{0} - {1}', True, False)],
 'AGENT-MISSION-CONTENTNAME': [_NamedRule(200, None, True, False), _NamedRule(150, '{0} - {1}', False, False)],
 'AGENT-MISSION-MESSAGETEXT': [_NamedRule(150, '{0} - {1}', True, False)],
 'INCURSION-REWARD-MESSAGES': [_NamedRule(575, None, True, False)],
 'CORPORATION-ROLES-DESCRIPTION': [_NamedRule(180, None, True, False)],
 'CORPORATION-ROLES-SDESCRIPTION': [_NamedRule(132, None, True, False)]}

def UpdateMessage(mappingRule, key, messageID, messageText, context, columnName, revisionID, lookup, *args):
    """
    Goes through every rule found in mappingRule given and create missing groups where NamedRule.pattern is defined
    and if NamedRule.default is True then we want to check if message exists by the messageID otherwise create new
    message. Update is called on
    
    When using lookup:
        You want to [create new]/update Group under "22408:EVE/Inventory/Types/Names"
        lookup would be : "Sovereignty Structures/a/a"
    
        "EVE/Inventory/Types/Names/Sovereignty Structures/Defense Bunkers"
            
    
    Returns
    -------
    out: messageID
    
    Parameters
    ----------
    mappingRule : lookup value for _mappingRules
    key : record key usually single long value
    messageID : messageID from zlocalization.messages (table)
    messageText : English Text
    context : schema.table.columnName
    columnName : columnName
    revisionID : Parent RevisionID
    lookup : [array of string]
    *args : arguments used in the NamedRule.pattern
    
    Returns
    -------
    HTML String
    
    See also
    --------
    - GetLocalizationTextArea
    - GetLocalizationLabel
    """
    if boot.role == 'server' and not sm.GetService('localizationServer').IsBSDTableDataLoaded():
        log.LogTraceback('Attempting to edit / create localization data without bsdTable wrappers being loaded. Edit ignored! Load the localizationBSD.MessageText bsdTable wrappers first.')
        return -1
    _languageID = 'en-us'
    for mapping in _mappingRules[mappingRule]:
        group = MessageGroup.Get(mapping.parentID)
        if mapping.lookup:
            if lookup is None:
                raise Exception('lookup defined in rule but not passed in!')
            for lookupItem in lookup.split('/'):
                if lookupItem == '':
                    break
                for groupItem in MessageGroup.GetMessageGroupsByParentID(parentID=group.groupID):
                    if groupItem.groupName == lookupItem:
                        group = groupItem
                        break
                else:
                    raise Exception("Can't find MessageGroup(s) in lookup", lookup, lookupItem)

        if mapping.pattern is not None:
            groupName = mapping.pattern.format(*args)
            groupID = _GetGroupID(group.groupID, key)
            if groupID is None:
                group = MessageGroup.Create(parentID=group.groupID, groupName=groupName)
            else:
                group = MessageGroup.Get(groupID)
            if group.groupName != groupName:
                group.groupName = groupName
        if mapping.default:
            message = None
            if messageID is None or messageID == 'None' or messageID == '':
                if messageText is not None and len(messageText) > 0:
                    message = Message.Create(label=None, groupID=group.groupID, text=messageText, context='%s: %s' % (context, key))
                    if '/jessica' in blue.pyos.GetArg():
                        import bsd
                        userID = bsd.login.GetCurrentUserIdOrLogin()
                    else:
                        userID = session.userid
                        if userID is None:
                            raise RuntimeError("Can't edit BSD! No username for editing.")
                    sm.GetService('BSD').RevisionEdit(userID, None, revisionID, **{columnName: message.messageID})
            else:
                message = Message.Get(int(messageID))
                messageEnglishText = message.GetTextEntry(_languageID)
                if messageText is None or len(messageText) == 0:
                    if messageEnglishText is not None:
                        messageEnglishText.text = ''
                    if '/jessica' in blue.pyos.GetArg():
                        import bsd
                        userID = bsd.login.GetCurrentUserIdOrLogin()
                    else:
                        userID = session.userid
                        if userID is None:
                            raise RuntimeError("Can't edit BSD! No username for editing.")
                    sm.GetService('BSD').RevisionEdit(userID, None, revisionID, **{columnName: None})
                    message = None
                elif messageEnglishText is not None:
                    if messageEnglishText.text != messageText:
                        messageEnglishText.text = messageText
                else:
                    message.AddTextEntry(_languageID, messageText)
            if message is not None:
                messageID = message.messageID

    return messageID


def DeleteMessageGroups(mappingRule, key, lookup, *args):
    """
    Goes through every rule found in mappingRule given and deletes the associated
    message groups and all children (groups and messages).
    """
    groupsToDelete = []
    for mapping in _mappingRules[mappingRule]:
        group = MessageGroup.Get(mapping.parentID)
        if mapping.lookup:
            if lookup is None:
                raise Exception('lookup defined in rule but not passed in!')
            for lookupItem in lookup.split('/'):
                for groupItem in MessageGroup.GetMessageGroupsByParentID(parentID=group.groupID):
                    if groupItem.groupName == lookupItem:
                        groupsToDelete.append(groupItem.groupID)
                        break

        if mapping.pattern is not None:
            groupID = _GetGroupID(group.groupID, key)
            if groupID is not None:
                groupsToDelete.append(groupID)

    for groupID in groupsToDelete:
        g = MessageGroup.Get(groupID)
        if not g.Delete():
            log.LogError('Localization update tool:: Error deleting group with id %d and name %s' % (groupID, g.groupName))


def _GetGroupID(parentID, key):
    """
    Try to find groupID of MessageGroup by searching where parent is x and groupName starts with y.
    If we get more that 1 result then we need to go through the result set and return row where
    groupName is equal to key. Is some cases groupName contains "ID - Entitity Name"
    """
    SQL = "\n    SELECT groupID, groupName\n      FROM zlocalization.messageGroups\n     WHERE parentID = %(parentID)i AND\n           groupName like '%(key)s%%'\n    " % {'parentID': parentID,
     'key': str(key).replace("'", "''")}
    rs = sm.GetService('DB2').SQL(SQL)
    if len(rs) == 0:
        return None
    if len(rs) == 1:
        return rs[0].groupID
    for row in rs:
        if row.groupName == key:
            return row.groupID
