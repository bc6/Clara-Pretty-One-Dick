#Embedded file name: scriber\utils.py
"""
Scriber internal Utility functions
"""
import logging
import jinja2
from jinja2 import utils as jinja_utils
from scriber import const
log = logging.getLogger(const.LOGGER_NAME)

def filter_name(name):

    def inner(filter_function):
        setattr(filter_function, '__filter_name__', name)
        return filter_function

    return inner


def get_filter_name(filter_function):
    name = getattr(filter_function, '__filter_name__', filter_function.__name__)
    return name


class ScriberUndefined(jinja2.Undefined):

    @jinja_utils.internalcode
    def _fail_with_undefined_error(self, *args, **kwargs):
        if self._undefined_obj is jinja_utils.missing:
            hint = '{{%r}}' % self._undefined_name
            log.error('%s: Undefined variable found, in template' % hint)
        elif not isinstance(self._undefined_name, basestring):
            hint = '{{%s[%r]}}' % (jinja_utils.object_type_repr(self._undefined_obj), self._undefined_name)
            log.error('%s: Element not found, in template' % hint)
        else:
            hint = '{{%s.%s}}' % (jinja_utils.object_type_repr(self._undefined_obj), self._undefined_name)
            log.error('%s: Attribute not found, in template' % hint)
        return hint

    def _nonzero_fail_with_undefined_error(self, *args, **kwargs):
        if self._undefined_obj is jinja_utils.missing:
            hint = '{{%r}}' % self._undefined_name
            log.error('%s: Undefined variable found, in template' % hint)
        elif not isinstance(self._undefined_name, basestring):
            hint = '{{%s[%r]}}' % (jinja_utils.object_type_repr(self._undefined_obj), self._undefined_name)
            log.error('%s: Element not found, in template' % hint)
        else:
            hint = '{{%s.%s}}' % (jinja_utils.object_type_repr(self._undefined_obj), self._undefined_name)
            log.error('%s: Attribute not found, in template' % hint)
        return False

    __iter__ = _fail_with_undefined_error
    __unicode__ = _fail_with_undefined_error
    __str__ = _fail_with_undefined_error
    __len__ = _fail_with_undefined_error
    __nonzero__ = _nonzero_fail_with_undefined_error
    __eq__ = _fail_with_undefined_error
    __ne__ = _fail_with_undefined_error
    __bool__ = _fail_with_undefined_error
