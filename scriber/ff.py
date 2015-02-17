#Embedded file name: scriber\ff.py
"""
Fantastic Formatting
"""

def o(format_str, *args):
    """Optinal Formating
    
    Example:
    
        >>> o('foo', 1, 2, 3)
        'foo'
        >>> o('foo %% bar', 1, 2, 3)
        'foo % bar'
        >>> o('foo %s bar', 1, 2, 3)
        'foo 1 bar'
        >>> o('foo %s, %s, %s bar', 1, 2, 3)
        'foo 1, 2, 3 bar'
        >>> o('foo %s, %s, %s, %s, %s bar', 1, 2, 3)
        'foo 1, 2, 3, ,  bar'
        >>> o('foo %s%%, %s%%, %s, %s, %s bar', 1, 2, 3)
        'foo 1%, 2%, 3, ,  bar'
        >>> o('foo %s%%, %s%%, %s, %s, %s bar')
        'foo %, %, , ,  bar'
    
    :param format_str:
    :type format_str:
    :param args:
    :type args:
    :return:
    :rtype:
    """
    format_count = format_str.count('%')
    if not format_count:
        return format_str
    percent_count = format_str.count('%%')
    format_count -= percent_count * 2
    if not format_count:
        return format_str.replace('%%', '%')
    missing_args = format_count - len(args)
    if missing_args > 0:
        return format_str % (args + tuple([''] * missing_args))
    elif missing_args < 0:
        return format_str % args[:missing_args]
    else:
        return format_str % args


def pl(value, one_format = '', many_format = None, zero_format = None):
    """Plural Formating
    
    Examples:
    
        >>> pl(0)
        's'
        >>> pl(1)
        ''
        >>> pl(2)
        's'
        >>> pl(0, 'thing')
        'things'
        >>> pl(1, 'thing')
        'thing'
        >>> pl(2, 'thing')
        'things'
        >>> pl(0, '%s thing')
        '0 things'
        >>> pl(1, '%s thing')
        '1 thing'
        >>> pl(2, '%s thing')
        '2 things'
        >>> pl(0, '%s platypus', '%s platypi')
        '0 platypi'
        >>> pl(1, '%s platypus', '%s platypi')
        '1 platypus'
        >>> pl(2, '%s platypus', '%s platypi')
        '2 platypi'
        >>> pl(0, 'One platipus', 'Many platypi', 'Not a single platypus')
        'Not a single platypus'
        >>> pl(1, 'One platipus', 'Many platypi', 'Not a single platypus')
        'One platipus'
        >>> pl(2, 'One platipus', 'Many platypi', 'Not a single platypus')
        'Many platypi'
    
    :param value:
    :type value:
    :param one_format:
    :type one_format:
    :param many_format:
    :type many_format:
    :param zero_format:
    :type zero_format:
    :return:
    :rtype:
    """
    if many_format is None:
        many_format = '%ss' % one_format
    if value == 0:
        if zero_format is not None:
            return o(zero_format, value)
        else:
            return o(many_format, value)
    else:
        if value == 1:
            return o(one_format, value)
        return o(many_format, value)
