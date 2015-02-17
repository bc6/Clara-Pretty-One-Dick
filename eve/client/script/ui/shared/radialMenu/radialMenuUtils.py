#Embedded file name: eve/client/script/ui/shared/radialMenu\radialMenuUtils.py
import util

class SimpleRadialMenuAction(util.KeyVal):
    """
        KeyVal that store information about the simplest radial menu actions
    """

    def __init__(self, option1 = None, option2 = None, *args, **kw):
        self.option1Path = option1
        self.option2Path = option2
        self.activeOption = option1
        self.func = None
        self.funcArgs = ()
        for attrname, val in kw.iteritems():
            setattr(self, attrname, val)


class RangeRadialMenuAction(util.KeyVal):
    """
        KeyVal that store information about the range radial menu actions
    """

    def __init__(self, optionPath = None, optionPath2 = None, rangeList = None, defaultRange = None, callback = None, *args, **kw):
        self.option1Path = optionPath
        self.option2Path = optionPath2
        self.activeOption = optionPath
        self.rangeList = rangeList
        self.defaultRange = defaultRange
        self.callback = callback
        for attrname, val in kw.iteritems():
            setattr(self, attrname, val)


class SecondLevelRadialMenuAction(util.KeyVal):

    def __init__(self, levelType = '', texturePath = 'res:/UI/Texture/classes/RadialMenu/plus.png', *args, **kw):
        self.option1Path = ''
        self.activeOption = ''
        self.levelType = levelType
        self.texturePath = texturePath
        for attrname, val in kw.iteritems():
            setattr(self, attrname, val)


class RadialMenuOptionsInfo:
    """
        Data construct for configuring the options available for a radial menu.
    
            The menu option info consists of:
                allWantedMenuOptions =  a list of all options we that should be in the radial menu
                activeSingleOptions =   a dictionary with all the avaible clickable options. The key is the labelpath and the value is
                                        the menu option keyval which contains the callback and arguments among other things
                inactiveSingleOptions = a set of menu options(labelpath) that we want in our radial menu but are not available (and are therefore greyed out)
                activeRangeOptions =    a dictionary with all the available range options. The key is the labelpath and the value is
                                         the menu option keyval which contains the callback, rangeOptions and default distance among other things
                inactiveRangeOptions =  a set with all the range options(labelpath) we want, but are not available
    
    
        SimpleRadialMenuAction in activeSingleOptions need to have at least "option1" textpath, and a function it should call.
        (for the RadialMenuSpace class, this is built from the info from the menu service, and the func depends on which
        option is available. For simple case, just give the function you want to use.)
    """

    def __init__(self, allWantedMenuOptions, activeSingleOptions = None, inactiveSingleOptions = None, activeRangeOptions = None, inactiveRangeOptions = None):
        self.allWantedMenuOptions = allWantedMenuOptions
        self.activeSingleOptions = activeSingleOptions or {}
        self.inactiveSingleOptions = inactiveSingleOptions or set()
        self.activeRangeOptions = activeRangeOptions or {}
        self.inactiveRangeOptions = inactiveRangeOptions or set()


def FindOptionsDegree(counter, degreeStep, startingDegree = 0, alternate = False):
    if counter == 0:
        return startingDegree
    if alternate:
        rightSide = counter % 2
        numOnSide = counter / 2
        if rightSide:
            numOnSide += 1
        degree = numOnSide * degreeStep
        if not rightSide:
            degree = -degree + 360
    else:
        degree = counter * degreeStep
    degree = startingDegree + degree
    if degree >= 360:
        degree -= 360
    return degree


class RadialMenuSizeInfo:

    def __init__(self, width, height, shadowSize, rangeSize, sliceCount, buttonHeight, buttonWidth, buttonPaddingTop, buttonPaddingBottom, actionDistance):
        self.width = width
        self.height = height
        self.shadowSize = shadowSize
        self.rangeSize = rangeSize
        self.sliceCount = sliceCount
        self.buttonHeight = buttonHeight
        self.buttonWidth = buttonWidth
        self.buttonPaddingTop = buttonPaddingTop
        self.buttonPaddingBottom = buttonPaddingBottom
        self.actionDistance = actionDistance
