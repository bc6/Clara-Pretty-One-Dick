#Embedded file name: eve/client/script/ui/shared\killReportUtil.py
import carbonui.const as uiconst

def CleanKillMail(killMailText):
    """
        Unified place to strip formatting from killMails
    """
    ret = killMailText
    import uiutil
    if '<localized' in ret:
        ret = ret.replace('*</localized>', '</localized>')
        ret = uiutil.StripTags(ret, stripOnly=['localized'])
    return ret.replace('<br>', '\r\n').replace('<t>', '   ')


def OpenKillReport(kill, *args):
    """
        Function to open kill reports
    """
    if uicore.uilib.Key(uiconst.VK_SHIFT):
        windowID = 'KillReport_%i' % kill.killID
    else:
        windowID = 'KillReportWnd'
    from eve.client.script.ui.shared.killReport import KillReportWnd
    wnd = KillReportWnd.GetIfOpen(windowID)
    if wnd:
        wnd.LoadInfo(killmail=kill)
        wnd.Maximize()
    else:
        KillReportWnd.Open(create=1, killmail=kill, windowID=windowID)


exports = {'util.CleanKillMail': CleanKillMail}
