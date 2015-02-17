#Embedded file name: eve/client/script/util\contractutils.py
"""
This file contains several utility and helper functions for the ui
part of the contract system
"""
from contractscommon import *
import eve.common.script.sys.rowset as rowset
import uicontrols
import util
import blue
import uix
import localization
COL_PAY = '0xffcc2222'
COL_GET = '0xff00bb00'

def FmtISKWithDescription(isk, justDesc = False):
    iskFmt = util.FmtISK(isk, showFractionsAlways=0)
    isk = float(isk)
    if abs(isk) >= 1000000000:
        isk = long(isk / 10000000L)
        if justDesc:
            iskFmt = localization.GetByLabel('UI/Contracts/Util/AmountInBillions', amount=isk / 100.0)
        else:
            iskFmt = localization.GetByLabel('UI/Contracts/Util/AmountInBillionsDetailed', iskAmount=iskFmt, amount=isk / 100.0)
    elif abs(isk) >= 1000000:
        isk = long(isk / 10000L)
        if justDesc:
            iskFmt = localization.GetByLabel('UI/Contracts/Util/AmountInMillions', amount=isk / 100.0)
        else:
            iskFmt = localization.GetByLabel('UI/Contracts/Util/AmountInMillionDetailed', iskAmount=iskFmt, amount=isk / 100.0)
    elif abs(isk) >= 10000:
        isk = long(isk / 10L)
        if justDesc:
            iskFmt = localization.GetByLabel('UI/Contracts/Util/AmountInThousands', amount=isk / 100.0)
        else:
            iskFmt = localization.GetByLabel('UI/Contracts/Util/AmountInThousandsDetailed', iskAmount=iskFmt, amount=isk / 100.0)
    return iskFmt


def GetMarketTypes():
    data = []
    for t in cfg.invtypes:
        if t.published:
            g = cfg.invgroups.Get(t.groupID)
            if g.published:
                c = cfg.invcategories.Get(g.categoryID)
                if c.published:
                    data.append(t.line)

    ret = rowset.Rowset(cfg.invtypes.header, data)
    return ret


def GetContractIcon(type):
    icons = {const.conTypeNothing: 'res:/ui/Texture/WindowIcons/contracts.png',
     const.conTypeItemExchange: 'res:/ui/Texture/WindowIcons/contractItemExchange.png',
     const.conTypeAuction: 'res:/ui/Texture/WindowIcons/contractAuction.png',
     const.conTypeCourier: 'res:/ui/Texture/WindowIcons/contractCourier.png',
     const.conTypeLoan: '64_15'}
    return icons.get(type, 'res:/ui/Texture/WindowIcons/contracts.png')


def GetColoredContractStatusText(status):
    cols = {0: 'ffffff',
     1: 'ffffff',
     2: 'ffffff',
     3: 'ffffff',
     4: 'ffffff',
     5: 'ffffff',
     6: 'ffffff',
     7: 'aa0000',
     8: 'ffffff'}
    col = cols[status]
    st = GetContractStatusText(status)
    return '<color=0xff%s>%s</color>' % (col, st)


def ConFmtDate(time, isText = False):
    if time < 0:
        return localization.GetByLabel('UI/Contracts/Util/ContractExpiredEmphasized')
    res = ''
    d = time / const.DAY
    h = (time - d * const.DAY) / const.HOUR
    if isText:
        if d >= 1:
            res = localization.GetByLabel('/Carbon/UI/Common/WrittenDateTimeQuantity/Day', days=d)
        elif d < 0:
            res = localization.GetByLabel('UI/Contracts/Util/ContractExpiredEmphasized')
        elif h >= 1:
            res = localization.GetByLabel('UI/Contracts/Util/LessThanADay')
        else:
            res = localization.GetByLabel('UI/Contracts/Util/LessThanAnHour')
    else:
        if d >= 1:
            if h > 0:
                res = localization.GetByLabel('UI/Contracts/Util/DayToHour', days=d, hours=h)
            else:
                res = localization.GetByLabel('/Carbon/UI/Common/WrittenDateTimeQuantity/Day', days=d)
        elif h >= 1 and d == 0:
            res = localization.GetByLabel('/Carbon/UI/Common/WrittenDateTimeQuantity/Hour', hours=h)
        if time / const.HOUR == 0:
            res = localization.GetByLabel('UI/Contracts/Util/LessThanAnHour')
    return res


def GetContractTimeLeftText(c):
    if c.status == const.conStatusOutstanding:
        if c.dateExpired < blue.os.GetWallclockTime():
            return localization.GetByLabel('UI/Contracts/Util/ContractExpired')
        else:
            return ConFmtDate(c.dateExpired - blue.os.GetWallclockTime(), c.type == const.conTypeAuction)
    else:
        return ''


def CutAt(txt, l):
    if len(txt) > l:
        return txt[:l - 3] + '...'
    else:
        return txt


def SelectItemTypeDlg(itemTypes):
    """
    use:  t = SelectItemTypeDlg(types)
    pre:  'types' is valid and contains at least 1 text entry
    post: iff 't': 't' contains the typeID that the user selected
          else: A message box has popped up notifying the user of failure    
    """
    tmplst = []
    for typeID in itemTypes:
        t = cfg.invtypes.Get(typeID)
        c = cfg.invcategories.Get(t.categoryID)
        itemTypeRow = localization.GetByLabel('UI/Contracts/Util/ItemTypeLine', item=typeID, categoryName=c.categoryName)
        tmplst.append((itemTypeRow, typeID))

    if not tmplst:
        eve.Message('ConNoItemsFound')
        return
    elif len(tmplst) == 1:
        return tmplst[0][1]
    else:
        ret = uix.ListWnd(tmplst, 'generic', localization.GetByLabel('UI/Contracts/Util/SelectItemType'), None, 1, windowName='contractSelectItemTypeDlg')
        return ret and ret[1]


def MatchInvTypeName(s, invType):
    """
    Return True if s is a case-insensitive-substring of the name of invType.
    
    Matches either the original (English) or the localized name.
    """
    cfgType = cfg.invtypes.Get(invType.typeID)
    localized = cfgType.typeName
    english = cfgType._typeName
    return CaseInsensitiveSubMatch(s, localized) or CaseInsensitiveSubMatch(s, english)


def CaseInsensitiveSubMatch(matchStr, inStr):
    """
    Return True if matchStr is a substring of inStr, when compared in a case
    insensitive way.
    """
    return matchStr.lower() in inStr.lower()


def TypeName(typeID):
    return cfg.invtypes.Get(typeID).typeName


def GroupName(groupID):
    return cfg.invgroups.Get(groupID).groupName


def CategoryName(categoryID):
    return cfg.invcategories.Get(categoryID).categoryName


def IsSearchStringLongEnough(txt):
    """
    Return True iff the given txt is long enough for the locale. Otherwise,
    display an appropriate error message and return False.
    
    Languages with ideographic scripts (e.g. Chinese) have a minimum size of 1
    for search strings, since each glyph is significant enough. Alphabet based
    languages (e.g. English, Russian) have a minimum of three letters.
    """
    error = None
    if IsIdeographic(eve.session.languageID) and not txt:
        error = 'ConNeedAtLeastOneLetter'
    if not IsIdeographic(eve.session.languageID) and (not txt or len(txt) < 3):
        error = 'ConNeedAtLeastThreeLetters'
    if error:
        eve.Message(error)
    return not error


def IsIdeographic(languageID):
    return languageID == 'ZH'


def DoParseItemType(wnd, prevVal = None, marketOnly = False):
    itemTypes = []
    txt = wnd.GetValue()
    if len(txt) == 0 or not IsSearchStringLongEnough(txt):
        return
    if txt == prevVal:
        return
    for t in GetMarketTypes():
        if t.marketGroupID is None and marketOnly:
            continue
        if MatchInvTypeName(txt, t):
            itemTypes.append(t.typeID)

    typeID = SelectItemTypeDlg(itemTypes)
    if typeID:
        wnd.SetValue(TypeName(typeID))
    return typeID


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('contractutils', locals())
