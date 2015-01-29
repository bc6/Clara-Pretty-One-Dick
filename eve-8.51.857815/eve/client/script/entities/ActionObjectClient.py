#Embedded file name: eve/client/script/entities\ActionObjectClient.py
import svc
import localization

class EveActionObjectClientSvc(svc.actionObjectClientSvc):
    """
    TODO: Move the UI specific code that is handled here to a UI class!
    """
    __guid__ = 'svc.eveActionObjectClientSvc'
    __replaceservice__ = 'actionObjectClientSvc'

    def SetupComponent(self, entity, component):
        """
            Gets called in order to setup a component. All other components can be referred to
        """
        infoComponent = entity.GetComponent('info')
        if infoComponent and not infoComponent.name and component in self.preservedStates:
            recipeRow = cfg.recipes.Get(self.preservedStates[component]['_recipeID'])
            infoComponent.name = recipeRow.recipeName
        svc.actionObjectClientSvc.SetupComponent(self, entity, component)

    def Run(self, *args):
        svc.actionObjectClientSvc.Run(self, *args)

    def GetActionNodeTranslatedText(self, actionID, fallbackText):
        """
            Do translation using localization for the eve side.
        """
        treeNodeNameID = cfg.treeNodes.Get(actionID).treeNodeNameID
        return localization.GetByMessageID(treeNodeNameID)
