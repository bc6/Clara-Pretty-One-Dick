#Embedded file name: eve/client/script/util\godmarowset.py
"""
Specialized C*Rowset subclasses for godma
"""
import dbutil
import blue
import types
import log
from service import *
DEBUG = True

def rowsetIterator(rowset):
    """ 
    Standard iterators for built in collection types do not go through __getitem__ 
    when they return the item from the collection.  In order to support the rowClass
    feature, we sometimes need this iterator in the below classes.
    """
    if isinstance(rowset, (GodmaIndexedRowset, GodmaFilterRowset)):
        for key in rowset.iterkeys():
            yield rowset.__getitem__(key)

    elif isinstance(rowset, (GodmaRowset,)):
        for i in xrange(len(rowset)):
            yield rowset.__getitem__(i)

    else:
        raise NotImplementedError('Yikes, what are you? rowsetIterator does not operate on %s (%s)' % (str(type(rowset)), str(rowset.__class__)))
    raise StopIteration


class GodmaRowset(dbutil.CRowset):
    """
    Extension of the CRowset wrapper class for DBRow lists.
    """
    __passbyvalue__ = 1

    def __init__(self, header, rows, rowClass = blue.DBRow):
        dbutil.CRowset.__init__(self, header, rows)
        self.rowClass = rowClass

    def __getitem__(self, index):
        ret = dbutil.CRowset.__getitem__(self, index)
        if isinstance(self.rowClass, types.MethodType) or not isinstance(ret, self.rowClass):
            if not isinstance(ret, blue.DBRow):
                ret = blue.DBRow(self.header, ret)
            return self.rowClass(self.header, ret)
        return ret

    def __setitem__(self, idx, row):
        if not isinstance(row, blue.DBRow):
            log.LogTraceback('__setitem__:Storing non-dbrow in GodmaRowset')
        dbutil.CRowset.__setitem__(self, idx, row)

    def __iter__(self):
        """ 
        When rowClass doesn't match the default, we need an iterator that 
        goes through __getitem__
        """
        if self.rowClass != blue.DBRow:
            return rowsetIterator(self)
        return dbutil.CRowset.__iter__(self)

    def __getslice__(self, i, j):
        return GodmaRowset(self.header, list.__getslice__(self, i, j), rowClass=self.rowClass)

    def pop(self, idx = -1):
        """ Overridden to go through __getitem__"""
        ret = self.__getitem__(idx)
        dbutil.CRowset.pop(self, idx)
        return ret

    def Index(self, columnName):
        """
        rs.Index(columnName) -> GodmaIndexedRowset
        Returns an indexed rowset. The row objects themselves are shared between the
        new indexed rowset and the original rowset.
        To create multi-keyed index, separate the column names with a dot. Example:
        "fromObjectID.shipGroupID"
        """
        return GodmaIndexedRowset(self.header, columnName, dbutil.CRowset.Index(self, columnName), rowClass=self.rowClass)

    def Filter(self, columnName, indexName = None):
        """
        rs.Filter(columnName) -> GodmaFilterRowset
        Returns a filter rowset. It's like CRowset but allows duplicate keys, 
        each of which refers to a CRowset or CFilterRowset
        """
        return GodmaFilterRowset(self.header, columnName, indexName, dbutil.CRowset.Filter(self, columnName, indexName), rowClass=self.rowClass)


class GodmaIndexedRowset(dbutil.CIndexedRowset):

    def __init__(self, header, columnName, ccdict = {}, rowClass = blue.DBRow):
        dbutil.CIndexedRowset.__init__(self, header, columnName)
        self.rowClass = rowClass
        if len(ccdict):
            self.update(ccdict)

    def __getitem__(self, key):
        ret = dbutil.CIndexedRowset.__getitem__(self, key)
        if isinstance(self.rowClass, types.MethodType) or not isinstance(ret, self.rowClass):
            if not isinstance(ret, blue.DBRow):
                ret = blue.DBRow(self.header, ret)
            ret = self.rowClass(self.header, ret)
        return ret

    def values(self):
        """ Overridden to return a rowset instead of a list of values to maintain rowClass magic"""
        return GodmaRowset(self.header, dbutil.CIndexedRowset.values(self), rowClass=self.rowClass)

    def itervalues(self):
        if self.rowClass != blue.DBRow:
            return rowsetIterator(self)
        return dbutil.CIndexedRowset.itervalues(self)

    def get(self, k, d = None):
        """ Overridden to go through __getitem__"""
        try:
            ret = self.__getitem__(k)
        except KeyError:
            return d

        return ret

    def pop(self, *args):
        """ Overridden to go through __getitem__"""
        if len(args) > 2 or len(args) < 1:
            raise TypeError('pop expected at most 2 arguments, got %d' % len(args))
        try:
            ret = self.__getitem__(args[0])
            del self[args[0]]
        except KeyError:
            if len(args) != 2:
                raise
            return args[1]

        return ret

    def popitem(self):
        """ Overridden to go through __getitem__"""
        if len(self) == 0:
            raise KeyError
        import random
        key = random.randrange(len(self))
        ret = self.__getitem__(key)
        del self[key]
        return ret


class GodmaFilterRowset(dbutil.CFilterRowset):

    def __init__(self, header, columnName, indexName, ccdict = {}, rowClass = blue.DBRow):
        dbutil.CFilterRowset.__init__(self, header, columnName)
        self.indexName = indexName
        self.rowClass = rowClass
        if len(ccdict) > 0:
            self.update(ccdict)

    def __getitem__(self, key):
        ret = dbutil.CFilterRowset.__getitem__(self, key)
        if isinstance(ret, dict):
            if not isinstance(ret, GodmaIndexedRowset):
                return GodmaIndexedRowset(self.header, self.indexName, ret, rowClass=self.rowClass)
            return ret
        if isinstance(self.rowClass, types.MethodType) or not isinstance(ret, self.rowClass):
            if not isinstance(ret, blue.DBRow):
                print ' _!_ GodmaFilteredRowset storing non-DBRow as leaf-element:', type(ret)
                ret = blue.DBRow(self.header, ret)
            return self.rowClass(self.header, ret)
        return ret

    def values(self):
        v = dbutil.CFilteredRowset.values(self)
        if isinstance(v, list):
            return v
        return GodmaIndexedRowset(self.header, self.indexName, v, rowClass=self.rowClass)

    def itervalues(self):
        if self.rowClass != blue.DBRow:
            return rowsetIterator(self)
        return dbutil.CFilterRowset.itervalues(self)

    def get(self, k, d = None):
        """ Overridden to go through __getitem__"""
        try:
            ret = self.__getitem__(k)
        except KeyError:
            return d

        return ret

    def pop(self, *args):
        """ Overridden to go through __getitem__"""
        if len(args) > 2 or len(args) < 1:
            raise TypeError('pop expected at most 2 arguments, got %d' % len(args))
        try:
            ret = self.__getitem__(args[0])
            del self[args[0]]
        except KeyError:
            if len(args) != 2:
                raise
            return args[1]

        return ret

    def popitem(self):
        """ Overridden to go through __getitem__"""
        if len(self) == 0:
            raise KeyError
        import random
        key = self.keys()[random.randrange(len(self))]
        ret = self.__getitem__(key)
        del self[key]
        return ret
