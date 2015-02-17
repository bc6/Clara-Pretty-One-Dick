#Embedded file name: carbonui/primitives\gridcontainer.py
import math
from .container import Container
from .base import Base

class GridContainer(Container):
    """
    GridContainer is similar to a regular container, except it allocates
    the alignment budget evenly distributed between its children, rather
    than allowing them to consume from it.
    """
    __guid__ = 'uicls.GridContainer'
    default_name = 'gridContainer'
    default_columns = 0
    default_lines = 0

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.columns = attributes.get('columns', self.default_columns)
        self.lines = attributes.get('lines', self.default_lines)

    @apply
    def lines():
        doc = 'Number of lines in the grid'

        def fget(self):
            return self._lines

        def fset(self, value):
            self._lines = value
            self.FlagMyChildrenAlignmentDirty()

        return property(**locals())

    @apply
    def columns():
        doc = 'Number of columns in the grid'

        def fget(self):
            return self._columns

        def fset(self, value):
            self._columns = value
            self.FlagMyChildrenAlignmentDirty()

        return property(**locals())

    def FlagMyChildrenAlignmentDirty(self):
        """
        Flags immediate children with alignment dirty.
        """
        self.FlagAlignmentDirty()
        for each in self.children:
            each._alignmentDirty = True

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
        else:
            budgetLeft, budgetTop, budgetWidth, budgetHeight, sizeChange = Base.UpdateAlignment(self, budgetLeft, budgetTop, budgetWidth, budgetHeight)
            childrenDirty = self._childrenAlignmentDirty
        self._childrenAlignmentDirty = False
        if childrenDirty or displayDirty or sizeChange:
            numChildren = len(self.children)
            numColumns = self.columns
            numLines = self.lines
            if numColumns < 1:
                if numLines > 0:
                    numColumns = int(float(numChildren) / float(numLines) + 0.5)
                    if numColumns * numLines < numChildren:
                        numColumns += 1
            if numLines < 1:
                if numColumns < 1:
                    aspectRatio = float(self.displayWidth) / float(self.displayHeight)
                    numColumns = int(math.sqrt(numChildren) * aspectRatio + 0.5)
                    numLines = int(float(numChildren) / float(numColumns) + 0.5)
                    if numColumns * numLines < numChildren:
                        numLines += 1
                    if self.displayWidth > self.displayHeight:
                        while numColumns * numLines > numChildren:
                            numColumns -= 1

                        if numColumns * numLines < numChildren:
                            numColumns += 1
                    else:
                        while numColumns * numLines > numChildren:
                            numLines -= 1

                        if numColumns * numLines < numChildren:
                            numLines += 1
                else:
                    numLines = int(float(numChildren) / float(numColumns) + 0.5)
                    if numColumns * numLines < numChildren:
                        numLines += 1
            w = self.displayWidth / float(numColumns)
            h = self.displayHeight / float(numLines)
            t = 0
            for line in xrange(numLines):
                l = 0
                b = int(h * (line + 1))
                for column in xrange(numColumns):
                    ix = line * numColumns + column
                    if ix < numChildren:
                        r = min(self.displayWidth, int(w * (column + 1)))
                        budget = (l,
                         t,
                         r - l,
                         b - t)
                        child = self.children[ix]
                        child._alignmentDirty = True
                        child.UpdateAlignment(*budget)
                        l = r

                t = min(self.displayHeight, b)

        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight,
         sizeChange)
