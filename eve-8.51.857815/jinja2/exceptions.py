#Embedded file name: jinja2\exceptions.py
"""
    jinja2.exceptions
    ~~~~~~~~~~~~~~~~~

    Jinja exceptions.

    :copyright: (c) 2010 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""

class TemplateError(Exception):
    """Baseclass for all template errors."""

    def __init__(self, message = None):
        if message is not None:
            message = unicode(message).encode('utf-8')
        Exception.__init__(self, message)

    @property
    def message(self):
        if self.args:
            message = self.args[0]
            if message is not None:
                return message.decode('utf-8', 'replace')


class TemplateNotFound(IOError, LookupError, TemplateError):
    """Raised if a template does not exist."""
    message = None

    def __init__(self, name, message = None):
        IOError.__init__(self)
        if message is None:
            message = name
        self.message = message
        self.name = name
        self.templates = [name]

    def __str__(self):
        return self.message.encode('utf-8')

    def __unicode__(self):
        return self.message


class TemplatesNotFound(TemplateNotFound):
    """Like :class:`TemplateNotFound` but raised if multiple templates
    are selected.  This is a subclass of :class:`TemplateNotFound`
    exception, so just catching the base exception will catch both.
    
    .. versionadded:: 2.2
    """

    def __init__(self, names = (), message = None):
        if message is None:
            message = u'non of the templates given were found: ' + u', '.join(map(unicode, names))
        TemplateNotFound.__init__(self, names and names[-1] or None, message)
        self.templates = list(names)


class TemplateSyntaxError(TemplateError):
    """Raised to tell the user that there is a problem with the template."""

    def __init__(self, message, lineno, name = None, filename = None):
        TemplateError.__init__(self, message)
        self.lineno = lineno
        self.name = name
        self.filename = filename
        self.source = None
        self.translated = False

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        if self.translated:
            return self.message
        location = 'line %d' % self.lineno
        name = self.filename or self.name
        if name:
            location = 'File "%s", %s' % (name, location)
        lines = [self.message, '  ' + location]
        if self.source is not None:
            try:
                line = self.source.splitlines()[self.lineno - 1]
            except IndexError:
                line = None

            if line:
                lines.append('    ' + line.strip())
        return u'\n'.join(lines)


class TemplateAssertionError(TemplateSyntaxError):
    """Like a template syntax error, but covers cases where something in the
    template caused an error at compile time that wasn't necessarily caused
    by a syntax error.  However it's a direct subclass of
    :exc:`TemplateSyntaxError` and has the same attributes.
    """
    pass


class TemplateRuntimeError(TemplateError):
    """A generic runtime error in the template engine.  Under some situations
    Jinja may raise this exception.
    """
    pass


class UndefinedError(TemplateRuntimeError):
    """Raised if a template tries to operate on :class:`Undefined`."""
    pass


class SecurityError(TemplateRuntimeError):
    """Raised if a template tries to do something insecure if the
    sandbox is enabled.
    """
    pass


class FilterArgumentError(TemplateRuntimeError):
    """This error is raised if a filter was called with inappropriate
    arguments
    """
    pass
