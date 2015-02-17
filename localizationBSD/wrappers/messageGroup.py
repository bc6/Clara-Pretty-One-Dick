#Embedded file name: localizationBSD/wrappers\messageGroup.py
from . import AuthoringValidationError
from ..const import MESSAGE_GROUPS_TABLE
import bsdWrappers
import bsd
import wordType as locWordType
import message as locMessage
import project as locProject

class MessageGroup(bsdWrappers.BaseWrapper):
    """
    A wrapper object for message groups, where a message is a labeled English string or localized string.  
    """
    __primaryTable__ = bsdWrappers.RegisterTable(MESSAGE_GROUPS_TABLE)

    def __setattr__(self, key, value):
        """
        Sets an attribute on the group, with special behavior when changing the word type.
        Changing the word type will propagate to all messages in the group, removing metadata if messages with a different word type are present.
        """
        if key == 'wordTypeID':
            if self.wordTypeID:
                wordType = locWordType.WordType.Get(self.wordTypeID)
                wordTypeName = wordType.typeName if wordType else 'None'
                raise AuthoringValidationError("Cannot change wordTypeID: Group '%s' (groupID %s) may contain metadata for wordType '%s'; call ResetWordType first to delete all metadata in this group and try again." % (self.groupName, self.groupID, wordTypeName))
            if locWordType.WordType.Get(value) == None:
                raise AuthoringValidationError('WordTypeID (%s) does not exist.' % value)
            with bsd.BsdTransaction():
                for message in locMessage.Message.GetMessagesByGroupID(self.groupID):
                    message.wordTypeID = value

                bsdWrappers.BaseWrapper.__setattr__(self, key, value)
            return
        if key == 'parentID' and value is not None:
            if not MessageGroup.Get(value):
                raise AuthoringValidationError("Cannot set parentID: '%s' is not a valid groupID." % value)
            if self._IsSubGroup(value):
                subGroup = MessageGroup.Get(value)
                raise AuthoringValidationError("You cannot assign group '%s' as a child of group '%s' because it would create a circular reference." % (self.groupName, subGroup.groupName))
        bsdWrappers.BaseWrapper.__setattr__(self, key, value)

    @classmethod
    def Create(cls, parentID = None, groupName = 'New Folder', isReadOnly = None, wordTypeID = None):
        """
        Create a new group.
        parameters:
            wordTypeID - type of the group. Note this parameter doesnt get inherited from parent.
        """
        if not groupName:
            raise AuthoringValidationError('You must specify a group name.')
        messageGroupTable = bsdWrappers.GetTable(MessageGroup.__primaryTable__)
        if groupName:
            groupName = MessageGroup.GenerateUniqueName(parentID, groupName)
        if parentID is not None and MessageGroup.Get(parentID) is None:
            raise AuthoringValidationError('Parent(%s) was not found. Can not create this group. groupName : %s ' % (parentID, groupName))
        newGroup = bsdWrappers.BaseWrapper._Create(cls, parentID=parentID, groupName=groupName, isReadOnly=isReadOnly, wordTypeID=wordTypeID)
        if parentID is not None:
            projectList = locProject.Project.GetProjectsForGroup(parentID)
            for aProject in projectList:
                aProject.AddGroupToProject(newGroup.groupID)

            if MessageGroup.Get(parentID).important:
                newGroup.important = MessageGroup.Get(parentID).important
        return newGroup

    @classmethod
    def Get(cls, groupID):
        """
        Returns the group wrapper corresponding to the supplied groupID.
        """
        return bsdWrappers._TryGetObjByKey(MessageGroup, keyID1=groupID, keyID2=None, keyID3=None, _getDeleted=False)

    def Copy(self, destGroupID):
        """
        Copies the current group wrapper to the destination group, as well as all messages and folders it contains.
        """
        if destGroupID:
            destGroup = MessageGroup.Get(destGroupID)
            if not destGroup:
                raise AuthoringValidationError('Invalid groupID %s' % destGroupID)
            if destGroup.groupID == self.groupID:
                raise AuthoringValidationError('You cannot copy a group into itself.')
            if self._IsSubGroup(destGroup.groupID):
                raise AuthoringValidationError("You cannot copy group '%s' into group '%s' because it is a subgroup of '%s'." % (self.groupName, destGroup.groupName, self.groupName))
        newGroupName = MessageGroup.GenerateUniqueCopyName(self.groupID, destGroupID)
        self._Copy(destGroupID, newGroupName)

    def GetFolderPath(self, projectID = None):
        """
        Generate path to this group as it'll appear in export/pickle file(s).
        NOTE: This is primarily used in UI/Content Browser to show the user how the paths would look like.
              This function doesnt actually care whether this message was tagged with the projectID or not.
              It is also meant to be used by a similar function on Message: GetLabelPath
        parameters:
            projectID - optional parameter. When specified will use Project's working directory when rendering
                        final path string
        returns:
            a path string, of the form: u'/UI/Generic/Buttons'
        """
        pathList = [self.groupName]
        groupDepth = 0
        currentNode = self
        while currentNode.parentID is not None and groupDepth < 100:
            currentNode = MessageGroup.Get(currentNode.parentID)
            if currentNode is not None:
                pathList = [currentNode.groupName] + pathList
            groupDepth += 1

        pathString = '/'.join(pathList)
        if projectID is not None:
            pathString = MessageGroup.TurnIntoRelativePath(pathString, locProject.Project.Get(projectID).workingDirectory)
        return pathString

    @staticmethod
    def TurnIntoRelativePath(absolutePath, workingDirectoryPath):
        """
        Function takes label (absolute) directory path, and project (absolute) working directory path
        then returns relative path version of the first directory path.
        """
        if workingDirectoryPath:
            workingDirectoryPath = workingDirectoryPath.strip('/')
        if absolutePath:
            absolutePath = absolutePath.strip('/')
        if workingDirectoryPath and absolutePath:
            rootPathPrefix = '/'
            workingPathWithSlash = workingDirectoryPath + '/'
            absolutePath += '/'
            if absolutePath.startswith(workingPathWithSlash):
                newPath = absolutePath.replace(workingPathWithSlash, '', 1)
            else:
                newPath = rootPathPrefix + absolutePath
            return newPath.rstrip('/')
        else:
            return absolutePath

    def MarkImportant(self, impValue):
        """
            Sets the "important" bit on the message group to the requested value.
            If includeSubfolders is true, then this affects all subfolders of the 
            group as well.
        """
        self.important = impValue
        childGroups = MessageGroup.GetMessageGroupsByParentID(self.groupID)
        for childGroup in childGroups:
            childGroup.MarkImportant(impValue)

    def RemoveFromProject(self, projectName):
        """
        Untag this group from the project
        """
        projectRow = locProject.Project.GetByName(projectName)
        if not projectRow:
            raise AuthoringValidationError('No project (%s) was found. Can not tag with this project name.' % projectName)
        projectRow.RemoveGroupFromProject(self.groupID)

    def AddToProject(self, projectID):
        """
        Tag this group (and subgroups) with the project
        """
        projectRow = locProject.Project.Get(projectID)
        if not projectRow:
            raise AuthoringValidationError('No project (%s) was found. Can not tag with this project id.' % projectID)
        projectRow.AddGroupToProject(self.groupID)

    def AddToProjectByName(self, projectName):
        """
        Tag this group (and subgroups) with the project
        """
        projectRow = locProject.Project.GetByName(projectName)
        if not projectRow:
            raise AuthoringValidationError('No project (%s) was found. Can not tag with this project name.' % projectName)
        projectRow.AddGroupToProject(self.groupID)

    def GetWordCount(self, languageID = 'en-us', recursive = False, includeMetadata = True, projectID = None):
        """
        Aggregates the word count of all messages in this folder for the specified language.
        """
        wordCount = sum([ message.GetWordCount(languageID=languageID, includeMetadata=includeMetadata) for message in locMessage.Message.GetMessagesByGroupID(self.groupID) ])
        if recursive:
            childGroups = MessageGroup.GetMessageGroupsByParentID(self.groupID, projectID=projectID)
            for childGroup in childGroups:
                wordCount += childGroup.GetWordCount(languageID=languageID, recursive=recursive, projectID=projectID)

        return wordCount

    def _Copy(self, destGroupID, groupName):
        """
        Helper function for the Copy method.
        """
        if sm.GetService('BSD').TransactionOngoing():
            raise AuthoringValidationError('You cannot copy groups from within a transaction.')
        groupID = MessageGroup.Create(parentID=destGroupID, groupName=groupName, isReadOnly=self.isReadOnly, wordTypeID=self.wordTypeID).groupID
        with bsd.BsdTransaction("Copying messages from group '%s' (groupID %s) to %s (groupID %s)" % (self.groupName,
         self.groupID,
         groupName,
         groupID)):
            for message in locMessage.Message.GetMessagesByGroupID(self.groupID):
                message.TransactionAwareCopy(groupID)

        childGroups = MessageGroup.GetMessageGroupsByParentID(self.groupID)
        for group in childGroups:
            group._Copy(groupID, group.groupName)

    def _DeleteChildren(self):
        """
        Deletes all items contained beneath this group.
        """
        with bsd.BsdTransaction():
            childGroups = MessageGroup.GetMessageGroupsByParentID(self.groupID)
            for group in childGroups:
                if not group.Delete():
                    return False

            messages = locMessage.Message.GetMessagesByGroupID(self.groupID)
            for message in messages:
                if not message.Delete():
                    return False

            for aProject in locProject.Project.GetProjectsForGroup(self.groupID):
                aProject.RemoveGroupFromProject(self.groupID)

        return True

    def ResetWordType(self):
        """
        Deletes all existing metadata on all messages in the group, sets their word type to None, and sets the word type of the group to None. 
        """
        with bsd.BsdTransaction():
            for message in locMessage.Message.GetMessagesByGroupID(self.groupID):
                message.ResetWordType()

            bsdWrappers.BaseWrapper.__setattr__(self, 'wordTypeID', None)

    def _IsSubGroup(self, groupID):
        """
        Returns True if the specified groupID is in a folder beneath the current group.
        """
        testGroup = MessageGroup.Get(groupID)
        while testGroup.parentID != None:
            if testGroup.parentID == self.groupID:
                return True
            testGroup = MessageGroup.Get(testGroup.parentID)

        return False

    @staticmethod
    def GetMessageGroupsByParentID(parentID, projectID = None):
        """
        Returns all subgroups directly beneath the parent group. 
        If ProjectID is specified then return all subgroups under this group, tagged for this project.
        """
        if projectID:
            currentProject = locProject.Project.Get(projectID)
            return currentProject.GetMessageGroupsByParentID(parentID)
        else:
            return MessageGroup.GetWithFilter(parentID=parentID)

    @staticmethod
    def GetVisibleGroupsByParentID(parentID, projectID = None):
        """
        Returns all subgroups directly beneath the parent group.
        If ProjectID is specified then return all subgroups under this group, tagged for this project, 
        plus those that have at least one child group tagged for this project as well.
        NOTE: this method in particular useful for UI that's building the group tree structure.
        """
        if projectID:
            currentProject = locProject.Project.Get(projectID)
            return currentProject.GetVisibleGroupsByParentID(parentID)
        else:
            return MessageGroup.GetMessageGroupsByParentID(parentID)

    @staticmethod
    def GenerateUniqueName(destGroupID, groupName):
        """
        Given a target location and a requested group name, creates an Explorer-style unique name by appending (n)
        to the end of the group name, where n is the first available number not in use by another group.
        
        It is acceptable for groups and messages to have the same name, but two groups with the same parent must have unique names. 
        """
        groupNames = [ group.groupName for group in MessageGroup.GetMessageGroupsByParentID(destGroupID) ]
        numDuplicates = 2
        newLabel = groupName
        while True:
            if newLabel not in groupNames:
                return newLabel
            newLabel = ''.join((groupName,
             ' (',
             str(numDuplicates),
             ')'))
            numDuplicates += 1

    @staticmethod
    def GenerateUniqueCopyName(sourceGroupID, destGroupID):
        """
        Given source and destination groups, creates an Explorer-style unique name, either by
        appending (n) to the end of the group name, if the group is being copied to another folder, or by 
        appending "- Copy" to the end of the name (and then potentially adding (n)) if the group is being
        copied to the same folder.  
        
        It is acceptable for groups and messages to have the same name, but two groups with the same parent must have unique names.
        
        parameters:
            sourceGroupID    - groupID of the group being copied.
            destGroupID      - groupID of the group we are copying the source group to.         
        """
        sourceGroup = MessageGroup.Get(sourceGroupID)
        if not sourceGroup:
            raise AuthoringValidationError('%s is not a valid groupID' % sourceGroupID)
        if sourceGroup.parentID == destGroupID:
            return MessageGroup.GenerateUniqueName(destGroupID, sourceGroup.groupName + ' - Copy')
        return MessageGroup.GenerateUniqueName(destGroupID, sourceGroup.groupName)
