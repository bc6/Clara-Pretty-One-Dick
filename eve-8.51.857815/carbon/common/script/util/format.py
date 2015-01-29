#Embedded file name: carbon/common/script/util\format.py
"""
This files contain stateless dependency free string formatting utilities
"""
import log
import blue
import string
import re
import math
import datetime
import localization
import eveLocalization
from stdlogutils import LineWrap
SMALLDATETIME_MIN = 94432608000000000L
SMALLDATETIME_MAX = 150973632000000000L
__dateseptbl = string.maketrans('/-. ', '----')
DECIMAL = prefs.GetValue('decimal', '.')
DIGIT = prefs.GetValue('digit', ',')
ROMAN_NUMERAL_MAP = (('X', 1, 10),
 ('IX', 2, 9),
 ('V', 1, 5),
 ('IV', 2, 4),
 ('I', 1, 1))
romanNumeralPattern = re.compile("^                   # beginning of string\n(X{0,3})            # tens - 0-30 (0 to 3 X's),\n                    #\n(IX|IV|V?I{0,3})    # ones - 9 (IX), 4 (IV), 0-3 (0 to 3 I's),\n                    #        or 5-8 (V, followed by 0 to 3 I's)\n$                   # end of string\n", re.VERBOSE)
urlHttpCheck = re.compile('\\Ahttp(s)?://', re.I)

def EscapeSQL(s, exactMatch = 0, min = 3):
    if not exactMatch:
        s = s.replace('%', '')
        s = s.replace('[', '[[]')
        s = s.replace('_', '[_]')
    return s


def EscapeAdHocSQL(s):
    s = s.replace("'", "''")
    s = s.replace('%', '')
    s = s.replace('[', '[[]')
    s = s.replace('_', '[_]')
    return s


def FmtTimeIntervalMaxParts(interval, breakAt = 'msec', maxParts = None):
    if interval < 10000L:
        return localization.GetByLabel('/Carbon/UI/Common/Formatting/ShortAmountTime')
    breakAt2 = breakAt
    if breakAt2 == 'min':
        breakAt2 = 'minute'
    elif breakAt2 == 'sec':
        breakAt2 = 'second'
    elif breakAt2 in ('msec', None):
        breakAt2 = 'millisecond'
    timeInterval = localization.formatters.FormatTimeIntervalWritten(interval, showFrom='year', showTo=breakAt2, maxParts=maxParts)
    return timeInterval


def FmtTimeInterval(interval, breakAt = 'msec', *args):
    return FmtTimeIntervalMaxParts(interval=interval, breakAt=breakAt)


def FmtDate(date, fmt = 'll'):
    """
    Returns a formatted date, datetime or time string, or None if 'date' is None
    
     'date' is a Blue Time value (64 bit integer where const.SEC is one second).
     'fmt' is the format, fmt[0] is date format, fmt[1] is time format:
     "n" for None (not display)
     "l" for long format
     "s" for short format
     "x" for eXtended format (includes milliseconds)
    
    # There is no support now for negative values, will be added again if needed
    
    """
    if date is None:
        return
    if fmt == 'nn':
        log.LogTraceback("Incorrect format statement used, 'nn' would result in a return value of None for all input.")
        fmt = 'll'
    if date < 0:
        log.LogTraceback('Negative value in FmtDate')
        date *= -1
    year1800 = const.YEAR365 * 199L
    if fmt[1] not in ('l', 's', 'n'):
        log.LogTraceback('Incorrect format statement used', fmt)
        raise RuntimeError('InvalidArg', fmt)
    if date < year1800:
        if fmt[1] == 's':
            return localization.formatters.FormatTimeIntervalShortWritten(date, showFrom='day', showTo='second')
        else:
            return localization.formatters.FormatTimeIntervalWritten(date, showFrom='day', showTo='second')
    else:
        if fmt in ('ll', 'sl', 'nn', 'xs'):
            return localization.GetByLabel('/Carbon/UI/Common/DateTime/SimpleDateUTC', datetime=date)
        if fmt in ('ls', 'ss'):
            return localization.GetByLabel('/Carbon/UI/Common/DateTime/DateLongShort', datetime=date)
        if fmt in ('ln', 'sn', 'xn'):
            return localization.GetByLabel('/Carbon/UI/Common/DateTime/DateLongNone', datetime=date)
        if fmt == 'nl':
            return localization.GetByLabel('/Carbon/UI/Common/DateTime/Time', datetime=date)
        if fmt == 'ns':
            return localization.GetByLabel('/Carbon/UI/Common/DateTime/HoursAndMinutes', datetime=date)
        if fmt == 'xl':
            return localization.GetByLabel('/Carbon/UI/Common/DateTime/SimpleDateUTC', datetime=date)
        if fmt == 'el':
            return localization.GetByLabel('/Carbon/UI/Common/DateTime/DateExtendedLong', datetime=date)
        if fmt == 'es':
            return localization.GetByLabel('/Carbon/UI/Common/DateTime/DateExtendedShort', datetime=date)
        if fmt == 'en':
            return localization.GetByLabel('/Carbon/UI/Common/DateTime/DateExtendedNone', datetime=date)
        log.LogTraceback('InvalidArg', fmt)
        raise RuntimeError('InvalidArg', fmt)


def FmtSimpleDateUTC(date):
    """
    Returns a string on the format 'yyyy.mm.dd hh:mm:ss'
    'date' is a Blue Time
    """
    if date is None:
        return
    return localization.GetByLabel('/Carbon/UI/Common/DateTime/SimpleDateUTC', datetime=date)


def FmtTime(time):
    hours = localization.formatters.FormatNumeric(time / const.HOUR, leadingZeroes=2)
    mins = localization.formatters.FormatNumeric(time % const.HOUR / const.MIN, leadingZeroes=2)
    secs = localization.formatters.FormatNumeric(time % const.MIN / const.SEC, leadingZeroes=2)
    return localization.GetByLabel('/Carbon/UI/Common/DateTimeQuantity/DateTimeShort3Elements', value1=hours, value2=mins, value3=secs)


def FmtSec(time):
    if not time:
        return localization.uiutil.PrepareLocalizationSafeString('0', messageID='time')
    h = time / const.HOUR
    m = time % const.HOUR / const.MIN
    s = time % const.MIN / float(const.SEC)
    return localization.GetByLabel('/Carbon/UI/Common/FormatTime/FmtSecSpecial', hours=h, minutes=m, seconds=s)


def FmtAmt(amount, fmt = 'ln', showFraction = 0, *args):
    """
     Returns a formatted amount value.
    'fmt' works in the same manner as in FmtDate here above.
    
     fmt[0] is the format of the value itself. It can be:
     "s" for as-short-as-possible,
     "l" for dot every 3 decimals.
    
     "ln": 1,234,567,890
     "sn": always 4-5 characters  (plus optional sign) using 3 digits + optional digit
      separator and 1 scale indicator (which is T, B, M, or K, for pow. 12, 9, 6 and 3):
           1.23B   1.23 billions
           0.15B    150 millions
           0.23M    230 thousand
           1.29K    one thousand two hundred ninety
           -68.1K  -68 thousand one hundred
           0.95K   ca. 950
           76.3T   76.3 Trillions
    
     showFraction > determines how many xtraletters are shown in "l" mode
     """
    if amount == None:
        amount = 0
    orgamount = amount
    try:
        amount = long(amount)
    except:
        raise RuntimeError('Amount (%s) is not an integer' % str(amount))

    if fmt[0] == 'l':
        amt = orgamount
        if showFraction == 0:
            amt = amount
        return localization.formatters.FormatNumeric(amt, useGrouping=True, decimalPlaces=showFraction)
    if fmt[0] == 's':
        amt = amount
        val = abs(amount)
        labelPathDict = {('thousand', 'short'): '/Carbon/UI/Common/Formatting/FmtThousandShort',
         ('thousand', 'long'): '/Carbon/UI/Common/Formatting/FmtThousandLong',
         ('million', 'short'): '/Carbon/UI/Common/Formatting/FmtMillionShort',
         ('million', 'long'): '/Carbon/UI/Common/Formatting/FmtMillionLong',
         ('billion', 'short'): '/Carbon/UI/Common/Formatting/FmtBillionShort',
         ('billion', 'long'): '/Carbon/UI/Common/Formatting/FmtBillionLong',
         ('trillion', 'short'): '/Carbon/UI/Common/Formatting/FmtTrillionShort',
         ('trillion', 'long'): '/Carbon/UI/Common/Formatting/FmtTrillionLong'}
        if fmt[1] == 'l':
            labelLength = 'long'
        else:
            labelLength = 'short'
        if val >= 100000000000000.0:
            raise UserError('WhatKindOfAmountIsThis', {'amount': amount})
        if val < 10000.0:
            return localization.formatters.FormatNumeric(amt, useGrouping=True)
        if val < 100000.0:
            amt = float(amt) / long(1000.0)
            labelPath = labelPathDict.get(('thousand', labelLength))
        elif val < 100000000.0:
            amt = float(amt) / long(1000000.0)
            labelPath = labelPathDict.get(('million', labelLength))
        elif val < 100000000000.0:
            amt = float(amt) / long(1000000000.0)
            labelPath = labelPathDict.get(('billion', labelLength))
        elif val < 100000000000000.0:
            amt = float(amt) / long(1000000000000.0)
            labelPath = labelPathDict.get(('trillion', labelLength))
        return localization.GetByLabel(labelPath, amount=amt)
    return localization.uiutil.PrepareLocalizationSafeString(orgamount, messageID='amount')


def FmtDist(dist, maxdemicals = 2, signed = False):
    """
    Returns a formatted distance.
    dist cannot be negative, strictly speaking, but this function is also used to
    format the elements in coordinate vectors, see FmtVec
    """
    if signed and dist < 0.0:
        dist = abs(dist)
    dist = max(0, dist)
    if dist < 10000.0:
        if dist == 0 or dist >= 1.0:
            dist = int(dist)
            maxdemicals = None
        fmtUrl = '/Carbon/UI/Common/FormatDistance/fmtDistInMeters'
    elif dist < 10000000000.0:
        dist = long(dist / 1000.0)
        maxdemicals = None
        fmtUrl = '/Carbon/UI/Common/FormatDistance/fmtDistInKiloMeters'
    else:
        dist = round(dist / const.AU, maxdemicals)
        fmtUrl = '/Carbon/UI/Common/FormatDistance/fmtDistInAU'
    if maxdemicals == 0:
        maxdemicals = None
        dist = int(dist)
    distStr = localization.formatters.FormatNumeric(dist, useGrouping=True, decimalPlaces=maxdemicals)
    return localization.GetByLabel(fmtUrl, distance=distStr)


def FmtVec(vec, maxdecimals = 3):
    """
    Returns a vector with formatted distance.
    not displayed, so it doesn't need to be translation safe
    """
    return '[%s, %s, %s]' % (FmtDist(vec[0], maxdecimals, signed=True), FmtDist(vec[1], maxdecimals, signed=True), FmtDist(vec[2], maxdecimals, signed=True))


def FmtYesNo(isYes):
    if isYes:
        return localization.GetByLabel('UI/Common/Yes')
    else:
        return localization.GetByLabel('UI/Common/No')


def ParseDate(date):
    """
    Parses a date string into a Blue time. Returns None if 'date' is None or empty
    string, raises InvalidDate if the string is incorrectly formatted or a Blue time
    if successfull.
    
    'date' is a string with these parts: "[yyyy-m-d]".
    Note: The separator can be dash, slash or dot: - . /
    """
    if date is None or date == '':
        return
    if type(date) == unicode:
        date = str(date)
    try:
        date = string.translate(date.split(' ')[0], __dateseptbl)
        dp = date.split('-', 2)
        return blue.os.GetTimeFromParts(int(dp[0]), int(dp[1]), int(dp[2]), 0, 0, 0, 0)
    except:
        raise UserError('InvalidDate', {'date': date})


def ParseTime(time, isInterval = False):
    """
    Parses a time string into a Blue time. Returns None if 'time' is None or empty
    string, raises InvalidDate if the string is incorrectly formatted or a Blue time
    if successfull.
    
    'time' is a string with these parts: "[h:m]" or "[h:m:s]"
    """
    if time is None or time == '':
        return
    try:
        tp = time.split(':', 2)
        time = int(tp[0]) * const.HOUR + int(tp[1]) * const.MIN
        if len(tp) == 3:
            time = time + int(tp[2]) * const.SEC
        if not isInterval and boot.region == 'optic':
            time -= eveLocalization.GetTimeDelta() * const.SEC
            if time < 0:
                time += 24 * const.HOUR
        return time
    except:
        raise UserError('InvalidTime', {'time': time})


def ParseDateTime(dateTime):
    if dateTime is None or dateTime == '':
        return
    if ' ' in dateTime:
        d, t = dateTime.split(' ')
        dateTime = ParseDate(d)
        dateTime += ParseTime(t)
    else:
        dateTime = ParseDate(dateTime)
    return dateTime


def ParseTimeInterval(time):
    return ParseTime(time, True)


def GetTimeParts(datetime, utc = False):
    if not utc and datetime % const.DAY and boot.region == 'optic':
        datetime += eveLocalization.GetTimeDelta() * const.SEC
    return blue.os.GetTimeParts(datetime)


months = [31,
 59,
 90,
 120,
 151,
 181,
 212,
 243,
 273,
 304,
 334,
 365]
monthsl = [31,
 60,
 91,
 121,
 152,
 182,
 213,
 244,
 274,
 305,
 335,
 366]

def isleap(year):
    return not year % 4


def dateConvert(tmp):
    """
    dateConvert, convert a tuple from blue.os.GetTimeParts to a python time tuple
    nb. not leapYear not taken into consideration
    """
    if isleap(tmp[const.TP_YEAR]):
        m = monthsl
    else:
        m = months
    return (tmp[const.TP_YEAR],
     tmp[const.TP_MONTH],
     tmp[const.TP_DAY],
     tmp[const.TP_HOUR],
     tmp[const.TP_MIN],
     tmp[const.TP_SEC],
     tmp[const.TP_DAY_OF_WEEK],
     m[tmp[const.TP_MONTH] - 1] + tmp[const.TP_DAY],
     0)


def ConvertDate(blueTime):
    import time
    return time.mktime(dateConvert(blue.os.GetTimeParts(blueTime)))


def BlueToDate(time):
    """
    Converts a python datetime object into an EVE blue time.
    """
    parts = blue.os.GetTimeParts(time)
    return datetime.datetime(*(parts[:2] + parts[3:]))


def DateToBlue(time):
    """
    Converts an EVE blue time into a python datetime object.
    """
    return blue.os.GetTimeFromParts(time.year, time.month, time.day, time.hour, time.minute, time.second, time.microsecond / 1000)


def FmtCdkey(cdkey):
    if not cdkey:
        return ''
    return '%s-%s-%s-%s-%s-%s-%s' % (cdkey[0:5],
     cdkey[5:10],
     cdkey[10:15],
     cdkey[15:20],
     cdkey[20:25],
     cdkey[25:30],
     cdkey[30:35])


def CaseFold(s):
    s2 = s.upper().lower()
    if s2 != s:
        return CaseFold(s2)
    return s2


def CaseFoldCompare(l, r):
    """
    Compares two strings in a case-insensitive, unicode-safe manner
    Can return false positives for weird chars, but shouldn't return
    false negatives
    """
    l2 = l.upper().lower()
    r2 = r.upper().lower()
    if l2 != l or r2 != r:
        return CaseFoldCompare(l2, r2)
    return cmp(l, r)


def CaseFoldEquals(l, r):
    return CaseFoldCompare(l, r) == 0


class PasswordString(unicode):
    __guid__ = 'util.PasswordString'

    def __str__(self):
        return '*****'

    def __repr__(self):
        return '*****'


def LFromUI(ui):
    return ui & 4294967295L


def StrFromColor(color):
    return hex(LFromUI(color.AsInt()))


def GetKeyAndNormalize(string):
    """
    This returns two values:
     * A key version of the string, i.e. in lowercase, with whitespace stripped
     * A normalized version of the string, i.e. with duplicate whitespace replaced
       by a single one
    """
    key = string
    norm = string
    for c in key:
        if c.isspace():
            key = key.replace(c, '')
            while True:
                prev = norm
                norm = norm.replace(c + c, c)
                if prev == norm:
                    break
                blue.pyos.BeNice()

    key = key.split('\\')[-1]
    return (CaseFold(key), norm)


def SecsFromBlueTimeDelta(t):
    return t / const.SEC


def HoursMinsSecsFromSecs(s):
    s = max(0, s)
    secs = int(s % 60)
    mins = int(s / 60 % 60)
    hours = int(s / 3600)
    return (hours, mins, secs)


def FormatTimeAgo(theTime):
    delta = blue.os.GetWallclockTime() - theTime
    hours, minutes, seconds = HoursMinsSecsFromSecs(SecsFromBlueTimeDelta(delta))
    if hours + minutes + seconds <= 0:
        howLongAgo = localization.GetByLabel('/Carbon/UI/Common/FormatTime/FmtTimeAgoRightNow')
    else:
        howLongAgo = localization.GetByLabel('/Carbon/UI/Common/FormatTime/FmtTimeAgoDays', time=delta)
    return howLongAgo


def ParseSmallDate(date):
    """
    Parses a date string using ParseDate() and then checks if the date is
    within SmallDateTime bounds.
    (Testing showed approx. Apr 1 1900 - Jun 2 2079 which is not exactly
    by SmallDateTime specs but close enough)
    
    'date' is a string with these parts: "[yyyy-m-d]".
    Note: The separator can be dash, slash or dot: - . /
    """
    parsedDate = ParseDate(date)
    if parsedDate > SMALLDATETIME_MIN and parsedDate < SMALLDATETIME_MAX:
        return parsedDate
    raise TypeError('Date is not a legal SmallDateTime value.')


def RomanToInt(roman):
    """
    Will translate roman numerals in the range of 0 - 39 to integers.
    Note that an empty string will translate to 0 which strictly speaking is not
    correct but is implemented for sorting reasons.
    """
    result = 0
    index = 0
    if not romanNumeralPattern.search(roman):
        raise RuntimeError, 'Invalid Roman numeral: %s' % roman
    for numeral, length, integer in ROMAN_NUMERAL_MAP:
        while roman[index:index + length] == numeral:
            result += integer
            index += length

    return result


def IntToRoman(n):
    """Translates integers on the range 0 < x < 40 to roman numerals."""
    if not 0 < n < 40:
        raise RuntimeError, 'number out of range (must be 1..4999)'
    if int(n) != n:
        raise RuntimeError, 'non-integers can not be converted'
    result = ''
    for numeral, length, integer in ROMAN_NUMERAL_MAP:
        while n >= integer:
            result += numeral
            n -= integer

    return localization.uiutil.PrepareLocalizationSafeString(result, messageID='intToRoman')


def GetYearMonthFromTime(blueTime):
    t = blue.os.GetTimeParts(blueTime)
    return (t[0], t[1])


def FormatUrl(url):
    url = url.strip()
    if len(url) and not urlHttpCheck.match(url):
        return 'http://%s' % url
    return url


def FmtDateEng(date, fmt = 'll'):
    """
    This is an unlocalized version of FmtDate and it is never supposed to be used for anything 
    the player will see. It should only be used by ESP and low-level systems
    
    Returns a formatted date, datetime or time string, or None if 'date' is None
    
        # 'date' is a Blue Time value (64 bit integer where const.SEC is one second).
    'fmt' is the format, fmt[0] is date format, fmt[1] is time format:
    "n" for None (not display)
    "l" for long format
    "s" for short format
    "x" for eXtended format (includes milliseconds)
    """
    if date is None:
        return
    if fmt == 'nn':
        log.LogTraceback("Incorrect format statement used, 'nn' would result in a return value of None for all input.")
        fmt = 'll'
    if date < 0:
        date *= -1
        neg = '-'
    else:
        neg = ''
    year1800 = const.YEAR365 * 199L
    if date >= year1800 and date % const.DAY and boot.region == 'optic':
        date += 8 * const.HOUR
    year, month, wd, day, hour, min, sec, ms = blue.os.GetTimeParts(date)
    sd = '%d.%.2d.%.2d' % (year, month, day)
    ld = sd
    lt = '%.2d:%.2d:%.2d' % (hour, min, sec)
    if fmt[0] == 'x':
        lt += ':%3d' % ms
    ed = '%d-%.2d-%.2d' % (year, month, day)
    st = lt[:-3]
    if fmt[1] == 'l':
        hrs = lt
    elif fmt[1] == 's':
        hrs = st
    elif fmt[1] == 'n':
        hrs = None
    else:
        raise RuntimeError('InvalidArg', fmt)
    if date % const.DAY == 0:
        hrs = None
    if date < year1800:
        datefmt = None
        days = date / const.DAY
        s = date % const.MIN / const.SEC
        m = date % const.HOUR / const.MIN
        h = date % const.DAY / const.HOUR
        hrs = ''
        if fmt[1] == 's':
            if days:
                hrs = '%d%s' % (days, 'D')
            if h:
                hrs = hrs + ' %d%s' % (h, 'H')
            if m:
                hrs = hrs + ' %d%s' % (m, 'M')
            if s:
                hrs = hrs + ' %d%s' % (s, 'S')
        else:
            if days:
                hrs = '%d %s' % (days, ['day', 'days'][days != 1])
            if h:
                hrs = hrs + ' %d %s' % (h, ['hour', 'hours'][h != 1])
            if m:
                hrs = hrs + ' %d %s' % (m, ['minute', 'minutes'][m != 1])
            if s or hrs == '':
                hrs = hrs + ' %d %s' % (s, ['second', 'seconds'][s != 1])
    elif fmt[0] == 'l' or fmt[0] == 'x':
        datefmt = ld
    elif fmt[0] == 's':
        datefmt = sd
    elif fmt[0] == 'n':
        datefmt = None
    elif fmt[0] == 'e':
        datefmt = ed
    else:
        raise RuntimeError('InvalidArg', fmt)
    if datefmt is None and hrs is None:
        return
    elif datefmt is not None and hrs is None:
        return neg + datefmt
    elif datefmt is None and hrs is not None:
        return neg + hrs.strip()
    elif fmt[0] == 'e':
        return '%s%sT%s.000' % (neg, datefmt, hrs)
    else:
        return '%s%s %s' % (neg, datefmt, hrs)


def FmtTimeIntervalEng(interval, breakAt = None, *args, **kwargs):
    """
    This is an unlocalized version of FmtTimeInterval and it is never supposed to be used for anything 
    the player will see. It should only be used by ESP and low-level systems
    
    Returns string representing the given timeframe 'interval' at the
    time resolution of 'breakAt' which can be one of the following:
      year, month, day, hour, min, sec, ms
    """
    if interval < 10000L:
        return 'A short amount of time'
    year, month, wd, day, hour, min, sec, ms = blue.os.GetTimeParts(interval)
    year -= 1601
    month -= 1
    day -= 1
    items = []
    while 1:
        if year:
            items.append(str(year) + ' ' + ['year', 'years'][year > 1])
        if breakAt == 'year':
            break
        if month:
            items.append(str(month) + ' ' + ['month', 'months'][month > 1])
        if breakAt == 'month':
            break
        if day:
            items.append(str(day) + ' ' + ['day', 'days'][day > 1])
        if breakAt == 'day':
            break
        if hour:
            items.append(str(hour) + ' ' + ['hour', 'hours'][hour > 1])
        if breakAt == 'hour':
            break
        if min:
            items.append(str(min) + ' ' + ['minute', 'minutes'][min > 1])
        if breakAt == 'min':
            break
        if sec:
            items.append(str(sec) + ' ' + ['second', 'seconds'][sec > 1])
        if breakAt == 'sec':
            break
        if ms:
            items.append(str(ms) + ' ' + ['millisecond', 'milliseconds'][ms > 1])
        break

    if items:
        if len(items) == 1:
            return items[0]
        else:
            lastItem = items.pop()
            return ', '.join(items) + ' ' + 'and' + ' ' + lastItem
    else:
        if breakAt == 'sec':
            return 'Less than a second'
        if breakAt == 'min':
            return 'Less than a minute'
        return {'DAY': 'less than a day',
         'HOUR': 'less than an hour',
         'MILLISECOND': 'less than a millisecond',
         'MINUTE': 'less than a minute',
         'MONTH': 'less than a month',
         'SECOND': 'less than a second',
         'YEAR': 'less than a year'}.get(breakAt.upper(), 'less than a ' + breakAt)


def FmtTimeEng(time):
    """
    This is an unlocalized version of FmtTime and it is never supposed to be used for anything 
    the player will see. It should only be used by ESP and low-level systems
    """
    return '%.2d:%.2d:%.2d' % (time / const.HOUR, time % const.HOUR / const.MIN, time % const.MIN / const.SEC)


def FmtAmtEng(amount, fmt = 'ln', showFraction = 0, fillWithZero = 0):
    """
    This is an unlocalized version of FmtAmt and it is never supposed to be used for anything 
    the player will see. It should only be used by ESP and low-level systems
    """
    if amount == None:
        amount = 0
    orgamount = amount
    try:
        amount = long(amount)
    except:
        raise RuntimeError('AmountMustBeInteger', amount)

    minus = ['', '-'][float(orgamount) < 0.0]
    fraction = ''
    ret = ''
    fractionNumber = None
    if fmt[0] == 'l':
        if showFraction:
            fraction = abs(math.fmod(orgamount, 1.0))
            fraction = round(fraction, showFraction)
            if fraction >= 1.0:
                amount += [-1, 1][amount >= 0.0]
                fraction = 0.0
            fraction = str(fraction)[2:]
            if fillWithZero:
                while len(fraction) < showFraction:
                    fraction += '0'

            fractionNumber = float('%s.%s' % (amount, fraction))
            fraction = DECIMAL + str(fraction)
        digit = ''
        amt = '%d' % abs(amount)
        for i in xrange(len(amt) % 3, len(amt) + 3, 3):
            if i < 3:
                ret = ret + amt[:i]
            else:
                ret = ret + digit + amt[i - 3:i]
            if i != 0:
                digit = DIGIT

    elif fmt[0] == 's':
        val = abs(amount)
        fractionNumber = val
        isOne = str(val)[0] == '1'
        if val < 10000.0:
            ret = str(val)
        elif val < 100000.0:
            if fmt[1] == 'l':
                unitString = ['thousands', 'thousand'][isOne]
            else:
                unitString = 'K'
            ret = '%s%s' % (TruncateAmt(val, long(1000.0)), unitString)
        elif val < 100000000.0:
            if fmt[1] == 'l':
                unitString = ['millions', 'million'][isOne]
            else:
                unitString = 'M'
            ret = '%s%s' % (TruncateAmt(val, long(1000000.0)), unitString)
        elif val < 100000000000.0:
            if fmt[1] == 'l':
                unitString = ['billions', 'billion'][isOne]
            else:
                unitString = 'B'
            ret = '%s%s' % (TruncateAmt(val, long(1000000000.0)), unitString)
        elif val < 100000000000000.0:
            if fmt[1] == 'l':
                unitString = ['trillions', 'trillion'][isOne]
            else:
                unitString = 'T'
            ret = '%s%s' % (TruncateAmt(val, long(1000000000000.0)), unitString)
        else:
            raise UserError('WhatKindOfAmountIsThis', {'amount': amount})
    else:
        ret = '%d' % abs(amount)
    if fractionNumber == 0:
        minus = ''
    return minus + ret + fraction


def TruncateAmt(val, unit):
    rest = val % unit / (unit / 100L)
    ret = str(val / unit)
    if rest > 0:
        ret = ret + '%s%02d' % (DECIMAL, rest)
        if ret[-1:] == '0':
            ret = ret[:-1]
    return ret


def FmtSecEng(time):
    """
    This is an unlocalized version of FmtSec and it is never supposed to be used for anything 
    the player will see. It should only be used by ESP and low-level systems
    """
    if not time:
        return '0'
    h = time / const.HOUR
    m = time % const.HOUR / const.MIN
    s = time % const.MIN / float(const.SEC)
    return "%.2d:%.2d'%06.3f" % (h, m, s)


exports = {'util.GetKeyAndNormalize': GetKeyAndNormalize,
 'util.CaseFoldCompare': CaseFoldCompare,
 'util.CaseFold': CaseFold,
 'util.CaseFoldEquals': CaseFoldEquals,
 'util.LineWrap': LineWrap,
 'util.EscapeSQL': EscapeSQL,
 'util.EscapeAdHocSQL': EscapeAdHocSQL,
 'util.FmtDate': FmtDate,
 'util.FmtSimpleDateUTC': FmtSimpleDateUTC,
 'util.FmtTime': FmtTime,
 'util.FmtSec': FmtSec,
 'util.FmtTimeInterval': FmtTimeInterval,
 'util.FmtAmt': FmtAmt,
 'util.FmtDist': FmtDist,
 'util.ParseDate': ParseDate,
 'util.ParseSmallDate': ParseSmallDate,
 'util.ParseTime': ParseTime,
 'util.ParseDateTime': ParseDateTime,
 'util.ParseTimeInterval': ParseTimeInterval,
 'util.GetTimeParts': GetTimeParts,
 'util.dateConvert': dateConvert,
 'util.ConvertDate': ConvertDate,
 'util.BlueToDate': BlueToDate,
 'util.DateToBlue': DateToBlue,
 'util.FmtCdkey': FmtCdkey,
 'util.StrFromColor': StrFromColor,
 'util.LFromUI': LFromUI,
 'util.RomanToInt': RomanToInt,
 'util.IntToRoman': IntToRoman,
 'util.FmtVec': FmtVec,
 'util.DECIMAL': DECIMAL,
 'util.DIGIT': DIGIT,
 'util.GetYearMonthFromTime': GetYearMonthFromTime,
 'util.FormatUrl': FormatUrl,
 'util.FormatTimeAgo': FormatTimeAgo,
 'util.FmtTimeIntervalEng': FmtTimeIntervalEng,
 'util.FmtDateEng': FmtDateEng,
 'util.FmtTimeEng': FmtTimeEng,
 'util.FmtAmtEng': FmtAmtEng,
 'util.FmtSecEng': FmtSecEng}
