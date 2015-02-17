#Embedded file name: scriber\__init__.py
"""
Scriber contains utilities, tools, functions, widgets, gadgets and gizmos
related to the building and manipulation of HTML including related stuff like
CSS, JavaScripts, JSON, XHTML, HTML5, XML and so on.

!!!WORK IN PROGRESS!!!

Most of these will involve rendering jinja2 templates and cooking data for
template context.

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
import types
import logging
import os
import sys
import traceback
try:
    import json
except ImportError:
    import simplejson as json

import jinja2
from scriber import filters
from scriber import utils
from scriber.const import *
environment = None
log = logging.getLogger(LOGGER_NAME)
LOCAL_MACHINES = ('THORDURM-WS',)
local_mode = False
if os.environ.get('COMPUTERNAME', object()) in LOCAL_MACHINES:
    log.addHandler(logging.StreamHandler(sys.stdout))
    log.level = logging.DEBUG
    log.debug('Package scriber initialized for LOCAL testing')
    local_mode = True

def init(template_dir_list = '', force_reload = False):
    global environment
    if not environment or force_reload:
        if not isinstance(template_dir_list, list):
            template_dir_list = list(template_dir_list)
        if local_mode:
            undefined_class = utils.ScriberUndefined
        else:
            undefined_class = jinja2.DebugUndefined
        environment = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir_list), undefined=undefined_class)
        _load_filters()


def _load_filters():
    for name, item in filters.__dict__.iteritems():
        if isinstance(item, types.FunctionType):
            filter_name = utils.get_filter_name(item)
            environment.filters[filter_name] = item


def scribe_json(**kwargs):
    return json.dumps(kwargs)


def scribe(template, *args, **kwargs):
    template = environment.get_template(template)
    return template.render(*args, **kwargs)


def error(message, details = ''):
    if details:
        if isinstance(details, BaseException):
            details = traceback.format_exc()
        elif not isinstance(details, basestring):
            details = '%r' % details
    return scribe('/pages/error.html', message=message, details=details)
