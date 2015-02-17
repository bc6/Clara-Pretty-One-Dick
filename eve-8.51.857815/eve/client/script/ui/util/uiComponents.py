#Embedded file name: eve/client/script/ui/util\uiComponents.py
import functools
import math
from threadutils import Signal
import carbonui.const as uiconst
from carbonui.primitives.fill import Fill
from carbonui.primitives.gradientSprite import GradientSprite
import logging
import uthread
logger = logging.getLogger(__name__)

def Component(component):

    def AttachComponent(cls):
        for methodName in component.__observed_methods__:
            method = getattr(cls, methodName, None)
            if method is None:
                continue
            signal = getattr(method, '_component_method_observers', None)
            if signal is None:
                signal = Signal()

                def GetWrapper(_method, _signal):

                    @functools.wraps(method)
                    def Wrapper(*args, **kwargs):
                        try:
                            result = _method(*args, **kwargs)
                        except:
                            logger.exception('Method %s raised an exception before signal could emit', methodName)
                            raise

                        try:
                            _signal.emit(*args, **kwargs)
                        except Exception:
                            logger.exception('Failed while notifying observers for method %s', methodName)

                        return result

                    return Wrapper

                wrapper = GetWrapper(method, signal)
                setattr(wrapper, '_component_method_observers', signal)
                setattr(cls, methodName, wrapper)
            signal.connect(getattr(component, methodName))

        return cls

    return AttachComponent


THREADS_BY_KEY = {}

def RunThreadOnce(threadKey):
    """
    Makes sure that only one thread of with the same key is running at any one time.
    """

    def Wrapper(func):

        @functools.wraps(func)
        def RunThread(*args, **kwargs):
            if threadKey not in THREADS_BY_KEY:
                THREADS_BY_KEY[threadKey] = uthread.new(ExecuteAndRelease, func, *args, **kwargs)

        return RunThread

    def ExecuteAndRelease(func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        finally:
            del THREADS_BY_KEY[threadKey]

    return Wrapper


class ButtonEffect:
    """
    This makes a ui control behave as a button, with mouse over highlights and click action, sound and highlight as well
    """
    __observed_methods__ = ['ApplyAttributes',
     'OnMouseEnter',
     'OnMouseExit',
     'OnMouseUp',
     'OnMouseDown',
     'OnClick']
    isToggleButton = False
    isRadioButton = False

    def __init__(self, opacityIdle = 0.0, opacityHover = 0.5, opacityMouseDown = 0.85, idx = 0, bgElementFunc = None, audioOnEntry = None, audioOnClick = None, exitDuration = 0.3):
        self.opacityIdle = opacityIdle
        self.opacityHover = opacityHover
        self.opacityMouseDown = opacityMouseDown
        self.bgElementFunc = bgElementFunc
        self.audioOnEntry = audioOnEntry
        self.audioOnClick = audioOnClick
        self.idx = idx
        self.exitDuration = exitDuration

    def ApplyAttributes(self, _self, attributes, *args):
        if self.bgElementFunc:
            _self._buttonEffect_bgElement = self.bgElementFunc(_self, attributes)
        else:
            _self._buttonEffect_bgElement = GradientSprite(name='hoverGradient', bgParent=_self, rotation=-math.pi / 2, rgbData=[(0, (1.0, 1.0, 1.0))], alphaData=[(0, 0.5), (0.3, 0.2), (0.6, 0.08)], idx=self.idx)
        _self._buttonEffect_bgElement.opacity = self.opacityIdle
        if not hasattr(_self, 'disabled'):
            setattr(_self, 'disabled', attributes.disabled or False)
        if self.isToggleButton:
            setattr(_self, 'isActive', attributes.isActive or False)
            if _self.isActive:
                _self._buttonEffect_bgElement.opacity = self.opacityMouseDown

            def SetActive(isActive):
                _self.isActive = isActive
                if _self.isActive:
                    uicore.animations.FadeTo(_self._buttonEffect_bgElement, _self._buttonEffect_bgElement.opacity, self.opacityMouseDown, duration=0.1)
                else:
                    uicore.animations.FadeTo(_self._buttonEffect_bgElement, _self._buttonEffect_bgElement.opacity, self.opacityIdle, duration=self.exitDuration)
                onActiveStateChange = getattr(_self, 'OnActiveStateChange', None)
                if onActiveStateChange is not None:
                    onActiveStateChange()

            _self.SetActive = SetActive

    def OnMouseEnter(self, _self, *args):
        if _self.disabled:
            return
        if not self.IsActiveToggle(_self):
            uicore.animations.FadeTo(_self._buttonEffect_bgElement, _self._buttonEffect_bgElement.opacity, self.opacityHover, duration=0.1)
        if self.audioOnEntry:
            sm.GetService('audio').SendUIEvent(self.audioOnEntry)

    def OnMouseExit(self, _self, *args):
        if not (self.isToggleButton and _self.isActive):
            uicore.animations.FadeTo(_self._buttonEffect_bgElement, _self._buttonEffect_bgElement.opacity, self.opacityIdle, duration=0.3)

    def OnMouseDown(self, _self, *args):
        if _self.disabled:
            return
        if self.IsActiveToggle(_self):
            uicore.animations.FadeTo(_self._buttonEffect_bgElement, _self._buttonEffect_bgElement.opacity, self.opacityMouseDown, duration=0.1)

    def OnMouseUp(self, _self, *args):
        if _self.disabled:
            return
        if self.IsActiveToggle(_self):
            return
        uicore.animations.FadeTo(_self._buttonEffect_bgElement, _self._buttonEffect_bgElement.opacity, self.opacityHover, duration=0.2)

    def OnClick(self, _self, *args):
        if _self.disabled:
            return
        self.Toggle(_self)
        if not self.IsActiveToggle(_self):
            uicore.animations.FadeTo(_self._buttonEffect_bgElement, self.opacityMouseDown, _self._buttonEffect_bgElement.opacity, duration=self.exitDuration)
        if self.audioOnClick:
            sm.GetService('audio').SendUIEvent(self.audioOnClick)

    def IsActiveToggle(self, _self):
        return self.isToggleButton and _self.isActive

    def Toggle(self, _self):
        if self.isRadioButton:
            _self.SetActive(True)
        elif self.isToggleButton:
            _self.SetActive(not _self.isActive)


class ToggleButtonEffect(ButtonEffect):
    isToggleButton = True


class RadioButtonEffect(ButtonEffect):
    isToggleButton = True
    isRadioButton = True


class HoverEffect:
    """
    This makes a ui control have basic mouse highlights
    """
    __observed_methods__ = ['ApplyAttributes',
     'OnMouseEnter',
     'OnMouseExit',
     'OnClick']

    def __init__(self, padding = (1, 1, 1, 1), color = (1.0, 1.0, 1.0, 0.25), audioOnEntry = None, audioOnClick = None):
        self.padding = padding
        self.color = color
        self.audioOnEntry = audioOnEntry
        self.audioOnClick = audioOnClick

    def _GetHoverElement(self, _self):
        return getattr(_self, '_hoverEffect_bgFill', None)

    def ApplyAttributes(self, _self, *args):
        setattr(_self, '_hoverEffect_bgFill', Fill(bgParent=_self, padding=self.padding, color=self.color, state=uiconst.UI_HIDDEN))

    def OnMouseEnter(self, _self, *args):
        fill = self._GetHoverElement(_self)
        if fill is None:
            return
        fill.state = uiconst.UI_NORMAL
        if self.audioOnEntry:
            sm.GetService('audio').SendUIEvent(self.audioOnEntry)

    def OnMouseExit(self, _self, *args):
        fill = self._GetHoverElement(_self)
        if fill:
            fill.state = uiconst.UI_HIDDEN

    def OnClick(self, _self, *args):
        if self.audioOnClick:
            sm.GetService('audio').SendUIEvent(self.audioOnClick)
