#Embedded file name: spacecomponents/common/components\bookmark.py
from spacecomponents.common.components.component import Component
from spacecomponents.common.componentConst import BOOKMARK_CLASS

class Bookmark(Component):

    def IsBookmarkable(self):
        return self.attributes.isBookmarkable


def IsTypeBookmarkable(typeID, spaceComponentStaticData):
    try:
        attributes = spaceComponentStaticData.GetAttributes(typeID, BOOKMARK_CLASS)
    except (KeyError, AttributeError):
        return True

    return attributes.isBookmarkable
