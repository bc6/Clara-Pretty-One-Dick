#Embedded file name: eveprefs\filebased.py
import abc
import logging
import blue
from . import BaseIniFile, get_filename
L = logging.getLogger(__name__)

class FileBasedIniFile(BaseIniFile):

    def __init__(self, shortname, ext, root = None, readOnly = False):
        self.filename = get_filename(blue, shortname, ext, root)
        self.readOnly = readOnly

    def _Read(self):
        """
        Tries to read `self.filename` data as a string.
        If it fails, return empty string.
        """
        try:
            result = blue.win32.AtomicFileRead(self.filename)[0]
        except WindowsError:
            result = ''

        return result

    @abc.abstractmethod
    def _GetSaveStr(self):
        """
        Return the string that should be written to the prefs file on save.
        """
        pass

    def _FlushToDisk(self):
        """
        Saves the current state to disk.
        
        If `readOnly` or `filename` evaluates to False, noop.
        
        If file fails to write, log an error and switch to readonly.
        """
        if self.readOnly or not self.filename:
            return
        s = self._GetSaveStr()
        try:
            blue.win32.AtomicFileWrite(self.filename, s)
        except Exception:
            L.error('Failed writing %s, switching to read-only', self.filename)
            self.readOnly = True
