#Embedded file name: reprocessing/ui\tileplacer.py
"""
Code for a tile container
"""
from carbonui.const import TOTOP
from collections import OrderedDict
import math

class TilePlacer(object):
    """
    This object's only job is to place items within a container.
    It only handles square containers and adds them one after another and if there isn't
    enough space in the line it adds the container in the first row in next line.
    """

    def __init__(self, container, tileSize):
        self.tileSize = tileSize
        self.mainContainer = container
        self.mainContainer.SetAlign(TOTOP)
        self.mainContainer.SetSize(0, 0)
        self.width = self._GetContainerWidth()
        self.mainContainer._OnResize = self.OnResize
        self.items = OrderedDict()

    def AddItem(self, ctrlID, item):
        left, top = self._GetPosition(len(self.items))
        self.items[ctrlID] = item
        item.SetParent(self.mainContainer)
        item.SetPosition(left, top)
        self.mainContainer.height = top + self.tileSize

    def _GetPosition(self, idx):
        itemsPerLine = self._GetItemsPerLine(self.width)
        top = idx / itemsPerLine
        width = idx % itemsPerLine
        return (width * self.tileSize, top * self.tileSize)

    def OnWidthChanged(self, newWidth):
        oldItemsPerLine = self._GetItemsPerLine(self.width)
        newItemsPerLine = self._GetItemsPerLine(newWidth)
        self.width = newWidth
        updateFrom = None
        if oldItemsPerLine != newItemsPerLine:
            updateFrom = min(oldItemsPerLine, newItemsPerLine)
        if updateFrom is not None:
            self._UpdatePositions(newItemsPerLine, updateFrom)

    def _UpdatePositions(self, itemsPerLine, updateFromIdx):
        for offset, item in enumerate(self.items.values()[updateFromIdx:]):
            item.SetPosition(*self._GetPosition(updateFromIdx + offset))

        self.mainContainer.height = self.tileSize * math.ceil(float(len(self.items)) / itemsPerLine)

    def _GetItemsPerLine(self, width):
        itemsPerLine = width / self.tileSize
        return itemsPerLine

    def OnResize(self):
        width = self._GetContainerWidth()
        self.OnWidthChanged(width)

    def GetItems(self):
        return self.items.values()

    def GetItem(self, ctrlID):
        return self.items[ctrlID]

    def _GetContainerWidth(self):
        width, _ = self.mainContainer.GetAbsoluteSize()
        return width

    def Clear(self):
        self.items.clear()
        self.mainContainer.Flush()

    def RemoveItem(self, ctrlID):
        idx = self.items.keys().index(ctrlID)
        containerToRemove = self.items.pop(ctrlID)
        containerToRemove.SetParent(None)
        self._UpdatePositions(self._GetItemsPerLine(self.width), idx)
