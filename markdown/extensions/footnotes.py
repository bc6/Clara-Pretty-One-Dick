#Embedded file name: markdown/extensions\footnotes.py
"""
========================= FOOTNOTES =================================

This section adds footnote handling to markdown.  It can be used as
an example for extending python-markdown with relatively complex
functionality.  While in this case the extension is included inside
the module itself, it could just as easily be added from outside the
module.  Not that all markdown classes above are ignorant about
footnotes.  All footnote functionality is provided separately and
then added to the markdown instance at the run time.

Footnote functionality is attached by calling extendMarkdown()
method of FootnoteExtension.  The method also registers the
extension to allow it's state to be reset by a call to reset()
method.

Example:
    Footnotes[^1] have a label[^label] and a definition[^!DEF].

    [^1]: This is a footnote
    [^label]: A footnote on "label"
    [^!DEF]: The footnote for definition

"""
import re
import markdown
from markdown.util import etree
FN_BACKLINK_TEXT = 'zz1337820767766393qq'
NBSP_PLACEHOLDER = 'qq3936677670287331zz'
DEF_RE = re.compile('[ ]{0,3}\\[\\^([^\\]]*)\\]:\\s*(.*)')
TABBED_RE = re.compile('((\\t)|(    ))(.*)')

class FootnoteExtension(markdown.Extension):
    """ Footnote Extension. """

    def __init__(self, configs):
        """ Setup configs. """
        self.config = {'PLACE_MARKER': ['///Footnotes Go Here///', 'The text string that marks where the footnotes go'],
         'UNIQUE_IDS': [False, 'Avoid name collisions across multiple calls to reset().'],
         'BACKLINK_TEXT': ['&#8617;', "The text string that links from the footnote to the reader's place."]}
        for key, value in configs:
            self.config[key][0] = value

        self.unique_prefix = 0
        self.reset()

    def extendMarkdown(self, md, md_globals):
        """ Add pieces to Markdown. """
        md.registerExtension(self)
        self.parser = md.parser
        self.md = md
        md.preprocessors.add('footnote', FootnotePreprocessor(self), '<reference')
        FOOTNOTE_RE = '\\[\\^([^\\]]*)\\]'
        md.inlinePatterns.add('footnote', FootnotePattern(FOOTNOTE_RE, self), '<reference')
        md.treeprocessors.add('footnote', FootnoteTreeprocessor(self), '_begin')
        md.postprocessors.add('footnote', FootnotePostprocessor(self), '>amp_substitute')

    def reset(self):
        """ Clear the footnotes on reset, and prepare for a distinct document. """
        self.footnotes = markdown.odict.OrderedDict()
        self.unique_prefix += 1

    def findFootnotesPlaceholder(self, root):
        """ Return ElementTree Element that contains Footnote placeholder. """

        def finder(element):
            for child in element:
                if child.text:
                    if child.text.find(self.getConfig('PLACE_MARKER')) > -1:
                        return (child, element, True)
                if child.tail:
                    if child.tail.find(self.getConfig('PLACE_MARKER')) > -1:
                        return (child, element, False)
                finder(child)

        res = finder(root)
        return res

    def setFootnote(self, id, text):
        """ Store a footnote for later retrieval. """
        self.footnotes[id] = text

    def makeFootnoteId(self, id):
        """ Return footnote link id. """
        if self.getConfig('UNIQUE_IDS'):
            return 'fn:%d-%s' % (self.unique_prefix, id)
        else:
            return 'fn:%s' % id

    def makeFootnoteRefId(self, id):
        """ Return footnote back-link id. """
        if self.getConfig('UNIQUE_IDS'):
            return 'fnref:%d-%s' % (self.unique_prefix, id)
        else:
            return 'fnref:%s' % id

    def makeFootnotesDiv(self, root):
        """ Return div of footnotes as et Element. """
        if not self.footnotes.keys():
            return None
        div = etree.Element('div')
        div.set('class', 'footnote')
        hr = etree.SubElement(div, 'hr')
        ol = etree.SubElement(div, 'ol')
        for id in self.footnotes.keys():
            li = etree.SubElement(ol, 'li')
            li.set('id', self.makeFootnoteId(id))
            self.parser.parseChunk(li, self.footnotes[id])
            backlink = etree.Element('a')
            backlink.set('href', '#' + self.makeFootnoteRefId(id))
            if self.md.output_format not in ('html5', 'xhtml5'):
                backlink.set('rev', 'footnote')
            backlink.set('class', 'footnote-backref')
            backlink.set('title', 'Jump back to footnote %d in the text' % (self.footnotes.index(id) + 1))
            backlink.text = FN_BACKLINK_TEXT
            if li._children:
                node = li[-1]
                if node.tag == 'p':
                    node.text = node.text + NBSP_PLACEHOLDER
                    node.append(backlink)
                else:
                    p = etree.SubElement(li, 'p')
                    p.append(backlink)

        return div


class FootnotePreprocessor(markdown.preprocessors.Preprocessor):
    """ Find all footnote references and store for later use. """

    def __init__(self, footnotes):
        self.footnotes = footnotes

    def run(self, lines):
        """
        Loop through lines and find, set, and remove footnote definitions.
        
        Keywords:
        
        * lines: A list of lines of text
        
        Return: A list of lines of text with footnote definitions removed.
        
        """
        newlines = []
        i = 0
        while True:
            m = DEF_RE.match(lines[i])
            if m:
                fn, _i = self.detectTabbed(lines[i + 1:])
                fn.insert(0, m.group(2))
                i += _i - 1
                self.footnotes.setFootnote(m.group(1), '\n'.join(fn))
            else:
                newlines.append(lines[i])
            if len(lines) > i + 1:
                i += 1
            else:
                break

        return newlines

    def detectTabbed(self, lines):
        """ Find indented text and remove indent before further proccesing.
        
        Keyword arguments:
        
        * lines: an array of strings
        
        Returns: a list of post processed items and the index of last line.
        
        """
        items = []
        blank_line = False
        i = 0

        def detab(line):
            match = TABBED_RE.match(line)
            if match:
                return match.group(4)

        for line in lines:
            if line.strip():
                detabbed_line = detab(line)
                if detabbed_line:
                    items.append(detabbed_line)
                    i += 1
                    continue
                elif not blank_line and not DEF_RE.match(line):
                    items.append(line)
                    i += 1
                    continue
                else:
                    return (items, i + 1)
            else:
                blank_line = True
                i += 1
                for j in range(i, len(lines)):
                    if lines[j].strip():
                        next_line = lines[j]
                        break
                else:
                    break

                if detab(next_line):
                    items.append('')
                    continue
                else:
                    break
        else:
            i += 1

        return (items, i)


class FootnotePattern(markdown.inlinepatterns.Pattern):
    """ InlinePattern for footnote markers in a document's body text. """

    def __init__(self, pattern, footnotes):
        markdown.inlinepatterns.Pattern.__init__(self, pattern)
        self.footnotes = footnotes

    def handleMatch(self, m):
        id = m.group(2)
        if id in self.footnotes.footnotes.keys():
            sup = etree.Element('sup')
            a = etree.SubElement(sup, 'a')
            sup.set('id', self.footnotes.makeFootnoteRefId(id))
            a.set('href', '#' + self.footnotes.makeFootnoteId(id))
            if self.footnotes.md.output_format not in ('html5', 'xhtml5'):
                a.set('rel', 'footnote')
            a.set('class', 'footnote-ref')
            a.text = unicode(self.footnotes.footnotes.index(id) + 1)
            return sup
        else:
            return None


class FootnoteTreeprocessor(markdown.treeprocessors.Treeprocessor):
    """ Build and append footnote div to end of document. """

    def __init__(self, footnotes):
        self.footnotes = footnotes

    def run(self, root):
        footnotesDiv = self.footnotes.makeFootnotesDiv(root)
        if footnotesDiv:
            result = self.footnotes.findFootnotesPlaceholder(root)
            if result:
                child, parent, isText = result
                ind = parent._children.index(child)
                if isText:
                    parent.remove(child)
                    parent.insert(ind, footnotesDiv)
                else:
                    parent.insert(ind + 1, footnotesDiv)
                    child.tail = None
            else:
                root.append(footnotesDiv)


class FootnotePostprocessor(markdown.postprocessors.Postprocessor):
    """ Replace placeholders with html entities. """

    def __init__(self, footnotes):
        self.footnotes = footnotes

    def run(self, text):
        text = text.replace(FN_BACKLINK_TEXT, self.footnotes.getConfig('BACKLINK_TEXT'))
        return text.replace(NBSP_PLACEHOLDER, '&#160;')


def makeExtension(configs = []):
    """ Return an instance of the FootnoteExtension """
    return FootnoteExtension(configs=configs)
