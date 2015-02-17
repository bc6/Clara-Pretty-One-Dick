#Embedded file name: eve/client/script/parklife\billboardMgr.py
from service import *
import uicontrols
import uthread
import blue
import urllib2
import sys
import util
import random
import trinity
import carbonui.const as uiconst
import uicls
import localization
import log
from eve.client.script.util.webutils import WebUtils
TQ_NEWS_HEADLINES_URL = 'http://www.eveonline.com/mb/news-headlines.asp'
SERENITY_NEWS_HEADLINES_URL = 'http://eve.tiancity.com/client/news.html'
UPDATE_TIME = 30000

class BillboardMgr(Service):
    __guid__ = 'svc.billboard'
    __exportedcalls__ = {'Update': [],
     'GenerateAdvert': []}
    __dependencies__ = ['michelle', 'photo']

    def __init__(self):
        Service.__init__(self)
        self.updateTimer = None

    def Run(self, memStream = None):
        Service.Run(self, memStream)
        self.updateCount = 0
        self.facePath = None
        self.advertPath = None
        self.bountyInfo = []
        uthread.new(self.DoNewsHeadlines)
        uthread.new(self.GenerateAdvert)
        uthread.new(self.GetBountyInfo)

    def GetLocalBillboards(self):
        bp = self.michelle.GetBallpark()
        billboards = []
        if bp is not None:
            for ballID in bp.balls.iterkeys():
                slimItem = bp.GetInvItem(ballID)
                if slimItem == None:
                    continue
                groupID = slimItem.groupID
                if groupID == const.groupBillboard:
                    billboardBall = bp.GetBall(ballID)
                    if billboardBall is not None:
                        billboards.append(billboardBall)

        return billboards

    def GetBountyInfo(self):
        self.bountyInfo = sm.GetService('bountySvc').GetTopPilotBounties()

    def GenerateAdvert(self):
        self.advertPath = self._GenerateAdvert()

    def _GenerateAdvert(self):
        URL = 'http://www.eveonline.com/billboard.asp?%s' % WebUtils.GetWebRequestParameters()
        pictureName = URL
        tex, tWidth, tHeight = self.photo.GetTextureFromURL(pictureName)
        codefile = blue.classes.CreateInstance('blue.ResFile')
        try:
            if not codefile.Open(tex.resPath):
                self.LogWarn('Cannot open texture file', tex.resPath, '- aborting refresh')
                return None
            modified = codefile.GetFileInfo()['ftLastWriteTime']
        except:
            self.LogWarn('Unable to open texture file', tex.resPath, '- skipping refresh for now')
            sys.exc_clear()
            return None

        if 'none.dds' in tex.resPath:
            return None
        else:
            return tex.resPath

    def DoNewsHeadlines(self):
        """
            Fetches headlines and renders them out to a texture.
            We always use the same headlines throughout the client run
        """
        headlinesFetched = False
        while not headlinesFetched:
            newsHeadlinesURL = TQ_NEWS_HEADLINES_URL
            if boot.region == 'optic':
                newsHeadlinesURL = SERENITY_NEWS_HEADLINES_URL
            newsHeadlinesURL += '?%s' % WebUtils.GetWebRequestParameters()
            try:
                f = urllib2.urlopen(newsHeadlinesURL, timeout=60)
                headlinesFetched = True
            except:
                self.LogError('Failed to get news headlines from: %s, Retrying in 1 minute' % newsHeadlinesURL)
                blue.pyos.synchro.SleepWallclock(const.MIN / const.MSEC)

        totaltext = ''
        for line in f.readlines():
            try:
                caption = line.split(';', 1)[1].strip()
            except IndexError:
                continue

            if (len(totaltext) + len(caption) + 3) * 8 > 2048:
                break
            totaltext += ' - ' + caption

        if totaltext:
            self.RenderText(totaltext, 'headlines')

    def Update(self, model = None):
        self.__UpdateBillboard(model)

    def __UpdateBillboard(self, model):
        """
            We have an advert in self.advertPath but generate new bounty information every few calls
        """
        if not hasattr(eve.session, 'solarsystemid') or eve.session.solarsystemid is None or model is None:
            return
        self.LogInfo('Updating billboard')
        if self.updateCount % 10 == 0:
            self.UpdateBounty()
        self.updateCount += 1
        model.UpdateBillboardContents(self.advertPath, self.facePath)

    def UpdateBounty(self):
        self.LogInfo('Updating bounty')
        currBounty = None
        if len(self.bountyInfo):
            m = self.bountyInfo[random.randint(0, len(self.bountyInfo) - 1)]
            currBounty = [m.targetID, cfg.eveowners.Get(m.targetID).ownerName, m.bounty]
        self.facePath = None
        if currBounty is not None:
            characterID, charName, bounty = currBounty
            serverLink = sm.RemoteSvc('charMgr').GetImageServerLink()
            if not serverLink:
                self.LogWarn("UpdateBounty: Couldn't find server Link")
                self.facePath = 'res:/UI/Texture/defaultFace.jpg'
                portraitURL = '<serverlink not found>'
                width = 256
                height = 32
            else:
                portraitURL = '%sCharacter/%d_256.jpg' % (serverLink, characterID)
                tex = self.photo.GetTextureFromURL(portraitURL, None)
                texture = tex[0]
                if 'none.dds' in texture.resPath:
                    self.facePath = None
                    self.LogError('Failed opening jpg picture for character', characterID)
                else:
                    self.facePath = texture.resPath
            amountText = util.FmtISK(bounty, showFractionsAlways=0)
            wantedText = localization.GetByLabel('UI/Inflight/Billboards/WantedCharacter', character=characterID, bountyAmount=amountText)
            self.RenderText(wantedText, 'bounty_caption')
            self.LogInfo('Updating billboard with bounty portrait', portraitURL, 'for character', charName, ', ID= ', characterID)

    def RenderText(self, text, name):
        txt = uicontrols.EveHeaderMedium(text=text, parent=None, state=uiconst.UI_NORMAL)
        hb = trinity.Tr2HostBitmap(txt.actualTextWidth, txt.actualTextHeight, 1, trinity.PIXEL_FORMAT.B8G8R8A8_UNORM)
        txt.measurer.DrawToHostBitmap(hb)
        fileName = 'cache:/Temp/%s.dds' % name
        hb.SaveAsync(blue.paths.ResolvePathForWriting(fileName))
        hb.WaitForSave()
