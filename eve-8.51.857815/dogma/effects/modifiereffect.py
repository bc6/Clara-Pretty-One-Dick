#Embedded file name: dogma/effects\modifiereffect.py
from dogma.effects import Effect

class ModifierEffect(Effect):
    __modifier_only__ = True

    def __init__(self, modifiers):
        self.isPythonEffect = False
        self.__modifies_ship__ = any((m.IsShipModifier() for m in modifiers))
        self.__modifies_character__ = any((m.IsCharModifier() for m in modifiers))
        self.modifiers = modifiers

    def Start(self, *args):
        for modifier in self.modifiers:
            modifier.Start(*args)

    def Stop(self, *args):
        for modifier in self.modifiers:
            modifier.Stop(*args)

    RestrictedStop = Stop
