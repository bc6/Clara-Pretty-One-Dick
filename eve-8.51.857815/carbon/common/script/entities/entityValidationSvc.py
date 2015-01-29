#Embedded file name: carbon/common/script/entities\entityValidationSvc.py
from carbon.common.script.cef.baseComponentView import BaseComponentView
import log
import service

class ValidationMessage(object):
    __guid__ = 'cef.ValidationMessage'
    VALID_RECIPE_DESCRIPTION = 'Recipe is valid.'

    def __init__(self, name = None, subPrefix = '  '):
        """
        Parameters
          name:        provides a header for all messages under this group.
          subPrefix:   allows you to alter the prefix for lines attached to sub-messages  (only used if name is provided)
        """
        self.messages = []
        self.isValid = True
        self.name = name
        self.subPrefix = subPrefix

    def AddMessage(self, message):
        """
        Add a string message, or a sub-ValidationMessage to this message.
        """
        if isinstance(message, str):
            self.isValid = False
        elif not message.IsValid():
            self.isValid = False
        self.messages.append(message)

    def IsValid(self):
        return self.isValid

    def GetReport(self):
        """
        Get a text report of all errors reported in this message.
        """
        if self.IsValid():
            return self.VALID_RECIPE_DESCRIPTION
        reportText = ''
        for message in self.messages:
            if isinstance(message, str):
                reportText += message
                reportText += '\n'
            elif not message.IsValid():
                reportText += message.GetReport()
                reportText += '\n'

        reportText = reportText.strip()
        if self.name is not None:
            reportText = self._AddSubPrefix(reportText)
            reportText = self.name + '\n' + reportText
        return reportText

    def _AddSubPrefix(self, textBlock):
        finishedText = textBlock.replace('\n', '\n' + self.subPrefix)
        finishedText = self.subPrefix + finishedText
        return finishedText


class EntityValidationSvc(service.Service):
    __guid__ = 'svc.entityValidationSvc'
    __dependencies__ = ['entityRecipeSvc']

    def Validate(self, recipeID):
        """
        Based on parentType, call the appropriate type-specific validation.
        """
        recipeDict = self.entityRecipeSvc.GetRecipe(recipeID)
        return self._ValidateRecipeDictionary(recipeID, recipeDict)

    def _ValidateRecipeDictionary(self, recipeID, recipeDict):
        """
        Return some basic validation information about this recipeDict.
        """
        result = ValidationMessage()
        self._ValidateEachComponent(result, recipeID, recipeDict)
        return result

    def _ValidateEachComponent(self, result, recipeID, recipeDict):
        """
        Iterate over every component and do the validation for each.
        Add any validation messages to result.
        """
        perComponentValidationFuncs = [self._ValidateComponentViewIsDefined,
         self._ValidateComponentSpawnInputs,
         self._ValidateComponentDependencies,
         self._ValidateCustomComponentInfo]
        for componentID in recipeDict:
            componentView = BaseComponentView.GetComponentViewByID(componentID)
            componentResult = ValidationMessage(name=self._GetComponentName(componentView, componentID))
            for validationFunc in perComponentValidationFuncs:
                try:
                    canContinue = validationFunc(componentResult, recipeID, recipeDict, componentView, componentID)
                except Exception as e:
                    self.LogError('An error occurred while running validation for component "%s" at recipeID=%s' % (componentView.__COMPONENT_DISPLAY_NAME__, recipeID))
                    log.LogException(e)
                    componentResult.AddMessage('An error occurred while running validation for this component')
                    canContinue = True

                if not canContinue:
                    break

            result.AddMessage(componentResult)

    def _GetComponentName(self, componentView, componentID):
        if componentView is not None:
            return componentView.__COMPONENT_DISPLAY_NAME__
        return '<Invalid Component %s>' % componentID

    def _ValidateComponentViewIsDefined(self, result, recipeID, recipeDict, componentView, componentID):
        """
        Determine that the component attached to this entity actually exists.
        """
        if componentView is None:
            result.AddMessage('Component is not valid: %s' % componentID)
        return componentView is not None

    def _ValidateComponentSpawnInputs(self, result, recipeID, recipeDict, componentView, componentID):
        """
        Validate that the spawn-level inputs only exist on spawns.
        Add any validation messages to result.
        """
        spawnInputs = set()
        missingInputs = set()
        componentRecipe = recipeDict[componentID]
        spawnInitValueNameTuples = componentView.GetInputs(groupFilter=componentView.ALL_SPAWN)
        for initValueNameTuple in spawnInitValueNameTuples:
            for initialValueName in initValueNameTuple:
                if initialValueName in componentRecipe:
                    spawnInputs.add(initValueNameTuple)
                else:
                    missingInputs.add(initValueNameTuple)

        isSpawn = recipeID in cfg.entitySpawnsByRecipeID
        if isSpawn and len(missingInputs) == 0:
            return True
        if not isSpawn and len(spawnInputs) == 0:
            return True
        if isSpawn:
            for initValueNameTuple in missingInputs:
                result.AddMessage('Missing input: %s' % initValueNameTuple)

        if not isSpawn:
            for initValueNameTuple in spawnInputs:
                result.AddMessage('Spawn input on non-spawn: %s' % initValueNameTuple)

        return True

    def _ValidateComponentDependencies(self, result, recipeID, recipeDict, componentView, componentID):
        """
        Verify that each component's necessary dependencies exist.
        """
        dependentComponentIDs = componentView.GetDependencies()
        for otherComponentID in dependentComponentIDs:
            otherComponentView = BaseComponentView.GetComponentViewByID(otherComponentID)
            if otherComponentView is None:
                result.AddMessage('Contact Programmer: Invalid dependent component: %s' % otherComponentID)
                continue
            if otherComponentID not in recipeDict:
                result.AddMessage('Missing component: %s' % otherComponentView.__COMPONENT_DISPLAY_NAME__)

        return True

    def _ValidateCustomComponentInfo(self, result, recipeID, recipeDict, componentView, componentID):
        """
        Call the custom per-component validation logic.
        """
        return componentView.ValidateComponent(result, recipeID, recipeDict)
