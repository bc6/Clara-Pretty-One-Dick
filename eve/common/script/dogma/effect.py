#Embedded file name: eve/common/script/dogma\effect.py


class Effect:
    __guid__ = 'dogmaXP.Effect'
    isPythonEffect = True
    __modifier_only__ = False
    __modifies_character__ = False
    __modifies_ship__ = False

    def RestrictedStop(self, *args):
        pass

    def PreStartChecks(self, *args):
        """
            These are the custom checks that have to be made before the toll for
            starting the effect is taken.
        """
        pass

    def StartChecks(self, *args):
        pass

    def Start(self, *args):
        pass

    def Stop(self, *args):
        pass
