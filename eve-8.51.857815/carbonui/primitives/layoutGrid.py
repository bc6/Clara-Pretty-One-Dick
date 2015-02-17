#Embedded file name: carbonui/primitives\layoutGrid.py
import carbonui.const as uiconst
import blue
import weakref
from .container import Container
from .frame import Frame
from .fill import Fill
from .childrenlist import PyChildrenList as ChildrenList
CELLUSED = 1
CELLUSED_ROWSPAN = 2
TOPBOTTOM_ALIGNMENTS = (uiconst.TOTOP,
 uiconst.TOBOTTOM,
 uiconst.TOTOP_NOPUSH,
 uiconst.TOBOTTOM_NOPUSH,
 uiconst.TOTOP_PROP,
 uiconst.TOBOTTOM_PROP)
LEFTRIGHT_ALIGNMENTS = (uiconst.TOLEFT,
 uiconst.TORIGHT,
 uiconst.TOLEFT_NOPUSH,
 uiconst.TORIGHT_NOPUSH,
 uiconst.TOLEFT_PROP,
 uiconst.TORIGHT_PROP)
CENTER_ALIGNMENTS = (uiconst.CENTER, uiconst.CENTERBOTTOM, uiconst.CENTERTOP)

class LayoutGridCell(Container):
    rowSpan = 1
    colSpan = 1
    gridCellPadding = None
    _cellPadding = None

    def ApplyAttributes(self, attributes):
        attributes.state = uiconst.UI_PICKCHILDREN
        Container.ApplyAttributes(self, attributes)
        self._content = Container(parent=self, align=uiconst.TOALL)
        self.cellPadding = attributes.cellPadding
        self.gridCellPadding = attributes.gridCellPadding
        self.colSpan = attributes.colSpan or 1
        self.rowSpan = attributes.rowSpan or 1
        cellObject = attributes.cellObject
        if cellObject:
            if cellObject.align != uiconst.TOALL:
                cellObject._originalUpdateAlignment = cellObject.UpdateAlignment
                cellObject.UpdateAlignment = lambda *args, **kwds: self.UpdateCellObjectAlignment(cellObject, *args, **kwds)
            cellObject._originalClose = cellObject.Close
            cellObject.Close = lambda *args: self.CloseCellObject(cellObject, *args)
            self._content.children.append(cellObject)

    def CloseCellObject(self, cellObject, *args):
        if cellObject.destroyed:
            return
        cellObject._originalClose()
        cellObject._originalUpdateAlignment = None
        cellObject._originalClose = None
        if not self._containerClosing:
            self.Close()

    def Close(self, *args):
        parent = self.parent
        Container.Close(self, *args)
        if parent and not parent.destroyed and not parent._containerClosing:
            parent.FlagGridLayoutDirty()

    def UpdateCellObjectAlignment(self, cellObject, *args, **kwds):
        preX = cellObject.renderObject.displayX
        preY = cellObject.renderObject.displayY
        preWidth = cellObject.renderObject.displayWidth
        preHeight = cellObject.renderObject.displayHeight
        ret = cellObject._originalUpdateAlignment(*args)
        align = cellObject.align
        if align in TOPBOTTOM_ALIGNMENTS:
            if preHeight != cellObject.renderObject.displayHeight or preY != cellObject.renderObject.displayY:
                self.parent.FlagCellSizesDirty()
        elif align in LEFTRIGHT_ALIGNMENTS:
            if preWidth != cellObject.renderObject.displayWidth or preX != cellObject.renderObject.displayX:
                self.parent.FlagCellSizesDirty()
        elif preX != cellObject.renderObject.displayX:
            self.parent.FlagCellSizesDirty()
        elif preY != cellObject.renderObject.displayY:
            self.parent.FlagCellSizesDirty()
        elif preWidth != cellObject.renderObject.displayWidth:
            self.parent.FlagCellSizesDirty()
        elif preHeight != cellObject.renderObject.displayHeight:
            self.parent.FlagCellSizesDirty()
        return ret

    def UpdateBackgrounds(self):
        if len(self.background) > 0:
            for each in self.background:
                each.displayRect = (0,
                 0,
                 self._displayWidth,
                 self._displayHeight)

    @apply
    def cellPadding():
        """cellPadding for this cell, to override the grid default padding """

        def fset(self, value):
            if isinstance(value, (tuple, list)):
                if len(value) == 4:
                    pass
                elif len(value) == 2:
                    value = (value[0],
                     value[1],
                     value[0],
                     value[1])
            elif isinstance(value, int):
                value = (value,
                 value,
                 value,
                 value)
            else:
                value = None
            if self._cellPadding != value:
                self._cellPadding = value

        def fget(self):
            if self._cellPadding:
                return self._cellPadding
            if self.gridCellPadding:
                return self.gridCellPadding
            return (0, 0, 0, 0)

        return property(**locals())

    def GetCellObject(self):
        if self._content.children:
            return self._content.children[0]

    def GetCellSize(self):
        """
        Returns size needed for cell content.
        """
        neededCellWidth = 0
        neededCellHeight = 0
        if self._content.children:
            self._content.padding = self.cellPadding
            cellObject = self.GetCellObject()
            cellObjectAlign = cellObject.align
            if cellObjectAlign in (uiconst.CENTERLEFT, uiconst.CENTERRIGHT):
                neededCellWidth = cellObject.width + cellObject.padLeft + cellObject.padRight + cellObject.left
                neededCellHeight = cellObject.height + cellObject.padTop + cellObject.padBottom + cellObject.top * 2
            elif cellObjectAlign in (uiconst.CENTERTOP, uiconst.CENTERBOTTOM):
                neededCellWidth = cellObject.width + cellObject.padLeft + cellObject.padRight + cellObject.left * 2
                neededCellHeight = cellObject.height + cellObject.padTop + cellObject.padBottom + cellObject.top
            elif cellObjectAlign == uiconst.CENTER:
                neededCellWidth = cellObject.width + cellObject.padLeft + cellObject.padRight + cellObject.left * 2
                neededCellHeight = cellObject.height + cellObject.padTop + cellObject.padBottom + cellObject.top * 2
            elif not cellObject.isAffectedByPushAlignment:
                neededCellWidth = cellObject.width + cellObject.padLeft + cellObject.padRight + cellObject.left
                neededCellHeight = cellObject.height + cellObject.padTop + cellObject.padBottom + cellObject.top
            elif cellObjectAlign in TOPBOTTOM_ALIGNMENTS:
                neededCellWidth = cellObject.padLeft + cellObject.padRight
                neededCellHeight = cellObject.height + (cellObject.padTop + cellObject.padBottom + cellObject.top)
            elif cellObjectAlign in LEFTRIGHT_ALIGNMENTS:
                neededCellWidth = cellObject.width + (cellObject.padLeft + cellObject.padRight + cellObject.left)
                neededCellHeight = cellObject.padTop + cellObject.padBottom
            elif cellObject.align == uiconst.TOALL:
                neededCellWidth = cellObject.padLeft + cellObject.padRight
                neededCellHeight = cellObject.padTop + cellObject.padBottom
            else:
                neededCellWidth = uicore.ReverseScaleDpi(cellObject.displayWidth) + (cellObject.padLeft + cellObject.padRight)
                neededCellHeight = uicore.ReverseScaleDpi(cellObject.displayHeight) + (cellObject.padTop + cellObject.padBottom)
        ccpl, ccpt, ccpr, ccpb = self.cellPadding
        return (ccpl + neededCellWidth + ccpr, ccpt + neededCellHeight + ccpb)

    @apply
    def pos():
        doc = 'Position of UI element'

        def fget(self):
            return (self._left,
             self._top,
             self._width,
             self._height)

        def fset(self, value):
            left, top, width, height = value
            self._left = left
            self._top = top
            self._width = width
            self._height = height
            self.displayX = uicore.ScaleDpiF(self._left)
            self.displayY = uicore.ScaleDpiF(self._top)
            self.FlagAlignmentDirty()

        return property(**locals())


class LayoutGridRowCell(LayoutGridCell):

    def ApplyAttributes(self, attributes):
        attributes.align = uiconst.TOPLEFT
        LayoutGridCell.ApplyAttributes(self, attributes)


class LayoutGrid(Container):
    default_align = uiconst.TOPLEFT
    default_columns = 2
    default_margin = 0
    default_cellPadding = 0
    default_cellSpacing = (0, 0)
    default_cellBgColor = None
    _nextColumnIndex = 0
    _sizesDirty = False
    _layoutDirty = False
    _fixedGridWidth = None
    _columns = 2
    _grid_cellSpacing = (0, 0)
    _grid_cellPadding = (0, 0, 0, 0)
    _grid_margin = (0, 0, 0, 0)
    debug_showCells = False
    gridSize = (0, 0)
    OnGridSizeChanged = None

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.cellPadding = attributes.get('cellPadding', self.default_cellPadding)
        self.cellSpacing = attributes.get('cellSpacing', self.default_cellSpacing)
        self.columns = attributes.get('columns', self.default_columns)
        self.margin = attributes.get('margin', self.default_margin)
        self._grid_cellBgColor = attributes.get('cellBgColor', self.default_cellBgColor)
        self._layoutData = []
        self.children.insert = self._InsertChild
        self.children.append = self._AppendChild
        self.children.remove = self._RemoveChild
        self.OnGridSizeChanged = attributes.OnGridSizeChanged

    @apply
    def columns():
        doc = 'Amount of columns in the grid'

        def fset(self, value):
            if self._columns != value:
                self._columns = value
                self.FlagGridLayoutDirty()

        def fget(self):
            return self._columns

        return property(**locals())

    @apply
    def margin():
        doc = 'Outer margin of the grid'

        def fset(self, value):
            if isinstance(value, (tuple, list)):
                if len(value) == 4:
                    pass
                elif len(value) == 2:
                    value = (value[0],
                     value[1],
                     value[0],
                     value[1])
            elif isinstance(value, int):
                value = (value,
                 value,
                 value,
                 value)
            else:
                value = (0, 0, 0, 0)
            if self._grid_margin != value:
                self._grid_margin = value
                self.FlagCellSizesDirty()

        def fget(self):
            return self._grid_margin

        return property(**locals())

    @apply
    def cellPadding():
        """global cellPadding in the grid, padding around cell content"""

        def fset(self, value):
            if isinstance(value, (tuple, list)):
                if len(value) == 4:
                    pass
                elif len(value) == 2:
                    value = (value[0],
                     value[1],
                     value[0],
                     value[1])
            elif isinstance(value, int):
                value = (value,
                 value,
                 value,
                 value)
            else:
                value = (0, 0, 0, 0)
            if self._grid_cellPadding != value:
                self._grid_cellPadding = value
                for each in self.children:
                    if isinstance(each, LayoutGridCell):
                        each.gridCellPadding = value

                self.FlagCellSizesDirty()

        def fget(self):
            return self._grid_cellPadding

        return property(**locals())

    @apply
    def cellSpacing():
        """global cellSpacing in the grid, the space between cell on x,y"""

        def fset(self, value):
            if isinstance(value, int):
                value = (value, value)
            elif isinstance(value, (tuple, list)) and len(value) == 2:
                value = value
            else:
                value = (0, 0)
            if self._grid_cellSpacing != value:
                self._grid_cellSpacing = value
                self.FlagCellSizesDirty()

        def fget(self):
            return self._grid_cellSpacing

        return property(**locals())

    def _InsertChild(self, idx, obj):
        if not isinstance(obj, LayoutGridCell):
            return self.AddCell(cellObject=obj, idx=idx)
        return ChildrenList.insert(self.children, idx, obj)

    def _AppendChild(self, obj):
        self._InsertChild(-1, obj)

    def _RemoveChild(self, obj):
        if isinstance(obj, LayoutGridCell):
            return ChildrenList.remove(self.children, obj)
        return ChildrenList.remove(self.children, obj.parent)

    def FlagCellSizesDirty(self):
        self._sizesDirty = True
        self.FlagAlignmentDirty()

    def FlagGridLayoutDirty(self):
        self._layoutDirty = True
        self.FlagAlignmentDirty()

    def AddCell(self, cellObject = None, colSpan = 1, rowSpan = 1, cellPadding = None, bgColor = None, cellClipChildren = False, cellClass = None, **keywords):
        if self.destroyed:
            return
        if cellObject is None:
            cellObject = Container()
        else:
            cellObjects = [ child.GetCellObject() for child in self.children if isinstance(child, LayoutGridCell) ]
            if cellObject in cellObjects:
                raise RuntimeError('This object has already been inserted to the layout grid', cellObject)
        if cellClass is None:
            cellClass = LayoutGridCell
        cell = cellClass(parent=self, align=uiconst.NOALIGN, colSpan=colSpan, rowSpan=rowSpan, cellObject=cellObject, cellPadding=cellPadding, gridCellPadding=self.cellPadding, clipChildren=cellClipChildren, bgColor=bgColor)
        if self.debug_showCells:
            Frame(bgParent=cell, color=(1, 0, 0, 0.5))
        self.FlagGridLayoutDirty()
        return cell

    def DebugCells(self):
        self.debug_showCells = True

    def AddRow(self, rowObjects = None, rowClass = None, **keywords):
        """Returns 'sub' layout grid which aligns to the parent grid"""
        keywords['columns'] = self.columns
        keywords.setdefault('cellPadding', self.cellPadding)
        keywords.setdefault('cellSpacing', self.cellSpacing)
        if rowClass is None:
            rowClass = LayoutGridRow
        elif not issubclass(rowClass, LayoutGridRow):
            raise RuntimeError('rowClass has to be based on LayoutGridRow')
        rowGrid = rowClass(parentGrid=self, **keywords)
        if rowObjects:
            for each in rowObjects:
                rowGrid.AddCell(cellObject=each)

        self.AddCell(cellObject=rowGrid, colSpan=self.columns, cellClass=LayoutGridRowCell)
        return rowGrid

    def Flush(self):
        for child in self.children[:]:
            child.Close()

        self.FlagGridLayoutDirty()

    def SetFixedGridWidth(self, fixedWidth = None):
        if fixedWidth and self.align in TOPBOTTOM_ALIGNMENTS:
            raise RuntimeError('Cannot set fixedWidth when using TOTOP or TOBOTTOM alignment')
        elif self.isAffectedByPushAlignment:
            raise RuntimeError('Cannot set fixed grid size when alignment is', self.alignment)
        self._fixedGridWidth = fixedWidth
        self.FlagCellSizesDirty()

    def RefreshGridLayout(self):
        """
        Refreshes layout of the content if needed. Intended to trigger
        update instantly instead of waiting for new alignment tick update
        """
        if self._layoutDirty:
            self.UpdateGridLayout()
        if self._sizesDirty:
            self.UpdateCellsPositionAndSize()
        if self._layoutDirty or self._sizesDirty:
            self.RefreshGridLayout()

    def UpdateAlignment(self, *args, **kwds):
        if self._layoutDirty:
            self.UpdateGridLayout()
        if self._sizesDirty:
            self.UpdateCellsPositionAndSize()
        return Container.UpdateAlignment(self, *args, **kwds)

    def UpdateCellsPositionAndSize(self):
        self._sizesDirty = False
        rowHeights = {}
        spreadRows = {}
        columnWidths = {}
        spreadColumns = []
        scaledCellSpacingX, scaledCellSpacingY = self.cellSpacing
        for rowIndex, columnData in enumerate(self._layoutData):
            if columnData and isinstance(columnData[0], LayoutGridRowCell):
                rowCell = columnData[0]
                rowGrid = rowCell.GetCellObject()
                if rowGrid._layoutDirty:
                    rowGrid.UpdateGridLayout()
                if rowGrid._sizesDirty:
                    rowGrid.UpdateCellsPositionAndSize()
                columnData = rowGrid._layoutData[0]
            for columnIndex, cell in enumerate(columnData):
                if cell is None or cell == CELLUSED or cell == CELLUSED_ROWSPAN:
                    rowHeights.setdefault(rowIndex, []).append(0)
                    continue
                cW, cH = cell.GetCellSize()
                cW += scaledCellSpacingX
                cH += scaledCellSpacingY
                if cell.rowSpan == 1:
                    rowHeights.setdefault(rowIndex, []).append(cH)
                else:
                    for r in xrange(cell.rowSpan - 1):
                        rowHeights.setdefault(rowIndex + 1, []).append(0)

                    spreadRows[rowIndex] = (cell.rowSpan, cH)
                colSpan = cell.colSpan
                if columnIndex + colSpan > self._columns:
                    colSpan = min(self._columns - columnIndex, colSpan)
                if colSpan == 1:
                    columnWidths.setdefault(columnIndex, []).append(cW)
                    if cell.rowSpan - 1:
                        for r in xrange(cell.rowSpan - 1):
                            columnWidths.setdefault(columnIndex, []).append(0)

                else:
                    for i in xrange(colSpan):
                        for r in xrange(cell.rowSpan):
                            columnWidths.setdefault(columnIndex + i, []).append(0)

                    spreadColumns.append((rowIndex,
                     columnIndex,
                     colSpan,
                     cW))

        if spreadColumns:
            for rowIndex, columnIndex, colSpan, columnWidth in spreadColumns:
                spreadToColumns = []
                used = 0
                equalSplitWidth = columnWidth / colSpan
                for i in xrange(colSpan):
                    currentColumnWidth = max(columnWidths[columnIndex + i])
                    if currentColumnWidth > equalSplitWidth:
                        used += currentColumnWidth
                    else:
                        spreadToColumns.append(columnIndex + i)

                if spreadToColumns:
                    splitWidth = (columnWidth - used) / len(spreadToColumns)
                    for spreadColumnIndex in spreadToColumns:
                        columnWidths[spreadColumnIndex].append(splitWidth)

        for rowIndex, (rowSpan, spanHeight) in spreadRows.iteritems():
            totalHeight = 0
            for i in xrange(rowSpan - 1):
                if rowIndex + i in rowHeights:
                    totalHeight += max(rowHeights[rowIndex + i])

            if rowIndex + rowSpan - 1 in rowHeights:
                currentHeight = max(rowHeights[rowIndex + rowSpan - 1])
            else:
                currentHeight = 0
            rowHeights[rowIndex + rowSpan - 1] = [max(currentHeight, spanHeight - totalHeight)]

        colsMaxed = [ (k, max(v)) for k, v in columnWidths.items() ]
        colsMaxed.sort()
        rowsMaxed = [ (k, max(v)) for k, v in rowHeights.items() ]
        rowsMaxed.sort()
        if getattr(self, 'doPrint', False):
            print '=' * 30
            print 'spreadRows', spreadRows
            print 'spreadColumns', spreadColumns
            print 'rowHeights', rowHeights
            print 'columnWidths', columnWidths
            print 'rowsMaxed', rowsMaxed
            print 'colsMaxed', colsMaxed
            print 'scaledCellSpacingY', scaledCellSpacingY
            print 'scaledCellSpacingX', scaledCellSpacingX
            print '=' * 30
        ml, mt, mr, mb = self.margin
        maxScaledHeight = 0
        maxScaledWidth = 0
        for rowIndex, columnData in enumerate(self._layoutData):
            for columnIndex, cell in enumerate(columnData):
                if cell is None or cell == CELLUSED or cell == CELLUSED_ROWSPAN:
                    continue
                rowSpan = cell.rowSpan
                colSpan = cell.colSpan
                if columnIndex + colSpan > self._columns:
                    colSpan = min(self._columns - columnIndex, colSpan)
                cellWidth = sum([ colsMaxed[columnIndex + i][1] for i in xrange(colSpan) ]) - scaledCellSpacingX
                cellHeight = sum([ rowsMaxed[rowIndex + i][1] for i in xrange(rowSpan) ]) - scaledCellSpacingY
                cellLeft = sum([ w[1] for w in colsMaxed[:columnIndex] ])
                cellTop = sum([ h[1] for h in rowsMaxed[:rowIndex] ])
                maxScaledWidth = max(maxScaledWidth, cellLeft + cellWidth)
                maxScaledHeight = max(maxScaledHeight, cellTop + cellHeight)
                cell.pos = (ml + cellLeft,
                 mt + cellTop,
                 cellWidth,
                 cellHeight)
                cell.name = 'Row%s_Col%s' % (rowIndex, columnIndex)

            cell = columnData[0]
            if isinstance(cell, LayoutGridRowCell):
                rowGrid = cell.GetCellObject()
                rowColumnData = rowGrid._layoutData[0]
                for columnIndex, cell in enumerate(rowColumnData):
                    if cell is None or cell == CELLUSED or cell == CELLUSED_ROWSPAN:
                        continue
                    rowSpan = cell.rowSpan
                    colSpan = cell.colSpan
                    if columnIndex + colSpan > self._columns:
                        colSpan = min(self._columns - columnIndex, colSpan)
                    rowCellWidth = sum([ colsMaxed[columnIndex + i][1] for i in xrange(colSpan) ]) - scaledCellSpacingX
                    rowCellHeight = sum([ rowsMaxed[rowIndex + i][1] for i in xrange(rowSpan) ]) - scaledCellSpacingY
                    rowCellLeft = sum([ w[1] for w in colsMaxed[:columnIndex] ])
                    rowCellTop = 0
                    cell.pos = (rowCellLeft,
                     rowCellTop,
                     rowCellWidth,
                     rowCellHeight)
                    cell.name = 'RowGrid_Row%s_Col%s' % (rowIndex, columnIndex)

                rowGrid.width = cellWidth
                rowGrid.height = cellHeight
                rowGrid._sizesDirty = False
                rowGrid._layoutDirty = False

        if not isinstance(self, LayoutGridRow):
            self.gridSize = (max(self._fixedGridWidth, maxScaledWidth) + ml + mr, maxScaledHeight + mt + mb)
            preWidth, preHeight = self.width, self.height
            if self.align in TOPBOTTOM_ALIGNMENTS:
                self.width = 0
                self.height = maxScaledHeight + mt + mb
            elif self.align in LEFTRIGHT_ALIGNMENTS:
                self.width = max(self._fixedGridWidth, maxScaledWidth) + ml + mr
                self.height = 0
            elif not self.isAffectedByPushAlignment:
                self.width = max(self._fixedGridWidth, maxScaledWidth) + ml + mr
                self.height = maxScaledHeight + mt + mb
            if self.OnGridSizeChanged and (self.width, self.height) != (preWidth, preHeight):
                self.OnGridSizeChanged(self.width, self.height)

    def UpdateGridLayout(self):
        rows = []
        rowIndex = 0
        columnIndex = 0
        taken = []
        for cell in self.children:
            rowSpan = cell.rowSpan
            colSpan = cell.colSpan
            if (rowIndex, columnIndex) in taken:
                rowIndex, columnIndex = self.GetFirstEmpty(rows)
            if columnIndex + colSpan > self._columns:
                colSpan = min(self._columns - columnIndex, colSpan)
            for columnIndexShift in xrange(colSpan):
                for rowIndexShift in xrange(rowSpan):
                    while len(rows) <= rowIndex + rowIndexShift:
                        rows.append([None] * self._columns)

                    if rows[rowIndex + rowIndexShift][columnIndex + columnIndexShift]:
                        cell.colSpan = columnIndexShift
                        continue
                    if not columnIndexShift:
                        if not rowIndexShift:
                            register = cell
                        else:
                            register = CELLUSED_ROWSPAN
                    else:
                        register = CELLUSED
                    taken.append((rowIndex + rowIndexShift, columnIndex + columnIndexShift))
                    rows[rowIndex + rowIndexShift][columnIndex + columnIndexShift] = register

            columnIndex = min(self._columns, columnIndex + colSpan)
            if columnIndex == self._columns:
                columnIndex = 0
                rowIndex += 1

        self._nextColumnIndex = columnIndex
        self._layoutData = rows
        self._layoutDirty = False
        self._sizesDirty = True

    def GetFirstEmpty(self, rows):
        rowIndex = 0
        for rowData in rows:
            for columnIndex, cell in enumerate(rowData):
                if cell is None:
                    return (rowIndex, columnIndex)

            rowIndex += 1

        rows.append([None] * self._columns)
        return (rowIndex, 0)

    def FillRow(self):
        """Util to fill last row if it isn't filled with cells"""
        self.UpdateGridLayout()
        if self._nextColumnIndex != 0:
            self.AddCell()
            self.FillRow()


class LayoutGridRow(LayoutGrid):

    def ApplyAttributes(self, attributes):
        self.parentGrid = weakref.ref(attributes.parentGrid)
        LayoutGrid.ApplyAttributes(self, attributes)

    def FlagCellSizesDirty(self):
        self._sizesDirty = True
        if self.parentGrid:
            parentGrid = self.parentGrid()
            if parentGrid:
                parentGrid.FlagCellSizesDirty()

    def FlagGridLayoutDirty(self):
        self._layoutDirty = True
        if self.parentGrid:
            parentGrid = self.parentGrid()
            if parentGrid:
                parentGrid.FlagGridLayoutDirty()

    def _InsertChild(self, idx, obj):
        if len(self.children) == self.columns:
            raise RuntimeError('The layout grid row is configured for %s columns layout and all columns are taken' % self.columns)
        return LayoutGrid._InsertChild(self, idx, obj)
