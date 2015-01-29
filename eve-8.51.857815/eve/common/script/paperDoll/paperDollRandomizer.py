#Embedded file name: eve/common/script/paperDoll\paperDollRandomizer.py
"""
Base module for randomizing paperdolls
"""
import random
import itertools
from . import paperDollDefinitions as pdDef
from . import paperDollCommonFunctions as pdCf
from . import paperDollDataManagement as pdDm

class AbstractRandomizer(object):
    """
    Utility class for random selection
    """
    __guid__ = 'paperDoll.AbstractRandomizer'

    @staticmethod
    def SelectManyFromCollection(collection, minElems = None, maxElems = None):
        """
        Selects multiple unique elements at random from 'collection', which is assumed to be indexable.
        
        If 'minElems' is set to an integer value, at least that many elements will be selected, iif the collection is large enough.
        If 'minElems' is not set, it defaults to 0
        
        If 'maxElems' is set to an integer value, only that many elements will be selected at maximum,
        If 'maxElems' is not set, it defaults to the number of items in collection.
        
        Returns a list, either empty or populated with x elements selected from collection where x is a random number between ['minElems', 'maxElems']
        """
        if collection:
            cLen = len(collection)
            minElems = min(cLen, minElems or 0)
            maxElems = min(cLen, maxElems or cLen)
            elemsToChoose = random.randint(minElems, maxElems)
            return random.sample(collection, elemsToChoose)
        return []

    @staticmethod
    def SelectOneFromCollection(collection, oddsOfSelectingNone = None):
        """
        Selects 1 element at random from 'collection', which is assumed to be indexable.
        If 'oddsOfSelectingNone' is set, it should be a floating number in the range [0.0, 1.0].
        Returns a single element or None
        """
        if collection:
            oddsOfSelectingNone = oddsOfSelectingNone or 0.0
            oddsOfSelectingNone = min(oddsOfSelectingNone, 1.0)
            if random.random() >= oddsOfSelectingNone:
                return random.choice(collection)


class DollRandomizer(object):
    """
    Base class to generate a randomized paperdoll
    """
    __guid__ = 'paperDoll.DollRandomizer'
    dollCategories = property(lambda self: list(set(self.completeDollCategories) - set(self.defaultIgnoreCategories)))
    gender = property(fget=lambda self: self.GetGender(), fset=lambda self, x: self.setgender(x))

    def setgender(self, gender):
        self.__gender = gender

    options = property(fget=lambda self: self.GetOptions())
    blendshapeOptions = property(fget=lambda self: self.GetBlendshapeOptions())
    RESOURCE_OPTION = 'option'
    RESOURCE_TYPE = 'type'

    def __init__(self, modifierLoader):
        self.modifierLoader = modifierLoader
        self.categoriesThatMustHaveEntries = list(set([pdDef.DOLL_PARTS.HEAD,
         pdDef.BODY_CATEGORIES.SKINTONE,
         pdDef.BODY_CATEGORIES.TOPINNER,
         pdDef.BODY_CATEGORIES.BOTTOMINNER,
         pdDef.BODY_CATEGORIES.TOPMIDDLE,
         pdDef.BODY_CATEGORIES.BOTTOMOUTER,
         pdDef.BODY_CATEGORIES.FEET,
         pdDef.MAKEUP_EYEBROWS,
         pdDef.DOLL_PARTS.HAIR,
         pdDef.MAKEUP_EYES]))
        self.completeDollCategories = list(pdDef.DOLL_PARTS + pdDef.DOLL_EXTRA_PARTS + pdDef.HEAD_CATEGORIES + pdDef.HAIR_CATEGORIES + pdDef.BODY_CATEGORIES + pdDef.ACCESSORIES_CATEGORIES)
        self.completeDollCategories.extend([pdDef.MAKEUP_EYEBROWS, pdDef.MAKEUP_EYES])
        self.completeDollCategories = list(set(self.completeDollCategories))
        self.defaultIgnoreCategories = list(set(pdDef.BLENDSHAPE_CATEGORIES + (pdDef.DOLL_EXTRA_PARTS.DEPENDANTS,)))
        self.filterCategoriesForRandomization = []
        self.__gender = None
        self.__resources = None
        self.__blendshapeOptions = None
        self.__blendshapeLimits = {}
        self.weights = {}
        self.__pathsToRandomizeWeights = {}
        self.oddsOfSelectingNoneForCategory = {}

    def ListOptions(self, category):
        """
        Override or reroute this method if the options to be listed are game specific, i.e race/gender filtered.
        """
        return self.modifierLoader.ListOptions(self.gender, cat=category)

    def ListTypes(self, category):
        """
        Override or reroute this method if the options to be listed are game specific, i.e race/gender filtered.
        """
        return self.modifierLoader.ListTypes(self.gender, cat=category)

    def GetGender(self):
        """
        Returns a randomized and sets a gender if none has been set.
        """
        if not self.__gender:
            if random.randint(0, 1) == 0:
                self.__gender = pdDef.GENDER.FEMALE
            else:
                self.__gender = pdDef.GENDER.MALE
        return self.__gender

    def GetResources(self):
        """
        Returns a set of randomized resources for an entire doll based on the constraints set.
        If 'categoryFilter' is provided, it will only randomize and return options for that category.
        
        Returns a set of options that can then be added to a doll via AddRandomizedOptionsToDoll
        """
        if not self.__resources:
            catToResources = {}

            def ChooseResource(category, resourceList, isType):
                odds = 0.0 if category in self.categoriesThatMustHaveEntries else self.oddsOfSelectingNoneForCategory.get(category, 0.22)
                res = AbstractRandomizer.SelectOneFromCollection(resourceList, oddsOfSelectingNone=odds)
                if res:
                    resourceType = self.RESOURCE_TYPE if isType else self.RESOURCE_OPTION
                    catToResources[category] = [(resourceType, res)]
                    if category in self.__pathsToRandomizeWeights:
                        self.AddRandomizedWeightForOption(res, *self.__pathsToRandomizeWeights[category])

            catPath = ''
            for category in self.dollCategories:
                pdCf.BeFrameNice()
                if self.filterCategoriesForRandomization:
                    continueOut = True
                    if category in (pdDef.DOLL_PARTS.ACCESSORIES,
                     pdDef.HEAD_CATEGORIES.MAKEUP,
                     pdDef.BODY_CATEGORIES.TATTOO,
                     pdDef.BODY_CATEGORIES.SCARS):
                        for wCat in self.filterCategoriesForRandomization:
                            if category in wCat.split(pdDef.SEPERATOR_CHAR):
                                continueOut = False
                                break

                    else:
                        continueOut = category not in self.filterCategoriesForRandomization
                    if continueOut:
                        continue
                if category in (pdDef.DOLL_PARTS.ACCESSORIES,
                 pdDef.HEAD_CATEGORIES.MAKEUP,
                 pdDef.BODY_CATEGORIES.TATTOO,
                 pdDef.BODY_CATEGORIES.SCARS):
                    options = self.ListOptions(category)
                    for option in options:
                        subcategory = category + '/' + option
                        if not catPath or catPath and subcategory == catPath:
                            if self.filterCategoriesForRandomization:
                                if category in self.filterCategoriesForRandomization or subcategory in self.filterCategoriesForRandomization:
                                    if self.modifierLoader.CategoryHasTypes(subcategory):
                                        ChooseResource(subcategory, self.ListTypes(subcategory), True)
                                    else:
                                        ChooseResource(subcategory, self.ListOptions(subcategory), False)

                elif not catPath or catPath == category:
                    if self.modifierLoader.CategoryHasTypes(category) > 0:
                        ChooseResource(category, self.ListTypes(category), True)
                    else:
                        options = [ option for option in self.ListOptions(category) if 'nude' not in option ]
                        ChooseResource(category, options, False)

            self.__resources = catToResources
        return self.__resources

    def SetBlendshapeLimits(self, limitsResPath):
        """
        Sets the limits for blendshapes by reading a limitations file generated by the BlendshapeLimiting Editor
        """
        data = pdDm.ModifierLoader.LoadBlendshapeLimits(limitsResPath)
        if data and data.get('gender') == self.gender:
            limits = data['limits']
            for key in limits:
                self.__blendshapeLimits[key.lower()] = limits[key]

    def GetBlendshapeOptions(self):
        """
        Randomizes blendshape options. In order to limit the randomization, see SetBlendShapeLimits()
        """
        if not self.__blendshapeOptions:
            self.__blendshapeOptions = {}
            categories = pdDef.BLENDSHAPE_CATEGORIES - (pdDef.BLENDSHAPE_CATEGORIES.UTILITYSHAPES, pdDef.BLENDSHAPE_CATEGORIES.ARCHETYPES)
            for category in categories:
                pdCf.BeFrameNice()
                options = [ option for option in self.ListOptions(category) ]
                options = AbstractRandomizer.SelectManyFromCollection(options, minElems=8)
                pairToElem = {}
                for key, group in itertools.groupby(options, lambda x: x[:x.find('_')]):
                    elems = list(group)
                    if len(elems) > 0 and len(elems) < 2:
                        pairToElem[key] = elems[0]
                    else:
                        random.shuffle(elems)
                        for elem in elems:
                            for pair in pdDef.BLENDSHAPE_AXIS_PAIRS:
                                for pairElem in pair:
                                    if pairElem in elem:
                                        pairToElem[pair] = elem
                                        break

                options = pairToElem.values()
                self.__blendshapeOptions[category] = [ (self.RESOURCE_OPTION, option) for option in options ]
                for option in options:
                    lowerlimit, upperlimit = self.__blendshapeLimits.get(option, (0.0, 1.0))
                    self.AddRandomizedWeightForOption(option, lowerlimit, upperlimit)

        return self.__blendshapeOptions

    def AddCategoryForWhitelistRandomization(self, category, oddsOfSelectingNone = None):
        """
        Once this function is called, it will start whitelisting categories that GetOptions will return
        randomized options for
        """
        self.filterCategoriesForRandomization.append(category)
        if oddsOfSelectingNone is not None:
            self.oddsOfSelectingNoneForCategory[category] = oddsOfSelectingNone

    def AddPathForWeightRandomization(self, path, lowerlimit, upperlimit):
        """
        Call this function to specify that a given path should be randomized for weights in the
        range of [lowerlimit, upperlimit].
        It is an error to specify a lowerlimit of 0 or less and upperlimit above 1.0
        """
        if lowerlimit <= 0.0 or upperlimit > 1.0:
            raise ValueError('Limits are not within ]0.0, 1.0]')
        self.__pathsToRandomizeWeights[path] = (lowerlimit, upperlimit)

    def AddRandomizedWeightForOption(self, option, lowerlimit, upperlimit):
        self.weights[option] = lowerlimit + round((upperlimit - lowerlimit) * random.random(), 4)

    def GetColorVariations(self, modifier):
        """
        Subclass to implement game specific filters on color variations
        """
        return modifier.GetColorVariations()

    def GetVariations(self, modifier):
        """
        Subclass to implement game specific filters on variations
        """
        return modifier.GetVariations()

    def GetCategoryWeight(self, category):
        return self.weights.get(category, 1.0)

    def AddRandomizedResourcesToDoll(self, doll, randomizedResources):
        """
        Adds the options in the format returned via GetOptions to the given doll.
        Will attempt to randomly select variation and color variation if any exist, but it is also
        possible no variation at all will be set.
        """
        for category in randomizedResources:
            pdCf.BeFrameNice()
            for resType, res in randomizedResources[category]:
                if not res:
                    continue
                weight = self.weights.get(res, 1.0)
                if resType == self.RESOURCE_TYPE:
                    doll.AddItemType(self.modifierLoader, res, weight)
                else:
                    modifier = doll.AddResource(category + '/' + res, weight, self.modifierLoader)
                    variations = self.GetVariations(modifier)
                    colorVariations = self.GetColorVariations(modifier)
                    variation = AbstractRandomizer.SelectOneFromCollection(variations, oddsOfSelectingNone=0.3)
                    if variation:
                        modifier.SetVariation(variation)
                    variation = AbstractRandomizer.SelectOneFromCollection(colorVariations, oddsOfSelectingNone=0.3)
                    if variation:
                        modifier.SetColorVariation(variation)
                    modifier.weight = weight

    def RemoveAllOptionsByCategory(self, doll, options):
        for category in options:
            mods = doll.GetBuildDataByCategory(category)
            for m in mods:
                doll.RemoveResource(m.categorie + '/' + m.name, self.modifierLoader)

    def GetDoll(self, randomizeBlendshapes = True, doll = None):
        """
        Returns a doll that is randomized except for constraints that have already been set.
        For instance, if gender is set manually on this instance, that value is used instead of randomizing.
        
        
        THIS METHOD SHOULDN'T BE IN COMMON SINCE IT WILL BREAK SHIT ON THE SERVER
        """
        resourceDict = self.GetResources()
        if randomizeBlendshapes:
            blendshapeOptions = self.GetBlendshapeOptions()
        if doll is not None:
            self.RemoveAllOptionsByCategory(doll, resourceDict)
            if randomizeBlendshapes:
                self.RemoveAllOptionsByCategory(doll, blendshapeOptions)
        else:
            import eve.client.script.paperDoll.paperDollImpl as pdImp
            doll = pdImp.Doll('randomized', gender=self.GetGender())
        self.AddRandomizedResourcesToDoll(doll, resourceDict)
        if randomizeBlendshapes:
            self.AddRandomizedResourcesToDoll(doll, blendshapeOptions)
        return doll
