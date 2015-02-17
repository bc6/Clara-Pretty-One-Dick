#Embedded file name: carbon/common/script/util\commonutils.py
"""
    This file contains declarations and common helper functions used in the UI
    and Server Pages; most of these are formatting and parsing functions
"""
import re
import blue
from carbon.common.script.sys.service import ROLEMASK_ELEVATEDPLAYER

def IsFullLogging():
    """
        use:  b = util.IsFullLogging()
        pre:  application has valid session context
        post: iff b: the caller is safe to write sensitive data out to a log stream
                     because we are either on a server or with an internal user account
    """
    return boot.role != 'client' or not blue.pyos.packaged or session.role & ROLEMASK_ELEVATEDPLAYER


class Object:
    __guid__ = 'util.Object'

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def Get(self, key, defval = None):
        return self.__dict__.get(key, defval)

    def Set(self, key, value):
        self.__dict__[key] = value


def Truncate(number, numdec):
    """
        Truncates the  number to one that has the specified number of decimal digits
    
        use:    num = util.Truncate(number, numdec)
        pre:    number is a valid number, and numdec is an integer
        post:   num is the truncated version of number (everything after the first numdec decimals cut) 
        
        example:    util.Truncated(0.49999,  2)  = 0.48999999999999999 (which is really 0.49)
                    util.Truncated(0.49999,  3)  = 0.499
                    util.Truncated(-0.49999, 1) = -0.4
    """
    if numdec >= 0:
        decshift = float(pow(10, numdec))
        return float(int(number * decshift)) / decshift
    else:
        return number


def Clamp(val, min_, max_):
    """
    Return the given val, constrained to be not lesser than min_ and not 
    greater than max_.
    """
    return min(max_, max(min_, val))


def GetAttrs(obj, *names):
    """
    Chained getattr. Returns None if any of the attributes is missing or None.
    """
    for name in names:
        obj = getattr(obj, name, None)
        if obj is None:
            return

    return obj


def HasDialogueHyperlink(rawText):
    """
    Given raw dialog, return true if there is a hyperlink.
    """
    hasHyperlink = False
    openBracket = rawText.find('[')
    if openBracket > -1:
        nextCloseBracket = rawText.find(']', openBracket)
        if nextCloseBracket > -1:
            hasHyperlink = True
    return hasHyperlink


def StripTags(s, ignoredTags = tuple(), stripOnly = tuple()):
    """
        Removes html tags from text, leaving the fresh, quivering text it contained (if any) untouched.
        ignoredTags is a list of tags that should not be stripped
        stripOnly is a list of specific tags to remove while leaving the others intact
    """
    if not s or not isinstance(s, basestring):
        return s
    regex = '|'.join([ '</%s>|<%s>|<%s .*?>|<%s *=.*?>' % (tag,
     tag,
     tag,
     tag) for tag in stripOnly or ignoredTags ])
    if stripOnly:
        return ''.join(re.split(regex, s))
    elif ignoredTags:
        for matchingTag in [ tag for tag in re.findall('<.*?>', s) if tag not in re.findall(regex, s) ]:
            s = s.replace(matchingTag, '')

        return s
    else:
        return ''.join(re.split('<.*?>', s))


exports = {'util.IsFullLogging': IsFullLogging,
 'util.Truncate': Truncate,
 'util.Clamp': Clamp,
 'util.GetAttrs': GetAttrs,
 'util.HasDialogueHyperlink': HasDialogueHyperlink,
 'uiutil.StripTags': StripTags}
