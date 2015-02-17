#Embedded file name: markdown/extensions\attr_list.py
"""
Attribute List Extension for Python-Markdown
============================================

Adds attribute list syntax. Inspired by 
[maruku](http://maruku.rubyforge.org/proposal.html#attribute_lists)'s
feature of the same name.

Copyright 2011 [Waylan Limberg](http://achinghead.com/).

Contact: markdown@freewisdom.org

License: BSD (see ../LICENSE.md for details) 

Dependencies:
* [Python 2.4+](http://python.org)
* [Markdown 2.1+](http://packages.python.org/Markdown/)

"""
import markdown
import re
from markdown.util import isBlockLevel
try:
    Scanner = re.Scanner
except AttributeError:
    from sre import Scanner

def _handle_double_quote(s, t):
    k, v = t.split('=')
    return (k, v.strip('"'))


def _handle_single_quote(s, t):
    k, v = t.split('=')
    return (k, v.strip("'"))


def _handle_key_value(s, t):
    return t.split('=')


def _handle_word(s, t):
    if t.startswith('.'):
        return (u'.', t[1:])
    if t.startswith('#'):
        return (u'id', t[1:])
    return (t, t)


_scanner = Scanner([('[^ ]+=".*?"', _handle_double_quote),
 ("[^ ]+='.*?'", _handle_single_quote),
 ('[^ ]+=[^ ]*', _handle_key_value),
 ('[^ ]+', _handle_word),
 (' ', None)])

def get_attrs(str):
    """ Parse attribute list and return a list of attribute tuples. """
    return _scanner.scan(str)[0]


def isheader(elem):
    return elem.tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')


class AttrListTreeprocessor(markdown.treeprocessors.Treeprocessor):
    BASE_RE = '\\{\\:?([^\\}]*)\\}'
    HEADER_RE = re.compile('[ ]*%s[ ]*$' % BASE_RE)
    BLOCK_RE = re.compile('\\n[ ]*%s[ ]*$' % BASE_RE)
    INLINE_RE = re.compile('^%s' % BASE_RE)

    def run(self, doc):
        for elem in doc.getiterator():
            if isBlockLevel(elem.tag):
                RE = self.BLOCK_RE
                if isheader(elem):
                    RE = self.HEADER_RE
                if len(elem) and elem[-1].tail:
                    m = RE.search(elem[-1].tail)
                    if m:
                        self.assign_attrs(elem, m.group(1))
                        elem[-1].tail = elem[-1].tail[:m.start()]
                        if isheader(elem):
                            elem[-1].tail = elem[-1].tail.rstrip('#').rstrip()
                elif elem.text:
                    m = RE.search(elem.text)
                    if m:
                        self.assign_attrs(elem, m.group(1))
                        elem.text = elem.text[:m.start()]
                        if isheader(elem):
                            elem.text = elem.text.rstrip('#').rstrip()
            elif elem.tail:
                m = self.INLINE_RE.match(elem.tail)
                if m:
                    self.assign_attrs(elem, m.group(1))
                    elem.tail = elem.tail[m.end():]

    def assign_attrs(self, elem, attrs):
        """ Assign attrs to element. """
        for k, v in get_attrs(attrs):
            if k == '.':
                cls = elem.get('class')
                if cls:
                    elem.set('class', '%s %s' % (cls, v))
                else:
                    elem.set('class', v)
            else:
                elem.set(k, v)


class AttrListExtension(markdown.extensions.Extension):

    def extendMarkdown(self, md, md_globals):
        if 'headerid' in md.treeprocessors.keys():
            md.treeprocessors.add('attr_list', AttrListTreeprocessor(md), '>headerid')
        else:
            md.treeprocessors.add('attr_list', AttrListTreeprocessor(md), '>inline')


def makeExtension(configs = {}):
    return AttrListExtension(configs=configs)
