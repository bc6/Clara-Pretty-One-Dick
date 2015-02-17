#Embedded file name: eveinventory\voucher.py
import types
import inventorycommon.const as invconst

def GetObject(voucherItem, description = None):
    classType = VOUCHER_BY_TYPE.get(voucherItem.typeID, None)
    if classType is not None:
        return classType(voucherItem, description)


class Voucher:
    __passbyvalue__ = 1
    __vouchertype__ = None
    __parameters__ = ['param1', 'param2', 'text']
    __verbs__ = {}
    __typeDefiningParameters__ = []
    __description__ = ''

    def __init__(self, voucherItem = None, description = None):
        if voucherItem is not None:
            header = voucherItem.header
            data = voucherItem.line
        else:
            header, data = (None, None)
        self.__dict__['header'] = header
        self.__dict__['data'] = data
        self.__dict__['description'] = description

    def __getattr__(self, name):
        header = self.__dict__['header']
        params = self.__class__.__dict__['__parameters__']
        data = self.__dict__['data']
        if name not in header:
            if name in params:
                return self.customInfo[params.index(name) + 1]
            if len(name) > 1:
                if name[:2] == '__':
                    return getattr(self.__dict__, name)
            raise RuntimeError('InvalidFieldName', name)
        return data[header.index(name)]

    def __setattr__(self, key, value):
        if key == 'header':
            self.__dict__['header'] = value
            return
        if key == 'data':
            self.__dict__['data'] = value
            return
        header = self.__dict__['header']
        params = self.__class__.__dict__['__parameters__']
        if key not in header:
            if key in params:
                raise RuntimeError('ReadOnly', key)
            else:
                raise RuntimeError('InvalidFieldName', key)
        self.__dict__['data'][header.index(key)] = value

    def __getitem__(self, i):
        if type(i) == types.StringType:
            return self.__getattr__(i)
        return self.__dict__['data'][i]

    def __setitem__(self, key, value):
        if type(key) == types.StringType:
            return self.__setattr__(key, value)
        self.__dict__['data'][key] = value

    def __repr__(self):
        return self.GetDescription()

    def __len__(self):
        return len(self.__dict__['data'])

    def __getslice__(self, i, j):
        return self.__class__(self.header[i:j], self.data[i:j])

    def __cmp__(self, other):
        return not (type(other) == types.InstanceType and cmp(self.header, other.header) and cmp(self.data, other.data))

    def GetDescription(self):
        if len(self.__dict__['description']):
            return self.__dict__['description']
        header = self.__dict__['header']
        data = self.__dict__['data']
        if len(header) > len(data):
            return '%s(MANGLED VOUCHER,%s,%s)' % (self.__guid__, header, data)
        ret = '%s(' % self.__guid__
        for i in range(len(header)):
            if i != const.ixCustomInfo:
                ret = ret + header[i] + ':' + str(data[i]) + ','
            else:
                params = self.__class__.__dict__['__parameters__']
                for p in range(len(params)):
                    ret = ret + params[p] + ':' + str(self.customInfo[p + 1]) + ','

        return ret[:-1] + ')'

    def IsSameType(self, other):
        if self.__vouchertype__ != other.__vouchertype__:
            return 0
        if len(self.__parameters__) != len(other.__parameters__):
            return 0
        if self.GetType() != other.GetType():
            return 0
        return 1

    def GetVerbs(self):
        return self.__verbs__

    def GetType(self):
        typeStr = self.__vouchertype__
        for param in self.__typeDefiningParameters__:
            typeStr = '%s-%s' % (typeStr, self.__getattr__(param))

        return typeStr

    def GetTypeInfo(self):
        typeInfo = [self.__vouchertypeid__]
        for param in self.__typeDefiningParameters__:
            typeInfo.append(self.__getattr__(param))

        return tuple(typeInfo)


class Share(Voucher):
    __passbyvalue__ = 1
    __vouchertype__ = 'typeCompanyShares'
    __vouchertypeid__ = invconst.typeCompanyShares
    __parameters__ = ['corporationID', 'someOtherStuff', 'andEvenMoreOtherStuff']
    __verbs__ = {'sell': 'Sell'}
    __typeDefiningParameters__ = ['corporationID']


class Bookmark(Voucher):
    __passbyvalue__ = 1
    __vouchertype__ = 'typeBookmark'
    __vouchertypeid__ = invconst.typeBookmark
    __parameters__ = ['bookmarkID', 'NotUsed', 'text']
    __verbs__ = {'copy': 'Copy'}
    __typeDefiningParameters__ = ['bookmarkID']


class PlayerKill(Voucher):
    __passbyvalue__ = 1
    __vouchertype__ = 'typePlayerKill'
    __vouchertypeid__ = invconst.typePlayerKill
    __parameters__ = ['victimID', 'NotUsed', 'text']
    __verbs__ = {'delete': 'Delete'}
    __typeDefiningParameters__ = ['victimID']


VOUCHER_BY_TYPE = {invconst.typeBookmark: Bookmark,
 invconst.typePlayerKill: PlayerKill,
 invconst.typeCompanyShares: Share}
