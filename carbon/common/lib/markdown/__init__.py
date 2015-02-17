#Embedded file name: carbon/common/lib/markdown\__init__.py
"""
Python Markdown
===============

Python Markdown converts Markdown to HTML and can be used as a library or
called from the command line.

## Basic usage as a module:

    import markdown
    html = markdown.markdown(your_text_string)

See <http://packages.python.org/Markdown/> for more
information and instructions on how to extend the functionality of
Python Markdown.  Read that before you try modifying this file.

## Authors and License

Started by [Manfred Stienstra](http://www.dwerg.net/).  Continued and
maintained  by [Yuri Takhteyev](http://www.freewisdom.org), [Waylan
Limberg](http://achinghead.com/) and [Artem Yunusov](http://blog.splyer.com).

Contact: markdown@freewisdom.org

Copyright 2007-2012 The Python Markdown Project (v. 1.7 and later)
Copyright 200? Django Software Foundation (OrderedDict implementation)
Copyright 2004, 2005, 2006 Yuri Takhteyev (v. 0.2-1.6b)
Copyright 2004 Manfred Stienstra (the original version)

License: BSD (see LICENSE for details).
"""
version = '2.2.1'
version_info = (2,
 2,
 1,
 'final')
import re
import codecs
import sys
import logging
import warnings
import markdown.util as util
from preprocessors import build_preprocessors
from blockprocessors import build_block_parser
from treeprocessors import build_treeprocessors
from inlinepatterns import build_inlinepatterns
from postprocessors import build_postprocessors
from extensions import Extension
from serializers import to_html_string, to_xhtml_string
__all__ = ['Markdown', 'markdown', 'markdownFromFile']
logger = logging.getLogger('MARKDOWN')

class Markdown():
    """Convert Markdown to HTML."""
    doc_tag = 'div'
    option_defaults = {'html_replacement_text': '[HTML_REMOVED]',
     'tab_length': 4,
     'enable_attributes': True,
     'smart_emphasis': True,
     'lazy_ol': True}
    output_formats = {'html': to_html_string,
     'html4': to_html_string,
     'html5': to_html_string,
     'xhtml': to_xhtml_string,
     'xhtml1': to_xhtml_string,
     'xhtml5': to_xhtml_string}
    ESCAPED_CHARS = ['\\',
     '`',
     '*',
     '_',
     '{',
     '}',
     '[',
     ']',
     '(',
     ')',
     '>',
     '#',
     '+',
     '-',
     '.',
     '!']

    def __init__(self, *args, **kwargs):
        """
        Creates a new Markdown instance.
        
        Keyword arguments:
        
        * extensions: A list of extensions.
           If they are of type string, the module mdx_name.py will be loaded.
           If they are a subclass of markdown.Extension, they will be used
           as-is.
        * extension_configs: Configuration settingis for extensions.
        * output_format: Format of output. Supported formats are:
            * "xhtml1": Outputs XHTML 1.x. Default.
            * "xhtml5": Outputs XHTML style tags of HTML 5
            * "xhtml": Outputs latest supported version of XHTML (currently XHTML 1.1).
            * "html4": Outputs HTML 4
            * "html5": Outputs HTML style tags of HTML 5
            * "html": Outputs latest supported version of HTML (currently HTML 4).
            Note that it is suggested that the more specific formats ("xhtml1"
            and "html4") be used as "xhtml" or "html" may change in the future
            if it makes sense at that time.
        * safe_mode: Disallow raw html. One of "remove", "replace" or "escape".
        * html_replacement_text: Text used when safe_mode is set to "replace".
        * tab_length: Length of tabs in the source. Default: 4
        * enable_attributes: Enable the conversion of attributes. Default: True
        * smart_emphasis: Treat `_connected_words_` intelegently Default: True
        * lazy_ol: Ignore number of first item of ordered lists. Default: True
        
        """
        pos = ['extensions',
         'extension_configs',
         'safe_mode',
         'output_format']
        c = 0
        for arg in args:
            if not kwargs.has_key(pos[c]):
                kwargs[pos[c]] = arg
            c += 1
            if c == len(pos):
                break

        for option, default in self.option_defaults.items():
            setattr(self, option, kwargs.get(option, default))

        self.safeMode = kwargs.get('safe_mode', False)
        if self.safeMode and not kwargs.has_key('enable_attributes'):
            self.enable_attributes = False
        self.registeredExtensions = []
        self.docType = ''
        self.stripTopLevelTags = True
        self.build_parser()
        self.references = {}
        self.htmlStash = util.HtmlStash()
        self.registerExtensions(extensions=kwargs.get('extensions', []), configs=kwargs.get('extension_configs', {}))
        self.set_output_format(kwargs.get('output_format', 'xhtml1'))
        self.reset()

    def build_parser(self):
        """ Build the parser from the various parts. """
        self.preprocessors = build_preprocessors(self)
        self.parser = build_block_parser(self)
        self.inlinePatterns = build_inlinepatterns(self)
        self.treeprocessors = build_treeprocessors(self)
        self.postprocessors = build_postprocessors(self)
        return self

    def registerExtensions(self, extensions, configs):
        """
        Register extensions with this instance of Markdown.
        
        Keyword arguments:
        
        * extensions: A list of extensions, which can either
           be strings or objects.  See the docstring on Markdown.
        * configs: A dictionary mapping module names to config options.
        
        """
        for ext in extensions:
            if isinstance(ext, basestring):
                ext = self.build_extension(ext, configs.get(ext, []))
            if isinstance(ext, Extension):
                ext.extendMarkdown(self, globals())
            elif ext is not None:
                raise TypeError('Extension "%s.%s" must be of type: "markdown.Extension"' % (ext.__class__.__module__, ext.__class__.__name__))

        return self

    def build_extension(self, ext_name, configs = []):
        """Build extension by name, then return the module.
        
        The extension name may contain arguments as part of the string in the
        following format: "extname(key1=value1,key2=value2)"
        
        """
        configs = dict(configs)
        pos = ext_name.find('(')
        if pos > 0:
            ext_args = ext_name[pos + 1:-1]
            ext_name = ext_name[:pos]
            pairs = [ x.split('=') for x in ext_args.split(',') ]
            configs.update([ (x.strip(), y.strip()) for x, y in pairs ])
        module_name = ext_name
        if '.' not in ext_name:
            module_name = '.'.join(['markdown.extensions', ext_name])
        try:
            module = __import__(module_name, {}, {}, [module_name.rpartition('.')[0]])
        except ImportError:
            module_name_old_style = '_'.join(['mdx', ext_name])
            try:
                module = __import__(module_name_old_style)
            except ImportError as e:
                message = "Failed loading extension '%s' from '%s' or '%s'" % (ext_name, module_name, module_name_old_style)
                e.args = (message,) + e.args[1:]
                raise

        try:
            return module.makeExtension(configs.items())
        except AttributeError as e:
            message = e.args[0]
            message = "Failed to initiate extension '%s': %s" % (ext_name, message)
            e.args = (message,) + e.args[1:]
            raise

    def registerExtension(self, extension):
        """ This gets called by the extension """
        self.registeredExtensions.append(extension)
        return self

    def reset(self):
        """
        Resets all state variables so that we can start with a new text.
        """
        self.htmlStash.reset()
        self.references.clear()
        for extension in self.registeredExtensions:
            if hasattr(extension, 'reset'):
                extension.reset()

        return self

    def set_output_format(self, format):
        """ Set the output format for the class instance. """
        self.output_format = format.lower()
        try:
            self.serializer = self.output_formats[self.output_format]
        except KeyError as e:
            valid_formats = self.output_formats.keys()
            valid_formats.sort()
            message = 'Invalid Output Format: "%s". Use one of %s.' % (self.output_format, '"' + '", "'.join(valid_formats) + '"')
            e.args = (message,) + e.args[1:]
            raise

        return self

    def convert(self, source):
        """
        Convert markdown to serialized XHTML or HTML.
        
        Keyword arguments:
        
        * source: Source text as a Unicode string.
        
        Markdown processing takes place in five steps:
        
        1. A bunch of "preprocessors" munge the input text.
        2. BlockParser() parses the high-level structural elements of the
           pre-processed text into an ElementTree.
        3. A bunch of "treeprocessors" are run against the ElementTree. One
           such treeprocessor runs InlinePatterns against the ElementTree,
           detecting inline markup.
        4. Some post-processors are run against the text after the ElementTree
           has been serialized into text.
        5. The output is written to a string.
        
        """
        if not source.strip():
            return u''
        try:
            source = unicode(source)
        except UnicodeDecodeError as e:
            e.reason += '. -- Note: Markdown only accepts unicode input!'
            raise

        source = source.replace(util.STX, '').replace(util.ETX, '')
        source = source.replace('\r\n', '\n').replace('\r', '\n') + '\n\n'
        source = re.sub('\\n\\s+\\n', '\n\n', source)
        source = source.expandtabs(self.tab_length)
        self.lines = source.split('\n')
        for prep in self.preprocessors.values():
            self.lines = prep.run(self.lines)

        root = self.parser.parseDocument(self.lines).getroot()
        for treeprocessor in self.treeprocessors.values():
            newRoot = treeprocessor.run(root)
            if newRoot is not None:
                root = newRoot

        output = self.serializer(root)
        if self.stripTopLevelTags:
            try:
                start = output.index('<%s>' % self.doc_tag) + len(self.doc_tag) + 2
                end = output.rindex('</%s>' % self.doc_tag)
                output = output[start:end].strip()
            except ValueError:
                if output.strip().endswith('<%s />' % self.doc_tag):
                    output = ''
                else:
                    raise ValueError('Markdown failed to strip top-level tags. Document=%r' % output.strip())

        for pp in self.postprocessors.values():
            output = pp.run(output)

        return output.strip()

    def convertFile(self, input = None, output = None, encoding = None):
        """Converts a markdown file and returns the HTML as a unicode string.
        
        Decodes the file using the provided encoding (defaults to utf-8),
        passes the file content to markdown, and outputs the html to either
        the provided stream or the file with provided name, using the same
        encoding as the source file. The 'xmlcharrefreplace' error handler is
        used when encoding the output.
        
        **Note:** This is the only place that decoding and encoding of unicode
        takes place in Python-Markdown.  (All other code is unicode-in /
        unicode-out.)
        
        Keyword arguments:
        
        * input: File object or path. Reads from stdin if `None`.
        * output: File object or path. Writes to stdout if `None`.
        * encoding: Encoding of input and output files. Defaults to utf-8.
        
        """
        encoding = encoding or 'utf-8'
        if input:
            if isinstance(input, str):
                input_file = codecs.open(input, mode='r', encoding=encoding)
            else:
                input_file = codecs.getreader(encoding)(input)
            text = input_file.read()
            input_file.close()
        else:
            text = sys.stdin.read()
            if not isinstance(text, unicode):
                text = text.decode(encoding)
        text = text.lstrip('\\ufeff')
        html = self.convert(text)
        if output:
            if isinstance(output, str):
                output_file = codecs.open(output, 'w', encoding=encoding, errors='xmlcharrefreplace')
                output_file.write(html)
                output_file.close()
            else:
                writer = codecs.getwriter(encoding)
                output_file = writer(output, errors='xmlcharrefreplace')
                output_file.write(html)
        elif sys.stdout.encoding:
            sys.stdout.write(html)
        else:
            writer = codecs.getwriter(encoding)
            stdout = writer(sys.stdout, errors='xmlcharrefreplace')
            stdout.write(html)
        return self


def markdown(text, *args, **kwargs):
    """Convert a markdown string to HTML and return HTML as a unicode string.
    
    This is a shortcut function for `Markdown` class to cover the most
    basic use case.  It initializes an instance of Markdown, loads the
    necessary extensions and runs the parser on the given text.
    
    Keyword arguments:
    
    * text: Markdown formatted text as Unicode or ASCII string.
    * Any arguments accepted by the Markdown class.
    
    Returns: An HTML document as a string.
    
    """
    md = Markdown(*args, **kwargs)
    return md.convert(text)


def markdownFromFile(*args, **kwargs):
    """Read markdown code from a file and write it to a file or a stream.
    
    This is a shortcut function which initializes an instance of Markdown,
    and calls the convertFile method rather than convert.
    
    Keyword arguments:
    
    * input: a file name or readable object.
    * output: a file name or writable object.
    * encoding: Encoding of input and output.
    * Any arguments accepted by the Markdown class.
    
    """
    pos = ['input',
     'output',
     'extensions',
     'encoding']
    c = 0
    for arg in args:
        if not kwargs.has_key(pos[c]):
            kwargs[pos[c]] = arg
        c += 1
        if c == len(pos):
            break

    md = Markdown(**kwargs)
    md.convertFile(kwargs.get('input', None), kwargs.get('output', None), kwargs.get('encoding', None))
