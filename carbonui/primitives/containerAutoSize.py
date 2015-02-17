#Embedded file name: carbonui/primitives\containerAutoSize.py
import carbonui.const as uiconst
import telemetry
from .container import Container
from .childrenlist import PyChildrenList as UIChildrenList
ALLOWED_ALIGNMENTS = (uiconst.TOLEFT,
 uiconst.TORIGHT,
 uiconst.TOTOP,
 uiconst.TOBOTTOM,
 uiconst.TOPLEFT,
 uiconst.TOPRIGHT,
 uiconst.CENTER,
 uiconst.CENTERTOP,
 uiconst.CENTERBOTTOM,
 uiconst.CENTERLEFT)

class ContainerAutoSize(Container):
    """
    A container that automatically adjusts its size and alignment mode to it's children. 
    """
    __guid__ = 'uicontrols.ContainerAutoSize'
    default_name = 'containerAutoSize'
    default_align = uiconst.TOPLEFT
    default_alignMode = None
    _childrenAlign = None
    isAutoSizeEnabled = True
    alignMode = None
    callback = None

    def ApplyAttributes(self, attributes):
        """ 
            Width and height is interperated depending on the alignment modes of the children:
            1) TOLEFT/TORIGHT aligned: width is set automatically
            2) TOTOP/TOBOTTOM aligned: height is set automatically
            3) TOPLEFT aligned: width and height is set automatically
            Children that don't have an alignment mode matching alignMode (if passed in) will be ignored
        """
        self.alignMode = attributes.Get('alignMode', self.default_alignMode)
        self.callback = attributes.Get('callback', None)
        Container.ApplyAttributes(self, attributes)

    @telemetry.ZONE_METHOD
    def SetSizeAutomatically(self):
        """ Set own width and height according to children and alignment mode """
        if self.align == uiconst.TOALL:
            self.DisableAutoSize()
        if not self.isAutoSizeEnabled:
            return
        width, height = self.GetAutoSize()
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height
        if self.callback:
            self.callback()

    @telemetry.ZONE_METHOD
    def GetAutoSize(self):
        if self._childrenAlign in (uiconst.TOLEFT, uiconst.TORIGHT):
            width = 0
            for child in self.children:
                if self._IgnoreChild(child):
                    continue
                width += child.width + child.left + child.padLeft + child.padRight

            return (width, None)
        elif self._childrenAlign in (uiconst.TOTOP, uiconst.TOBOTTOM):
            height = 0
            for child in self.children:
                if self._IgnoreChild(child):
                    continue
                height += child.height + child.top + child.padTop + child.padBottom

            return (None, height)
        elif self._childrenAlign in ALLOWED_ALIGNMENTS:
            width = height = 0
            for child in self.children:
                if self._IgnoreChild(child):
                    continue
                x = child.left + child.width + child.padLeft + child.padRight
                if x > width:
                    width = x
                y = child.top + child.height + child.padTop + child.padBottom
                if y > height:
                    height = y

            return (width, height)
        else:
            return (0, 0)

    def _IgnoreChild(self, child):
        if not child.display:
            return True
        if self.alignMode is not None and child.align != self._childrenAlign:
            return True
        return False

    @telemetry.ZONE_METHOD
    def _VerifyNewChild(self, child):
        if self.alignMode is not None:
            self._childrenAlign = self.alignMode
            return
        if child.align not in ALLOWED_ALIGNMENTS:
            raise ValueError('ContainerAutoSize only supports TOLEFT, TORIGHT, TOTOP, TOBOTTOM, TOPLEFT, TOPRIGHT or CENTER aligned children')
        if self.children and child.align != self._childrenAlign:
            raise ValueError('All children of ContainerAutoSize must have the same alignment (Got %s, expecting %s)' % (child.align, self._childrenAlign))
        if not self.children:
            self._childrenAlign = child.align

    def GetChildrenList(self):
        return UIChildrenListAutoSize(self)

    def DisableAutoSize(self):
        self.isAutoSizeEnabled = False

    def EnableAutoSize(self):
        self.isAutoSizeEnabled = True
        self.SetSizeAutomatically()

    def UpdateAlignment(self, *args, **kwds):
        budget = Container.UpdateAlignment(self, *args, **kwds)
        if self._childrenAlign is not None:
            self.SetSizeAutomatically()
        return budget

    def GetAbsoluteSize(self):
        self.SetSizeAutomatically()
        return Container.GetAbsoluteSize(self)


class UIChildrenListAutoSize(UIChildrenList):
    """
    A list of children owned by a uicontrols.ContainerAutoSize that makes sure that we
    update the 
    """
    __guid__ = 'uicls.UIChildrenListAutoSize'

    def append(self, obj):
        owner = self.GetOwner()
        if owner:
            owner._VerifyNewChild(obj)
            UIChildrenList.append(self, obj)

    def insert(self, idx, obj):
        owner = self.GetOwner()
        if owner:
            owner._VerifyNewChild(obj)
            UIChildrenList.insert(self, idx, obj)

    def remove(self, obj):
        owner = self.GetOwner()
        if owner:
            UIChildrenList.remove(self, obj)
