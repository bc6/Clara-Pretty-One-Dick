#Embedded file name: notifications/client/controls\notificationEntry.py
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from eve.client.script.ui.shared.stateFlag import AddAndSetFlagIconFromData
import localization
import blue
import carbon.common.script.util.format as formatUtil
import carbonui.const as uiconst
import eve.common.script.util.notificationconst as notificationConst
import math
from notifications.common.formatters.killMailBase import KillMailBaseFormatter
from notifications.common.formatters.killMailFinalBlow import KillMailFinalBlowFormatter
import uthread
import eve.client.script.ui.util.uix as uiUtils
from carbonui.primitives.container import Container
from eve.client.script.ui.control.eveLabel import EveLabelMedium
from eve.client.script.ui.control.eveLabel import EveLabelSmall
from eve.client.script.ui.control.eveLabel import EveLabelMediumBold
from eve.client.script.ui.control.eveIcon import Icon
from carbonui.primitives.line import Line
from carbonui.primitives.sprite import Sprite
from carbonui.primitives.frame import Frame
from carbonui.primitives.fill import Fill
from carbonui.primitives.sprite import Sprite
from utillib import KeyVal
from eve.client.script.ui.control.eveIcon import GetLogoIcon
MAINAREA_WIDTH = 224
TITLE_PADDING = (0, 5, 0, 0)
SUBTEXT_PADDING = (0, 0, 0, 0)
TIMETEXT_PADDING = (0, 5, 0, 5)
MINENTRYHEIGHT = 50

class NotificationEntry(Container):
    default_height = MINENTRYHEIGHT
    default_state = uiconst.UI_NORMAL
    BACKGROUNDTEX = 'res:/UI/Texture/classes/Notification/popupBackEventUp.png'
    demoTextures = {'default': 'res:/ui/Texture/WindowIcons/bountyoffice.png',
     'online': 'res:/UI/Texture/icons/107_64_4.png'}
    notification = None
    contentLoaded = False
    blinkSprite = None
    titleLabel = None
    subtextLabel = None
    timeLabel = None

    def GetFormattedTimeString(self, timestamp):
        delta = blue.os.GetWallclockTime() - timestamp
        return formatUtil.FmtTimeIntervalMaxParts(delta, breakAt='second', maxParts=2)

    def UpdateNotificationEntryHeight(self):
        height = 0
        pl, pt, pr, pb = TITLE_PADDING
        size = EveLabelMedium.MeasureTextSize(self.title, width=MAINAREA_WIDTH - pl - pr, bold=True)
        height = size[1] + pt + pb
        if self.subtext:
            pl, pt, pr, pb = SUBTEXT_PADDING
            size = EveLabelMedium.MeasureTextSize(self.subtext, width=MAINAREA_WIDTH - pl - pr)
            height += size[1] + pt + pb
        if self.created:
            pl, pt, pr, pb = TIMETEXT_PADDING
            size = EveLabelSmall.MeasureTextSize('123', width=MAINAREA_WIDTH - pl - pr)
            height += size[1] + pt + pb
        return max(MINENTRYHEIGHT, height)

    def ApplyAttributes(self, attributes):
        self.notification = attributes.notification
        self.developerMode = attributes.developerMode
        self.created = attributes.created
        self.title = self.notification.subject
        self.subtext = self.notification.subtext
        attributes.height = self.UpdateNotificationEntryHeight()
        Container.ApplyAttributes(self, attributes)

    def LoadContent(self):
        if self.contentLoaded:
            return
        self.contentLoaded = True
        self.filler = Frame(name='myFrame', bgParent=self, texturePath='res:/UI/Texture/classes/Notifications/historyBackReadUp.png', cornerSize=6, offset=-5)
        self.leftContainer = Container(name='leftContainer', width=40, padding=(5, 5, 10, 5), parent=self, align=uiconst.TOLEFT)
        self.rightContainer = ContainerAutoSize(name='rightContainer', width=MAINAREA_WIDTH, parent=self, align=uiconst.TOLEFT)
        self.titleLabel = EveLabelMedium(name='subject', parent=self.rightContainer, align=uiconst.TOTOP, text=self.title, padding=TITLE_PADDING, bold=True)
        if self.subtext:
            self.subtextLabel = EveLabelMedium(name='subtext', parent=self.rightContainer, align=uiconst.TOTOP, text=self.subtext, padding=SUBTEXT_PADDING)
        if self.notification:
            texture = self.GetTexturePathForNotification(self.notification.typeID)
        else:
            texture = 'res:/ui/Texture/WindowIcons/bountyoffice.png'
        self.imageSprite = Sprite(name='MySprite', parent=self.leftContainer, texturePath=texture, align=uiconst.TOPLEFT, width=40, height=40)
        self.characterSprite = Sprite(name='CharacterSprite', parent=self.leftContainer, texturePath=texture, align=uiconst.TOPLEFT, width=40, height=40, state=uiconst.UI_HIDDEN)
        if self.created:
            timeinterval = blue.os.GetWallclockTime() - self.created
            createdText = localization.GetByLabel('Notifications/NotificationWidget/NotificationTimeAgo', time=timeinterval)
            self.timeLabel = EveLabelSmall(name='timeLabel', parent=self.rightContainer, align=uiconst.TOTOP, color=(0.5, 0.5, 0.5), padding=TIMETEXT_PADDING)
            self.timeLabel.text = createdText
        notification = self.notification
        if notification.typeID in [notificationConst.notificationTypeKillReportFinalBlow, notificationConst.notificationTypeKillReportVictim]:
            shipTypeID = KillMailFinalBlowFormatter.GetVictimShipTypeID(notification.data)
            if shipTypeID is not None:
                parentContainer = self.leftContainer
                Icon(parent=parentContainer, align=uiconst.TOPRIGHT, size=40, typeID=shipTypeID)
                shipTechIcon = Sprite(name='techIcon', parent=parentContainer, width=16, height=16, idx=0)
                uiUtils.GetTechLevelIcon(shipTechIcon, 0, shipTypeID)
                self.imageSprite.GetDragData = lambda *args: self.MakeKillDragObject(notification)
        if self.ShouldDisplayPortrait(notification):
            item = cfg.eveowners.Get(notification.senderID)
            if item.IsCharacter():
                sm.GetService('photo').GetPortrait(notification.senderID, 128, self.characterSprite)
                if notification.typeID in notificationConst.notificationShowStanding:
                    charinfo = item
                    self.imageSprite.GetMenu = lambda : sm.GetService('menu').GetMenuFormItemIDTypeID(notification.senderID, charinfo.typeID)
                    self.imageSprite.GetDragData = lambda *args: self.MakeCharacterDragObject(notification.senderID)
                    charData = KeyVal()
                    charData.charID = notification.senderID
                    charData.charinfo = charinfo
                    AddAndSetFlagIconFromData(charData, parentCont=self.leftContainer, top=self.characterSprite.height - 10)
            else:
                self.corpLogo = GetLogoIcon(itemID=notification.senderID, parent=self.leftContainer, align=uiconst.TOPLEFT, size=40, state=uiconst.UI_DISABLED, ignoreSize=True)
            self.characterSprite.state = uiconst.UI_NORMAL

    def BlinkFinished(self, *args):
        if self.blinkSprite and not self.blinkSprite.destroyed:
            self.blinkSprite.Close()
            self.blinkSprite = None

    def Blink(self):
        if self.blinkSprite is None:
            self.blinkSprite = Sprite(bgParent=self, name='blinkSprite', texturePath='res:/UI/Texture/classes/Neocom/buttonBlink.png', idx=0)
        self.blinkSprite.Show()
        uicore.animations.SpSwoopBlink(self.blinkSprite, rotation=math.pi * 0.75, duration=0.8, loops=1, callback=self.BlinkFinished)

    def GetTexturePathForNotification(self, notificationTypeID):
        NOTIFICATION_TYPE_TO_TEXTURE = {1234: 'res:/UI/Texture/icons/50_64_11.png'}
        tex = NOTIFICATION_TYPE_TO_TEXTURE.get(notificationTypeID)
        if tex:
            texture = tex
        else:
            texture = 'res:/UI/Texture/Icons/notifications/notificationIcon_%s.png' % notificationTypeID
        if not blue.paths.exists(texture):
            texture = None
        return texture

    def ShouldDisplayPortrait(self, notification):
        if notification and notification.typeID in notificationConst.notificationDisplaySender:
            return True
        else:
            return False

    def GetHint(self):
        if self.notification and self.developerMode:
            return '%s %s %s %s' % (str(self.notification.typeID),
             str(self.notification.subject),
             str(self.notification.senderID),
             self.notification.body)
        else:
            return ''

    def MakeCharacterDragObject(self, charid):
        typeID = cfg.eveowners.Get(charid).typeID
        fakeNode = KeyVal()
        fakeNode.charID = charid
        fakeNode.info = cfg.eveowners.Get(charid)
        fakeNode.itemID = charid
        fakeNode.__guid__ = 'listentry.User'
        return [fakeNode]

    def MakeKillDragObject(self, notification):
        fakeNode = KeyVal()
        kmID, kmHash = KillMailBaseFormatter.GetKillMailIDandHash(notification.data)
        theRealKm = sm.RemoteSvc('warStatisticMgr').GetKillMail(kmID, kmHash)
        fakeNode.mail = theRealKm
        fakeNode.__guid__ = 'listentry.KillMail'
        return [fakeNode]

    def OnMouseEnter(self, *args):
        self.filler.texturePath = 'res:/UI/Texture/classes/Notifications/historyBackReadOver.png'

    def OnMouseExit(self, *args):
        self.filler.texturePath = 'res:/UI/Texture/classes/Notifications/historyBackReadUp.png'
