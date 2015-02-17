#Embedded file name: carbon/common/lib/urllib3/packages/ssl_match_hostname\__init__.py
"""The match_hostname() function from Python 3.2, essential when using SSL."""
import re
__version__ = '3.2.2'

class CertificateError(ValueError):
    pass


def _dnsname_to_pat(dn):
    pats = []
    for frag in dn.split('.'):
        if frag == '*':
            pats.append('[^.]+')
        else:
            frag = re.escape(frag)
            pats.append(frag.replace('\\*', '[^.]*'))

    return re.compile('\\A' + '\\.'.join(pats) + '\\Z', re.IGNORECASE)


def match_hostname(cert, hostname):
    """Verify that *cert* (in decoded format as returned by
    SSLSocket.getpeercert()) matches the *hostname*.  RFC 2818 rules
    are mostly followed, but IP addresses are not accepted for *hostname*.
    
    CertificateError is raised on failure. On success, the function
    returns nothing.
    """
    if not cert:
        raise ValueError('empty or no certificate')
    dnsnames = []
    san = cert.get('subjectAltName', ())
    for key, value in san:
        if key == 'DNS':
            if _dnsname_to_pat(value).match(hostname):
                return
            dnsnames.append(value)

    if not dnsnames:
        for sub in cert.get('subject', ()):
            for key, value in sub:
                if key == 'commonName':
                    if _dnsname_to_pat(value).match(hostname):
                        return
                    dnsnames.append(value)

    if len(dnsnames) > 1:
        raise CertificateError("hostname %r doesn't match either of %s" % (hostname, ', '.join(map(repr, dnsnames))))
    elif len(dnsnames) == 1:
        raise CertificateError("hostname %r doesn't match %r" % (hostname, dnsnames[0]))
    else:
        raise CertificateError('no appropriate commonName or subjectAltName fields were found')
