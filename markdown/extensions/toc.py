#Embedded file name: markdown/extensions\toc.py
"""
Table of Contents Extension for Python-Markdown
* * *

(c) 2008 [Jack Miller](http://codezen.org)

Dependencies:
* [Markdown 2.1+](http://packages.python.org/Markdown/)

"""
import markdown
from markdown.util import etree
from markdown.extensions.headerid import slugify, unique, itertext
import re

class TocTreeprocessor(markdown.treeprocessors.Treeprocessor):

    def iterparent(self, root):
        for parent in root.getiterator():
            for child in parent:
                yield (parent, child)

    def run(self, doc):
        marker_found = False
        div = etree.Element('div')
        div.attrib['class'] = 'toc'
        last_li = None
        if self.config['title']:
            header = etree.SubElement(div, 'span')
            header.attrib['class'] = 'toctitle'
            header.text = self.config['title']
        level = 0
        list_stack = [div]
        header_rgx = re.compile('[Hh][123456]')
        used_ids = []
        for c in doc.getiterator():
            if 'id' in c.attrib:
                used_ids.append(c.attrib['id'])

        for p, c in self.iterparent(doc):
            text = ''.join(itertext(c)).strip()
            if not text:
                continue
            if c.text and c.text.strip() == self.config['marker'] and not header_rgx.match(c.tag) and c.tag not in ('pre', 'code'):
                for i in range(len(p)):
                    if p[i] == c:
                        p[i] = div
                        break

                marker_found = True
            if header_rgx.match(c.tag):
                try:
                    tag_level = int(c.tag[-1])
                    while tag_level < level:
                        list_stack.pop()
                        level -= 1

                    if tag_level > level:
                        newlist = etree.Element('ul')
                        if last_li:
                            last_li.append(newlist)
                        else:
                            list_stack[-1].append(newlist)
                        list_stack.append(newlist)
                        if level == 0:
                            level = tag_level
                        else:
                            level += 1
                    if 'id' not in c.attrib:
                        id = unique(self.config['slugify'](text, '-'), used_ids)
                        c.attrib['id'] = id
                    else:
                        id = c.attrib['id']
                    last_li = etree.Element('li')
                    link = etree.SubElement(last_li, 'a')
                    link.text = text
                    link.attrib['href'] = '#' + id
                    if self.config['anchorlink'] in [1,
                     '1',
                     True,
                     'True',
                     'true']:
                        anchor = etree.Element('a')
                        anchor.text = c.text
                        anchor.attrib['href'] = '#' + id
                        anchor.attrib['class'] = 'toclink'
                        c.text = ''
                        for elem in c._children:
                            anchor.append(elem)
                            c.remove(elem)

                        c.append(anchor)
                    list_stack[-1].append(last_li)
                except IndexError:
                    pass

        if not marker_found:
            prettify = self.markdown.treeprocessors.get('prettify')
            if prettify:
                prettify.run(div)
            toc = self.markdown.serializer(div)
            for pp in self.markdown.postprocessors.values():
                toc = pp.run(toc)

            self.markdown.toc = toc


class TocExtension(markdown.Extension):

    def __init__(self, configs):
        self.config = {'marker': ['[TOC]', 'Text to find and replace with Table of Contents -Defaults to "[TOC]"'],
         'slugify': [slugify, "Function to generate anchors based on header text-Defaults to the headerid ext's slugify function."],
         'title': [None, 'Title to insert into TOC <div> - Defaults to None'],
         'anchorlink': [0, '1 if header should be a self linkDefaults to 0']}
        for key, value in configs:
            self.setConfig(key, value)

    def extendMarkdown(self, md, md_globals):
        tocext = TocTreeprocessor(md)
        tocext.config = self.getConfigs()
        md.treeprocessors.add('toc', tocext, '<prettify')


def makeExtension(configs = {}):
    return TocExtension(configs=configs)
