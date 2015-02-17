#Embedded file name: scriber\htmlutils.py
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
import re
import HTMLParser
from scriber import const

class TolerantParser(HTMLParser.HTMLParser):
    """Base class for deriving HTMLParsers that should be error tolerant.
    The default strategy is ON_ERROR_REPLACE which calls the
    on_error_replace_with() function which returns &lt; by default but can be
    overwritten to return a string (even an empty one) with whatever should
    replace the opening < of the HTML tag (or closing tag) that breaks the
    parsing.
    
    Errors encountered are stored up in the parse_errors list.
    """
    ON_ERROR_THROW = 0
    ON_ERROR_REPLACE = 1
    ON_ERROR_SKIP = 2

    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.on_error = self.ON_ERROR_REPLACE
        self.parse_errors = []

    def on_error_replace_with(self):
        """Overwrite at will to change what should replace the offending tag's
        start
        
        :return: Whatever should replace the starting < of a tag (or tag end)
                 that's causing a parse error
        :rtype: basestring
        """
        return '&lt;'

    def parse_starttag(self, i):
        """Overwritten private function from HTMLParser to catch
        HTMLParseErrors and ignore them (if applicable)"""
        try:
            return HTMLParser.HTMLParser.parse_starttag(self, i)
        except HTMLParser.HTMLParseError as e:
            self.parse_errors.append(e)
            if self.on_error == self.ON_ERROR_REPLACE:
                self.handle_data(self.on_error_replace_with())
                return i + 1
            if self.on_error == self.ON_ERROR_SKIP:
                return i + 1
            raise

    def parse_endtag(self, i):
        """Overwritten private function from HTMLParser to catch
        HTMLParseErrors and ignore them (if applicable)"""
        try:
            return HTMLParser.HTMLParser.parse_endtag(self, i)
        except HTMLParser.HTMLParseError as e:
            self.parse_errors.append(e)
            if self.on_error == self.ON_ERROR_REPLACE:
                self.handle_data(self.on_error_replace_with())
                return i + 1
            if self.on_error == self.ON_ERROR_SKIP:
                return i + 1
            raise

    def unknown_decl(self, data):
        """Overwritten private function from HTMLParser to catch unknown
        <!DECLERATIONS> and ignore them."""
        pass

    def goahead(self, end):
        """Overwritten to fix funky handling of Urls with & in them (the
        unaltered parser tries to turn them into character references."""
        rawdata = self.rawdata
        i = 0
        n = len(rawdata)
        while i < n:
            match = self.interesting.search(rawdata, i)
            if match:
                j = match.start()
            else:
                j = n
            if i < j:
                self.handle_data(rawdata[i:j])
            i = self.updatepos(i, j)
            if i == n:
                break
            startswith = rawdata.startswith
            if startswith('<', i):
                if HTMLParser.starttagopen.match(rawdata, i):
                    k = self.parse_starttag(i)
                elif startswith('</', i):
                    k = self.parse_endtag(i)
                elif startswith('<!--', i):
                    k = self.parse_comment(i)
                elif startswith('<?', i):
                    k = self.parse_pi(i)
                elif startswith('<!', i):
                    k = self.parse_declaration(i)
                elif i + 1 < n:
                    self.handle_data('<')
                    k = i + 1
                else:
                    break
                if k < 0:
                    if end:
                        self.error('EOF in middle of construct')
                    break
                i = self.updatepos(i, k)
            elif startswith('&#', i):
                match = HTMLParser.charref.match(rawdata, i)
                if match:
                    name = match.group()[2:-1]
                    k = match.end()
                    if not startswith(';', k - 1):
                        self.handle_data('&#' + name)
                        k = k - 1
                    else:
                        self.handle_charref(name)
                    i = self.updatepos(i, k)
                    continue
                else:
                    if ';' in rawdata[i:]:
                        self.handle_data(rawdata[0:2])
                        i = self.updatepos(i, 2)
                    break
            elif startswith('&', i):
                match = HTMLParser.entityref.match(rawdata, i)
                if match:
                    name = match.group(1)
                    k = match.end()
                    if not startswith(';', k - 1):
                        self.handle_data('&' + name)
                        k = k - 1
                    else:
                        self.handle_entityref(name)
                    i = self.updatepos(i, k)
                    continue
                match = HTMLParser.incomplete.match(rawdata, i)
                if match:
                    self.handle_data(rawdata[i:])
                    if end and match.group() == rawdata[i:]:
                        self.error('EOF in middle of entity or char ref')
                    break
                elif i + 1 < n:
                    self.handle_data('&')
                    i = self.updatepos(i, i + 1)
                else:
                    self.handle_data('&')
                    break

        if end and i < n:
            self.handle_data(rawdata[i:n])
            i = self.updatepos(i, n)
        self.rawdata = rawdata[i:]


class TagStripper(TolerantParser):
    """Extension to the python HTMLParser that removes a subset of tags only,
    leaving other content and tags unchanged.
    
    Usage: Create a new stripper, feed it HTML through feed() and collect text
    using get_stripped() when done.
    
    :param tag_list: List of tags to strip
    :type tag_list: list or tuple
    :param preserve_content_list: A (sub)list of tags to strip but who's
                                  content to save (like: "foo <b>bar</b> foo"
                                  => "foo bar foo" as oppose to "foo  foo").
                                  Tags in this list must be present in the
                                  tag_list to strip.
    :type preserve_content_list: list or tuple
    """

    def __init__(self, tag_list = tuple(), preserve_content_list = tuple()):
        TolerantParser.__init__(self)
        self._stripped = []
        self.tag_list = tag_list
        self.preserve_content_list = preserve_content_list
        self.ignore_content_until = None

    def handle_data(self, data):
        if not self.ignore_content_until:
            self._stripped.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in self.tag_list:
            if tag not in self.preserve_content_list:
                self.ignore_content_until = tag
        else:
            attributes = ''
            if attrs:
                attributes = ' %s' % attr_str(attrs)
            self._stripped.append('<%s%s>' % (tag, attributes))

    def handle_endtag(self, tag):
        if self.ignore_content_until == tag:
            self.ignore_content_until = None
        if tag not in self.tag_list:
            self._stripped.append('</%s>' % tag)

    def handle_entityref(self, name):
        if not self.ignore_content_until:
            self._stripped.append('&%s;' % name)

    def handle_charref(self, name):
        if not self.ignore_content_until:
            self._stripped.append('&#%s;' % name)

    def get_stripped(self):
        """Returns the text data collected from the HTML the HTMLStripper has
        been fed"""
        return ''.join(self._stripped)

    def flush_stripped(self):
        """Returns the text data collected from the HTML the HTMLStripper has
        been fed and clears the buffer"""
        text = self.get_stripped()
        self._stripped = []
        return text


class HTMLStripper(TolerantParser):
    """Extension to the python HTMLParser that removes tags and collects text
    data while parsing.
    
    Usage: Create a new stripper, feed it HTML through feed() and collect text
    using get_text() when done
    
    Header and paragraph tag get two newline characters appended to their
    content's end and br tags turn into a single newline character.
    
    The content of any tags that never contain any relevant text data is also
    removed. These tags are:
    
        - head
        - script
        - style
        - embed
        - frameset
        - object
        - iframe
        - source
        - track
        - video
        - audio
        - canvas
        - meta
    
    If preserve_links is True, the href attribute of a tags gets appended to
    the end of that tags content in brackets.
    
    Setting preserve_images to True does the same for the src attribute of img tags.
    
    :param preserve_links: Appends the href attribute of a tags to the
                               end of their content in brackets if set to True
    :type preserve_links: bool
    :param preserve_images: Appends the src attribute of img tags to the
                            end of their content in brackets if set to True
    :type preserve_images: bool
    :param decode_chars: Should HTML character references be decoded to actual
                         characters (like "&lt;" to "<")?
    :type decode_chars: bool
    :param error_tolerance: Should parse errors and exceptions be swallowed up
                            (instead of thrown) and malformed tags be inserted
                            unparsed?
    :type error_tolerance: bool
    """
    HTML_WHITESPACE = '[ \\t\\r\\n]+'
    HTML_BREAKS = '( \\n|\\n )'
    HTML_NON_CONTENT_TAGS = ['head',
     'script',
     'style',
     'embed',
     'frameset',
     'object',
     'iframe',
     'source',
     'track',
     'video',
     'audio',
     'canvas',
     'meta']

    def __init__(self, preserve_links = True, preserve_images = False, decode_chars = True, error_tolerance = True):
        TolerantParser.__init__(self)
        self._text = []
        self.preserve_links = preserve_links
        self.preserve_images = preserve_images
        self.decode_chars = decode_chars
        self.error_tolerance = error_tolerance
        self.link = ''
        self.ignore_content_until = None

    def handle_data(self, data):
        if not self.ignore_content_until:
            self._text.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in self.HTML_NON_CONTENT_TAGS:
            self.ignore_content_until = tag
        if tag == 'a':
            if self.preserve_links and attrs:
                attrs = dict(attrs)
                self.link = attrs.get('href', '')
        if tag == 'img':
            if self.preserve_images and attrs:
                attrs = dict(attrs)
                self._text.append('[%s]' % attrs.get('src', ''))
        elif tag == 'br':
            self._add_linefeed()

    def handle_endtag(self, tag):
        if self.ignore_content_until == tag:
            self.ignore_content_until = None
        if tag in ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self._add_linefeed(2)
        elif tag == 'a' and self.preserve_links and self.link:
            self._text.append(' [%s]' % self.link)
            self.link = ''

    def handle_entityref(self, name):
        if not self.ignore_content_until:
            code = '&%s;' % name
            if self.decode_chars:
                code = self.unescape(code)
            self._text.append(code)

    def handle_charref(self, name):
        if not self.ignore_content_until:
            code = '&#%s;' % name
            if self.decode_chars:
                code = self.unescape(code)
            self._text.append(code)

    def on_error_replace_with(self):
        """Since this parser should return pure text in most cases, we'll
        replace the opening < with a [ if character references should be
        decoded, which is a common replacement for < when disabling HTML
        rendering or with &lt; if references should not be decoded.
        
        :rtype: basestring
        """
        if self.decode_chars:
            return '['
        else:
            return '&lt;'

    def _add_linefeed(self, count = 1):
        self._text.append('{{LF}}' * count)

    def get_text(self):
        """Returns the text data collected from the HTML the HTMLStripper has
        been fed"""
        text = ''.join(self._text)
        text = re.sub(self.HTML_WHITESPACE, ' ', text)
        text = text.replace('{{LF}}', '\n')
        text = re.sub(self.HTML_BREAKS, '\n', text)
        return text.strip()

    def flush_text(self):
        """Returns the text data collected from the HTML the HTMLStripper has
        been fed and clears the buffer"""
        text = self.get_text()
        self._text = []
        return text


def strip_html(html_string, preserve_links = True, preserve_images = False, decode_chars = True):
    """See the class HTMLStripper documentation
    
    :type html_string: basestring
    :type preserve_links: bool
    :type preserve_images: bool
    :type decode_chars: bool
    :rtype: basestring
    """
    stripper = HTMLStripper(preserve_links, preserve_images, decode_chars)
    stripper.feed(html_string)
    return stripper.get_text()


def newline_to_html(string):
    """Turns one newline character into a <br /> tag and two newline characters
    into an HTML paragraph using the <p> tag and also encases the string in
    with a <p> tag.
    
    :type string: basestring
    :rtype: basestring
    """
    return '<p>%s</p>' % reduce(lambda h, n: h.replace(*n), (('\r', ''), ('\n\n', '</p><p>'), ('\n', '<br />')), string)


def sanitize(html_string):
    """Replaces any &, < and > characters with their respective HTML special
    character tags (&amp;, &lt; and &gt;)
    
    :type html_string: basestring
    :rtype: basestring
    """
    return reduce(lambda string, params: string.replace(*params), (('&', '&amp;'), ('<', '&lt;'), ('>', '&gt;')), html_string)


def unsanitize(string):
    """Replaces any of the &, < and > HTML special character tags (&amp;, &lt;
    and &gt;) characters with their respective real characters.
    
    :type string: basestring
    :rtype: basestring
    """
    return reduce(lambda string, params: string.replace(*params), (('&gt;', '>'), ('&lt;', '<'), ('&amp;', '&')), string)


def esc_email_tags(html, replacer = const.EMAIL_TAG_REPLACE_HTML):
    """Replaces and occurrence of "email tags" like "<foo@bar.com>",
    "</foo@bar.com>" and "<foo@bar.com />" with HTML escaped versions like
    "&lt;foo@bar.com&gt;".
    
    This format of email addresses is commonly found in raw SMTP headers and
    some email clients mistakenly parse this as an HTML tag with strange
    results like adding a "closing" tag and such nonsense.
    
    :type html: basestring
    :param replacer: The regular expression string that will replace the "tag"
                     where group 1 contains a "/" if this was a closing tag,
                     group 2 contains the email address and group 3 contains a
                     "/" with or without a leading zero in cases of self
                     closing XHTML compliant tags. Example and default:
                     '&lt;\x01\x02\x03&gt;'
    :type replacer: basestring
    :rtype: basestring
    """
    return const.EMAIL_TAG_GRABBER.sub(replacer, html)


def strip_bad_tags(html_string):
    """Strips any tags away from a piece of HTML code that might contain
    executable code, style breakers, external data (iframes/embeds) or
    irrelevant stuff. These tags are:
    
        - head
        - script
        - style
        - embed
        - frameset
        - object
        - iframe
        - source
        - track
        - video
        - audio
        - canvas
        - meta
    
    :type html_string: basestring
    :rtype: basestring
    """
    stripper = TagStripper(HTMLStripper.HTML_NON_CONTENT_TAGS)
    stripper.feed(html_string)
    return stripper.get_stripped()


def attr_str(attribute_list, xhtml_strict = False):
    """Constructs a string of html tag attributes from either a list of name &
    value pair tuples or a dict.
    
    :type attribute_list: list or tuple or dict
    :param xhtml_strict: Designates if value-less attributes should adhere to
                         xhtml standards or stand alone (like
                         'selected="selected"' vs. 'selected').
    :type xhtml_strict: bool
    :rtype: basestr
    """
    buff = []
    if isinstance(attribute_list, dict):
        attribute_list = attribute_list.items()
    for attr in attribute_list:
        if len(attr) > 1:
            buff.append('%s="%s"' % (attr[0], attr[1]))
        elif xhtml_strict:
            buff.append('%s="%s"' % (attr[0], attr[0]))
        else:
            buff.append('%s' % attr[0])

    return ' '.join(buff)


def parse_user_notes(raw_notes):
    return re.sub(const.PETITION_LINK_NOTE_PATTERN, const.PETITION_LINK_NOTE_REPLACE, raw_notes).replace('\n', '<br>')


def strip_extra_amp(string):
    return re.sub(const.EXTRA_AMP_MATCHER, const.EXTRA_AMP_REPLACER, string)
