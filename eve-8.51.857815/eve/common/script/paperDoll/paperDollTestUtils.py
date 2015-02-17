#Embedded file name: eve/common/script/paperDoll\paperDollTestUtils.py
import blue
import random
import eve.common.script.paperDoll.paperDollDefinitions as pdDef
import eve.common.script.paperDoll.paperDollCommonFunctions as pdCf

class RandomModifierManager(object):
    """
    Used to test randomly removing and adding modifiers to a doll that is wrapped in a 
    PaperDollCharacter class
    """
    __guid__ = 'paperDoll.RandomModifierMananger'

    def __init__(self, pdc):
        self.pdc = pdc
        self.modifiers = [ modifier for modifier in self.pdc.doll.buildDataManager.GetSortedModifiers() if modifier.categorie != pdDef.DOLL_PARTS.HEAD ]

    def ActOnRandomModifier(self, fun, candidates):
        """
        Calls fun(random_modifier) and updates the doll
        """
        limit = len(candidates)
        if limit > 0:
            ridx = random.randint(0, limit) - 1
            modifier = candidates[ridx]
            fun(modifier)
            print 'Modifier chosen is %s' % modifier.name
            self.pdc.doll.Update(self.pdc.factory, self.pdc.avatar)
            while self.pdc.doll.busyUpdating:
                pdCf.Yield()

        else:
            raise Exception('Candidates are empty!')

    def RandomRemover(self):
        """
        Removes a random modifier from the doll
        """
        currentModifiers = map(lambda x: x.name, self.pdc.doll.buildDataManager.GetSortedModifiers())
        candidates = [ modifier for modifier in self.modifiers if modifier.name in currentModifiers ]
        self.ActOnRandomModifier(lambda x: self.pdc.doll.RemoveResource(x.GetResPath(), self.pdc.factory), candidates)

    def RandomDresser(self):
        """
        Adds a random modifier from modifiers to the doll.
        """
        currentModifiers = map(lambda x: x.name, self.pdc.doll.buildDataManager.GetSortedModifiers())
        candidates = [ modifier for modifier in self.modifiers if modifier.name not in currentModifiers ]
        self.ActOnRandomModifier(lambda x: self.pdc.doll.AddResource(x.GetResPath(), 1.0, self.pdc.factory), candidates)

    def UndressDress(self):
        blue.synchro.SleepWallclock(1000)
        removedCount = 0
        while removedCount < len(self.modifiers):
            print 'Removing random modifier'
            self.RandomRemover()
            removedCount += 1

        while removedCount > 0:
            print 'Adding random modifier'
            self.RandomDresser()
            removedCount -= 1

        print 'Done!'
