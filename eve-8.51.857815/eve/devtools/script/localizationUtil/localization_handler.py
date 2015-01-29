#Embedded file name: eve/devtools/script/localizationUtil\localization_handler.py
"""
A presenter for the insider tool for editing of EVE localization strings.
"""
from eve.client.script.ui.control import entries as listentry
import localization
import os
try:
    from fsdLocalizationCache import SetPerforceWrapper
    from fsdLocalizationCache.messageGroupHierarchy import MessageGroupHierarchy
    from fsdLocalizationCache.idGenerator import GetNewMessageID
except ImportError:
    pass

try:
    from P4 import P4
except ImportError:
    P4 = None

DISALLOWED_GROUPS = [476]

def HasP4Wrapper():
    return P4 is not None


branchRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
eveDataRoot = os.path.join(branchRoot, 'eve', 'staticData', 'localization', 'data')

class LocalizationHandler(object):

    def __init__(self):
        self.hierarchy = MessageGroupHierarchy()
        self.hierarchy.LoadGroupHierarchyFromFolder(eveDataRoot)
        if HasP4Wrapper():
            self.p4 = P4()
            self.p4.connect()
            self.SetP4()
        else:
            eve.Message('CustomNotify', {'notify': "Unable to connect to Perforce. You can browse messages but you can't change anything"})

    def SetP4(self):
        SetPerforceWrapper(self.p4)

    def GetScrollList(self, groupEntry = None):
        if groupEntry is not None:
            group = self.hierarchy.GetGroup(groupEntry.groupID)
            groupsForGroup = self.GetGroupsForGroup(group)
            messagesForGroup = self.GetMessagesForGroup(group)
            scrolllist = self.GetGroupScrollList(groupsForGroup, messagesForGroup, self.GetSubLevel(groupEntry), group.groupID)
        else:
            scrolllist = self.GetGroupScrollList([self.hierarchy.GetGroup(1)], [], level=0)
        return scrolllist

    def GetSubLevel(self, group):
        return group.sublevel + 1

    def GetGroupsForGroup(self, group):
        groupsForGroup = []
        for groupID in self.hierarchy.GetAllSubgroupIDsForGroupID(group.groupID):
            if groupID not in DISALLOWED_GROUPS:
                groupsForGroup.append(self.hierarchy.GetGroup(groupID))

        return groupsForGroup

    def GetMessagesForGroup(self, group):
        messagesForGroup = []
        for messageID in group.messages:
            message = group.GetMessage(messageID)
            if message.label:
                messagesForGroup.append(message)

        return messagesForGroup

    def GetGroupScrollList(self, groupsOfGroup, messagesOfGroup, level, groupID = None):
        groupList = []
        messageList = []
        for group in groupsOfGroup:
            groupData = self.GetGroupData(group, level)
            groupList.append((group.groupName, listentry.Get('Group', groupData)))

        for message in messagesOfGroup:
            messageData = self.GetMessageData(message, level, groupID)
            messageList.append((message.label, listentry.Get('Generic', messageData)))

        groupList = [ item for item in localization.util.Sort(groupList, key=lambda x: x[0][1].lower()) ]
        messageList = [ item for item in localization.util.Sort(messageList, key=lambda x: x[0][1].lower()) ]
        groupList = [ item[1] for item in sorted(groupList, key=lambda x: x[0][0].lower()) ]
        messageList = [ item[1] for item in sorted(messageList, key=lambda x: x[0][0].lower()) ]
        return groupList + messageList

    def GetGroupData(self, group, level):
        return {'GetSubContent': self.GetScrollList,
         'label': group.groupName,
         'id': (group.groupName, group.groupID),
         'groupID': group.groupID,
         'type': 'group',
         'GetGroup': self.GetGroup,
         'CreateMessage': self.CreateMessage,
         'CreateNewMessage': self.CreateNewMessage,
         'AddMessage': group.AddMessage,
         'sublevel': level,
         'showlen': 0,
         'BlockOpenWindow': 1,
         'MenuFunction': self.GetGroupContextMenu}

    def GetMessageData(self, message, level, groupID):
        return {'label': message.label,
         'id': (message.label, message.messageID),
         'messageID': message.messageID,
         'type': 'message',
         'parentGroupID': groupID,
         'OnClick': self.SelectMessage,
         'GetMessage': self.GetMessage,
         'DeleteEntry': self.DeleteEntry,
         'DeleteMessage': self.DeleteMessage,
         'GetTextVersion': self.GetTextVersion,
         'UpdateMessage': self.UpdateMessage,
         'sublevel': level,
         'showlen': 0,
         'BlockOpenWindow': 1,
         'GetMenu': self.GetMessageContextMenu}

    def GetGroupContextMenu(self, groupNode, *args):
        groupContextMenu = []
        groupContextMenu.append(('New Message', self.CreateMessage, (groupNode,)))
        return groupContextMenu

    def GetMessageContextMenu(self, messageEntry):
        messageNode = messageEntry.sr.node
        messageContextMenu = []
        messageContextMenu.append(('Delete Message', self.DeleteEntry, (messageNode,)))
        return messageContextMenu

    def GetMessage(self, messageID):
        return self.hierarchy.GetMessageByID(messageID)

    def GetGroup(self, groupID):
        return self.hierarchy.GetGroup(groupID)

    def DeleteMessage(self, messageNode):
        self.IsPerforceConnected()
        group = self.GetGroup(messageNode.parentGroupID)
        group.DeleteMessage(messageNode.messageID)
        self.WriteChanges()

    def GetTextVersion(self, messageNode):
        group = self.hierarchy.GetGroup(messageNode.parentGroupID)
        message = group.GetMessage(messageNode.messageID)
        return message.GetTextVersion('en-us')

    def CreateNewMessage(self, groupNode, label, text, context):
        self.IsPerforceConnected()
        newMessageID = GetNewMessageID()
        groupNode.AddMessage(newMessageID, label, context, {u'en-us': text}, {})
        self.WriteChanges()
        return newMessageID

    def WriteChanges(self):
        self.hierarchy.WriteHierarchyToDisk(eveDataRoot)

    def IsPerforceConnected(self):
        try:
            self.p4.run_login('-s')
            return True
        except Exception:
            raise UserError('CustomError', {'error': 'Your Perforce connection has expired, please relog. You might also need to re-open this localization window.'})

    def UpdateMessage(self, messageNode, label, text, context):
        self.IsPerforceConnected()
        message = self.GetMessage(messageNode.messageID)
        message.UpdateText('en-us', text)
        message.label = label
        message.context = context
        self.WriteChanges()

    def IterAllowedMessages(self, messages):
        """
        Takes in a list of messages and returns a filtered list based on illegal groups.
        """
        for message in messages:
            yield message

    def GetSearchedMessagesByLabel(self, label):
        """
        Takes in a string of text and returns messages that have the text in their label.
        """
        messages = self.IterAllowedMessages(self.hierarchy.IterMessagesByLabel(label))
        return self.GetGroupScrollList([], messages, 0)

    def GetSearchedMessagesByID(self, messageID):
        """
        Takes in an int and returns messages that have the value a part of their messageID.
        """
        messages = self.IterAllowedMessages(self.hierarchy.IterMessagesByID(messageID))
        return self.GetGroupScrollList([], messages, 0)

    def GetSearchedMessagesByText(self, text):
        """
        Takes in a string of text and returns messages that have the text in their english text.
        """
        messages = self.IterAllowedMessages(self.hierarchy.IterMessagesByText(text))
        return self.GetGroupScrollList([], messages, 0)

    def GetSearchedMessagesByPath(self, path):
        """
        Takes in a string of text and returns messages that have the text in their localization path.
        """
        messages = self.IterAllowedMessages(self.hierarchy.IterMessagesByPath(path))
        return self.GetGroupScrollList([], messages, 0)
