#Embedded file name: coverage\version.py
"""The version and URL for coverage.py"""
__version__ = '3.7'
__url__ = 'http://nedbatchelder.com/code/coverage'
if max(__version__).isalpha():
    __url__ += '/' + __version__
