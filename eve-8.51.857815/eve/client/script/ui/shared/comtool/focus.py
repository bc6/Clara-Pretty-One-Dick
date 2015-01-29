#Embedded file name: eve/client/script/ui/shared/comtool\focus.py
import service
import carbonui.const as uiconst
import weakref

class Focus(service.Service):
    """
        Yet Another Stupid Chat Service
    """
    __guid__ = 'svc.focus'
    __servicename__ = 'focus'
    __displayname__ = 'Focus Tool'
    __dependencies__ = []

    def Run(self, memStream = None):
        self.focusChannelWindow = None

    def SetChannelFocus(self, char = None):
        channel = self.GetFocusChannel()
        if channel is not None:
            channel.Maximize()
            stack = getattr(channel.sr, 'stack', None)
            if stack and stack.state == uiconst.UI_HIDDEN:
                return
            channel.SetCharFocus(char)

    def SetFocusChannel(self, channel = None):
        """
            Sets the focus channel window
        """
        if channel is not None:
            self.focusChannelWindow = weakref.ref(channel)
        else:
            self.focusChannelWindow = None

    def GetFocusChannel(self):
        """
            Gets the focus channel window
        """
        if self.focusChannelWindow:
            ch = self.focusChannelWindow()
            if ch and not ch.destroyed:
                return ch
