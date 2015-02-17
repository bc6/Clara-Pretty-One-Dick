#Embedded file name: carbon/common/script/util\callback.py


class Callback(object):
    __guid__ = 'util.Callback'

    def __init__(self, func):
        self.func = func
        self.instance = []
        self.fixedArgs = []
        self.fixedKWArgs = {}

    def Using(self, instance):
        self.instance = [instance]
        return self

    def WithParams(self, *args, **kwargs):
        self.fixedArgs.extend(args)
        self.fixedKWArgs.update(kwargs)
        return self

    def DoCall(self, *extraArgs, **extraKWArgs):
        args = list(self.instance)
        args.extend(self.fixedArgs)
        args.extend(extraArgs)
        kwargs = dict(self.fixedKWArgs)
        kwargs.update(extraKWArgs)
        return self.func(*args, **kwargs)

    def __call__(self, *extraArgs, **extraKWArgs):
        return self.DoCall(*extraArgs, **extraKWArgs)
