#Embedded file name: coverage\phystokens.py
"""Better tokenizing for coverage.py."""
import codecs, keyword, re, sys, token, tokenize
from coverage.backward import StringIO

def phys_tokens(toks):
    """Return all physical tokens, even line continuations.
    
    tokenize.generate_tokens() doesn't return a token for the backslash that
    continues lines.  This wrapper provides those tokens so that we can
    re-create a faithful representation of the original source.
    
    Returns the same values as generate_tokens()
    
    """
    last_line = None
    last_lineno = -1
    last_ttype = None
    for ttype, ttext, (slineno, scol), (elineno, ecol), ltext in toks:
        if last_lineno != elineno:
            if last_line and last_line[-2:] == '\\\n':
                inject_backslash = True
                if last_ttype == tokenize.COMMENT:
                    inject_backslash = False
                elif ttype == token.STRING:
                    if '\n' in ttext and ttext.split('\n', 1)[0][-1] == '\\':
                        inject_backslash = False
                if inject_backslash:
                    ccol = len(last_line.split('\n')[-2]) - 1
                    yield (99999,
                     '\\\n',
                     (slineno, ccol),
                     (slineno, ccol + 2),
                     last_line)
            last_line = ltext
            last_ttype = ttype
        yield (ttype,
         ttext,
         (slineno, scol),
         (elineno, ecol),
         ltext)
        last_lineno = elineno


def source_token_lines(source):
    """Generate a series of lines, one for each line in `source`.
    
    Each line is a list of pairs, each pair is a token::
    
        [('key', 'def'), ('ws', ' '), ('nam', 'hello'), ('op', '('), ... ]
    
    Each pair has a token class, and the token text.
    
    If you concatenate all the token texts, and then join them with newlines,
    you should have your original `source` back, with two differences:
    trailing whitespace is not preserved, and a final line with no newline
    is indistinguishable from a final line with a newline.
    
    """
    ws_tokens = [token.INDENT,
     token.DEDENT,
     token.NEWLINE,
     tokenize.NL]
    line = []
    col = 0
    source = source.expandtabs(8).replace('\r\n', '\n')
    tokgen = tokenize.generate_tokens(StringIO(source).readline)
    for ttype, ttext, (_, scol), (_, ecol), _ in phys_tokens(tokgen):
        mark_start = True
        for part in re.split('(\n)', ttext):
            if part == '\n':
                yield line
                line = []
                col = 0
                mark_end = False
            elif part == '':
                mark_end = False
            elif ttype in ws_tokens:
                mark_end = False
            else:
                if mark_start and scol > col:
                    line.append(('ws', ' ' * (scol - col)))
                    mark_start = False
                tok_class = tokenize.tok_name.get(ttype, 'xx').lower()[:3]
                if ttype == token.NAME and keyword.iskeyword(ttext):
                    tok_class = 'key'
                line.append((tok_class, part))
                mark_end = True
            scol = 0

        if mark_end:
            col = ecol

    if line:
        yield line


def source_encoding(source):
    """Determine the encoding for `source` (a string), according to PEP 263.
    
    Returns a string, the name of the encoding.
    
    """
    cookie_re = re.compile('coding[:=]\\s*([-\\w.]+)')
    readline = iter(source.splitlines(True)).next

    def _get_normal_name(orig_enc):
        """Imitates get_normal_name in tokenizer.c."""
        enc = orig_enc[:12].lower().replace('_', '-')
        if re.match('^utf-8($|-)', enc):
            return 'utf-8'
        if re.match('^(latin-1|iso-8859-1|iso-latin-1)($|-)', enc):
            return 'iso-8859-1'
        return orig_enc

    if sys.version_info <= (2, 4):
        default = 'iso-8859-1'
    else:
        default = 'ascii'
    bom_found = False
    encoding = None

    def read_or_stop():
        """Get the next source line, or ''."""
        try:
            return readline()
        except StopIteration:
            return ''

    def find_cookie(line):
        """Find an encoding cookie in `line`."""
        try:
            line_string = line.decode('ascii')
        except UnicodeDecodeError:
            return None

        matches = cookie_re.findall(line_string)
        if not matches:
            return None
        encoding = _get_normal_name(matches[0])
        try:
            codec = codecs.lookup(encoding)
        except LookupError:
            raise SyntaxError('unknown encoding: ' + encoding)

        if bom_found:
            codec_name = getattr(codec, 'name', encoding)
            if codec_name != 'utf-8':
                raise SyntaxError('encoding problem: utf-8')
            encoding += '-sig'
        return encoding

    first = read_or_stop()
    if first.startswith(codecs.BOM_UTF8):
        bom_found = True
        first = first[3:]
        default = 'utf-8-sig'
    if not first:
        return default
    encoding = find_cookie(first)
    if encoding:
        return encoding
    second = read_or_stop()
    if not second:
        return default
    encoding = find_cookie(second)
    if encoding:
        return encoding
    return default
