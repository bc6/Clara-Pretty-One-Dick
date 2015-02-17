#Embedded file name: eve/client/script/ui/services\mouseInputSvc.py
import service
import carbonui.const as uiconst

class MouseInputService(service.Service):
    """
    Routes mouse input towards interested CEF subsystems.
    """
    __guid__ = 'svc.mouseInput'
    __translateUIConst__ = {uiconst.MOUSELEFT: const.INPUT_TYPE_LEFTCLICK,
     uiconst.MOUSERIGHT: const.INPUT_TYPE_RIGHTCLICK,
     uiconst.MOUSEMIDDLE: const.INPUT_TYPE_MIDDLECLICK,
     uiconst.MOUSEXBUTTON1: const.INPUT_TYPE_EX1CLICK,
     uiconst.MOUSEXBUTTON2: const.INPUT_TYPE_EX2CLICK}

    def __init__(self):
        self.selectedEntityID = None
        service.Service.__init__(self)
        self.callbacks = {const.INPUT_TYPE_LEFTCLICK: [],
         const.INPUT_TYPE_RIGHTCLICK: [],
         const.INPUT_TYPE_MIDDLECLICK: [],
         const.INPUT_TYPE_EX1CLICK: [],
         const.INPUT_TYPE_EX2CLICK: [],
         const.INPUT_TYPE_DOUBLECLICK: [],
         const.INPUT_TYPE_MOUSEMOVE: [],
         const.INPUT_TYPE_MOUSEWHEEL: [],
         const.INPUT_TYPE_MOUSEDOWN: [],
         const.INPUT_TYPE_MOUSEUP: []}

    def GetSelectedEntityID(self):
        """
        Returns the entityID of the currently selectd entity.
        Returns None if nothing is selected
        """
        return sm.GetService('selectionClient').GetSelectedEntityID()

    def RegisterCallback(self, type, callback):
        """
        Registers a callback for a specific type of mouse event.
        """
        self.callbacks[type].append(callback)

    def UnRegisterCallback(self, type, callback):
        """
        Removes a previously registered callback for a specific type of mouse event.
        """
        self.callbacks[type].remove(callback)

    def OnDoubleClick(self, entityID):
        for callback in self.callbacks[const.INPUT_TYPE_DOUBLECLICK]:
            callback(entityID)

    def OnMouseUp(self, button, posX, posY, entityID):
        """
        Handles events when the user takes their finger off a mouse button. This counts
        as two seperate events for simplified entity click handling.
        """
        inputType = self.__translateUIConst__[button]
        for callback in self.callbacks[const.INPUT_TYPE_MOUSEUP]:
            callback(inputType, posX, posY, entityID)

        for callback in self.callbacks[inputType]:
            callback(entityID)

    def OnMouseDown(self, button, posX, posY, entityID):
        inputType = self.__translateUIConst__[button]
        for callback in self.callbacks[const.INPUT_TYPE_MOUSEDOWN]:
            callback(inputType, posX, posY, entityID)

    def OnMouseWheel(self, delta):
        for callback in self.callbacks[const.INPUT_TYPE_MOUSEWHEEL]:
            callback(delta)

    def OnMouseMove(self, deltaX, deltaY, entityID):
        for callback in self.callbacks[const.INPUT_TYPE_MOUSEMOVE]:
            callback(deltaX, deltaY, entityID)
