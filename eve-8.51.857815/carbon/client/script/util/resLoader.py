#Embedded file name: carbon/client/script/util\resLoader.py
"""
resLoader.py

Moved from misc.py in client/script/util

Author: Unknown
Moved By: Paul Gilmore
Moved On: July 2008

This is a utility for loading resfiles on the client.
"""
import blue

class _ResFileRaw(object):
    """A class that wraps a binary resfile"""
    __slots__ = ['resfile', 'closed']

    def __init__(self, respath):
        self.resfile = blue.ResFile()
        self.resfile.OpenAlways(respath)
        self.closed = False

    def read(self, size = -1):
        if self.closed:
            raise ValueError('file is closed')
        return self.resfile.Read(size)

    def seek(self, offset, whence = 0):
        if whence == 0:
            r = self.resfile.Seek(offset)
        elif whence == 1:
            r = self.resfile.Seek(offset + self.file.pos)
        elif whence == -1:
            r = self.resfile.Seek(self.file.size - offset)
        else:
            raise ValueError("'whence' must be 0, 1 or -1, not %s" % whence)

    def tell(self):
        return self.resfile.pos

    def close(self):
        if not self.closed:
            self.resfile.Close()
        self.closed = True


def ResFile(respath, mode = 'rb', bufsize = -1):
    """
    Open a resfile.  If in text mode, create a stringIO on a translated file 
    instead.    
    
    Default is rb, for backwards compatibility.
    """
    if mode.count('b'):
        return _ResFileRaw(respath)
    else:
        s = _ResFileRaw(respath).read().replace('\r\n', '\n')
        import StringIO
        return StringIO.StringIO(s)


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('util', globals())
