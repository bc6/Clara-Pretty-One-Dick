#Embedded file name: machonethelpers\argchecker.py
import functools

class ValidateArgTypes(object):
    """
        Decorates a function and allows you to specify types of variables you'd expect them to be.
        It then casts them to the desired type
    """

    def __init__(self, **argTypes):
        self.argTypes = argTypes

    def __call__(self, func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            newArgs = list(args[:])
            newKwargs = kwargs.copy()
            for argName, typeCast in self.argTypes.iteritems():
                if argName in newKwargs:
                    newKwargs[argName] = self._Cast(typeCast, newKwargs[argName])
                else:
                    try:
                        idx = func.func_code.co_varnames.index(argName)
                    except ValueError:
                        raise ValidateArgTypeException('CheckArgs failed because "%s" is not one of the arguments of "%s"' % (argName, func.func_name))

                    newArgs[idx] = self._Cast(typeCast, newArgs[idx])

            return func(*newArgs, **newKwargs)

        return wrapper

    def _Cast(self, typeCast, value):
        try:
            return typeCast(value)
        except ValueError:
            raise ValidateArgTypeException('CheckArgs failed Was expecting %s but got "%s" of type %s' % (typeCast, value, type(value)))


class ValidateArgTypeException(RuntimeError):
    pass
