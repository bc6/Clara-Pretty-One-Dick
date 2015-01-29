#Embedded file name: datetimeutils\__init__.py
"""
Utilities for date and/or time objects and values. This includes any type
creation, manipulation, validation, checking or extensions of "temporal
objects", i.e. objects that store temporal values (date, time, datetime,
duration or any sort of measurement of time).

As a very generally rule of thumb, anything put in here should fulfill one of
these criteria:

    - return a temporal object, either after manipulation or creation
    - take in a temporal object as a parameter and have some sort of processing
      of it as it's main job
    - return the result of such processing
    - act as a mutator function on a temporal object
    - be independent, generic and "black-boxy". If your function would not be
      useable to anyone else either because of dependency on other packages or
      because of specialization bordering on "adhocyness", it probably doesn't
      belong here
    - type-cast one type of temporal object to another
    - classes in this file should extend other temporal object or be used
      almost exclusively to store temporal values
    - you as a programmer feel very strongly it should be here

Type-casting utilities involving temporal object and non-temporal objects
(date-to-whatever, whatever-to-time, etc.) should be put in typeutils, not
here.

This code uses the PEP 8 python coding style guide in accordance with internal
CCP standards with a few things borrowed from the Google python coding
guidelines.

    - http://www.python.org/dev/peps/pep-0008/
    - http://eve/wiki/Python_Coding_Guidelines
    - http://google-styleguide.googlecode.com/svn/trunk/pyguide.html

This code uses reStructuredText/Sphinx docstring markup mainly for parameter
and return value type hinting.

    - http://www.python.org/dev/peps/pep-0287/
    - http://sphinx-doc.org/markup/desc.html#info-field-lists
"""
import datetime
import re
_NOT_SUPPLIED = object()
FILETIME_NULL_DATE = datetime.datetime(1601, 1, 1, 0, 0, 0)
ISODATE_REGEX = re.compile('([0]{0,3}[1-9]\\d{0,3})[- /.,\\\\](1[012]|0?\\d)[- /.,\\\\](3[01]|[012]?\\d)(?:[ @Tt]+([2][0-3]|[01]?\\d)(?:[ .:,]([012345]?\\d)(?:[ .:,]([012345]?\\d)(?:[ .:,](\\d{0,6}))?)?)?)?')
MEAN_MONTH = 30.436875
MEAN_YEAR = 365.2425

def filetime_to_datetime(filetime):
    """Converts a windows file time value (number of 100-nanosecond ticks since
    1 January 1601 00:00:00 UT) to a standard python datetime.
    Valid values are approx. -5.04911232e17 to 2.65046774399999999e18
    
    :param filetime: long
    :rtype: datetime.datetime
    :raise OverflowError: if filetime value is out of the range of python
                          datetime (between the year 1 and 9999 AD)
    """
    return FILETIME_NULL_DATE + datetime.timedelta(microseconds=filetime / 10)


def datetime_to_filetime(dt):
    """Converts a python datetime object to windows filetime value (number of
    100-nanosecond ticks since 1 January 1601 00:00:00 UT).
    
    If the supplied parameter is a date as oppose to a datetime, it will first
    be converted locally to a datetime with the time 00:00:00.000000
    
    :type dt: datetime.datetime or datetime.date
    :rtype: long
    """
    if not isinstance(dt, datetime.datetime) and isinstance(dt, datetime.date):
        dt = datetime.datetime.combine(dt, datetime.time(0, 0, 0))
    delta = dt - FILETIME_NULL_DATE
    return 10 * ((delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds)


def isostr_to_datetime(string):
    r"""Converts an iso(-ish) formated string to datetime.
    
    The pattern is quite forgiving in a few ways so context based
    sanity-checking might be in order when parsing strings from "iffy"
    sources (user input):
    
        - The time part is optional, as well as individual time parts
        - Seperator character for date parts can be: dash (-), slash (/),
          backslash (\), dot (.), comma (,), or space ( )
        - Seperator character for time parts can be: colum (:), dot (.),
          comma (,), or space ( )
        - Seperator character of date and time halves can be: either case of
          the letter T (T or t), the at symbol (@) or space ( )
        - Values less than ten to not have to be zero-filled
          ("2013-1-2T3:4:5.6789" == "2013-01-02T03:04:05.6789")
        - The year can be any value from 1-9999
    
    Otherwise normal datetime restrictions apply (month must be 1-12, minutes
    hust me 0-59 etc.)
    
    :type string: str or unicode
    :rtype: datetime or None
    """
    match = ISODATE_REGEX.match(string.strip())
    if match:
        return datetime.datetime(*[ (int(i) if i else 0) for i in match.groups() ])


def any_to_datetime(temporal_object, default = _NOT_SUPPLIED):
    """Turns datetime, date, windows filetime and posix time into a python
    datetime if possible. By default returns the same input value on failed
    casting but another default return value can be given.
    
    :type temporal_object: datetime, date, long, int, str or unicode
    :type default: datetime or any
    :rtype: datetime or any
    """
    if default == _NOT_SUPPLIED:
        default = temporal_object
    try:
        if isinstance(temporal_object, datetime.datetime):
            return temporal_object
        if isinstance(temporal_object, datetime.date):
            return datetime.datetime.combine(temporal_object, datetime.time())
        if isinstance(temporal_object, float):
            if temporal_object > 99999999999L:
                temporal_object = long(temporal_object)
            else:
                return datetime.datetime.fromtimestamp(temporal_object)
        if isinstance(temporal_object, (int, long)):
            if temporal_object > 99999999999L:
                return filetime_to_datetime(temporal_object)
            else:
                return datetime.datetime.fromtimestamp(temporal_object)
        if isinstance(temporal_object, (str, unicode)):
            value = isostr_to_datetime(temporal_object)
            if value:
                return value
    except (OverflowError, ValueError):
        pass

    return default


def _div_and_rest(total, chunk):
    """Integer division of the total value by the chunk value. The result is
    then multiplied by the chunk and subtracted from the total and the two are
    then returned in a tuple, the division results first, the the remainder.
    
    Example:
    
        >>> total_days = 2000
        >>> years, total_days = _div_and_rest(total_days, 365.25)
        >>> years
        5
        >>> total_days
        173.75
        >>> months, total_days = _div_and_rest(total_days, 30)
        >>> months
        5
        >>> total_days
        23.75
    
    This small private utility function is here because something in me cringes
    like a kid at the dentists office by having to copy-paste a line of code 5
    times (so I wrote a 4 line function and 25 lines of documentation
    ...don't ask!)
    
    :type total: long or int or float
    :type chunk: long or int or float
    :rtype: tuple(int, long or int or float)
    """
    divs = int(total / chunk)
    return (divs, total - chunk * divs)


def split_delta(delta, include_weeks = True):
    """Splits a timedelta into a dictionary of time periods it aproximately
    contains. Mean length of years and months are used and fractional
    days/seconds might get shaved of but this is useful to evaluate individual
    period lengths of displaying the maximum chunk of period a timedelta
    contains.
    
    The dict includes a 'is_past' key in the returned dict which is True if
    the timedelta contained a negative value but all the values in the split
    dict are positive.
    
    It also includes a '1st' and '2nd' keys that contain the first and second
    keys that contain values greater than 0 in order of increasing accuracy
    (i.e. from year to second).
    
    Example:
    
        >>> total = datetime.timedelta(days=2002, seconds=20000)
        >>> parts = split_delta(total)
        >>> parts
        {'seconds': 20, 'months': 5, 'days': 2, '2nd': 'months', 'hours': 5, '1st': 'years', 'is_past': False, 'weeks': 3, 'years': 5, 'minutes': 33}
    
    :param delta: Time period to evaluate
    :type delta: datetime.timedelta
    :param include_weeks: Include weeks in the division (and reduce the days accordingly)?
    :type include_weeks: bool
    :rtype: dict
    """
    parts = {'1st': None,
     '2nd': None,
     'is_past': False}
    if delta.total_seconds() < 0:
        parts['is_past'] = True
        delta = datetime.timedelta(seconds=-delta.total_seconds())
    days = abs(delta.days)
    parts['years'], days = _div_and_rest(days, MEAN_YEAR)
    if parts['years']:
        parts['1st'] = 'years'
    parts['months'], days = _div_and_rest(days, MEAN_MONTH)
    if parts['months']:
        if not parts['1st']:
            parts['1st'] = 'months'
        else:
            parts['2nd'] = 'months'
    if include_weeks:
        parts['weeks'], days = _div_and_rest(days, 7)
        if not parts['1st'] and parts['weeks']:
            parts['1st'] = 'weeks'
        elif not parts['2nd'] and parts['weeks']:
            parts['2nd'] = 'weeks'
    parts['days'] = int(days)
    if not parts['1st'] and parts['days']:
        parts['1st'] = 'days'
    elif not parts['2nd'] and parts['days']:
        parts['2nd'] = 'days'
    seconds = abs(delta.seconds)
    parts['hours'], seconds = _div_and_rest(seconds, 3600)
    if not parts['1st'] and parts['hours']:
        parts['1st'] = 'hours'
    elif not parts['2nd'] and parts['hours']:
        parts['2nd'] = 'hours'
    parts['minutes'], seconds = _div_and_rest(seconds, 60)
    if not parts['1st'] and parts['minutes']:
        parts['1st'] = 'minutes'
    elif not parts['2nd'] and parts['minutes']:
        parts['2nd'] = 'minutes'
    parts['seconds'] = int(seconds)
    if not parts['1st'] and parts['seconds']:
        parts['1st'] = 'seconds'
    elif not parts['2nd'] and parts['seconds']:
        parts['2nd'] = 'seconds'
    return parts


def deltastr(delta, default = ''):
    """Turns timedelta or date or time or datetime into a string like "3 weeks"
    or "a few seconds" or "1 year and 7 months".
    
    Example:
    
        >>> ago(datetime.timedelta(days=2002, seconds=20000))
        '5 years'
        >>> ago(datetime.timedelta(days=366, seconds=20000))
        '1 year and 5 hours'
        >>> ago(datetime.timedelta(seconds=360))
        '6 minutes'
        >>> ago(datetime.timedelta(seconds=90))
        '1 minute'
        >>> ago(datetime.timedelta(seconds=59))
        'a few seconds'
    
    :param delta_or_date:
    :type delta_or_date:
    :param default:
    :type default:
    :return:
    :rtype: str
    """
    if not isinstance(delta, datetime.timedelta):
        return default
    parts = split_delta(delta)
    if parts['1st']:
        first_key = parts['1st']
        if first_key == 'seconds':
            return 'a few seconds'
        first_value = parts[first_key]
        if first_value > 1:
            return '%s %s' % (first_value, first_key)
        first_key = first_key[:-1]
        if parts['2nd'] and parts['2nd'] != 'seconds':
            second_key = parts['2nd']
            second_value = parts[second_key]
            if second_value < 2:
                second_key = second_key[:-1]
            return '%s %s and %s %s' % (first_value,
             first_key,
             second_value,
             second_key)
        else:
            return '%s %s' % (first_value, first_key)
    else:
        return default


def ago(delta_or_date, default = ''):
    """Same as deltastr except if given a date/time/datetime value it
    automatically calculates the timedelta from (or to) now to (or from) the
    given value and uses that.
    
    :param delta_or_date:
    :type delta_or_date: datetime.timedelta or datetime.datetime or datetime.date or datetime.time
    :param default:
    :type default:
    :return:
    :rtype: str
    """
    if isinstance(delta_or_date, datetime.datetime):
        delta_or_date = datetime.datetime.now() - delta_or_date
    elif isinstance(delta_or_date, datetime.date):
        delta_or_date = datetime.datetime.now().date() - delta_or_date
    elif isinstance(delta_or_date, datetime.time):
        delta_or_date = datetime.datetime.combine(datetime.datetime.now().date(), delta_or_date)
    return deltastr(delta_or_date)
