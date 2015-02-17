#Embedded file name: httplib2\iri2uri.py
"""
iri2uri

Converts an IRI to a URI.

"""
__author__ = 'Joe Gregorio (joe@bitworking.org)'
__copyright__ = 'Copyright 2006, Joe Gregorio'
__contributors__ = []
__version__ = '1.0.0'
__license__ = 'MIT'
__history__ = '\n'
import urlparse
escape_range = [(160, 55295),
 (57344, 63743),
 (63744, 64975),
 (65008, 65519),
 (65536, 131069),
 (131072, 196605),
 (196608, 262141),
 (262144, 327677),
 (327680, 393213),
 (393216, 458749),
 (458752, 524285),
 (524288, 589821),
 (589824, 655357),
 (655360, 720893),
 (720896, 786429),
 (786432, 851965),
 (851968, 917501),
 (921600, 983037),
 (983040, 1048573),
 (1048576, 1114109)]

def encode(c):
    retval = c
    i = ord(c)
    for low, high in escape_range:
        if i < low:
            break
        if i >= low and i <= high:
            retval = ''.join([ '%%%2X' % ord(o) for o in c.encode('utf-8') ])
            break

    return retval


def iri2uri(uri):
    """Convert an IRI to a URI. Note that IRIs must be 
    passed in a unicode strings. That is, do not utf-8 encode
    the IRI before passing it into the function."""
    if isinstance(uri, unicode):
        scheme, authority, path, query, fragment = urlparse.urlsplit(uri)
        authority = authority.encode('idna')
        uri = urlparse.urlunsplit((scheme,
         authority,
         path,
         query,
         fragment))
        uri = ''.join([ encode(c) for c in uri ])
    return uri


if __name__ == '__main__':
    import unittest

    class Test(unittest.TestCase):

        def test_uris(self):
            """Test that URIs are invariant under the transformation."""
            invariant = [u'ftp://ftp.is.co.za/rfc/rfc1808.txt',
             u'http://www.ietf.org/rfc/rfc2396.txt',
             u'ldap://[2001:db8::7]/c=GB?objectClass?one',
             u'mailto:John.Doe@example.com',
             u'news:comp.infosystems.www.servers.unix',
             u'tel:+1-816-555-1212',
             u'telnet://192.0.2.16:80/',
             u'urn:oasis:names:specification:docbook:dtd:xml:4.1.2']
            for uri in invariant:
                self.assertEqual(uri, iri2uri(uri))

        def test_iri(self):
            """ Test that the right type of escaping is done for each part of the URI."""
            self.assertEqual('http://xn--o3h.com/%E2%98%84', iri2uri(u'http://\u2604.com/\u2604'))
            self.assertEqual('http://bitworking.org/?fred=%E2%98%84', iri2uri(u'http://bitworking.org/?fred=\u2604'))
            self.assertEqual('http://bitworking.org/#%E2%98%84', iri2uri(u'http://bitworking.org/#\u2604'))
            self.assertEqual('#%E2%98%84', iri2uri(u'#\u2604'))
            self.assertEqual('/fred?bar=%E2%98%9A#%E2%98%84', iri2uri(u'/fred?bar=\u261a#\u2604'))
            self.assertEqual('/fred?bar=%E2%98%9A#%E2%98%84', iri2uri(iri2uri(u'/fred?bar=\u261a#\u2604')))
            self.assertNotEqual('/fred?bar=%E2%98%9A#%E2%98%84', iri2uri(u'/fred?bar=\u261a#\u2604'.encode('utf-8')))


    unittest.main()
