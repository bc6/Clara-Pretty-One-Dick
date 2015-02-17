#Embedded file name: notifications/client\mailInteractor.py
import form
import eve.common.script.util.notificationconst as notificationConst
import blue

class MailInteractor(object):

    def GetMailWindow(self):
        return form.MailWindow.Open()

    def SelectGroupId(self, groupID):
        notificationForm = self.GetNotificationForm()
        notificationForm.SelectGroupById(groupID)

    def SleepIfTrue(self, sleep):
        if sleep:
            blue.pyos.synchro.SleepWallclock(50)

    def GetNotificationForm(self, doSleep = True):
        wnd = self.GetMailWindow()
        self.SleepIfTrue(doSleep)
        wnd.SelectNotificationTab()
        self.SleepIfTrue(doSleep)
        return wnd.sr.notifications

    def SelectGroupForTypeID(self, notificationTypeID):
        groupID = self.FindGroupForNotificationID(notificationTypeID)
        if groupID:
            self.SelectGroupId(groupID)

    def SelectByNotificationID(self, notificationID, notificationTypeID):
        self.SelectGroupForTypeID(notificationTypeID)
        notificationForm = self.GetNotificationForm(doSleep=False)
        notificationForm.SelectNodeByNotificationID(notificationID)

    def FindGroupForNotificationID(self, notificationTypeID):
        for groupID, notificationList in notificationConst.groupTypes.iteritems():
            for notificationid in notificationList:
                if notificationTypeID == notificationid:
                    return groupID
