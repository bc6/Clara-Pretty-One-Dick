#Embedded file name: carbon/common/script/util\xpermutations.py
"""
code borrowed from: http://code.activestate.com/recipes/190465/

Useful methods for generating combinations and permutations from any list

orginal doc:
xpermutations.py
Generators for calculating a) the permutations of a sequence and
b) the combinations and selections of a number of elements from a
sequence. Uses Python 2.2 generators.

Similar solutions found also in comp.lang.python

Keywords: generator, combination, permutation, selection

See also: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/105962
See also: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66463
See also: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66465
"""

def xcombinations(items, n):
    if n == 0:
        yield []
    else:
        for i in xrange(len(items)):
            for cc in xcombinations(items[:i] + items[i + 1:], n - 1):
                yield [items[i]] + cc


def xuniqueCombinations(items, n):
    if n == 0:
        yield []
    else:
        for i in xrange(len(items)):
            for cc in xuniqueCombinations(items[i + 1:], n - 1):
                yield [items[i]] + cc


def xselections(items, n):
    if n == 0:
        yield []
    else:
        for i in xrange(len(items)):
            for ss in xselections(items, n - 1):
                yield [items[i]] + ss


def xpermutations(items):
    return xcombinations(items, len(items))


exports = {'util.xcombinations': xcombinations,
 'util.xuniqueCombinations': xuniqueCombinations,
 'util.xselections': xselections,
 'util.xpermutations': xpermutations}
