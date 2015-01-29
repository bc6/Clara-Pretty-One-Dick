#Embedded file name: eve/client/script/ui/control\eveFrame.py
from carbonui.primitives.frame import Frame as FrameCore

class Frame(FrameCore):
    __guid__ = 'uicontrols.Frame'
    default_color = (1.0, 1.0, 1.0, 0.5)


from carbonui.primitives.frame import FrameCoreOverride
FrameCoreOverride.__bases__ = (Frame,)
