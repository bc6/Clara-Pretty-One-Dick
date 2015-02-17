#Embedded file name: carbon/common/script/net\httpUtil.py
"""
    Misc. http related utility functions.
"""
import blue
import json
import carbon.common.script.net.machobase as machobase
from carbon.common.script.net.machoNetAddress import MachoAddress
from carbon.common.script.net.machoNetPacket import MachoPacket
from eve.common.script.sys.rowset import Rowset, SparseRowset
from carbon.common.script.sys.row import Row
from eve.common.script.util.utillib_bootstrap import KeyVal
import bluepy

class ComplexEncoder(json.JSONEncoder):

    def default(self, obj):
        """
            A useful JSON encoder for development, as it dumps CCP objects.
        """
        if isinstance(obj, blue.MarshalStream):
            return machobase.Loads(obj)
        if isinstance(obj, MachoAddress) or isinstance(obj, MachoPacket):
            return obj.__getstate__()
        if isinstance(obj, blue.DBRow):
            item = {}
            for key in obj.__columns__:
                item[key] = obj[key]

            return item
        if isinstance(obj, Rowset):
            return [ r for r in obj ]
        if isinstance(obj, Row):
            item = {}
            for key in obj.header:
                item[key] = obj[key]

            return item
        if isinstance(obj, SparseRowset):
            items = []
            for item in obj:
                items.append(self.default(item))

            return items
        if isinstance(obj, KeyVal):
            return obj.__dict__
        if isinstance(obj, UserError):
            return dict({'error': obj.msg}, **obj.dict)
        print obj, 'cannot be encoded and has', dir(obj)
        return json.JSONEncoder.default(self, obj)


@bluepy.TimedFunction('Crest::ToJSON')
def ToJSON(data, encoding = 'utf-8'):
    """
        Dumps data in JSON format for external usage.
    """
    return json.dumps(data, encoding=encoding)


@bluepy.TimedFunction('Crest::ToComplexJSON')
def ToComplexJSON(data, encoding = 'utf-8'):
    """
        Dumps data in JSON format for external usage.
    """
    return json.dumps(data, cls=ComplexEncoder, encoding=encoding)


exports = {'httpUtil.ToJSON': ToJSON,
 'httpUtil.ToComplexJSON': ToComplexJSON}
