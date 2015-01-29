#Embedded file name: carbonui/util\stringManip.py
"""
This collection is all the functions performing straightforward string manipulation
"""
import re
import carbonui.const as uiconst
import string

def PrepareArgs(args):
    dest = {}
    arg = args.split('&')
    for i in arg:
        kv = i.split('=', 1)
        if len(kv) == 2:
            s = kv[1]
            if dest.has_key(kv[0]):
                if type(dest[kv[0]]) != type([]):
                    dest[kv[0]] = [dest[kv[0]]]
                dest[kv[0]].append(s)
            else:
                dest[kv[0]] = s
        else:
            dest[i] = ''

    return dest


def Zip(*parts):
    return '\t'.join(parts)


def Unzip(s):
    if '\t' in s:
        return s.split('\t')
    else:
        return [ each.replace('\\|', '|') for each in s.split('||') ]


def TruncateStringTo(s, length, addTrail = None):
    """
        Shortens string to given length ignoring all tags
    """
    tagSplit = re.split('(<.*?>)', s)
    done = False
    ret = u''
    counter = 0
    for part in tagSplit:
        if part.startswith('<'):
            ret += part
            continue
        if done:
            continue
        encoded = Encode(part)
        for letter in encoded:
            ret += Decode(letter)
            counter += 1
            if counter == length:
                done = True
                if addTrail:
                    ret += addTrail
                break

    return ret


def Encode(text):
    return text.replace(u'&gt;', u'>').replace(u'&lt;', u'<').replace(u'&amp;', u'&').replace(u'&AMP;', u'&').replace(u'&GT;', u'>').replace(u'&LT;', u'<')


def Decode(text):
    return text.replace(u'&', u'&amp;').replace(u'<', u'&lt;').replace(u'>', u'&gt;')


def FlattenListText(listText):
    """ Util to flatten lists of lists of lists...
    This is to deal with listtext which contain listtexts like:
    ["a", ["b", "<br>", ["c2"]], "d"]
    """
    ret = []
    for each in listText:
        if isinstance(each, (tuple, list)):
            ret += FlattenListText(each)
        else:
            ret.append(each)

    return ret


def ReplaceTags(textOrListText, tags_replace):
    """ Util to replace tags in text or list of texts.
    tags_replace can be single tuple or tuple of tuples
    altered = uiutil.ReplaceTags(orginalText, (sourceTag, replaceString))
    """
    if not isinstance(tags_replace[0], tuple):
        tags_replace = (tags_replace,)
    textOrListText = GetAsUnicode(textOrListText)
    for tag, replaceWith in tags_replace:
        textOrListText = textOrListText.replace(tag, replaceWith)

    return textOrListText


def GetAsUnicode(textOrListText):
    """ Util to convert a text or list of texts into single unicode string."""
    if isinstance(textOrListText, (list, tuple)):
        textOrListText = FlattenListText(textOrListText)
        return ''.join((unicode(each) for each in textOrListText))
    return unicode(textOrListText)


def GetLevel(lvl):
    return ['-',
     'I',
     'II',
     'III',
     'IV',
     'V'][min(5, lvl)]


def IntToRoman(value):
    if value > 3999 or value < 1:
        return 'N/A'
    roman = ''
    for r, v, s in (('M', 1000, (('CM', 900), ('D', 500), ('CD', 400))),
     ('C', 100, (('XC', 90), ('L', 50), ('XL', 40))),
     ('X', 10, (('IX', 9), ('V', 5), ('IV', 4))),
     ('I', 1, ())):
        while value > v - 1:
            roman += r
            value -= v

        for rs, vs in s:
            if value > vs - 1:
                roman += rs
                value -= vs

    return roman


def RomanToInt(roman):
    d = {'I': 1,
     'V': 5,
     'X': 10,
     'L': 50,
     'C': 100,
     'D': 500,
     'M': 1000}
    nums = []
    for r in roman.upper():
        i = d.get(r, 0)
        if not nums:
            nums.append(i)
            continue
        if i > nums[-1]:
            nums[-1] = -nums[-1]
        nums.append(i)

    return sum(nums)


def UpperCase(string):
    if session.languageID == 'RU':
        return string
    if string is None:
        return ''
    string = string.upper()
    return string


def FindTextBoundaries(text, regexObject = None):
    """
    Breaks a string along line break boundaries, returning the text as a list of substrings.  A substring represents an atomic
    unit of text that should not be split when performing word wrapping.
    
    For example: "Lorem ipsum dolor sit amet" would become ["Lorem ", "ipsum ", "dolor ", "sit ", "amet"].
    
    You can specify your own compiled regex object for alternative boundary detection.
    """
    regexObject = regexObject or uiconst.LINE_BREAK_BOUNDARY_REGEX
    return [ token for token in regexObject.split(text) if token ]


def ReplaceStringWithTags(string, old = ' ', new = '<br>'):
    """
        replaces the "old" with "new", but leaves all the tags alone.
    """
    tagSplit = re.split('(<.*?>)', string)
    ret = u''
    for part in tagSplit:
        if part.startswith('<'):
            ret += part
            continue
        ret += part.replace(old, new)

    return ret


def SanitizeFilename(filename, replacementChar = '_'):
    """
    Replaces all invalid characters in a filename with an underscore.
    """
    invalidChars = '\\/:*?"<>|'
    validatedName = filename
    for c in invalidChars:
        validatedName = validatedName.replace(c, replacementChar)

    return validatedName


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('uiutil', locals())
