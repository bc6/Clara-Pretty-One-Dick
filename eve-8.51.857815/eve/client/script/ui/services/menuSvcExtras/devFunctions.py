#Embedded file name: eve/client/script/ui/services/menuSvcExtras\devFunctions.py
import sys
import uix
import uiutil
import util
import blue
import carbonui.const as uiconst
import copy
import carbon.common.lib.serverInfo as serverInfo
from eveexceptions import UserError

def SlashCmd(cmd):
    try:
        sm.RemoteSvc('slash').SlashCmd(cmd)
    except RuntimeError:
        sm.GetService('gameui').MessageBox('This only works on items at your current location.', 'Oops!', buttons=uiconst.OK)


def SlashCmdTr(cmd):
    SlashCmd(cmd)
    sm.GetService('menu').ClearAlignTargets()


def GagPopup(charID, numMinutes):
    reason = 'Gagged for Spamming'
    ret = uiutil.NamePopup('Gag User', 'Enter Reason', reason)
    if ret:
        SlashCmd('/gag %s "%s" %s' % (charID, ret, numMinutes))


def BanIskSpammer(charID):
    if eve.Message('ConfirmBanIskSpammer', {'name': cfg.eveowners.Get(charID).name}, uiconst.YESNO) != uiconst.ID_YES:
        return
    SlashCmd('/baniskspammer %s' % charID)


def GagIskSpammer(charID):
    if eve.Message('ConfirmGagIskSpammer', {'name': cfg.eveowners.Get(charID).name}, uiconst.YESNO) != uiconst.ID_YES:
        return
    SlashCmd('/gagiskspammer %s' % charID)


def ReportISKSpammer(charID, channelID):
    if eve.Message('ConfirmReportISKSpammer', {'name': cfg.eveowners.Get(charID).name}, uiconst.YESNO) != uiconst.ID_YES:
        return
    if charID == session.charid:
        raise UserError('ReportISKSpammerCannotReportYourself')
    lscSvc = sm.GetService('LSC')
    c = lscSvc.GetChannelWindow(channelID)
    entries = copy.copy(c.output.GetNodes())
    spamEntries = []
    for e in entries:
        if e.charid == charID:
            who, txt, charid, time, colorkey = e.msg
            spamEntries.append('[%s] %s > %s' % (util.FmtDate(time, 'nl'), who, txt))

    if len(spamEntries) == 0:
        raise UserError('ReportISKSpammerNoEntries')
    spamEntries.reverse()
    spamEntries = spamEntries[:10]
    spammers = getattr(lscSvc, 'spammerList', set())
    if charID in spammers:
        return
    spammers.add(charID)
    lscSvc.spammerList = spammers
    c.LoadMessages()
    channel = lscSvc.channels.get(channelID, None)
    if channel and channel.info:
        channelID = channel.info.displayName
    sm.RemoteSvc('userSvc').ReportISKSpammer(charID, channelID, spamEntries)


def SetDogmaAttribute(itemID, attrName, actualValue):
    """
        Shortcut popup for setting dogma attributes for programmers
    """
    ret = uix.QtyPopup(None, None, actualValue, 'Set Dogma Attribute for <b>%s</b>' % attrName, 'Set Dogma Attribute', digits=5)
    if ret:
        cmd = '/dogma %s %s = %s' % (itemID, attrName, ret['qty'])
        SlashCmd(cmd)


def AttributeMenu(itemID, typeID):
    d = sm.StartService('info').GetAttributeDictForType(typeID)
    statemgr = sm.StartService('godma').GetStateManager()
    a = statemgr.attributesByID
    lst = []
    for attributeID, baseValue in d.iteritems():
        attrName = a[attributeID].attributeName
        try:
            actualValue = statemgr.GetAttribute(itemID, attrName)
        except:
            sys.exc_clear()
            actualValue = baseValue

        lst.append(('%s - %s' % (attrName, actualValue), SetDogmaAttribute, (itemID, attrName, actualValue)))

    lst.sort(lambda x, y: cmp(x[0], y[0]))
    return lst


def GetFromESP(action):
    """
        Constructs an URL using the connected to server info and the action parameter.
    """
    espaddy = serverInfo.GetServerInfo().espUrl
    blue.os.ShellExecute('http://%s/%s' % (espaddy, action))


def NPCInfoMenu(item):
    """
        Dynamic menu to open ESP pages regarding NPCs.
        As more ESP pages regarding NPCs are created then an entry should be created here.
    """
    lst = []
    action = 'gd/type.py?action=Type&typeID=' + str(item.typeID)
    lst.append(('Overview', GetFromESP, (action,)))
    action = 'gd/type.py?action=TypeDogma&typeID=' + str(item.typeID)
    lst.append(('Dogma Attributes', GetFromESP, (action,)))
    action = 'gd/npc.py?action=GetNPCInfo&shipID=' + str(item.itemID) + '&solarSystemID=' + str(session.solarsystemid)
    lst.append(('Info', GetFromESP, (action,)))
    return lst
