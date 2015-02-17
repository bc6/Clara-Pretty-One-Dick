#Embedded file name: eve/client/script/ui/services/mail\mailSvc.py
import service
import blue
import sys
import log
import os
import const
import carbonui.const as uiconst
import shelve
import util
import zlib
import form
import xtriui
from notifications.common.formatters.mailsummary import MailSummaryFormatter
from notifications.common.formatters.newMail import NewMailFormatter
import uiutil
import uthread
import copy
import localization
from characterSettingsStorage.characterSettingsObject import CharacterSettingsObject
from eve.common.script.util.notificationconst import groupNamePaths as notificationGroupNamePaths
import characterSettingsStorage.characterSettingsConsts as cSettings
from eveexceptions.exceptionEater import ExceptionEater
import eve.common.script.util.notificationconst as notificationConst
MAIL_PATH = blue.paths.ResolvePath('cache:/EveMail/')
BODIES_IN_CACHE = 30
MAIL_FILE_HEADER_VERSION = 5
MAIL_FILE_BODY_VERSION = 1
ALL_LABELS = 255
swatchColors = {0: ('ffffff', 0),
 1: ('ffff01', 1),
 2: ('ff6600', 2),
 3: ('fe0000', 3),
 4: ('9a0000', 4),
 5: ('660066', 5),
 6: ('0000fe', 6),
 7: ('0099ff', 7),
 8: ('01ffff', 8),
 9: ('00ff33', 9),
 10: ('349800', 10),
 11: ('006634', 11),
 12: ('666666', 12),
 13: ('999999', 13),
 14: ('e6e6e6', 14),
 15: ('ffffcd', 15),
 16: ('99ffff', 16),
 17: ('ccff9a', 17)}

class mailSvc(service.Service):
    __guid__ = 'svc.mailSvc'
    __displayname__ = 'Mail service'
    __exportedcalls__ = {'MoveMessagesToTrash': [],
     'MoveMessagesFromTrash': [],
     'MarkMessagesAsUnread': [],
     'MarkMessagesAsRead': [],
     'MoveAllToTrash': [],
     'MoveToTrashByLabel': [],
     'MoveToTrashByList': [],
     'MoveAllFromTrash': [],
     'MarkAllAsUnread': [],
     'MarkAsUnreadByLabel': [],
     'MarkAsUnreadByList': [],
     'MarkAllAsRead': [],
     'MarkAsReadByLabel': [],
     'MarkAsReadByList': [],
     'EmptyTrash': [],
     'DeleteMails': [],
     'GetBody': [],
     'GetMailsByLabelOrListID': [],
     'SyncMail': [],
     'GetLabels': [],
     'EditLabel': [],
     'CreateLabel': [],
     'DeleteLabel': [],
     'AssignLabels': [],
     'RemoveLabels': [],
     'SaveChangesToDisk': [],
     'ClearCache': [],
     'SendMail': [],
     'IsFileCacheCorrupted': [],
     'PrimeOwners': []}
    __notifyevents__ = ['OnMailSent',
     'OnMailDeleted',
     'OnMailUndeleted',
     'OnSessionChanged']
    __startupdependencies__ = ['settings']

    def __init__(self):
        service.Service.__init__(self)
        self.mailSynced = 0
        self.cacheFileCorruption = False

    def Run(self, ms = None):
        self.state = service.SERVICE_START_PENDING
        self.mailMgr = sm.RemoteSvc('mailMgr')
        self.mailHeaders = {}
        self.mailBodies = {}
        self.mailBodiesOrder = []
        self.labels = None
        self.needToSaveHeaders = False
        self.isSaving = False
        self.blinkTab = False
        self.blinkNeocom = False
        self.donePrimingRecipients = False
        self.characterSettings = None
        self.mailSettingObject = None
        if session.charid:
            self.mailFileHeaders = MAIL_PATH + 'mailheaders_' + str(session.charid)
            self.mailFileBodies = MAIL_PATH + 'mailbodies_' + str(session.charid)
        try:
            if not os.path.exists(MAIL_PATH):
                os.mkdir(MAIL_PATH)
        except:
            self.LogError('Error creating mail cache folder. charid:', str(session.charid))
            self.cacheFileCorruption = True
            self.TryCloseMailWindow()
            raise UserError('MailCacheFileError')

        self.state = service.SERVICE_RUNNING

    def OnSessionChanged(self, isremote, session, change):
        if 'charid' in change and session.charid:
            self.mailFileHeaders = MAIL_PATH + 'mailheaders_' + str(session.charid)
            self.mailFileBodies = MAIL_PATH + 'mailbodies_' + str(session.charid)

    def PrimeOwners(self, owners):
        """
            Prime the owners in the list
        """
        uthread.Lock(self, 'Prime')
        try:
            toprime = []
            for ownerID in owners:
                if ownerID not in cfg.eveowners:
                    toprime.append(ownerID)

            if len(toprime) > 0:
                primed = self.mailMgr.PrimeOwners(toprime)
                for ownerID in primed:
                    cfg.eveowners.data[ownerID] = primed[ownerID]

        finally:
            uthread.UnLock(self, 'Prime')

    def TrySyncMail(self):
        if not self.mailSynced:
            try:
                self.SyncMail()
            except UserError as e:
                raise
            except Exception as e:
                log.LogException('mail failed to load')
                raise UserError('CustomInfo', {'info': localization.GetByLabel('UI/Mail/FailedToLoad')})

    def SyncMail(self):
        """
            Synchronizes the mail that is cached on disk so it matches the status on the server.
            All mail headers in the cache are then put into memory.
            self.mailHeaders holds the mail headers in memory and that is a dict on the messageID
            with a keyval value containing:
             * senderID - int
             * senderName  - str
             * toCharacterIDs - list of characterIDs
             * toListID - the ID of the mailing list
             * toCorpOrAllianceID = id of the alliance or corp getting this mail
             * subject - str
             * sentDate - date
             * read - boolean
             * replied - boolean
             * forwarded - boolean
             * trashed - boolean
             * statusMask - int
             * labelMask - int
             * labels - list of int
        """
        self.LogInfo('Syncing mail')
        uthread.Lock(self)
        try:
            if self.__ReadFromHeaderFile('version') != MAIL_FILE_HEADER_VERSION:
                self.__ClearHeaderCache()
                self.__WriteToHeaderFile('version', MAIL_FILE_HEADER_VERSION)
            if self.__ReadFromBodyFile('version') != MAIL_FILE_BODY_VERSION:
                self.__ClearBodyCache()
                self.__WriteToBodyFile('version', MAIL_FILE_BODY_VERSION)
            self.mailHeaders = self.__ReadFromHeaderFile('mail')
            if self.mailHeaders is None:
                self.mailHeaders = {}
                self.__WriteToHeaderFile('mail', {})
            lastID = 0
            firstID = sys.maxint
            for messageID in self.mailHeaders:
                if messageID > lastID:
                    lastID = messageID
                if messageID < firstID:
                    firstID = messageID

            if lastID == 0:
                firstID = None
            mailbox = self.mailMgr.SyncMail(firstID, lastID)
            toPrime = set()
            incoming = mailbox.newMail
            if mailbox.oldMail is not None:
                incoming.extend(mailbox.oldMail)
            for mailRow in incoming:
                toPrime.add(mailRow.senderID)
                toListID = mailRow.toListID
                toCharacterIDs = []
                if mailRow.toCharacterIDs:
                    toCharacterIDs = [ int(x) for x in mailRow.toCharacterIDs.split(',') ]
                m = util.KeyVal(messageID=mailRow.messageID, senderID=mailRow.senderID, toCharacterIDs=toCharacterIDs, toListID=toListID, toCorpOrAllianceID=mailRow.toCorpOrAllianceID, subject=mailRow.title, sentDate=mailRow.sentDate)
                self.mailHeaders[mailRow.messageID] = m

            toDelete = self.mailHeaders.keys()
            toFetch = {}
            for statusRow in mailbox.mailStatus:
                if statusRow.messageID not in self.mailHeaders:
                    m = util.KeyVal(messageID=statusRow.messageID, read=statusRow.statusMask & const.mailStatusMaskRead == const.mailStatusMaskRead, replied=statusRow.statusMask & const.mailStatusMaskReplied == const.mailStatusMaskReplied, forwarded=statusRow.statusMask & const.mailStatusMaskForwarded == const.mailStatusMaskForwarded, trashed=statusRow.statusMask & const.mailStatusMaskTrashed == const.mailStatusMaskTrashed, statusMask=statusRow.statusMask, labels=self.GetLabelMaskAsList(statusRow.labelMask), labelMask=statusRow.labelMask)
                    toFetch[statusRow.messageID] = m
                else:
                    toDelete.remove(statusRow.messageID)
                    mail = self.mailHeaders[statusRow.messageID]
                    if getattr(mail, 'statusMask', None) != statusRow.statusMask:
                        mail.statusMask = statusRow.statusMask
                        mail.read = mail.statusMask & const.mailStatusMaskRead == const.mailStatusMaskRead
                        mail.replied = mail.statusMask & const.mailStatusMaskReplied == const.mailStatusMaskReplied
                        mail.forwarded = mail.statusMask & const.mailStatusMaskForwarded == const.mailStatusMaskForwarded
                        mail.trashed = mail.statusMask & const.mailStatusMaskTrashed == const.mailStatusMaskTrashed
                    if getattr(mail, 'labelMask', None) != statusRow.labelMask:
                        mail.labelMask = statusRow.labelMask
                        mail.labels = self.GetLabelMaskAsList(mail.labelMask)
                    if mail.statusMask & const.mailStatusMaskAutomated > 0 and mail.senderID == mail.toListID and mail.senderID in toPrime:
                        toPrime.remove(mail.senderID)

            if len(toFetch) > 0:
                revivedMail = self.mailMgr.GetMailHeaders(toFetch.keys())
                for mailRow in revivedMail:
                    toListID = mailRow.toListID
                    toCharacterIDs = []
                    if mailRow.toCharacterIDs:
                        toCharacterIDs = [ int(x) for x in mailRow.toCharacterIDs.split(',') ]
                    mail = toFetch[mailRow.messageID]
                    mail.senderID = mailRow.senderID
                    mail.toCharacterIDs = toCharacterIDs
                    mail.toListID = toListID
                    mail.toCorpOrAllianceID = mailRow.toCorpOrAllianceID
                    mail.subject = mailRow.title
                    mail.sentDate = mailRow.sentDate
                    if mail.statusMask & const.mailStatusMaskAutomated == 0 or mail.senderID != mail.toListID:
                        toPrime.add(mail.senderID)
                    self.mailHeaders[mailRow.messageID] = mail

            self.PrimeOwners(list(toPrime))
            for mail in self.mailHeaders.itervalues():
                if hasattr(mail, 'senderName'):
                    continue
                if mail.senderID is None:
                    raise RuntimeError('Invalid mail item', mail)
                if mail.statusMask & const.mailStatusMaskAutomated and mail.senderID == mail.toListID:
                    mail.senderName = sm.GetService('mailinglists').GetDisplayName(mail.senderID)
                else:
                    try:
                        mail.senderName = cfg.eveowners.Get(mail.senderID).name
                    except IndexError:
                        mail.senderName = localization.GetByLabel('UI/Generic/Unknown')

            for messageID in toDelete:
                del self.mailHeaders[messageID]
                self.__DeleteFromBodyFile(messageID)

            self.__WriteToHeaderFile('mail', self.mailHeaders)
            self.mailSynced = 1
        finally:
            uthread.UnLock(self)

        self.LogInfo('Done syncing mail')

    def GetLabelMaskAsList(self, mask):
        if mask < 0:
            raise RuntimeError('Invalid label mask', mask)
        counter = 0
        labels = []
        while mask != 0:
            mask, bitSet = divmod(mask, 2)
            if bitSet == 1:
                labels.append(pow(2, counter))
            counter += 1

        return labels

    def GetUnreadCounts(self):
        """
            Get unread counts for labels and mailing lists
        """
        self.LogInfo('GetUnreadCounts')
        unreadCounts = util.KeyVal(labels={}, lists={})
        totalUnread = 0
        for messageID, message in self.mailHeaders.iteritems():
            if not message.read and not message.trashed:
                totalUnread += 1
                mask = message.labelMask
                counter = 0
                while mask != 0:
                    mask, bitSet = divmod(mask, 2)
                    if bitSet == 1:
                        labelID = pow(2, counter)
                        if labelID in unreadCounts.labels:
                            unreadCounts.labels[labelID] += 1
                        else:
                            unreadCounts.labels[labelID] = 1
                    counter += 1

                if message.toListID is not None:
                    if message.toListID in unreadCounts.lists:
                        unreadCounts.lists[message.toListID] += 1
                    else:
                        unreadCounts.lists[message.toListID] = 1

        unreadCounts.labels[None] = totalUnread
        self.LogInfo('unreadCounts:', unreadCounts)
        return unreadCounts

    def CheckShouldStopBlinking(self, *args):
        allUnreadGroups = self.GetUnreadCounts()
        allUnread = allUnreadGroups.labels.get(None, 0)
        if allUnread == 0:
            self.StopMailBlinking()

    def StopMailBlinking(self, *args):
        self.SetBlinkTabState(False)
        sm.ScatterEvent('OnMailStartStopBlinkingTab', 'mail', 0)
        self.SetBlinkNeocomState(False)
        sm.GetService('neocom').BlinkOff('mail')

    def MoveMessagesToTrash(self, messageIDs):
        self.LogInfo('Move to trash', messageIDs)
        self.mailMgr.MoveToTrash(messageIDs)
        for messageID in messageIDs:
            mail = self.mailHeaders[messageID]
            mail.trashed = True
            mail.statusMask = mail.statusMask | const.mailStatusMaskTrashed

        self.needToSaveHeaders = True
        self.CheckShouldStopBlinking()

    def MoveMessagesFromTrash(self, messageIDs):
        self.LogInfo('Move from trash', messageIDs)
        self.mailMgr.MoveFromTrash(messageIDs)
        for messageID in messageIDs:
            mail = self.mailHeaders[messageID]
            mail.trashed = False
            mail.statusMask = mail.statusMask & ALL_LABELS - const.mailStatusMaskTrashed

        self.needToSaveHeaders = True
        sm.ScatterEvent('OnMailCountersUpdate')

    def MarkMessagesAsUnread(self, messageIDs):
        self.LogInfo('Mark as unread', messageIDs)
        self.mailMgr.MarkAsUnread(messageIDs)
        for messageID in messageIDs:
            mail = self.mailHeaders[messageID]
            mail.read = False
            mail.statusMask = mail.statusMask & ALL_LABELS - const.mailStatusMaskRead

        self.needToSaveHeaders = True
        sm.ScatterEvent('OnMailCountersUpdate')

    def MarkMessagesAsRead(self, messageIDs, notifyServer = True):
        self.LogInfo('Mark as read', messageIDs, notifyServer)
        if notifyServer:
            self.mailMgr.MarkAsRead(messageIDs)
        for messageID in messageIDs:
            mail = self.mailHeaders[messageID]
            mail.read = True
            mail.statusMask = mail.statusMask | const.mailStatusMaskRead

        self.needToSaveHeaders = True
        sm.ScatterEvent('OnMailCountersUpdate')
        self.CheckShouldStopBlinking()

    def MoveAllToTrash(self):
        """
            Move all mail to the trash
        """
        self.LogInfo('Move all to trash')
        self.mailMgr.MoveAllToTrash()
        for mail in self.mailHeaders.itervalues():
            mail.trashed = True
            mail.statusMask = mail.statusMask | const.mailStatusMaskTrashed

        self.needToSaveHeaders = True

    def MoveToTrashByLabel(self, labelID):
        """
            Move all mail that has the specified label to the trash 
        """
        self.LogInfo('Move label to trash', labelID)
        self.mailMgr.MoveToTrashByLabel(labelID)
        for mail in self.mailHeaders.itervalues():
            if mail.labelMask & labelID == labelID:
                mail.trashed = True
                mail.statusMask = mail.statusMask | const.mailStatusMaskTrashed

        self.needToSaveHeaders = True

    def MoveToTrashByList(self, listID):
        """
            Move all mail that was sent to the specified list to the trash 
        """
        self.LogInfo('Move list to trash', listID)
        self.mailMgr.MoveToTrashByList(listID)
        for mail in self.mailHeaders.itervalues():
            if mail.toListID is not None and listID == mail.toListID:
                mail.trashed = True
                mail.statusMask = mail.statusMask | const.mailStatusMaskTrashed

        self.needToSaveHeaders = True

    def MarkAllAsUnread(self):
        """
            Mark all mail as unread
        """
        self.LogInfo('Mark all as unread')
        self.mailMgr.MarkAllAsUnread()
        for mail in self.mailHeaders.itervalues():
            if not mail.trashed:
                mail.read = False
                mail.statusMask = mail.statusMask & ALL_LABELS - const.mailStatusMaskRead

        self.needToSaveHeaders = True

    def MarkAsUnreadByLabel(self, labelID):
        """
            Mark all mail that has the specified label as unread
        """
        self.LogInfo('Mark label unread', labelID)
        self.mailMgr.MarkAsUnreadByLabel(labelID)
        for mail in self.mailHeaders.itervalues():
            if not mail.trashed and mail.labelMask & labelID == labelID:
                mail.read = False
                mail.statusMask = mail.statusMask & ALL_LABELS - const.mailStatusMaskRead

        self.needToSaveHeaders = True

    def MarkAsUnreadByList(self, listID):
        """
            Mark all mail that was sent to the specified list as unread
        """
        self.LogInfo('Mark list unread', listID)
        self.mailMgr.MarkAsUnreadByList(listID)
        for mail in self.mailHeaders.itervalues():
            if not mail.trashed and mail.toListID is not None and listID == mail.toListID:
                mail.read = False
                mail.statusMask = mail.statusMask & ALL_LABELS - const.mailStatusMaskRead

        self.needToSaveHeaders = True

    def MarkAllAsRead(self):
        """
            Mark all mail as read
        """
        self.LogInfo('Mark all read')
        self.mailMgr.MarkAllAsRead()
        for mail in self.mailHeaders.itervalues():
            if not mail.trashed:
                mail.read = True
                mail.statusMask = mail.statusMask | const.mailStatusMaskRead

        self.needToSaveHeaders = True

    def MarkAsReadByLabel(self, labelID):
        """
            Mark all mail that has the specified label as read
        """
        self.LogInfo('Mark label read', labelID)
        self.mailMgr.MarkAsReadByLabel(labelID)
        for mail in self.mailHeaders.itervalues():
            if not mail.trashed and mail.labelMask & labelID == labelID:
                mail.read = True
                mail.statusMask = mail.statusMask | const.mailStatusMaskRead

        self.needToSaveHeaders = True

    def MarkAsReadByList(self, listID):
        """
            Mark all mail that was sent to the specified list as read
        """
        self.LogInfo('Mark list read', listID)
        self.mailMgr.MarkAsReadByList(listID)
        for mail in self.mailHeaders.itervalues():
            if not mail.trashed and mail.toListID is not None and listID == mail.toListID:
                mail.read = True
                mail.statusMask = mail.statusMask | const.mailStatusMaskRead

        self.needToSaveHeaders = True

    def MoveAllFromTrash(self):
        """
            Move all mail from the trash
        """
        self.LogInfo('Move all from trash')
        self.mailMgr.MoveAllFromTrash()
        for mail in self.mailHeaders.itervalues():
            mail.trashed = False
            mail.statusMask = mail.statusMask & ALL_LABELS - const.mailStatusMaskTrashed

        self.needToSaveHeaders = True

    def EmptyTrash(self):
        """
            Permanently delete all mail that is in the trash
        """
        self.LogInfo('Empty trash')
        self.mailMgr.EmptyTrash()
        deleted = []
        for messageID, mail in self.mailHeaders.iteritems():
            if mail.trashed:
                deleted.append(messageID)

        self.LogInfo('Deleted', len(deleted), 'messages')
        for messageID in deleted:
            del self.mailHeaders[messageID]
            if messageID in self.mailBodies:
                del self.mailBodies[messageID]
            if messageID in self.mailBodiesOrder:
                self.mailBodiesOrder.remove(messageID)
            self.__DeleteFromBodyFile(messageID)

        self.needToSaveHeaders = True

    def DeleteMails(self, messageIDs):
        self.LogInfo('Delete', messageIDs)
        self.mailMgr.DeleteMail(messageIDs)
        for messageID in messageIDs:
            if messageID in self.mailHeaders:
                del self.mailHeaders[messageID]
            if messageID in self.mailBodies:
                del self.mailBodies[messageID]
            if messageID in self.mailBodiesOrder:
                self.mailBodiesOrder.remove(messageID)
            self.__DeleteFromBodyFile(messageID)

        self.needToSaveHeaders = True

    def GetBody(self, messageID):
        self.LogInfo('GetMailBody', messageID)
        if messageID in self.mailBodies:
            self.LogInfo('Cached')
            if not self.mailHeaders[messageID].read:
                self.MarkMessagesAsRead([messageID])
            return self.mailBodies[messageID]
        if len(self.mailBodiesOrder) > BODIES_IN_CACHE:
            try:
                self.LogInfo('Must make room in cache')
                del self.mailBodies[self.mailBodiesOrder.pop(0)]
            except KeyError:
                pass

        if messageID in self.mailHeaders:
            body = self.__ReadFromBodyFile(messageID)
            if body is None:
                compressedBody = self.mailMgr.GetBody(messageID, not self.mailHeaders[messageID].read)
                if compressedBody is None:
                    return ''
                body = zlib.decompress(compressedBody).decode('utf-8')
                self.__WriteToBodyFile(messageID, body)
            self.MarkMessagesAsRead([messageID], False)
            self.mailBodies[messageID] = body
            self.mailBodiesOrder.append(messageID)
            return body
        self.LogError("Asking me to get a body, but I can't find the messageID asked for in self.mailHeaders. messageID:", messageID)

    def GetMailsByLabelOrListID(self, labelID = None, orderBy = None, ascending = False, pos = 0, count = 20, listID = None):
        """
           Gets either a list of mails with a specific label or that was sent to a specific mailinglist.
           It is first checked if you specified listID and then if you did not or the mail was not sent
           to that list it is checked if it is has the specified label(If labelID is None we get all mail the characer has)
           Either labelID or listID is supposed to be set, but nothing will break if they are both set.
           orderBy can be "date", "subject", "sender" and "status"
        """
        if orderBy is None:
            orderBy = localization.GetByLabel('UI/Mail/Received')
        self.LogInfo('Get messages', labelID, orderBy, ascending, pos, count, listID)
        tmpList = []
        isSentitems = labelID == const.mailLabelSent
        if isSentitems and orderBy == localization.GetByLabel('UI/Mail/Sender'):
            mails = []
            for message in self.mailHeaders.itervalues():
                if labelID in message.labels:
                    mails.append(message)

            self.TryPrimeRecipients(mails, setDone=True)
        for message in self.mailHeaders.itervalues():
            if message.trashed:
                continue
            if listID is not None:
                if message.toListID is not None and listID == message.toListID:
                    tmpList.append(self.PrepareOrder(message, orderBy, ascending, isSentitems))
                continue
            if labelID is None or message.labelMask & labelID == labelID:
                tmpList.append(self.PrepareOrder(message, orderBy, ascending, isSentitems))

        ret = util.KeyVal()
        ret.totalNum = len(tmpList)
        ret.sorted = self.DoSort(tmpList, ascending=ascending, pos=pos, count=count)
        if isSentitems and orderBy != localization.GetByLabel('UI/Mail/Sender'):
            self.TryPrimeRecipients(ret.sorted)
        return ret

    def GetTrashedMails(self, orderBy = None, ascending = False, pos = 0, count = 20):
        if orderBy is None:
            orderBy = localization.GetByLabel('UI/Mail/Received')
        self.LogInfo('Get trash', orderBy, ascending, pos, count)
        tmpList = []
        for message in self.mailHeaders.itervalues():
            if not message.trashed:
                continue
            tmpList.append(self.PrepareOrder(message, orderBy, ascending))

        ret = util.KeyVal()
        ret.totalNum = len(tmpList)
        ret.sorted = self.DoSort(tmpList, ascending=ascending, pos=pos, count=count)
        return ret

    def PrepareOrder(self, message, orderBy = None, ascending = False, sentItems = 0):
        if orderBy is None:
            orderBy = localization.GetByLabel('UI/Mail/Received')
        if ascending:
            secondarySortID = message.messageID
        else:
            secondarySortID = -message.messageID
        if orderBy == localization.GetByLabel('UI/Mail/Received'):
            return (message.messageID, secondarySortID)
        if orderBy == localization.GetByLabel('UI/Mail/Subject'):
            return (message.subject.lower(), secondarySortID)
        if orderBy == localization.GetByLabel('UI/Mail/Sender'):
            if sentItems:
                name = self.GetRecipient(message, getName=1)
            else:
                name = message.senderName
            return (name.lower(), secondarySortID)
        if orderBy == localization.GetByLabel('UI/Mail/Status'):
            order = 4
            if not message.read:
                order = 1
            elif message.replied:
                order = 2
            elif message.forwarded:
                order = 3
            return (order, secondarySortID)

    def DoSort(self, list, ascending = False, pos = 0, count = 20):
        self.LogInfo('Sort', ascending, pos, count)
        retMails = []
        list.sort(reverse=ascending)
        for message in list[pos:pos + count]:
            retMails.append(self.mailHeaders[abs(message[1])])

        return retMails

    def GetMailsByIDs(self, messageIDs):
        mailDict = {}
        for messageID in messageIDs:
            mailDict[messageID] = self.GetMailByID(messageID)

        return mailDict

    def GetMailByID(self, messageID):
        try:
            return self.mailHeaders[messageID]
        except KeyError:
            return None

    def TryPrimeRecipients(self, messages, setDone = False):
        """
            This function primes the recipient chars, corp and alliance of the mails
            that are sent to it.
            If the recipients have been primed once we don't need to loop
            through the list again, eveowners will just get the rest on demand
        """
        if getattr(self, 'donePrimingRecipients', False):
            return
        idSet = set()
        for msg in messages:
            entityID = self.GetRecipient(msg, getName=0)
            if entityID > 0:
                idSet.add(entityID)

        owners = list(idSet)
        self.PrimeOwners(owners)
        if setDone:
            self.donePrimingRecipients = True

    def GetRecipient(self, message, getName = 1):
        """
            This function returns the recipient of a mail.
            It can be used to get either its name or its ID.
            If there are more than one recipient, the name that is returned is
            '[multiple]' and the ID is -1.
            This is used either to get the name of a recipient in the mail scroll
            (when the view is 'sent items'), but is also used to get the IDs to prime 
            so there are fewer server calls when the scroll is loaded
        """
        toCharIDs = message.toCharacterIDs or []
        toListID = message.toListID
        if message.toCorpOrAllianceID is not None:
            toCorpIDs = [message.toCorpOrAllianceID]
        else:
            toCorpIDs = []
        if toListID is not None:
            numSentTo = 1
        else:
            numSentTo = 0
        numSentTo += len(toCharIDs) + len(toCorpIDs)
        if numSentTo > 1:
            if getName:
                return localization.GetByLabel('UI/Mail/Multiple')
            else:
                return -1
        for each in toCharIDs + toCorpIDs:
            if getName:
                return cfg.eveowners.Get(each).ownerName
            return each

        if toListID is not None:
            if getName:
                return sm.GetService('mailinglists').GetDisplayName(toListID)
            else:
                return -1
        self.LogWarn('In GetRecipient: message = ', message)
        if getName:
            return ''
        else:
            return -1

    def GetLabels(self):
        """
          Returns a dictionary with all player defined labels
        """
        if self.labels is None:
            self.labels = self.mailMgr.GetLabels()
        return self.labels

    def GetAllLabels(self, assignable = 0):
        """
          Returns a list of all player defined labels in alphabetical order, plus the static labels
        """
        self.LogInfo('GetAllLabels')
        allLabels = copy.copy(self.GetLabels())
        static = [(localization.GetByLabel('UI/Mail/LabelAlliance'), const.mailLabelAlliance),
         (localization.GetByLabel('UI/Mail/LabelCorp'), const.mailLabelCorporation),
         (localization.GetByLabel('UI/Mail/LabelInbox'), const.mailLabelInbox),
         (localization.GetByLabel('UI/Mail/LabelSent'), const.mailLabelSent)]
        for name, id in static:
            keyVal = allLabels.get(id, None)
            if keyVal is not None:
                keyVal.static = 1
                keyVal.name = name
            else:
                keyVal = util.KeyVal()
                keyVal.name = name
                keyVal.labelID = id
                keyVal.static = 1
                keyVal.color = None
                allLabels[id] = keyVal

        self.labels = allLabels.copy()
        if assignable:
            allLabels.pop(const.mailLabelSent, None)
        return allLabels

    def EditLabel(self, labelID, name = None, color = None):
        self.LogInfo('EditLabel', labelID, name, color)
        if name is None and color is None or name == '':
            raise UserError('MailLabelMustProvideName')
        self.mailMgr.EditLabel(labelID, name, color)
        staticLabels = [const.mailLabelSent,
         const.mailLabelInbox,
         const.mailLabelCorporation,
         const.mailLabelAlliance]
        self.GetLabels()
        if labelID not in self.labels and labelID not in staticLabels:
            raise RuntimeError("Invalid label cache, can't update", labelID, name)
        if name is not None:
            self.labels[labelID].name = name
        if color is not None:
            self.labels[labelID].color = color
        sm.ScatterEvent('OnMyLabelsChanged', 'mail_labels', None)

    def CreateLabel(self, name, color = None):
        self.LogInfo('CreateLabel', name, color)
        labelID = self.mailMgr.CreateLabel(name, color)
        self.GetLabels()
        self.labels[labelID] = util.KeyVal(labelID=labelID, name=name, color=color)
        sm.ScatterEvent('OnMyLabelsChanged', 'mail_labels', labelID)
        return labelID

    def DeleteLabel(self, labelID):
        self.LogInfo('DeleteLabel', labelID)
        self.mailMgr.DeleteLabel(labelID)
        self.GetLabels()
        try:
            del self.labels[labelID]
        except KeyError:
            raise RuntimeError("Invalid label cache, can't remove", labelID)

        for message in self.mailHeaders.itervalues():
            if labelID in message.labels:
                message.labelMask = message.labelMask & const.maxInt - labelID
                message.labels = self.GetLabelMaskAsList(message.labelMask)

        sm.ScatterEvent('OnMyLabelsChanged', 'mail_labels', None)

    def AssignLabels(self, messageIDs, labelID):
        self.LogInfo('AssignLabels', messageIDs, labelID)
        mailsToGetLabel = {}
        for messageID in messageIDs:
            mail = self.mailHeaders[messageID]
            if labelID & mail.labelMask != labelID:
                mailsToGetLabel[messageID] = mail

        if len(mailsToGetLabel) > 0:
            self.mailMgr.AssignLabels(mailsToGetLabel.keys(), labelID)
        for mail in mailsToGetLabel.itervalues():
            mail.labelMask = mail.labelMask | labelID
            mail.labels = self.GetLabelMaskAsList(mail.labelMask)

        self.needToSaveHeaders = True
        sm.ScatterEvent('OnMailCountersUpdate')

    def RemoveLabels(self, messageIDs, labelID):
        self.LogInfo('RemoveLabels', messageIDs, labelID)
        mailsToRemoveLabelFrom = {}
        for messageID in messageIDs:
            mail = self.mailHeaders[messageID]
            if labelID & mail.labelMask > 0:
                mailsToRemoveLabelFrom[messageID] = mail

        if len(mailsToRemoveLabelFrom) > 0:
            self.mailMgr.RemoveLabels(mailsToRemoveLabelFrom.keys(), labelID)
        for mail in mailsToRemoveLabelFrom.itervalues():
            mail.labelMask = mail.labelMask & const.maxInt - labelID
            mail.labels = self.GetLabelMaskAsList(mail.labelMask)

        self.needToSaveHeaders = True
        sm.ScatterEvent('OnMailCountersUpdate')

    def SaveChangesToDisk(self):
        """
            When the mail UI window is open this should be called "regularly" to save changes the
            character has made to the disk, also when he closes that window and exits the game.
        """
        if not self.needToSaveHeaders or self.isSaving:
            self.LogInfo('SaveChangesToDisk - nothing to do')
            return
        self.isSaving = True
        try:
            uthread.Lock(self)
            try:
                self.LogInfo('SaveChangesToDisk - saving')
                self.__WriteToHeaderFile('mail', self.mailHeaders)
                self.needToSaveHeaders = False
            finally:
                uthread.UnLock(self)

        finally:
            self.isSaving = False

    def TryCloseMailWindow(self):
        form.MailWindow.CloseIfOpen()

    def ClearMailCache(self):
        if eve.Message('AskClearMailCache', {}, uiconst.YESNO) == uiconst.ID_YES:
            self.TryCloseMailWindow()
            self.ClearCache()

    def ClearCache(self):
        """
            Deletes all cache files for the mail and clears all mail info from memory.
        """
        uthread.Lock(self)
        try:
            self.__ClearHeaderCache()
            self.__ClearBodyCache()
        finally:
            uthread.UnLock(self)

    def __ClearHeaderCache(self):
        try:
            if os.path.exists(self.mailFileHeaders + '.dir'):
                os.remove(self.mailFileHeaders + '.dir')
            if os.path.exists(self.mailFileHeaders + '.dat'):
                os.remove(self.mailFileHeaders + '.dat')
            if os.path.exists(self.mailFileHeaders + '.bak'):
                os.remove(self.mailFileHeaders + '.bak')
        except:
            self.cacheFileCorruption = True
            self.LogError('Error deleting header mail cache files. charid:', str(session.charid))
            raise UserError('MailCacheFileError')

        self.mailHeaders = {}
        self.labels = None
        self.needToSaveHeaders = False
        self.cacheFileCorruption = False
        self.mailSynced = 0

    def __ClearBodyCache(self):
        try:
            if os.path.exists(self.mailFileBodies + '.dir'):
                os.remove(self.mailFileBodies + '.dir')
            if os.path.exists(self.mailFileBodies + '.dat'):
                os.remove(self.mailFileBodies + '.dat')
            if os.path.exists(self.mailFileBodies + '.bak'):
                os.remove(self.mailFileBodies + '.bak')
        except:
            self.cacheFileCorruption = True
            self.LogError('Error deleting body mail cache files. charid:', str(session.charid))
            raise UserError('MailCacheFileError')

        self.mailBodies = {}
        self.mailBodiesOrder = []
        self.cacheFileCorruption = False
        self.mailSynced = 0

    def __WriteToShelveFile(self, fileName, key, value):
        self.LogInfo('WriteToShelve', fileName, key)
        s = blue.os.GetWallclockTimeNow()
        key = str(key)
        try:
            fileHandle = shelve.open(fileName)
            fileHandle[key] = value
            fileHandle.close()
        except:
            self.LogError('Error writing to shelve file (', fileName, ', ', key, ',', value, ')')
            self.cacheFileCorruption = True
            self.TryCloseMailWindow()
            raise UserError('MailCacheFileError')

        self.LogInfo('Writing', blue.os.TimeDiffInMs(s, blue.os.GetWallclockTimeNow()))

    def __ReadFromShelveFile(self, fileName, key):
        self.LogInfo('ReadingFromShelve', fileName, key)
        s = blue.os.GetWallclockTimeNow()
        key = str(key)
        retValue = None
        try:
            fileHandle = shelve.open(fileName)
            if key in fileHandle:
                retValue = fileHandle[key]
            fileHandle.close()
            return retValue
        except:
            self.LogError('Error reading from shelve file (', fileName, ', ', key, ')')
            self.cacheFileCorruption = True
            self.TryCloseMailWindow()
            raise UserError('MailCacheFileError')

        self.LogInfo('Reading', blue.os.TimeDiffInMs(s, blue.os.GetWallclockTimeNow()))

    def __WriteToHeaderFile(self, key, value):
        self.__WriteToShelveFile(self.mailFileHeaders, key, value)

    def __ReadFromHeaderFile(self, key):
        return self.__ReadFromShelveFile(self.mailFileHeaders, key)

    def __WriteToBodyFile(self, key, value):
        self.__WriteToShelveFile(self.mailFileBodies, key, value)

    def __ReadFromBodyFile(self, key):
        return self.__ReadFromShelveFile(self.mailFileBodies, key)

    def __DeleteFromBodyFile(self, key):
        self.LogInfo('DeletingFromShelve', key)
        s = blue.os.GetWallclockTimeNow()
        key = str(key)
        try:
            fileHandle = shelve.open(self.mailFileBodies)
            if key in fileHandle:
                del fileHandle[key]
            fileHandle.close()
        except:
            self.LogError('Error deleting from body shelve file (', key, ')')
            self.cacheFileCorruption = True
            self.TryCloseMailWindow()
            raise UserError('MailCacheFileError')

        self.LogInfo('Deleting', blue.os.TimeDiffInMs(s, blue.os.GetWallclockTimeNow()))

    def IsFileCacheCorrupted(self):
        return self.cacheFileCorruption

    def SendMail(self, toCharacterIDs = [], toListID = None, toCorpOrAllianceID = None, title = '', body = '', isReplyTo = 0, isForwardedFrom = 0):
        self.LogInfo('SendMail', toCharacterIDs, toListID, toCorpOrAllianceID, isReplyTo, isForwardedFrom)
        if toListID is not None:
            myLists = sm.GetService('mailinglists').GetMyMailingLists()
            if toListID not in myLists:
                raise UserError('EveMailCanOnlySendToOwnMailinglists')
        messageID = util.CSPAChargedAction('CSPAMailCheck', self.mailMgr, 'SendMail', toCharacterIDs, toListID, toCorpOrAllianceID, title, body, isReplyTo, isForwardedFrom)
        if messageID is None:
            return
        if len(self.mailBodiesOrder) > BODIES_IN_CACHE:
            try:
                del self.mailBodies[self.mailBodiesOrder.pop(0)]
            except KeyError:
                pass

        self.__WriteToBodyFile(messageID, body)
        self.mailBodies[messageID] = body
        self.mailBodiesOrder.append(messageID)
        if isReplyTo > 0:
            if isReplyTo in self.mailHeaders:
                mail = self.mailHeaders[isReplyTo]
                mail.replied = 1
                mail.statusMask = mail.statusMask | const.mailStatusMaskReplied
                self.needToSaveHeaders = True
        if isForwardedFrom > 0:
            if isForwardedFrom in self.mailHeaders:
                mail = self.mailHeaders[isForwardedFrom]
                mail.forwarded = 1
                mail.statusMask = mail.statusMask | const.mailStatusMaskForwarded
                self.needToSaveHeaders = True
        self.OnMailSent(messageID, session.charid, blue.os.GetWallclockTime() / const.MIN * const.MIN, toCharacterIDs, toListID, toCorpOrAllianceID, title, 0)
        sm.ScatterEvent('OnMailStatusUpdate', isReplyTo, isForwardedFrom)
        return messageID

    def SendMsgDlg(self, toCharacterIDs = [], toListID = None, toCorpOrAllianceID = [], isForwardedFrom = 0, isReplyTo = 0, subject = None, body = None):
        if session.inDetention:
            raise UserError('NotAllowedInDetention')
        if session.userType == const.userTypeTrial:
            n = 1
            t = getattr(self, 'lastMessageTime', blue.os.GetWallclockTime() - 10 * const.mailTrialAccountTimer * const.MIN)
            if blue.os.GetWallclockTime() - t < n * const.mailTrialAccountTimer * const.MIN:
                raise UserError('TrialAccountRestriction', {'what': localization.GetByLabel('UI/Mail/RestrictionTime', timeLeft=t + n * const.MIN - blue.os.GetWallclockTime())})
        sendPage = form.NewNewMessage.Open(windowID=('NewMessageWindow', blue.os.GetWallclockTime()), toCharacterIDs=toCharacterIDs, toListID=toListID, toCorpOrAllianceID=toCorpOrAllianceID, isForwardedFrom=isForwardedFrom, isReplyTo=isReplyTo, subject=subject, body=body)
        return sendPage

    def GetReplyWnd(self, msg, all = 0, *args):
        """
            called when either reply or reply all is clicked
            opens up a new window that has the replied e-mail in its body 
        """
        if msg is None:
            return
        toListID = None
        toCorpOrAllianceID = []
        toCharacterIDs = []
        senders = []
        if all:
            if msg.toCharacterIDs is not None:
                toCharacterIDs = msg.toCharacterIDs[:]
                if session.charid in toCharacterIDs:
                    toCharacterIDs.remove(session.charid)
            toCharacterIDs.append(msg.senderID)
            if msg.toCorpOrAllianceID is not None:
                toCorpOrAllianceID = [msg.toCorpOrAllianceID]
            toListID = msg.toListID
        else:
            toCharacterIDs = [msg.senderID]
        receiversText = self.GetReceiverText(msg)
        newmsg = self.SendMsgDlg(toCharacterIDs=toCharacterIDs, toListID=toListID, toCorpOrAllianceID=toCorpOrAllianceID, isReplyTo=msg.messageID)
        newmsgText = self.GetReplyMessage(msg)
        if msg.subject.startswith(localization.GetByLabel('UI/Mail/GenericInboxRe')):
            newSubjectText = msg.subject
        else:
            newSubjectText = '%s %s' % (localization.GetByLabel('UI/Mail/GenericInboxRe'), msg.subject)
        newmsg.sr.subjecField.SetValue(newSubjectText)
        newmsg.messageedit.SetValue(newmsgText, scrolltotop=1)

    def GetReceiverText(self, mail, format = 0):
        """
            Gets the text that says who receives the mail
            This is used for both displaying the mail and creating the
            body of a mail that is forwarded
            
            ARGUMENTS:
                mail    keyVal with info about the mail
                format  0 or 1, indicates if text should be formatted,
                        reply/fwd uses simpler formatting
        """
        receiversChar = mail.toCharacterIDs
        receiversMaillistID = mail.toListID
        receiversCorp = mail.toCorpOrAllianceID or ''
        receiversText = ''
        if receiversMaillistID is not None:
            name = sm.GetService('mailinglists').GetDisplayName(receiversMaillistID)
            if format:
                name = localization.GetByLabel('UI/Map/StarMap/lblBoldName', name=name)
                receiversText += '%s, ' % name
        if receiversCorp:
            name = cfg.eveowners.Get(receiversCorp).ownerName
            toAdd = '%s' % name
            if format:
                toAdd = localization.GetByLabel('UI/Map/StarMap/lblBoldName', name=toAdd)
            receiversText += '%s, ' % toAdd
        charsIDs = [ charID for charID in receiversChar if charID not in (-1, None) ]
        self.PrimeOwners(charsIDs)
        charNameList = []
        for each in charsIDs:
            name = cfg.eveowners.Get(each).ownerName
            text = '<a href="showinfo:1377//%s">%s</a>,  ' % (each, name)
            charNameList.append((name.lower(), text))

        charNameList = uiutil.SortListOfTuples(charNameList)
        for each in charNameList:
            receiversText += each

        return receiversText

    def GetMailText(self, node):
        msg = node
        body = self.GetBody(msg.messageID)
        subject = msg.subject
        senderID = msg.senderID
        senderName = msg.senderName
        date = msg.sentDate
        receiversText = self.GetReceiverText(msg, format=1)
        if msg.statusMask & const.mailStatusMaskAutomated == const.mailStatusMaskAutomated:
            senderText = localization.GetByLabel('UI/Map/StarMap/lblBoldName', name=senderName)
        else:
            senderText = '<a href="showinfo:1377//%s">%s</a>' % (senderID, senderName)
        txt = localization.GetByLabel('UI/Mail/MailText', subject=subject, sender=senderText, date=util.FmtDate(date, 'ls'), receivers=receiversText, body=body)
        return txt

    def GetReplyMessage(self, msg):
        """
            prepares the reply version of the message msg
        """
        if msg is None:
            return ''
        receiversText = self.GetReceiverText(msg)
        if msg.statusMask & const.mailStatusMaskAutomated == const.mailStatusMaskAutomated:
            senderText = localization.GetByLabel('UI/Map/StarMap/lblBoldName', name=msg.senderName)
        else:
            senderText = '<a href="showinfo:1377//%s">%s</a>' % (msg.senderID, cfg.eveowners.Get(msg.senderID).ownerName)
        body = self.GetBody(msg.messageID)
        newmsgText = '<br><br>%(line)s<br>%(subject)s<br>%(from)s: %(senders)s<br>%(sent)s: %(date)s<br>%(to)s: %(receivers)s<br><br>%(body)s' % {'line': '--------------------------------',
         'subject': msg.subject,
         'from': localization.GetByLabel('UI/Mail/From'),
         'senders': senderText,
         'sent': localization.GetByLabel('UI/Mail/Sent'),
         'date': util.FmtDate(msg.sentDate, 'ls'),
         'to': localization.GetByLabel('UI/Mail/To'),
         'receivers': receiversText,
         'body': body}
        maxLen = const.mailMaxBodySize * 0.9
        if len(newmsgText) > maxLen:
            while len(newmsgText) > maxLen:
                try:
                    brIndex = newmsgText.rindex('<br>', int(maxLen * 0.7))
                    newmsgText = newmsgText[:brIndex]
                except ValueError:
                    lastIndex = int(len(newmsgText) * 0.9)
                    newmsgText = newmsgText[:lastIndex]

            newmsgText += '<br>...'
        return newmsgText

    def GetForwardWnd(self, msg):
        if msg is None:
            return
        newmsg = self.SendMsgDlg(isForwardedFrom=msg.messageID)
        newmsgText = self.GetReplyMessage(msg)
        newmsg.sr.subjecField.SetValue('%s %s' % ('FW:', msg.subject))
        newmsg.messageedit.SetValue(newmsgText, scrolltotop=1)

    def OnMailSent(self, messageID, senderID, sentDate, toCharacterIDs, toListID, toCorpOrAllianceID, title, statusMask):
        uthread.Lock(self)
        try:
            if messageID in self.mailHeaders:
                return
            labelMask = 0
            read = False
            if session.charid in toCharacterIDs:
                labelMask = const.mailLabelInbox
            if senderID == session.charid:
                if labelMask == 0 and toCorpOrAllianceID is None and toListID is None:
                    read = True
                    statusMask = statusMask | 1
                labelMask = labelMask | const.mailLabelSent
            if toCorpOrAllianceID is not None:
                if util.IsCorporation(toCorpOrAllianceID):
                    labelMask = labelMask | const.mailLabelCorporation
                else:
                    labelMask = labelMask | const.mailLabelAlliance
            self.mailHeaders[messageID] = util.KeyVal(messageID=messageID, senderID=senderID, toCharacterIDs=toCharacterIDs, toListID=toListID, toCorpOrAllianceID=toCorpOrAllianceID, subject=title, sentDate=sentDate, read=read, replied=False, forwarded=False, trashed=False, statusMask=statusMask, labelMask=labelMask, labels=self.GetLabelMaskAsList(labelMask))
            if statusMask & const.mailStatusMaskAutomated > 0 and senderID == toListID:
                self.mailHeaders[messageID].senderName = sm.GetService('mailinglists').GetDisplayName(senderID)
            else:
                try:
                    self.mailHeaders[messageID].senderName = cfg.eveowners.Get(senderID).name
                except IndexError:
                    self.mailHeaders[messageID].senderName = localization.GetByLabel('UI/Generic/Unknown')

            self.needToSaveHeaders = True
            if not read:
                self.OnNewMailReceived(self.mailHeaders[messageID])
        finally:
            uthread.UnLock(self)

    def OnMailDeleted(self, messageIDs):
        """
            Mail was deleted by someone else
        """
        uthread.Lock(self)
        try:
            for messageID in messageIDs:
                if messageID in self.mailHeaders:
                    del self.mailHeaders[messageID]
                    self.needToSaveHeaders = True
                if messageID in self.mailBodies:
                    del self.mailBodies[messageID]
                if messageID in self.mailBodiesOrder:
                    self.mailBodiesOrder.remove(messageID)
                self.__DeleteFromBodyFile(messageID)

            sm.ScatterEvent('OnMailTrashedDeleted', None, 1)
        finally:
            uthread.UnLock(self)

    def OnMailUndeleted(self, messageIDs):
        """
            Mail was undeleted by someone else (a GM)
        """
        self.SyncMail()
        sm.ScatterEvent('OnNewMailReceived')

    def OnNewMailReceived(self, msg, *args):
        self.SetBlinkTabState(True)
        self.SetBlinkNeocomState(True)
        sm.ScatterEvent('OnNewMailReceived')
        mailSettings = self.GetMailSettings()
        if mailSettings.GetSingleValue(cSettings.MAIL_BLINK_NEOCOM, True):
            sm.GetService('neocom').Blink('mail')
        if mailSettings.GetSingleValue(cSettings.MAIL_SHOW_POPUP, True):
            self.GetMailNotification(msg)

    def GetMailNotification(self, msg):
        notificationData = NewMailFormatter.MakeData(msg)
        sm.ScatterEvent('OnNotificationReceived', 123, notificationConst.notificationTypeNewMailFrom, session.charid, blue.os.GetWallclockTime(), data=notificationData)

    def OnClickingMailPopup(self, popup, msg, *args):
        self.OnOpenPopupMail(msg)
        if popup and not popup.destroyed:
            popup.CloseNotification()

    def GetMailPopupOnCharacterLogin(self, mailCount):
        blue.pyos.synchro.SleepWallclock(7000)
        if mailCount < 1:
            return
        notificationData = MailSummaryFormatter.MakeData(mailCount)
        sm.GetService('notificationSvc').MakeAndScatterNotification(type=notificationConst.notificationTypeMailSummary, data=notificationData)

    def OnClickingPopup(self, popup, *args):
        sm.GetService('cmd').OpenMail()
        popup.CloseNotification()

    def OnOpenPopupMail(self, msg, *args):
        wndName = 'mail_readingWnd_%s' % msg.messageID
        wnd = form.MailReadingWnd.Open(windowID=wndName, mail=msg, msgID=msg.messageID, txt='', toolbar=1, trashed=msg.trashed, type=const.mailTypeMail)
        if not msg.read:
            sm.ScatterEvent('OnMailStatusUpdate', None, None, [msg.messageID])
        if wnd is not None:
            wnd.Maximize()
            blue.pyos.synchro.SleepWallclock(1)
            wnd.SetText(self.GetMailText(msg))

    def CheckNewMessages_thread(self, mailCount, notificationCount):
        blue.pyos.synchro.SleepSim(3000)
        endTime = blue.os.GetSimTime() + 10 * const.SEC
        while blue.os.GetSimTime() < endTime:
            if getattr(session, 'charid', None):
                break
            blue.pyos.synchro.SleepSim(1000)

        if getattr(session, 'charid', None) is None:
            log.LogWarn('Mail: Waited for 13 seconds to display new messages, gave up')
            return
        self.BlinkNeocomIfNeeded(mailCount)

    def BlinkNeocomIfNeeded(self, mailCount):
        shouldBlink = 0
        mailSettings = self.GetMailSettings()
        if mailCount:
            self.SetBlinkNeocomState(True)
            if mailSettings.GetSingleValue(cSettings.MAIL_BLINK_NEOCOM, True):
                self.SetBlinkTabState(True)
                shouldBlink = 1
            if mailSettings.GetSingleValue(cSettings.MAIL_SHOW_POPUP, True):
                self.GetMailPopupOnCharacterLogin(mailCount)
            if mailSettings.GetSingleValue(cSettings.MAIL_BLINK_TAB, True):
                self.SetBlinkTabState(True)
        if shouldBlink:
            sm.GetService('neocom').Blink('mail')

    def CheckLabelName(self, name, *args):
        name = name.strip()
        myLabelNames = [ label.name for label in self.GetAllLabels(assignable=0).values() ]
        if name in myLabelNames:
            return localization.GetByLabel('UI/Mail/LabelNameTaken')

    def RenameLabelFromUI(self, labelID):
        ret = uiutil.NamePopup(localization.GetByLabel('UI/Mail/LabelName'), localization.GetByLabel('UI/Mail/LabelTypeNew'), maxLength=const.mailMaxLabelSize, validator=self.CheckLabelName)
        if ret is None:
            return
        name = ret
        name = name.strip()
        if name:
            self.EditLabel(labelID, name=name)

    def ChangeLabelColorFromUI(self, color, labelID):
        allLabels = self.GetAllLabels()
        label = allLabels.get(labelID, None)
        if label is None:
            return
        if color != label.color:
            self.EditLabel(labelID, color=color)

    def GetSwatchColors(self, *args):
        return swatchColors

    def DeleteLabelFromUI(self, labelID, labelName):
        if eve.Message('DeleteMailLabel', {'labelName': labelName}, uiconst.YESNO) == uiconst.ID_YES:
            self.DeleteLabel(labelID)

    def ShouldTabBlink(self, *args):
        return self.blinkTab

    def SetBlinkTabState(self, state = False):
        self.blinkTab = state

    def ShouldNeocomBlink(self, *args):
        return self.blinkNeocom

    def SetBlinkNeocomState(self, state = False):
        self.blinkNeocom = state

    def GetAssignColorWnd(self, labelID, doneCallBack = None, doneArgs = (), width = 104, height = 74, *args):
        colorpar = xtriui.MailAssignColorWnd(name='colorpar', parent=uicore.layer.menu, idx=0, align=uiconst.TOPLEFT, pos=(0,
         0,
         width,
         height))
        colorpar.Startup(labelID, doneCallBack, doneArgs)

    def GetMailSettings(self):
        self.SetMailSettingsIfNeeded()
        return self.mailSettingObject

    def SetMailSettingsIfNeeded(self):
        if self.mailSettingObject is None:
            yamlString = self.FetchMailSettingsToServer()
            self.mailSettingObject = CharacterSettingsObject(yamlString)
            with ExceptionEater('Failed to migrate settings'):
                self.TryMigrateSettings(self.mailSettingObject)

    def FetchMailSettingsToServer(self):
        if self.characterSettings is None:
            self.characterSettings = sm.GetService('characterSettings')
        yamlString = self.characterSettings.Get('mailSettings')
        return yamlString

    def SaveMailSettingsOnServer(self, newSettingsObject):
        isSaveNeeded = self.mailSettingObject.IsSaveNeeded(newSettingsObject.allSettings)
        if not isSaveNeeded:
            return
        self.mailSettingObject.UpdateSettings(newSettingsObject.allSettings)
        newYamlString = self.mailSettingObject.GetYamlStringForServer()
        self.characterSettings.Save('mailSettings', newYamlString)

    def TryMigrateSettings(self, settingsObject):
        """
            migrating the client settings to the server. This should be removed not to long after this is deployed.
        """
        if settingsObject.GetSingleValue('settingMigrationDone1', False):
            return
        for settingKey in (cSettings.MAIL_BLINK_NEOCOM,
         cSettings.MAIL_SHOW_POPUP,
         cSettings.MAIL_BLINK_TAB,
         cSettings.MAIL_GET_SEARCH_WND):
            oldSetting = settings.user.ui.Get(settingKey, True)
            settingsObject.SetSingleValue(settingKey, oldSetting)

        oldMailPerPage = settings.user.ui.Get(cSettings.MAILS_PER_PAGE, 30)
        settingsObject.SetSingleValue(cSettings.MAILS_PER_PAGE, oldMailPerPage)
        allNotificationGroups = notificationGroupNamePaths.keys()
        for newSettingKey, oldSettingKey in ((cSettings.NOTIFICATIONS_GROUPS_DONT_BLINK_NEOCOM, 'notification_blinkNecom'), (cSettings.NOTIFICATIONS_GROUPS_DONT_BLINK_TAB, 'notification_blinkTab')):
            oldSetting = settings.user.ui.Get(oldSettingKey, True)
            if oldSetting:
                newValue = []
            else:
                newValue = allNotificationGroups
            settingsObject.UpdateSettingListWithNewValues(newSettingKey, newValue)

        settingsObject.SetSingleValue('settingMigrationDone1', True)
        newYamlString = settingsObject.GetYamlStringForServer()
        self.characterSettings.Save('mailSettings', newYamlString)
