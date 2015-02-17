#Embedded file name: carbon/common/lib/cherrypy/test\logtest.py
"""logtest, a unittest.TestCase helper for testing log output."""
import sys
import time
import cherrypy
try:
    import msvcrt

    def getchar():
        return msvcrt.getch()


except ImportError:
    import tty, termios

    def getchar():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        return ch


class LogCase(object):
    """unittest.TestCase mixin for testing log messages.
    
    logfile: a filename for the desired log. Yes, I know modes are evil,
        but it makes the test functions so much cleaner to set this once.
    
    lastmarker: the last marker in the log. This can be used to search for
        messages since the last marker.
    
    markerPrefix: a string with which to prefix log markers. This should be
        unique enough from normal log output to use for marker identification.
    """
    logfile = None
    lastmarker = None
    markerPrefix = 'test suite marker: '

    def _handleLogError(self, msg, data, marker, pattern):
        print ''
        print '    ERROR: %s' % msg
        if not self.interactive:
            raise self.failureException(msg)
        p = '    Show: [L]og [M]arker [P]attern; [I]gnore, [R]aise, or sys.e[X]it >> '
        print p,
        sys.stdout.flush()
        while True:
            i = getchar().upper()
            if i not in 'MPLIRX':
                continue
            print i.upper()
            if i == 'L':
                for x, line in enumerate(data):
                    if (x + 1) % self.console_height == 0:
                        print '<-- More -->\r',
                        m = getchar().lower()
                        print '            \r',
                        if m == 'q':
                            break
                    print line.rstrip()

            elif i == 'M':
                print repr(marker or self.lastmarker)
            elif i == 'P':
                print repr(pattern)
            else:
                if i == 'I':
                    return
                if i == 'R':
                    raise self.failureException(msg)
                elif i == 'X':
                    self.exit()
            print p,

    def exit(self):
        sys.exit()

    def emptyLog(self):
        """Overwrite self.logfile with 0 bytes."""
        open(self.logfile, 'wb').write('')

    def markLog(self, key = None):
        """Insert a marker line into the log and set self.lastmarker."""
        if key is None:
            key = str(time.time())
        self.lastmarker = key
        open(self.logfile, 'ab+').write('%s%s\n' % (self.markerPrefix, key))

    def _read_marked_region(self, marker = None):
        """Return lines from self.logfile in the marked region.
        
        If marker is None, self.lastmarker is used. If the log hasn't
        been marked (using self.markLog), the entire log will be returned.
        """
        logfile = self.logfile
        marker = marker or self.lastmarker
        if marker is None:
            return open(logfile, 'rb').readlines()
        data = []
        in_region = False
        for line in open(logfile, 'rb'):
            if in_region:
                if line.startswith(self.markerPrefix) and marker not in line:
                    break
                else:
                    data.append(line)
            elif marker in line:
                in_region = True

        return data

    def assertInLog(self, line, marker = None):
        """Fail if the given (partial) line is not in the log.
        
        The log will be searched from the given marker to the next marker.
        If marker is None, self.lastmarker is used. If the log hasn't
        been marked (using self.markLog), the entire log will be searched.
        """
        data = self._read_marked_region(marker)
        for logline in data:
            if line in logline:
                return

        msg = '%r not found in log' % line
        self._handleLogError(msg, data, marker, line)

    def assertNotInLog(self, line, marker = None):
        """Fail if the given (partial) line is in the log.
        
        The log will be searched from the given marker to the next marker.
        If marker is None, self.lastmarker is used. If the log hasn't
        been marked (using self.markLog), the entire log will be searched.
        """
        data = self._read_marked_region(marker)
        for logline in data:
            if line in logline:
                msg = '%r found in log' % line
                self._handleLogError(msg, data, marker, line)

    def assertLog(self, sliceargs, lines, marker = None):
        """Fail if log.readlines()[sliceargs] is not contained in 'lines'.
        
        The log will be searched from the given marker to the next marker.
        If marker is None, self.lastmarker is used. If the log hasn't
        been marked (using self.markLog), the entire log will be searched.
        """
        data = self._read_marked_region(marker)
        if isinstance(sliceargs, int):
            if isinstance(lines, (tuple, list)):
                lines = lines[0]
            if lines not in data[sliceargs]:
                msg = '%r not found on log line %r' % (lines, sliceargs)
                self._handleLogError(msg, [data[sliceargs]], marker, lines)
        else:
            if isinstance(lines, tuple):
                lines = list(lines)
            elif isinstance(lines, basestring):
                raise TypeError("The 'lines' arg must be a list when 'sliceargs' is a tuple.")
            start, stop = sliceargs
            for line, logline in zip(lines, data[start:stop]):
                if line not in logline:
                    msg = '%r not found in log' % line
                    self._handleLogError(msg, data[start:stop], marker, line)