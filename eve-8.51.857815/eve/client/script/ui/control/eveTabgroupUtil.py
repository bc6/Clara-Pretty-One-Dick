#Embedded file name: eve/client/script/ui/control\eveTabgroupUtil.py
import localization

def FixedTabName(tabNamePath):
    """
        The tab system in the UI uses localized tab labels to generate the name of the tab UI element. This is problematic
        when other systems rely on the tab having a predictable name (such as UI pointers pointing to a tab in a tutorial).
        This method returns both english and localized text in a tuple, which is then handled by the tab framework to
        ensure that the tab is named using the English text. Eventually, we should fix this issue to decouple the element
        name from the display name in a more reasonable way.
    """
    enText = localization.GetByLabel(tabNamePath, localization.const.LOCALE_SHORT_ENGLISH)
    text = localization.GetByLabel(tabNamePath)
    return (enText, text)


exports = {'uiutil.FixedTabName': FixedTabName}
