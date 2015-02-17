#Embedded file name: eve/client/script/ui/services/mail\mailingListsSvc.py
import service
import util

class MailingLists(service.Service):
    __exportedcalls__ = {'GetDisplayName': [],
     'GetMyMailingLists': [],
     'CreateMailingList': [],
     'JoinMailingList': [],
     'LeaveMaillist': [],
     'DeleteMaillist': [],
     'GetMembers': [],
     'KickMembers': [],
     'SetEntityAccess': [],
     'ClearEntityAccess': [],
     'SetMembersMuted': [],
     'SetMembersOperator': [],
     'SetMembersClear': [],
     'SetDefaultAccess': [],
     'GetSettings': [],
     'GetWelcomeMail': [],
     'SaveWelcomeMail': [],
     'SaveAndSendWelcomeMail': [],
     'ClearWelcomeMail': []}
    __guid__ = 'svc.mailinglists'
    __servicename__ = 'mailinglists'
    __displayname__ = 'Mailing Lists'
    __notifyevents__ = ['OnMailingListSetOperator',
     'OnMailingListSetMuted',
     'OnMailingListSetClear',
     'OnMailingListLeave',
     'OnMailingListDeleted']

    def __init__(self):
        service.Service.__init__(self)
        self.myMailingLists = None

    def Run(self, memStream = None):
        self.state = service.SERVICE_START_PENDING
        self.LogInfo('Starting Mailing Lists Svc')
        self.objectCaching = sm.services['objectCaching']
        self.mailingListsMgr = sm.RemoteSvc('mailingListsMgr')
        self.myMailingLists = self.mailingListsMgr.GetJoinedLists()
        self.externalLists = {}
        self.state = service.SERVICE_RUNNING

    def GetMyMailingLists(self):
        """
            Get the mailing lists that we have joined. The result is a dict of keyvals
            with the listID as the dict key and the keyval with the following entries:
             * name
             * displayName
             * isMuted
             * isOperator
             * isOwner
        """
        return self.myMailingLists

    def GetDisplayName(self, listID):
        """
            Get the name of a specified mailing list, this can be done also for lists
            that you don't belong to.
        """
        if listID in self.myMailingLists:
            return self.myMailingLists[listID].displayName
        if listID in self.externalLists:
            return self.externalLists[listID].displayName
        info = self.mailingListsMgr.GetInfo(listID)
        if info is None:
            raise UserError('MailingListNoSuchList')
        self.externalLists[listID] = info
        return info.displayName

    def CreateMailingList(self, name, defaultAccess = const.mailingListAllowed, defaultMemberAccess = const.mailingListMemberDefault, cost = 0):
        """
            Create a new mailing list. Raises a user error if creation fails, e.g. if
            the name is taken.
        """
        ret = sm.RemoteSvc('mailingListsMgr').Create(name, defaultAccess, defaultMemberAccess, cost)
        key, displayName = util.GetKeyAndNormalize(name)
        self.myMailingLists[ret] = util.KeyVal(name=key, displayName=displayName, isMuted=False, isOperator=False, isOwner=True)
        sm.ScatterEvent('OnMyMaillistChanged')
        return ret

    def JoinMailingList(self, name):
        """
            Join the specified mailing list. Raises a user error if the list doesn't exist.
        """
        ret = self.mailingListsMgr.Join(name)
        self.myMailingLists[ret.id] = ret
        sm.ScatterEvent('OnMyMaillistChanged')
        return ret.id

    def LeaveMaillist(self, listID):
        """
            Leave the specified mailing list
        """
        self.mailingListsMgr.Leave(listID)
        try:
            del self.myMailingLists[listID]
        except KeyError:
            pass

        sm.ScatterEvent('OnMyMaillistChanged')

    def DeleteMaillist(self, listID):
        """
            Delete the specified mailing list. Only the owner of the list can do this.
        """
        self.mailingListsMgr.Delete(listID)
        try:
            del self.myMailingLists[listID]
        except KeyError:
            pass

        sm.ScatterEvent('OnMyMaillistChanged')

    def KickMembers(self, listID, memberIDs):
        """
            Kicks the specified members from the list. Only an operator can do this.
        """
        self.mailingListsMgr.KickMembers(listID, memberIDs)
        self.objectCaching.InvalidateCachedMethodCall('mailingListsMgr', 'GetMembers', listID)

    def GetMembers(self, listID):
        """
            Gets all members of the list. Only an operator can do this.
        """
        members = self.mailingListsMgr.GetMembers(listID)
        sm.GetService('mailSvc').PrimeOwners(members.keys())
        return members

    def SetEntityAccess(self, listID, entityID, access):
        """
            Set mailing list access to const.mailingListBlocked or const.mailingListAllowed for 
            the specified entity (char, corp or alliance)
            This can only be done by an operator
        """
        self.mailingListsMgr.SetEntityAccess(listID, entityID, access)

    def ClearEntityAccess(self, listID, entityID):
        """
            Clear access setting (blocked/allowed) for the specified entity and the 
            given mailing list
            This can only be done by an operator
        """
        self.mailingListsMgr.ClearEntityAccess(listID, entityID)

    def SetMembersMuted(self, listID, memberIDs):
        """
            Set mailing list access to muted for the specified members.
            This can only be done by an operator
        """
        self.mailingListsMgr.SetMembersMuted(listID, memberIDs)
        self.objectCaching.InvalidateCachedMethodCall('mailingListsMgr', 'GetMembers', listID)

    def SetMembersOperator(self, listID, memberIDs):
        """
            Set mailing list access to operator for the specified members.
            This can only be done by an operator
        """
        self.mailingListsMgr.SetMembersOperator(listID, memberIDs)
        self.objectCaching.InvalidateCachedMethodCall('mailingListsMgr', 'GetMembers', listID)

    def SetMembersClear(self, listID, memberIDs):
        """
            Clear mailing list access (operator/muted) for the specified members.
            This can only be done by an operator
        """
        self.mailingListsMgr.SetMembersClear(listID, memberIDs)
        self.objectCaching.InvalidateCachedMethodCall('mailingListsMgr', 'GetMembers', listID)

    def SetDefaultAccess(self, listID, defaultAccess, defaultMemberAccess, mailCost = 0):
        """
            Set default mailing list access to const.mailingListBlocked or const.mailingListAllowed and
            defaultMemberAccess to const.mailingListMemberMuted, const.mailingListMemberDefault or 
            const.mailingListMemberOperator. Also set charge if any. 
            This can only be done by an operator
        """
        self.mailingListsMgr.SetDefaultAccess(listID, defaultAccess, defaultMemberAccess, mailCost)

    def GetSettings(self, listID):
        """
            Gets cost and access settings for the list
        """
        return self.mailingListsMgr.GetSettings(listID)

    def OnMailingListSetOperator(self, listID):
        """
            You have been set as operator on the list
        """
        if listID in self.myMailingLists:
            self.myMailingLists[listID].isOperator = True
            self.myMailingLists[listID].isMuted = False

    def OnMailingListSetMuted(self, listID):
        """
            You have been muted on the list
        """
        if listID in self.myMailingLists:
            self.myMailingLists[listID].isMuted = True
            self.myMailingLists[listID].isOperator = False

    def OnMailingListSetClear(self, listID):
        """
            You have been unmuted and unset as operator on the list
        """
        if listID in self.myMailingLists:
            self.myMailingLists[listID].isMuted = False
            self.myMailingLists[listID].isOperator = False

    def OnMailingListLeave(self, listID, characterID):
        """
            Notify when a character leaves a mailing list (is kicked out)
        """
        if characterID == session.charid and listID in self.myMailingLists:
            try:
                del self.myMailingLists[listID]
            except KeyError:
                pass

            sm.ScatterEvent('OnMyMaillistChanged')

    def OnMailingListDeleted(self, listID):
        """
            Notify when a list is deleted
        """
        if listID in self.myMailingLists:
            try:
                del self.myMailingLists[listID]
            except KeyError:
                pass

            sm.ScatterEvent('OnMyMaillistChanged')

    def GetWelcomeMail(self, listID):
        return self.mailingListsMgr.GetWelcomeMail(listID)

    def SaveWelcomeMail(self, listID, title, body):
        return self.mailingListsMgr.SaveWelcomeMail(listID, title, body)

    def SaveAndSendWelcomeMail(self, listID, title, body):
        return self.mailingListsMgr.SendWelcomeMail(listID, title, body)

    def ClearWelcomeMail(self, listID):
        self.mailingListsMgr.ClearWelcomeMail(listID)
