#Embedded file name: carbonui/primitives\flowcontainer.py
__author__ = 'fridrik'
from .container import Container
from .base import Base
import carbonui.const as uiconst

class FlowContainer(Container):
    """
    Container to arrange children position from topleft, wrapping when exceeding
    this container width.
    NOALIGN is the only supported children alignment to reduce
    mass alignment updates
    
    autoHeight, if True the total height of the content is applied
    to this container but only if the uiconst.TOPLEFT, uiconst.TOBOTTOM, uiconst.TOTOP
    
    centerContent, if True content will be centered horizontally
    """
    default_name = 'flowContainer'
    autoHeight = True
    centerContent = False
    contentSpacing = (0, 0)

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.centerContent = attributes.get('centerContent', self.centerContent)
        self.autoHeight = attributes.get('autoHeight', self.autoHeight)
        self.contentSpacing = attributes.get('contentSpacing', self.contentSpacing)

    def UpdateAlignment(self, budgetLeft = 0, budgetTop = 0, budgetWidth = 0, budgetHeight = 0, updateChildrenOnly = False):
        if self.destroyed:
            return (budgetLeft,
             budgetTop,
             budgetWidth,
             budgetHeight,
             False)
        displayDirty = self._displayDirty
        if updateChildrenOnly:
            childrenDirty = True
            sizeChange = False
            retBudgetLeft, retBudgetTop, retBudgetWidth, retBudgetHeight = (budgetLeft,
             budgetTop,
             budgetWidth,
             budgetHeight)
        else:
            retBudgetLeft, retBudgetTop, retBudgetWidth, retBudgetHeight, sizeChange = Base.UpdateAlignment(self, budgetLeft, budgetTop, budgetWidth, budgetHeight)
            childrenDirty = self._childrenAlignmentDirty
        self._childrenAlignmentDirty = False
        if childrenDirty or displayDirty or sizeChange:

            def AdjustRow(rowObjects, width, height, rowY):
                if self.centerContent:
                    centerOffset = (self.displayWidth - width) / 2
                else:
                    centerOffset = 0
                for item in rowObjects:
                    item.displayY = rowY
                    item.displayX += centerOffset

            x = 0
            y = 0
            rowItems = []
            rowHeight = 0
            rowWidth = 0
            spacingX = uicore.ScaleDpi(self.contentSpacing[0])
            spacingY = uicore.ScaleDpi(self.contentSpacing[1])
            for each in self.children:
                if each.align != uiconst.NOALIGN:
                    continue
                if each.display:
                    scaledWidth = uicore.ScaleDpi(each.width)
                    scaledHeight = uicore.ScaleDpi(each.height)
                    if scaledWidth != each.displayWidth or scaledHeight != each.displayHeight:
                        each.FlagAlignmentDirty()
                        each.UpdateAlignment()
                    if x + scaledWidth > self.displayWidth:
                        AdjustRow(rowItems, rowWidth - spacingX, rowHeight, y)
                        x = 0
                        y += rowHeight + spacingY
                        rowWidth = 0
                        rowHeight = 0
                        rowItems = []
                    rowItems.append(each)
                    rowHeight = max(rowHeight, scaledHeight)
                    rowWidth += scaledWidth + spacingX
                    each.displayX = x
                    x += scaledWidth + spacingX

            AdjustRow(rowItems, rowWidth - spacingX, rowHeight, y)
            if self.autoHeight and self.align in (uiconst.TOPLEFT, uiconst.TOBOTTOM, uiconst.TOTOP):
                newHeight = uicore.ReverseScaleDpi(y + rowHeight)
                if newHeight != self.height:
                    self.height = newHeight
                    retBudgetLeft, retBudgetTop, retBudgetWidth, retBudgetHeight, sizeChange = Base.UpdateAlignment(self, budgetLeft, budgetTop, budgetWidth, budgetHeight)
        return (retBudgetLeft,
         retBudgetTop,
         retBudgetWidth,
         retBudgetHeight,
         sizeChange)

    def UnifyContentSize(self):
        maxWidth = 0
        maxHeight = 0
        for each in self.children:
            maxWidth = max(maxWidth, each.width)
            maxHeight = max(maxHeight, each.height)

        for each in self.children:
            each.width = maxWidth
            each.height = maxHeight

    def _AppendChildRO(self, child):
        if child.align != uiconst.NOALIGN:
            raise ValueError('FlowContainer only supports NOALIGN aligned children')
        Container._AppendChildRO(self, child)

    def _InsertChildRO(self, idx, child):
        if child.align != uiconst.NOALIGN:
            raise ValueError('FlowContainer only supports NOALIGN aligned children')
        Container._InsertChildRO(self, idx, child)
