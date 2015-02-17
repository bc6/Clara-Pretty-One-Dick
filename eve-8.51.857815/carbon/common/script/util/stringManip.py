#Embedded file name: carbon/common/script/util\stringManip.py
"""
This collection is the functions performing straightforward string manipulation
"""
import re

def TruncateStringTo(s, length, addTrail = None):
    """
        Shortens string to given length ignoring all tags
        This is a duplicate of a function in the client code
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


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('util', locals())
