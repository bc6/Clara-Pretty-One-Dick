#Embedded file name: carbon/common/lib/jinja2\__init__.py
"""
    jinja2
    ~~~~~~

    Jinja2 is a template engine written in pure Python.  It provides a
    Django inspired non-XML syntax but supports inline expressions and
    an optional sandboxed environment.

    Nutshell
    --------

    Here a small example of a Jinja2 template::

        {% extends 'base.html' %}
        {% block title %}Memberlist{% endblock %}
        {% block content %}
          <ul>
          {% for user in users %}
            <li><a href="{{ user.url }}">{{ user.username }}</a></li>
          {% endfor %}
          </ul>
        {% endblock %}


    :copyright: (c) 2010 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
__docformat__ = 'restructuredtext en'
__version__ = '2.7-dev'
from jinja2.environment import Environment, Template
from jinja2.loaders import BaseLoader, FileSystemLoader, PackageLoader, DictLoader, FunctionLoader, PrefixLoader, ChoiceLoader, ModuleLoader
from jinja2.bccache import BytecodeCache, FileSystemBytecodeCache, MemcachedBytecodeCache
from jinja2.runtime import Undefined, DebugUndefined, StrictUndefined
from jinja2.exceptions import TemplateError, UndefinedError, TemplateNotFound, TemplatesNotFound, TemplateSyntaxError, TemplateAssertionError
from jinja2.filters import environmentfilter, contextfilter, evalcontextfilter
from jinja2.utils import Markup, escape, clear_caches, environmentfunction, evalcontextfunction, contextfunction, is_undefined
__all__ = ['Environment',
 'Template',
 'BaseLoader',
 'FileSystemLoader',
 'PackageLoader',
 'DictLoader',
 'FunctionLoader',
 'PrefixLoader',
 'ChoiceLoader',
 'BytecodeCache',
 'FileSystemBytecodeCache',
 'MemcachedBytecodeCache',
 'Undefined',
 'DebugUndefined',
 'StrictUndefined',
 'TemplateError',
 'UndefinedError',
 'TemplateNotFound',
 'TemplatesNotFound',
 'TemplateSyntaxError',
 'TemplateAssertionError',
 'ModuleLoader',
 'environmentfilter',
 'contextfilter',
 'Markup',
 'escape',
 'environmentfunction',
 'contextfunction',
 'clear_caches',
 'is_undefined',
 'evalcontextfilter',
 'evalcontextfunction']
