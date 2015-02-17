#Embedded file name: markdown\serializers.py
import markdown.util as util
ElementTree = util.etree.ElementTree
QName = util.etree.QName
if hasattr(util.etree, 'test_comment'):
    Comment = util.etree.test_comment
else:
    Comment = util.etree.Comment
PI = util.etree.PI
ProcessingInstruction = util.etree.ProcessingInstruction
__all__ = ['to_html_string', 'to_xhtml_string']
HTML_EMPTY = ('area', 'base', 'basefont', 'br', 'col', 'frame', 'hr', 'img', 'input', 'isindex', 'link', 'metaparam')
try:
    HTML_EMPTY = set(HTML_EMPTY)
except NameError:
    pass

_namespace_map = {'http://www.w3.org/XML/1998/namespace': 'xml',
 'http://www.w3.org/1999/xhtml': 'html',
 'http://www.w3.org/1999/02/22-rdf-syntax-ns#': 'rdf',
 'http://schemas.xmlsoap.org/wsdl/': 'wsdl',
 'http://www.w3.org/2001/XMLSchema': 'xs',
 'http://www.w3.org/2001/XMLSchema-instance': 'xsi',
 'http://purl.org/dc/elements/1.1/': 'dc'}

def _raise_serialization_error(text):
    raise TypeError('cannot serialize %r (type %s)' % (text, type(text).__name__))


def _encode(text, encoding):
    try:
        return text.encode(encoding, 'xmlcharrefreplace')
    except (TypeError, AttributeError):
        _raise_serialization_error(text)


def _escape_cdata(text):
    try:
        if '&' in text:
            text = text.replace('&', '&amp;')
        if '<' in text:
            text = text.replace('<', '&lt;')
        if '>' in text:
            text = text.replace('>', '&gt;')
        return text
    except (TypeError, AttributeError):
        _raise_serialization_error(text)


def _escape_attrib(text):
    try:
        if '&' in text:
            text = text.replace('&', '&amp;')
        if '<' in text:
            text = text.replace('<', '&lt;')
        if '>' in text:
            text = text.replace('>', '&gt;')
        if '"' in text:
            text = text.replace('"', '&quot;')
        if '\n' in text:
            text = text.replace('\n', '&#10;')
        return text
    except (TypeError, AttributeError):
        _raise_serialization_error(text)


def _escape_attrib_html(text):
    try:
        if '&' in text:
            text = text.replace('&', '&amp;')
        if '<' in text:
            text = text.replace('<', '&lt;')
        if '>' in text:
            text = text.replace('>', '&gt;')
        if '"' in text:
            text = text.replace('"', '&quot;')
        return text
    except (TypeError, AttributeError):
        _raise_serialization_error(text)


def _serialize_html(write, elem, qnames, namespaces, format):
    tag = elem.tag
    text = elem.text
    if tag is Comment:
        write('<!--%s-->' % _escape_cdata(text))
    elif tag is ProcessingInstruction:
        write('<?%s?>' % _escape_cdata(text))
    else:
        tag = qnames[tag]
        if tag is None:
            if text:
                write(_escape_cdata(text))
            for e in elem:
                _serialize_html(write, e, qnames, None, format)

        else:
            write('<' + tag)
            items = elem.items()
            if items or namespaces:
                items.sort()
                for k, v in items:
                    if isinstance(k, QName):
                        k = k.text
                    if isinstance(v, QName):
                        v = qnames[v.text]
                    else:
                        v = _escape_attrib_html(v)
                    if qnames[k] == v and format == 'html':
                        write(' %s' % v)
                    else:
                        write(' %s="%s"' % (qnames[k], v))

                if namespaces:
                    items = namespaces.items()
                    items.sort(key=lambda x: x[1])
                    for v, k in items:
                        if k:
                            k = ':' + k
                        write(' xmlns%s="%s"' % (k, _escape_attrib(v)))

            if format == 'xhtml' and tag in HTML_EMPTY:
                write(' />')
            else:
                write('>')
                tag = tag.lower()
                if text:
                    if tag == 'script' or tag == 'style':
                        write(text)
                    else:
                        write(_escape_cdata(text))
                for e in elem:
                    _serialize_html(write, e, qnames, None, format)

                if tag not in HTML_EMPTY:
                    write('</' + tag + '>')
    if elem.tail:
        write(_escape_cdata(elem.tail))


def _write_html(root, encoding = None, default_namespace = None, format = 'html'):
    data = []
    write = data.append
    qnames, namespaces = _namespaces(root, default_namespace)
    _serialize_html(write, root, qnames, namespaces, format)
    if encoding is None:
        return ''.join(data)
    else:
        return _encode(''.join(data))


def _namespaces(elem, default_namespace = None):
    qnames = {None: None}
    namespaces = {}
    if default_namespace:
        namespaces[default_namespace] = ''

    def add_qname(qname):
        try:
            if qname[:1] == '{':
                uri, tag = qname[1:].split('}', 1)
                prefix = namespaces.get(uri)
                if prefix is None:
                    prefix = _namespace_map.get(uri)
                    if prefix is None:
                        prefix = 'ns%d' % len(namespaces)
                    if prefix != 'xml':
                        namespaces[uri] = prefix
                if prefix:
                    qnames[qname] = '%s:%s' % (prefix, tag)
                else:
                    qnames[qname] = tag
            else:
                if default_namespace:
                    raise ValueError('cannot use non-qualified names with default_namespace option')
                qnames[qname] = qname
        except TypeError:
            _raise_serialization_error(qname)

    try:
        iterate = elem.iter
    except AttributeError:
        iterate = elem.getiterator

    for elem in iterate():
        tag = elem.tag
        if isinstance(tag, QName) and tag.text not in qnames:
            add_qname(tag.text)
        elif isinstance(tag, basestring):
            if tag not in qnames:
                add_qname(tag)
        elif tag is not None and tag is not Comment and tag is not PI:
            _raise_serialization_error(tag)
        for key, value in elem.items():
            if isinstance(key, QName):
                key = key.text
            if key not in qnames:
                add_qname(key)
            if isinstance(value, QName) and value.text not in qnames:
                add_qname(value.text)

        text = elem.text
        if isinstance(text, QName) and text.text not in qnames:
            add_qname(text.text)

    return (qnames, namespaces)


def to_html_string(element):
    return _write_html(ElementTree(element).getroot(), format='html')


def to_xhtml_string(element):
    return _write_html(ElementTree(element).getroot(), format='xhtml')
