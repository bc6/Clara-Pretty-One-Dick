#Embedded file name: carbon/common/lib/cherrypy/test\test_httplib.py
"""Tests for cherrypy/lib/httputil.py."""
import unittest
from cherrypy.lib import httputil

class UtilityTests(unittest.TestCase):

    def test_urljoin(self):
        self.assertEqual(httputil.urljoin('/sn/', '/pi/'), '/sn/pi/')
        self.assertEqual(httputil.urljoin('/sn/', '/pi'), '/sn/pi')
        self.assertEqual(httputil.urljoin('/sn/', '/'), '/sn/')
        self.assertEqual(httputil.urljoin('/sn/', ''), '/sn/')
        self.assertEqual(httputil.urljoin('/sn', '/pi/'), '/sn/pi/')
        self.assertEqual(httputil.urljoin('/sn', '/pi'), '/sn/pi')
        self.assertEqual(httputil.urljoin('/sn', '/'), '/sn/')
        self.assertEqual(httputil.urljoin('/sn', ''), '/sn')
        self.assertEqual(httputil.urljoin('/', '/pi/'), '/pi/')
        self.assertEqual(httputil.urljoin('/', '/pi'), '/pi')
        self.assertEqual(httputil.urljoin('/', '/'), '/')
        self.assertEqual(httputil.urljoin('/', ''), '/')
        self.assertEqual(httputil.urljoin('', '/pi/'), '/pi/')
        self.assertEqual(httputil.urljoin('', '/pi'), '/pi')
        self.assertEqual(httputil.urljoin('', '/'), '/')
        self.assertEqual(httputil.urljoin('', ''), '/')


if __name__ == '__main__':
    unittest.main()
