#Embedded file name: scriber\filters.py
"""
Utilities for python strings and string like objects (like unicode) containing
HTML. This includes any type string creation, manipulation, validation,
checking or extension.

As a very generally rule of thumb, anything put in here should fulfill one of
these criteria:

    - return an HTML string, either after manipulation or creation
    - take in an HTML string as a parameter and have some sort of processing
      of it as it's main job
    - return the result of such processing
    - this includes any sort of HTML parsing and extracting data from HTML
    - act as a mutator function on an HTML string
    - be independent, generic and "black-boxy". If your function would not be
      useable to anyone else either because of dependency on other packages or
      because of specialization bordering on "adhocyness", it probably doesn't
      belong here
    - classes in this file should extend string objects
    - you as a programmer feel very strongly it should be here
"""
import datetime
import datetimeutils
import typeutils
from scriber import htmlutils
from scriber import utils
from scriber import widgets
from scriber import ff

def date(date_obj, str_format = '%Y-%m-%d'):
    return datetime_filter(date_obj, str_format)


def time(date_obj, str_format = '%H:%M:%S'):
    return datetime_filter(date_obj, str_format)


def dt_sec(temporal_object):
    return datetime_filter(temporal_object, '%Y-%m-%d %H:%M:%S')


def dt_micro(temporal_object):
    return datetime_filter(temporal_object, '%Y-%m-%d .%f')


def dt(temporal_object):
    return datetime_filter(temporal_object)


@utils.filter_name('datetime')
def datetime_filter(temporal_object, str_format = '%Y-%m-%d %H:%M'):
    """Formats a datetime, date or timestamp object as a string
    
    :param temporal_object:
    :type temporal_object: datetime or date or long or float or int
    :param str_format: Same as strftime (http://docs.python.org/2/library/datetime.html#strftime-strptime-behavior)
    :type str_format: str
    :rtype: str or unicode
    """
    temporal_object = datetimeutils.any_to_datetime(temporal_object)
    if isinstance(temporal_object, datetime.datetime):
        return temporal_object.strftime(str_format)
    else:
        return temporal_object


def hide(content):
    return '<span style="display:none;text-indent:-10000;overflow:hidden;font-size:1px;color:#ffffff;">%s</span>' % content


def nl2br(content):
    return htmlutils.newline_to_html(content)


def unsanitize_html(content):
    return reduce(lambda h, n: h.replace(*n), (('&gt;', '>'), ('&lt;', '<')), content)


def a(model, icon_class = ''):
    href = getattr(model._meta, 'href', None)
    if href:
        if icon_class == '':
            icon_class = getattr(model._meta, 'icon', '')
        if icon_class:
            icon_class = '<i class="icon icon-%s"></i> ' % icon_class
        return '<a href="%s">%s%s</a>' % (href % model.get_id(), icon_class, model)
    return model


def btn_model(model, icon_class = ''):
    href = getattr(model._meta, 'href', None)
    if href:
        if icon_class == '':
            icon_class = getattr(model._meta, 'icon', '')
        if icon_class:
            icon_class = '<i class="icon icon-white icon-%s"></i> ' % icon_class
        return '<a class="btn btn-mini btn-info" href="%s">%s%s <i class="icon icon-share icon-white"></i></a>' % (href % model.get_id(), icon_class, model)
    return model


def btn(model_or_text, *args, **kwargs):
    if not isinstance(model_or_text, basestring):
        return btn_model(model_or_text)
    return model_or_text


def label(text, label_type = widgets.BADGE_DEFAULT):
    return widgets.Label.get(text, label_type)


def label_green(text):
    return widgets.Label.green(text)


def label_yellow(text):
    return widgets.Label.yellow(text)


def label_red(text):
    return widgets.Label.red(text)


def label_black(text):
    return widgets.Label.black(text)


def label_blue(text):
    return widgets.Label.blue(text)


def badge(text, label_type = widgets.BADGE_DEFAULT):
    return widgets.Badge.get(text, label_type)


def badge_green(text):
    return widgets.Badge.green(text)


def badge_yellow(text):
    return widgets.Badge.yellow(text)


def badge_red(text):
    return widgets.Badge.red(text)


def badge_black(text):
    return widgets.Badge.black(text)


def badge_blue(text):
    return widgets.Badge.blue(text)


def pl(value, one_format = '', many_format = None, zero_format = None):
    return ff.pl(value, one_format, many_format, zero_format)


def enum(model, field_name):
    """
    :type model: alexandria.orm.models.Model
    :type field_name: str
    :return:
    :rtype:
    """
    try:
        return model._meta.field_map[field_name].enum_map[getattr(model, field_name)]
    except (KeyError, AttributeError):
        return getattr(model, field_name, model)


def ago(delta_or_date):
    return datetimeutils.ago(delta_or_date, str(delta_or_date))


def ago_plus(datetime_object, ago_text = 'ago'):
    datetime_object = datetimeutils.any_to_datetime(datetime_object)
    if isinstance(datetime_object, datetime.datetime):
        return '%s %s <span class="muted">(%s)</span>' % (datetimeutils.ago(datetime_object, str(datetime_object)), ago_text, datetime_object.strftime('%Y-%m-%d %H:%M'))
    else:
        return '%s %s <span class="muted">(%s)</span>' % (datetimeutils.ago(datetime_object, str(datetime_object)), ago_text, str(datetime_object))


def ago_ttip(datetime_object, ago_text = 'ago'):
    datetime_object = datetimeutils.any_to_datetime(datetime_object)
    if isinstance(datetime_object, datetime.datetime):
        return '<span class="ttip" title="%s">%s %s</span>' % (datetime_object.strftime('%Y-%m-%d %H:%M'), datetimeutils.ago(datetime_object, str(datetime_object)), ago_text)
    else:
        return '<span class="ttip" title="%s">%s %s</span>' % (str(datetime_object), datetimeutils.ago(datetime_object, str(datetime_object)), ago_text)


def deltastr(delta):
    return datetimeutils.deltastr(delta, str(delta))


def floatformat(value, precision = 2):
    value = typeutils.float_eval(value, None)
    if value is None:
        return ''
    return ('{:,.' + str(precision) + 'f}').format(value)


def iif(value, if_true, if_false = ''):
    if value:
        return if_true
    return if_false


def yn(value):
    return iif(value, 'Yes', 'No')


def sel(value):
    return iif(value, ' selected')


def chk(value):
    return iif(value, ' checked')


def qtable(data, dom_id = None, dom_classes = '+', dom_style = None, **kwargs):
    class_list = []
    if isinstance(dom_classes, (list, tuple)):
        if '+' in dom_classes:
            class_list.extend(widgets.QuickTable.DEFAULT_DOM_CLASSES)
            dom_classes.remove('+')
            class_list.extend(dom_classes)
    elif isinstance(dom_classes, str):
        if dom_classes.startswith('+'):
            class_list.extend(widgets.QuickTable.DEFAULT_DOM_CLASSES)
            if len(dom_classes) > 1:
                class_list.extend(dom_classes[1:].strip().split(' '))
    return widgets.QuickTable.get(data, dom_id, class_list, dom_style, **kwargs)


def currsym(value):
    if not value:
        return '&curren;'
    lvalue = value.lower()
    if lvalue == 'usd':
        return '&#36;'
    if lvalue == 'eur':
        return '&euro;'
    if lvalue == 'gbp':
        return '&pound;'
    if lvalue == 'jpy':
        return '&yen;'
    return value


def numformat(value):
    value = typeutils.int_eval(value, None)
    if not value:
        return ''
    return '{:,.0f}'.format(value)
