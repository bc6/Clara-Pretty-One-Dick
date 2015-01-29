#Embedded file name: eveprefs\iniformat.py
from cPickle import Unpickler, dumps
import cStringIO
import re
import types
from . import DEFAULT_ENCODING
from .filebased import FileBasedIniFile

class IniIniFile(FileBasedIniFile):
    """
    Works like a normal .ini file except there are no groups. All non-blank
    lines should include a key value pair, where the key and value is a string,
    separated with a =. If the line starts with # it's ignored and considered
    a comment. If a line starts with a [ or ; it's also ignored, and is there
    for compatibility with external tools which expect an .ini file with groups.
    
    The file is kept opened for the whole time and writes are committed on
    every modification. Order of key-value pairs, comments and linebreaks are
    kept intact.
    """
    nopickles = [types.IntType,
     types.FloatType,
     types.LongType,
     types.StringType,
     types.UnicodeType]
    number = re.compile('[\\-]?[\\d.]+')

    def __init__(self, shortname, root = None, readOnly = False):
        FileBasedIniFile.__init__(self, shortname, '.ini', root, readOnly)
        self.keyval = {}
        self.lines = self._Read().splitlines()
        oldLines = self.lines
        self.lines = []
        for newLine in oldLines:
            try:
                self.lines.append(unicode(newLine, DEFAULT_ENCODING).encode(DEFAULT_ENCODING))
            except:
                print 'Unencodable data discovered in ini file. Removing offending data.'

        for line in self.lines:
            sline = line.strip()
            if sline and sline[0] not in '[;#':
                sep = sline.find('=')
                if sep >= 0:
                    key = sline[:sep].strip()
                    self.keyval[key] = line

    def _GetKeySet(self):
        return self.keyval

    def _GetValue(self, key):
        value = self.keyval[key]
        sep = value.find('=')
        value = value[sep + 1:].strip()
        if not len(value):
            return value
        if value.startswith('"') and value.endswith('"'):
            return unicode(value[1:-1])
        if value[:7] == 'pickle:':
            io = cStringIO.StringIO(value[7:].replace('\x1f', '\n'))
            return Unpickler(io).load()
        if self.number.match(value):
            try:
                return int(value)
            except ValueError:
                pass

            try:
                return float(value)
            except ValueError:
                pass

        return unicode(value)

    def _SetValue(self, key, value, forcePickle):
        line = self._GetLineFromFixedKeyAndValue(key, value, forcePickle)
        if key in self.keyval:
            old = self.keyval[key]
            if line == self.keyval[key]:
                return
            lineno = self.lines.index(old)
            self.lines.remove(old)
            self.lines.insert(lineno, line)
        else:
            self.lines.append(line)
        self.keyval[key] = line
        self._FlushToDisk()

    def _SpoofKey(self, key, value):
        key = self.FixKey(key)
        self.keyval[key] = self._GetLineFromFixedKeyAndValue(key, value)

    def FixKey(self, key):
        key = FileBasedIniFile.FixKey(self, key)
        return key.strip().replace('|', '||').replace('=', '-|-')

    def _GetLineFromFixedKeyAndValue(self, fixedKey, value, forcePickle = False):
        """
        Given a fixed key string and an input value, pickle or convert the value as
        necessary, then assemble the "key=value" string for internal storage purposes.
        """
        if type(value) in types.StringTypes:
            try:
                value = value.encode(DEFAULT_ENCODING)
            except UnicodeEncodeError:
                forcePickle = True
            except UnicodeDecodeError:
                forcePickle = True

        if forcePickle or type(value) not in self.nopickles:
            value = 'pickle:' + dumps(value).replace('\n', '\x1f')
        else:
            value = unicode(value).strip()
        return '%s=%s' % (fixedKey, value)

    def _DeleteValue(self, key):
        self.lines.remove(self.keyval[key])
        del self.keyval[key]
        self._FlushToDisk()

    def _GetSaveStr(self):
        sortlines = [ (line.lower()[:3], line) for line in self.lines ]
        sortlines.sort()
        lines = [ line[1] for line in sortlines ]
        savestr = '\r\n'.join(lines).encode('cp1252')
        return savestr
