#Embedded file name: carbon/common/lib/markdown/extensions\meta.py
"""
Meta Data Extension for Python-Markdown
=======================================

This extension adds Meta Data handling to markdown.

Basic Usage:

    >>> import markdown
    >>> text = '''Title: A Test Doc.
    ... Author: Waylan Limberg
    ...         John Doe
    ... Blank_Data:
    ...
    ... The body. This is paragraph one.
    ... '''
    >>> md = markdown.Markdown(['meta'])
    >>> print md.convert(text)
    <p>The body. This is paragraph one.</p>
    >>> print md.Meta
    {u'blank_data': [u''], u'author': [u'Waylan Limberg', u'John Doe'], u'title': [u'A Test Doc.']}

Make sure text without Meta Data still works (markdown < 1.6b returns a <p>).

    >>> text = '    Some Code - not extra lines of meta data.'
    >>> md = markdown.Markdown(['meta'])
    >>> print md.convert(text)
    <pre><code>Some Code - not extra lines of meta data.
    </code></pre>
    >>> md.Meta
    {}

Copyright 2007-2008 [Waylan Limberg](http://achinghead.com).

Project website: <http://packages.python.org/Markdown/meta_data.html>
Contact: markdown@freewisdom.org

License: BSD (see ../LICENSE.md for details)

"""
import re
import markdown
META_RE = re.compile('^[ ]{0,3}(?P<key>[A-Za-z0-9_-]+):\\s*(?P<value>.*)')
META_MORE_RE = re.compile('^[ ]{4,}(?P<value>.*)')

class MetaExtension(markdown.Extension):
    """ Meta-Data extension for Python-Markdown. """

    def extendMarkdown(self, md, md_globals):
        """ Add MetaPreprocessor to Markdown instance. """
        md.preprocessors.add('meta', MetaPreprocessor(md), '_begin')


class MetaPreprocessor(markdown.preprocessors.Preprocessor):
    """ Get Meta-Data. """

    def run(self, lines):
        """ Parse Meta-Data and store in Markdown.Meta. """
        meta = {}
        key = None
        while 1:
            line = lines.pop(0)
            if line.strip() == '':
                break
            m1 = META_RE.match(line)
            if m1:
                key = m1.group('key').lower().strip()
                value = m1.group('value').strip()
                try:
                    meta[key].append(value)
                except KeyError:
                    meta[key] = [value]

            else:
                m2 = META_MORE_RE.match(line)
                if m2 and key:
                    meta[key].append(m2.group('value').strip())
                else:
                    lines.insert(0, line)
                    break

        self.markdown.Meta = meta
        return lines


def makeExtension(configs = {}):
    return MetaExtension(configs=configs)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
