#Embedded file name: carbon/common/script/util\dbutil.py
"""
Utility and helper functions for database access

Note that many other sources currently add functions or classes to this namespace.
"""
from collections import defaultdict

def SQLStringify(data):
    """ Take in a python data, and format it so that it can be used in SQL.
    For most data this just means converting it to a string, but data that
    is already strings needs to be sanitized for any apostrophes.
    None in python equates to NULL in sql, so this check is explicitly made. """
    if isinstance(data, str) or isinstance(data, unicode):
        return "'" + data.replace("'", "''") + "'"
    if data is None:
        return 'NULL'
    if isinstance(data, bool):
        if data:
            return '1'
        else:
            return '0'
    else:
        return str(data)


def TuplesToCSVStrings(tuplelist, numLists, maxOutputLength = 4000):
    """
        This method is used to convert a list of lists (or tuples!) into CSV strings for use in
        related input variables to a SQL stored procedure. Returns the unprocessed parts
        of the input tuples as the second half of an output 2-tuple.
    
        Note that all of the lists/tuples in the input tuplelist must be of the same length
        for this method to not completely screw up.
    
        ARGUMENTS:
        'tuplelist':        A list of lists or tuples.
        'numLists':                The number of lists in 'tuplelist'.
        'maxOutputLength':  The maximum length of the output string, in characters. Includes commas.
    
    
        For example, if you have objectID and dataID, which both must be passed in
        properly to the database at the same position in a string (so they can then be
        related via zutil.IntListToOrderedTable, for example), then it is important
        that we don't pass through any objectIDs without their associated dataIDs.
    
        Returns a 2-tuple where the first element is itself a N-tuple of the strings
        and the 2nd element is a list of remaining tuples. (numLists = N)
    
        EXAMPLE, BECAUSE THIS IS COMPLEX:
    
        objectIDs = [1,2,3,4,5]
        dataIDs = [100,200,300,400,500]
        With a maxOutputLength of 15, this method will return:
         ( ("1,2,3,4", "100,200,300,400"), 
           ((5,), (500,)) 
          )
    
        Since the DataIDs were much longer, we could only fit 4 of them into a 15-character string.
        Hence, we return the first 4 elements of each list, stringified, and then return
        the remainder as a pair of tuples.
    
        Cribbed from the PI Database updating code.
    """
    if len(tuplelist) == 0:
        return (tuple([ '' for i in xrange(numLists) ]), tuplelist)
    maxstringlen = 0
    workingSet = tuplelist
    remains = []
    for i, t in enumerate(tuplelist):
        strlen = 0
        for e in t:
            if len(str(e)) > strlen:
                strlen = len(str(e))

        maxstringlen += strlen + 1
        if maxstringlen >= maxOutputLength:
            workingSet = tuplelist[:i]
            remains = tuplelist[i:]
            break

    retstrings = []
    for i in range(numLists):
        values = [ v[i] for v in workingSet ]
        retstrings.append(','.join([ str(v) for v in values ]))

    return (tuple(retstrings), remains)


def ExecuteProcInBlocks(proc, **kwargs):
    """
    This function is converting lists in the kwargs to a comma seperated list
    and parsed along to the DB proc provided.
    It is also making sure the length of the strings never exceed 8000 characters,
    and if it does it is split onto multiple calls to the same proc.
    Notice this only works if the arguments are specified as kwargs!
    """
    nonListArgs = dict()
    listArgs = dict()
    listLength = 0
    listName = None
    for name, value in kwargs.iteritems():
        if isinstance(value, (list, tuple)):
            listArgs[name] = value
            listLength = len(value)
            listName = name
        else:
            nonListArgs[name] = value

    stringListArgs = defaultdict(list)
    lengthListArgs = defaultdict(int)
    for i in xrange(listLength):
        singleStringListArgs = dict()
        shouldFlush = False
        for name, l in listArgs.iteritems():
            singleStringListArgs[name] = str(l[i])
            if lengthListArgs[name] + len(singleStringListArgs[name]) >= 8000:
                shouldFlush = True

        if shouldFlush:
            readyKwargs = dict()
            readyKwargs.update(nonListArgs)
            for name, value in stringListArgs.iteritems():
                readyKwargs[name] = ','.join(value)

            proc(**readyKwargs)
            stringListArgs = defaultdict(list)
            lengthListArgs = defaultdict(int)
        for name, value in singleStringListArgs.iteritems():
            stringListArgs[name].append(value)
            lengthListArgs[name] += len(value) + 1

    if listName is not None and len(stringListArgs[listName]) > 0:
        readyKwargs = dict()
        readyKwargs.update(nonListArgs)
        for name, value in stringListArgs.iteritems():
            readyKwargs[name] = ','.join(value)

        proc(**readyKwargs)


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('dbutil', locals())
