#Embedded file name: carbon/common/lib/markdown\util.py
import re
from logging import CRITICAL
import etree_loader
BLOCK_LEVEL_ELEMENTS = re.compile('^(p|div|h[1-6]|blockquote|pre|table|dl|ol|ul|script|noscript|form|fieldset|iframe|math|hr|hr/|style|li|dt|dd|thead|tbody|tr|th|td|section|footer|header|group|figure|figcaption|aside|article|canvas|output|progress|video)$', re.IGNORECASE)
STX = u'\x02'
ETX = u'\x03'
INLINE_PLACEHOLDER_PREFIX = STX + 'klzzwxh:'
INLINE_PLACEHOLDER = INLINE_PLACEHOLDER_PREFIX + '%s' + ETX
INLINE_PLACEHOLDER_RE = re.compile(INLINE_PLACEHOLDER % '([0-9]{4})')
AMP_SUBSTITUTE = STX + 'amp' + ETX
RTL_BIDI_RANGES = ((u'\u0590', u'\u07ff'), (u'\u2d30', u'\u2d7f'))
etree = etree_loader.importETree()

def isBlockLevel(tag):
    """Check if the tag is a block level HTML tag."""
    if isinstance(tag, basestring):
        return BLOCK_LEVEL_ELEMENTS.match(tag)
    return False


class AtomicString(unicode):
    """A string which should not be further processed."""
    pass


class Processor:

    def __init__(self, markdown_instance = None):
        if markdown_instance:
            self.markdown = markdown_instance


class HtmlStash:
    """
    This class is used for stashing HTML objects that we extract
    in the beginning and replace with place-holders.
    """

    def __init__(self):
        """ Create a HtmlStash. """
        self.html_counter = 0
        self.rawHtmlBlocks = []

    def store(self, html, safe = False):
        """
        Saves an HTML segment for later reinsertion.  Returns a
        placeholder string that needs to be inserted into the
        document.
        
        Keyword arguments:
        
        * html: an html segment
        * safe: label an html segment as safe for safemode
        
        Returns : a placeholder string
        
        """
        self.rawHtmlBlocks.append((html, safe))
        placeholder = self.get_placeholder(self.html_counter)
        self.html_counter += 1
        return placeholder

    def reset(self):
        self.html_counter = 0
        self.rawHtmlBlocks = []

    def get_placeholder(self, key):
        return '%swzxhzdk:%d%s' % (STX, key, ETX)
