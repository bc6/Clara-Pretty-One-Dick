#Embedded file name: carbon/common/lib\__init__.py
try:
    import sys
    import utillib
    sys.modules['carbon.common.lib.utillib'] = utillib
except ImportError:
    pass
