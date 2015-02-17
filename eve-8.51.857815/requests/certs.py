#Embedded file name: requests\certs.py
"""
certs.py
~~~~~~~~

This module returns the preferred default CA certificate bundle.

If you are packaging Requests, e.g., for a Linux distribution or a managed
environment, you can change the definition of where() to return a separately
packaged CA bundle.
"""
import os.path

def where():
    """Return the preferred certificate bundle."""
    return os.path.join(os.path.dirname(__file__), 'cacert.pem')


if __name__ == '__main__':
    print where()
