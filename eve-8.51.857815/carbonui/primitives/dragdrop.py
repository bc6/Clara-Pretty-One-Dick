#Embedded file name: carbonui/primitives\dragdrop.py
import carbonui.const as uiconst
import uthread

class DragDropObject(object):
    """
    Class for drag/drop functionality of a UI element.
    """
    __guid__ = 'uiprimitives.DragDropObject'
    dragData = []
    _dragEnabled = False
    _dragging = False
    _lastOverObject = None
    _dragMouseDown = None
    Draggable_blockDrag = False
    isDragObject = False
    isDropLocation = False

    def __init__(self):
        object.__init__(self)
        dragEvents = ['OnExternalDragInitiated', 'OnExternalDragEnded']
        if hasattr(self, '__notifyevents__') and self.__notifyevents__ is not None:
            self.__notifyevents__.extend(dragEvents)
        else:
            self.__notifyevents__ = dragEvents
        sm.RegisterNotify(self)

    def MakeDragObject(self):
        self.isDragObject = True

    def MakeDropLocation(self):
        self.isDropLocation = True

    def EnableDrag(self):
        self.Draggable_blockDrag = False

    def DisableDrag(self):
        self.Draggable_blockDrag = True

    def IsDraggable(self):
        return self.isDragObject and not self.Draggable_blockDrag

    def IsBeingDragged(self):
        return self._dragging

    def GetDragData(self):
        return self.dragData

    def PrepareDrag(self, dragContainer, dragSource):
        """
        Creates the display for a drag item and returns
        the mouse offset for where it appears on the screen.
        """
        from eve.client.script.ui.util.eveOverrides import PrepareDrag_Override
        return PrepareDrag_Override(dragContainer, dragSource)
        from carbonui.primitives.frame import FrameCoreOverride as Frame
        Frame(parent=dragContainer)
        return (0, 0)

    def OnDragCanceled(self, dragSource, dragData):
        """
        Called when a drag has been cancelled due to 
        verification failure.
        """
        pass

    def OnEndDrag(self, dragSource, dropLocation, dragData):
        """
        Called after a drag has been completed.
        """
        pass

    def VerifyDrag(self, dragDestination, dragData):
        """
        Verifies whether or not the object/data combination
        is valid to be dragged from here.
        
        Returns - Boolean
        """
        return True

    def OnMouseDownDrag(self, *args):
        """
        Called simultaneously with OnMouseDown for drag/drop objects.
        """
        if not uicore.IsDragging() and self.isDragObject:
            self._dragMouseDown = (uicore.uilib.x, uicore.uilib.y)
            self._dragEnabled = True
            uicore.dragObject = None

    def OnMouseMoveDrag(self, *args):
        """
        Called simultaneously with OnMouseMove for drag/drop objects.
        """
        if uicore.IsDragging():
            if uicore.dragObject is not self and self.isDropLocation:
                uthread.new(self.OnDragMove, uicore.dragObject, uicore.dragObject.dragData)
        elif not self.IsBeingDragged() and self._dragEnabled and not self.Draggable_blockDrag and uicore.uilib.mouseTravel >= 6:
            self._dragging = True
            uthread.new(self._BeginDrag).context = 'DragObject::_BeginDrag'

    def _BeginDrag(self):
        """
        Gets relevant drag data and prepares the visuals
        for the drag operation.
        """
        dragData = self.GetDragData()
        if not dragData:
            self._dragEnabled = False
            self._dragging = False
            return
        if uicore.uilib.GetMouseCapture() == self:
            uicore.uilib.ReleaseCapture()
        mouseExitArgs, mouseExitHandler = self.FindEventHandler('OnMouseExit')
        if mouseExitHandler:
            mouseExitHandler(*mouseExitArgs)
        from carbonui.control.dragitem import DragContainerCore
        dragContainer = DragContainerCore(name='dragContainer', align=uiconst.ABSOLUTE, idx=0, pos=(0, 0, 32, 32), state=uiconst.UI_DISABLED, parent=uicore.layer.dragging)
        dragContainer.dragData = dragData
        uicore.uilib.KillClickThreads()
        self._DoDrag(dragContainer)

    def _DoDrag(self, dragContainer):
        """
        Performs the actual drag operation.
        """
        if dragContainer.destroyed:
            return
        dragData = dragContainer.dragData
        mouseOffset = self.PrepareDrag(dragContainer, self)
        if self.destroyed:
            return
        uicore.dragObject = dragContainer
        sm.ScatterEvent('OnExternalDragInitiated', self, dragData)
        try:
            dragContainer.InitiateDrag(mouseOffset)
        finally:
            sm.ScatterEvent('OnExternalDragEnded')
            uicore.dragObject = None

        dropLocation = uicore.uilib.mouseOver
        if self._dragEnabled:
            self._dragEnabled = False
            self._dragging = False
            self.KillDragContainer(dragContainer)
            dropLocation = uicore.uilib.mouseOver
            if dropLocation.isDropLocation and self.VerifyDrag(dropLocation, dragData) and dropLocation.VerifyDrop(self, dragData):
                uthread.new(dropLocation.OnDropData, self, dragData)
            else:
                self.OnDragCanceled(self, dragData)
        self.OnEndDrag(self, dropLocation, dragData)

    def KillDragContainer(self, dragContainer):
        uicore.layer.dragging.Flush()

    def CancelDrag(self):
        self._dragEnabled = False
        self._dragging = None
        uicore.dragObject = None
        uicore.layer.dragging.Flush()

    def OnDragMove(self, dragSource, dragData):
        """
        Called on each mouse move event as a DragDropObject
        is moved over this object's area.
        """
        pass

    def OnDragExit(self, dragSource, dragData):
        """
        Called when a DragDropObject leaves this object's area.
        """
        pass

    def OnDragEnter(self, dragSource, dragData):
        """
        Called when a DragDropObject enters this object's area.
        """
        pass

    def OnDropData(self, dragSource, dragData):
        """
        Called after all verification has been performed to
        perform the actual drop.
        """
        pass

    def VerifyDrop(self, dragSource, dragData):
        """
        Verifies whether or not the object/data combination
        is valid to be dropped here.
        
        Returns - Boolean
        """
        return True

    def OnExternalDragInitiated(self, dragSource, dragData):
        """
        Called when an object has started being dragged somewhere
        on the screen.
        """
        pass

    def OnExternalDragEnded(self):
        """
        Called when an object has finished being dragged somewhere
        on the screen.
        """
        pass
