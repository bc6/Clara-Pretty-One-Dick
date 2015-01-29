#Embedded file name: eve/common/script/entities\inputComponents.py


class ContextMenuComponent:
    __guid__ = 'entities.ContextMenuComponent'

    def __init__(self):
        self.menuEntries = {}

    def AddMenuEntry(self, label, callback):
        """
        Extends the menu for a given entity.
        
        The callback should take the entityID as a parameter.
        """
        self.menuEntries[label] = callback
