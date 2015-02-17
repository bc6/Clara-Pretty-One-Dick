#Embedded file name: thinmock.py
"""Mock objects for masquerading as modules and other objects for the purpose of 
unit tests.  Unit tests for this module are contained in mocktest.py.  See that
file for usage notes and other information.

Note: if you edit this file you MUST add unit tests to mocktest.py, both to
maintain full coverage, and to ensure that the unit tests in mocktest.py are
re-run to test for regressions here. 
"""
import weakref
import types
globalReference = None
neverMockList = ['weakref',
 'types',
 '__builtins__',
 'mock']

def _MockSetAttrHelper(parent, attrName, attrRef):
    """
    Whenever possible, we want to bypass any magic that may be built into in the parent class setattr.
    Unfortunately, there's no shared __setattr__ function that applies to all base types.
    The various types we have to deal with are:
    (blue types), type, types.InstanceType, types.ClassType (old/default class types), and object (new class types) 
    There may be more, and we'll need to update this switch as more types come in.
    """
    if isinstance(parent, type):
        type.__setattr__(parent, attrName, attrRef)
    elif isinstance(parent, types.ClassType):
        types.ClassType.__setattr__(parent, attrName, attrRef)
    elif isinstance(parent, types.InstanceType):
        types.InstanceType.__setattr__(parent, attrName, attrRef)
    elif isinstance(parent, object):
        object.__setattr__(parent, attrName, attrRef)
    else:
        print ' *** WARNING: Unknown type being mocked:', type(parent), ':', parent
        setattr(parent, attrName, attrRef)


class ThinMock(object):
    """Mock object for emulating externals in unit tests.
    
       The mock object allows arbitrary attribute references and method calls, and logs
       them as appropriate (see the _Log method for current details).
    
       The calling code may assign attributes or methods of the mock object, and those
       assignments will be used when those attributes or methods are referenced later.
    
       The mock object does not actually insert anything into it's own __dict__, but
       rather keeps track of all attributes it is pretending to have in an explicit
       "attributes" dictionary.
    
       The mock object also keeps an attribute named "callableObject".  If this
       attribute is not none, then it must be a callable object.  In that case,
       whenever this mock object is invoked as a method call, the call is wrapped
       in order to provide logging services, but the assigned callable object is
       executed, and its return value is used.
    """

    def __init__(self, mockName = 'unnamed_Mock', insertAsGlobal = False, autoAddAttributes = True):
        """Initialize internals of the mock object.  By default, the mock remains local,
           however setting the insertAsGlobal flag to True causes a weak reference to
           the mock object to be inserted into the global namespace (this allows us to
           access it globally but still lets it follow predictable scoping and
           destruction).  If this would overwrite an existing entry in the globals
           dictionary, a reference to the old value is saved and will be restored with
           this mock object is destroyed.
           
           Note that if the name of the object being mocked is "blue", and the
           insertAsGlobal flag is set to True, then under the new global blue mock
           object, the methods blue.os.GetWallclockTime, blue.os.GetWallclockTimeNow,
           blue.os.GetSimTime, blue.pyos.synchro.Sleep, blue.pyos.synchro.SleepUntil,
           and blue.pyos.synchro.Yield are automatically mocked.  See the unit tests
           in mocktest.py for use cases of those methods.
        """
        global globalReference
        if '*alreadyInited' in self.__dict__:
            return
        if insertAsGlobal and mockName in neverMockList:
            raise RuntimeError, 'The module "%s" can never be mocked.' % mockName
        object.__setattr__(self, '*name', mockName)
        object.__setattr__(self, '*attributes', {})
        object.__setattr__(self, '*callableObject', None)
        object.__setattr__(self, '*insertAsGlobal', insertAsGlobal)
        object.__setattr__(self, '*globalReplacements', {})
        object.__setattr__(self, '*oldParent', None)
        object.__setattr__(self, '*oldAttribute', None)
        object.__setattr__(self, '*autoAddAttributes', autoAddAttributes)
        object.__setattr__(self, '*alreadyInited', True)
        if insertAsGlobal:

            def InjectGlobalMock(globalReference, mockName, refKey):
                oldReference = globalReference.get(mockName, None)
                if isinstance(oldReference, ThinMock):
                    object.__setattr__(self, '*insertAsGlobal', False)
                    raise RuntimeError, 'The module "' + mockName + '" is already mocked!  You cannot mock it again!'
                object.__setattr__(self, refKey, oldReference)
                globalReference[mockName] = weakref.proxy(self)

            if globalReference is not None:
                InjectGlobalMock(globalReference, mockName, '*oldReference')
                if '__oldglobals__' in globalReference:
                    InjectGlobalMock(globalReference['__oldglobals__'], mockName, '*oldReference2')
        if insertAsGlobal and mockName == 'blue':
            self.pyos.synchro.Sleep = _Sleep
            self.pyos.synchro.SleepSim = _Sleep
            self.pyos.synchro.SleepWallclock = _Sleep
            self.pyos.synchro.SleepUntil = SetTime
            self.pyos.synchro.SleepUntilSim = SetTime
            self.pyos.synchro.SleepUntilWallclock = SetTime
            self.pyos.synchro.Yield = _Yield
            self.os.GetTime = GetTime
            self.os.GetWallclockTime = GetTime
            self.os.GetWallclockTimeNow = GetTime
            self.os.GetSimTime = GetTime
            SetTime(0)
            SetYieldDuration(1)

    def __del__(self):
        """If the mock object is top level and has saved
           a reference to an existing global object (see
           __init__ for details on that process) then
           make sure we restore the old reference here.
        """

        def GetAttrHelper(obj, name, default):
            if name in object.__getattribute__(obj, '__dict__'):
                return object.__getattribute__(obj, name)
            else:
                return default

        insertAsGlobal = GetAttrHelper(self, '*insertAsGlobal', False)
        if insertAsGlobal:

            def RetractGlobalMock(globalReference, mockName, refKey):
                oldReference = GetAttrHelper(self, refKey, None)
                if oldReference is not None:
                    globalReference[mockName] = oldReference
                else:
                    del globalReference[mockName]

            mockName = GetAttrHelper(self, '*name', '')
            if globalReference is not None:
                RetractGlobalMock(globalReference, mockName, '*oldReference')
                if '__oldglobals__' in globalReference:
                    RetractGlobalMock(globalReference['__oldglobals__'], mockName, '*oldReference2')
        globalReplacements = GetAttrHelper(self, '*globalReplacements', {})
        for name in globalReplacements:
            globalReference[name] = globalReplacements[name]

    def __getattr__(self, name):
        """Note, this will only be called if the attribute
        does not really exist.  Since the current revision
        of the class doesn't let any new attributes be
        created, this should be every time.
        
        For safety sake, and as a holdover from previous
        implementation, all internal code should use the
        base class object.__getattribute__ method to
        retrieve attribute values."""
        fullName = object.__getattribute__(self, '*name') + '.' + name
        attributes = object.__getattribute__(self, '*attributes')
        if name in attributes:
            return attributes[name]
        if object.__getattribute__(self, '*autoAddAttributes'):
            child = ThinMock(fullName, insertAsGlobal=False)
            self._MockAttribute(name, child)
            return child
        raise AttributeError, "mock object '%s' does not have attribute '%s'" % (object.__getattribute__(self, '*name'), name)

    def __call__(self, *args, **kw):
        """If a callable object is assigned to this mock, then
           call it and report the return value.  Otherwise, return a
           new Mock object.  In any case, log the mocked call.
        """
        callableObject = object.__getattribute__(self, '*callableObject')
        if callableObject is not None:
            if type(callableObject) == types.UnboundMethodType:
                return callableObject(self, *args, **kw)
            else:
                return callableObject(*args, **kw)
        else:
            name = 'mockreturn<%s>' % id(self)
            return ThinMock(name)

    def __setattr__(self, name, value):
        """Automatically attempt to mock a new attribute or method
           when calling code uses assignment syntax.
           
           If the external code tries to mock certain important internal (real)
           attributes, weird behavior will result.  Guard against this situation
           here, before anything is really accessed.
        """
        if callable(value) and not isinstance(value, ThinMock):
            object.__getattribute__(self, '_MockMethod')(name, value)
        else:
            object.__getattribute__(self, '_MockAttribute')(name, value)

    def __getitem__(self, key):
        """Allow mock objects to pretend to be arrays or dictionaries by defining
        special functionality for the [] operator.  Values are stored in an
        internal dictionary.  If one exists, it is returned, otherwise, a new
        mock object is put in that place and returned."""
        if not object.__getattribute__(self, 'HasMockValue')():
            object.__getattribute__(self, 'SetMockValue')({})
        contents = object.__getattribute__(self, '*mockValue')
        try:
            result = contents[key]
        except KeyError:
            name = 'mockcontents[' + repr(key) + ']_' + object.__getattribute__(self, '*name')
            result = ThinMock(name)
            contents[key] = result

        return result

    def __setitem__(self, key, value):
        """Allow mock objects to pretend to be lists or dictionaries by defining
        special functionality for the [] operator.  Values are stored in an
        internal dictionary"""
        if not object.__getattribute__(self, 'HasMockValue')():
            object.__getattribute__(self, 'SetMockValue')({})
        object.__getattribute__(self, '*mockValue')[key] = value

    def __delitem__(self, key):
        """Allow mock objects emulating dictionaries to delete values.
        
        Note: if a value does not exist in the internal dictionary of values,
        this will silently return without doing anything."""
        if not object.__getattribute__(self, 'HasMockValue')():
            return
        contents = object.__getattribute__(self, '*mockValue')
        if isinstance(contents, ThinMock):
            raise TypeError, 'This mock object is mocking a mock object.  This is wrong.'
        try:
            del contents[key]
        except KeyError:
            pass

    def __nonzero__(self):
        if not object.__getattribute__(self, 'HasMockValue')():
            return True
        value = object.__getattribute__(self, '*mockValue')
        if value:
            return True
        return False

    def __len__(self):
        """- If a mock object does not have a mock value, return a length of zero.
        - If it does have a mock value, return the length of the mock value (note
          that this may cause an exception if the mock value does not support
          len()--this is by design).
        - If a mock object is masquerading as a dictionary, return the length of
          that dictionary (which is essentially a mock value)."""
        if not object.__getattribute__(self, 'HasMockValue')():
            return 0
        return len(object.__getattribute__(self, '*mockValue'))

    def __iter__(self):
        """Define an iterator for mock objects that iterates over contents that
        have been set (if any), so that we don't iterate endlessly returning
        Mock objects (as would otherwise happen with the __getitem__ that
        just keeps going."""
        if object.__getattribute__(self, 'HasMockValue')():
            return iter(object.__getattribute__(self, '*mockValue'))
        else:
            return iter({})

    def __eq__(self, other):
        """Equality operator.  If we have a mock value, use that for comparison
           and return True or False.  If this object does not have a mock value,
           raise a TypeError.
        """
        if '*mockValue' in object.__getattribute__(self, '__dict__'):
            if isinstance(other, ThinMock):
                if '*mockValue' in object.__getattribute__(other, '__dict__'):
                    return object.__getattribute__(self, '*mockValue') == object.__getattribute__(other, '*mockValue')
                raise TypeError, 'Right operand Mock object cannot be compared unless it has a mock value.'
            else:
                return object.__getattribute__(self, '*mockValue') == other
        else:
            raise TypeError, '"%s" Mock object cannot be compared unless it has a mock value.' % object.__getattribute__(self, '*name')

    def __gt__(self, other):
        """Greater than operator.  See __eq__ for other details."""
        if '*mockValue' in object.__getattribute__(self, '__dict__'):
            if isinstance(other, ThinMock):
                if '*mockValue' in object.__getattribute__(other, '__dict__'):
                    return object.__getattribute__(self, '*mockValue') > object.__getattribute__(other, '*mockValue')
                raise TypeError, 'Right operand Mock object cannot be compared unless it has a mock value.'
            else:
                return object.__getattribute__(self, '*mockValue') > other
        else:
            raise TypeError, 'Left operand Mock object cannot be compared unless it has a mock value.'

    def __ne__(self, other):
        """Not equal operator.  See __eq__ for details."""
        eq = object.__getattribute__(self, '__eq__')(other)
        return not eq

    def __ge__(self, other):
        """Greater than or equal operator.  See __eq__ for details."""
        gt = object.__getattribute__(self, '__gt__')(other)
        eq = object.__getattribute__(self, '__eq__')(other)
        return gt or eq

    def __lt__(self, other):
        """Less than operator.  See __eq__ for details."""
        ge = object.__getattribute__(self, '__ge__')(other)
        return not ge

    def __le__(self, other):
        """Less than or equal operator.  See __eq__ for details."""
        gt = object.__getattribute__(self, '__gt__')(other)
        return not gt

    def __neg__(self):
        """Returns a mock object and if we have a value return a mock object with the value negated"""
        name = 'negMockReturn<%s>' % id(self)
        mockReturn = ThinMock(name)
        if '*mockValue' in object.__getattribute__(self, '__dict__'):
            mockReturn.SetMockValue(-object.__getattribute__(self, '*mockValue'))
        return mockReturn

    def __str__(self):
        """Use the mock value if we have one, otherwise let the parent
           str method handle it.
        """
        if '*mockValue' in object.__getattribute__(self, '__dict__'):
            return str(object.__getattribute__(self, '*mockValue'))
        else:
            return object.__str__(self)

    def _MockAttribute(self, name, value):
        """Mock an attribute.
           This function should no longer be called by external code.
        """
        object.__getattribute__(self, '*attributes')[name] = value

    def _MockMethod(self, name, callableObject):
        """Mock the given name to the given callable object.
           This function should no longer be called by external code.
        
           Also, look through the globals() dictionary to see if
           there are any references to the method being mocked.
           If so, mock those too.
        """
        fullName = object.__getattribute__(self, '*name') + '.' + name
        child = ThinMock(fullName, insertAsGlobal=False)
        object.__setattr__(child, '*callableObject', callableObject)
        object.__getattribute__(self, '_MockAttribute')(name, child)
        if globalReference is not None:
            pathList = fullName.split('.')
            currentObject = ByPass(pathList[0])
            if currentObject is not None and not isinstance(currentObject, ThinMock):
                for name in pathList[1:]:
                    currentObject = getattr(currentObject, name, None)
                    if currentObject is None:
                        break

                for name, obj in globalReference.items():
                    if isinstance(obj, ThinMock):
                        continue
                    if obj == currentObject:
                        object.__getattribute__(self, '*globalReplacements')[name] = currentObject
                        globalReference[name] = child

    def Revert(self):
        """This function is for when this mock was assigned to mock an
           existing attribute (with the ReplaceAttribute method) and the
           user wants to restore the original attribute.
           
           If this mock was created in any other way, calling this method
           is an error and will raise an exception.
        """
        oldParent = object.__getattribute__(self, '*oldParent')
        oldAttribute = object.__getattribute__(self, '*oldAttribute')
        name = object.__getattribute__(self, '*name')
        if oldParent is None:
            raise RuntimeError, 'Only mocks created with ReplaceAttribute can be reverted.'
        else:
            if IsStaticMethod(oldAttribute) and type(oldParent) in [types.ClassType, type]:
                oldAttribute = staticmethod(oldAttribute)
            _MockSetAttrHelper(oldParent, name, oldAttribute)
            for index in range(len(_replacedAttributes))[::-1]:
                entry = _replacedAttributes[index]
                try:
                    if entry[0]() is oldParent and entry[1] == name:
                        _replacedAttributes.pop(index)
                        break
                except ReferenceError:
                    _replacedAttributes.pop(index)

    def SetCallable(self, callableObject):
        """Set this mock object to be callable with the given callable
           object as the method to be executed.
           
           Passing None as the callableObject will cause the mock object
           to no longer be callable.
        """
        object.__setattr__(self, '*callableObject', callableObject)

    def SetMockValue(self, value):
        """Set this mock object to pretend that it has the given value
           whenever any comparison operator is applied to it, or when
           a string representation is asked for.
           
           None is a valid value.  To remove the mock value, external
           code must use the RemoveMockValue method, below.
           
           Note that a mock value for this mock object may be set by this
           function, or it may be set by __getitem__ or other methods
           related to emulating a list or dictionary.
        """
        object.__setattr__(self, '*mockValue', value)

    def RemoveMockValue(self):
        """Remove a mock value that was previously set.  See SetMockValue
           for details on how those values are used.
        """
        if '*mockValue' in object.__getattribute__(self, '__dict__'):
            object.__delattr__(self, '*mockValue')

    def HasMockValue(self):
        """Return True if a mock value has been set for this mock object,
           or False otherwise.
        """
        return '*mockValue' in object.__getattribute__(self, '__dict__')


def ByPass(moduleName):
    """Used to bypass the mocking system and access functions
       or objects from the original modules.  The argument here
       is the name of the module for which we want to bypass
       the mock and access it directly.  The return value is
       a reference to that module.
    
       Example: if the module blue were mocked, but you wanted access to
       the real GetWallclockTime method, you would do it like this:
       mock.ByPass('blue').os.GetWallclockTime()
    """
    module = globalReference.get(moduleName)
    if module is None:
        return
    if not isinstance(module, ThinMock):
        raise RuntimeError, 'Cannot bypass a non-mock object!'
    else:
        return getattr(module, '*oldReference')


_replacedAttributes = []

def ReplaceAttribute(parent, attributeName, mockValue = None):
    """Replace the named attribute in the given parent object with a mock object.
       Save a reference to the parent and to the old attribute inside the mock object,
       so the old attribute can be restored on command.
       
       If mockValue is specified, and it is a callable object, make the new mock
       object callable, and set that as its internal callableObject.  If mockValue
       is specified and it is NOT callable, set the mock value of the new mock object.
       
       Note that None cannot be supplied as a mock value, as this function interprets
       that as having supplied no value.  If external code wants the mock object to
       have None as it's mock value, that must be done explicitly by calling the
       SetMockValue method on the mock object after it is returned.
    """
    oldAttribute = getattr(parent, attributeName)
    if isinstance(parent, ThinMock):
        raise TypeError, 'To mock methods or attributes on a mock object, assign to them directly.'
    if isinstance(oldAttribute, ThinMock):
        RevertAttribute(parent, attributeName)
        oldAttribute = getattr(parent, attributeName)
    newMock = ThinMock(attributeName, insertAsGlobal=False)
    object.__setattr__(newMock, '*oldParent', parent)
    object.__setattr__(newMock, '*oldAttribute', oldAttribute)
    _MockSetAttrHelper(parent, attributeName, newMock)
    if mockValue is not None:
        if callable(mockValue) and not isinstance(mockValue, ThinMock):
            newMock.SetCallable(mockValue)
        else:
            newMock.SetMockValue(mockValue)
    if type(parent) in (types.ModuleType, types.ClassType):
        reference = lambda *args, **kwargs: parent
    else:
        reference = weakref.ref(parent)
    _replacedAttributes.append((reference, attributeName))
    return newMock


def ReplaceMethod(parent, methodName, callableObject):
    """As ReplaceAttribute, except additionally set the new mock object to
       be callable, and used the given callableObject.
    """
    newMock = ReplaceAttribute(parent, methodName)
    object.__setattr__(newMock, '*callableObject', callableObject)
    return newMock


def RevertAttribute(parent, attributeName):
    """This method just simplifies the syntax for external code
       reverting a mocked attribute on an existing object.
    """
    oldMock = getattr(parent, attributeName)
    if hasattr(oldMock, 'Revert'):
        oldMock.Revert()
    else:
        errmsg = 'The mock framework tried to revert an an attribute "'
        errmsg += attributeName + '" on object ' + str(parent)
        errmsg += ', but that attribute is not currently mocked!'
        raise AttributeError, errmsg


def RevertMethod(parent, methodName):
    """Note: the method for reverting attributes and methods is
       exactly the same, since methods are attributes.
    """
    RevertAttribute(parent, methodName)


_builtinSaved = {}

def _ReplaceBuiltin(name, newFunction):
    """Replace the named builtin function with the given callable object.
       
       This can be very dangerous and should never really be necessary.
       The functionality is kept here since it is used internally (on the
       __import__ builtin), but it is no longer exposed externally and
       should not be used in unit tests.
    """
    builtins = globalReference.get('__builtins__')
    newMock = ThinMock(name)
    object.__setattr__(newMock, '*callableObject', newFunction)
    if name not in _builtinSaved:
        _builtinSaved[name] = builtins[name]
    builtins[name] = newMock


def _RevertBuiltin(name):
    """After a builtin has been mocked with the ReplaceBuiltin, you can
       restore the original builtin with this method.
    """
    builtins = globalReference.get('__builtins__')
    if name not in _builtinSaved:
        raise KeyError, 'You cannot revert a builtin until after you replace it!.'
    else:
        builtins[name] = _builtinSaved[name]
        del _builtinSaved[name]


def _RevertAllBuiltins():
    """Restore all builtins to their original values."""
    for name in _builtinSaved.keys():
        _RevertBuiltin(name)


def SetGlobalReference(reference):
    """Store the current global reference that we are working with.
       This is important because we want to mock in the "global"
       namespace, but each module has its own "global" namespace.
    """
    global globalReference
    globalReference = reference


_mockInternalTime = 0

def SetTime(timeValue):
    """Set the mock value in blue.os.Get*Time functions"""
    global _mockInternalTime
    blueReference = globalReference.get('blue')
    if not isinstance(blueReference, ThinMock):
        raise RuntimeError, 'blue module must be mocked to use mock.SetTime'
    else:
        _mockInternalTime = timeValue


def _Sleep(timeValue):
    """This function will be automatically bound to the blue.pyos.synchro.Sleep
    method whenever the blue module is mocked.  It increments the internal
    mock time value by the amount passed into the function."""
    blueReference = globalReference.get('blue')
    if not isinstance(blueReference, ThinMock):
        raise RuntimeError, 'blue module must be mocked to use mock._Sleep'
    else:
        newTime = GetTime() + timeValue
        SetTime(newTime)


_mockYieldDuration = 1

def _Yield():
    """This function will be automatically bound to the blue.pyos.synchro.Yield
    method whenever the blue module is mocked.  It increments the internal
    mock time value by an amount previously specified with SetYieldDuration."""
    global _mockYieldDuration
    _Sleep(_mockYieldDuration)


def SetYieldDuration(timeValue):
    """Set the value to increment the mock current time when Yield is called."""
    global _mockYieldDuration
    blueReference = globalReference.get('blue')
    if not isinstance(blueReference, ThinMock):
        raise RuntimeError, 'blue module must be mocked to use mock.SetYieldDuration'
    else:
        _mockYieldDuration = timeValue


def GetTime():
    """Get the mock time value."""
    return _mockInternalTime


_oldImport = __builtins__['__import__']

def _DoNotImport(moduleName, *args, **kw):
    """EVE code should not be doing local imports, but some stdlib python
       code relies on it, so we cannot ever disable imports completely.
       
       This method is used to override the default function for the builtin
       mock objects since they could potentially overwrite the mocks
       mid-test.
    """
    module = globalReference.get(moduleName)
    if isinstance(module, ThinMock):
        raise RuntimeError, 'Attempted to import module [' + moduleName + ']: You may not import modules during a unit test!'
    else:
        return _oldImport(moduleName, *args, **kw)


def IsStaticMethod(func):
    """
    There doesn't seem to be a good way to differentiate between
    a static method an a plain ol' function.  We'll just say that
    anything that fits the proper signature is a static method, and
    it's up to the calling code to determine if that function is
    actually a member of the class.
    """
    return type(func) == types.FunctionType
