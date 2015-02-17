#Embedded file name: carbonui/primitives\container.py
import carbonui.const as uiconst
import trinity
from .base import Base
from .backgroundList import BackgroundList
from .sprite import Sprite
from .fill import Fill
from .childrenlist import PyChildrenList

class Container(Base):
    """
    Standard UI container used for containing other UI objects in order to create layouts
    """
    __guid__ = 'uiprimitives.Container'
    __renderObject__ = trinity.Tr2Sprite2dContainer
    __members__ = Base.__members__ + ['opacity',
     'children',
     'background',
     'clipChildren']
    isDropLocation = True
    default_clipChildren = False
    default_pickRadius = 0
    default_opacity = 1.0
    default_align = uiconst.TOALL
    default_state = uiconst.UI_PICKCHILDREN
    default_depthMin = 0.0
    default_depthMax = 0.0
    default_bgColor = None
    default_bgTexturePath = None
    _cacheContents = False
    _containerClosing = False
    _childrenAlignmentDirty = False
    _backgroundlist = None
    _opacity = None

    def ApplyAttributes(self, attributes):
        self.children = self.GetChildrenList()
        Base.ApplyAttributes(self, attributes)
        self.depthMin = attributes.get('depthMin', self.default_depthMin)
        self.depthMax = attributes.get('depthMax', self.default_depthMax)
        self.pickRadius = attributes.get('pickRadius', self.default_pickRadius)
        self.opacity = attributes.get('opacity', self.default_opacity)
        self.clipChildren = attributes.get('clipChildren', self.default_clipChildren)
        bgColor = attributes.get('bgColor', self.default_bgColor)
        bgTexturePath = attributes.get('bgTexturePath', self.default_bgTexturePath)
        if bgTexturePath:
            Sprite(bgParent=self, texturePath=bgTexturePath, color=bgColor or (1.0, 1.0, 1.0, 1.0))
        elif bgColor:
            Fill(bgParent=self, color=bgColor)

    def Close(self):
        if getattr(self, 'destroyed', False):
            return
        self._containerClosing = True
        for child in self.children:
            child.Close()

        self.children = []
        if self._backgroundlist:
            for child in self.background[:]:
                child.Close()

            self.background = None
        Base.Close(self)

    def UpdateAlignment(self, budgetLeft = 0, budgetTop = 0, budgetWidth = 0, budgetHeight = 0, updateChildrenOnly = False):
        displayDirty = self._displayDirty
        if updateChildrenOnly:
            childrenDirty = True
            sizeChange = False
        else:
            budgetLeft, budgetTop, budgetWidth, budgetHeight, sizeChange = Base.UpdateAlignment(self, budgetLeft, budgetTop, budgetWidth, budgetHeight)
            childrenDirty = self._childrenAlignmentDirty
        self._childrenAlignmentDirty = False
        if childrenDirty or displayDirty or sizeChange:
            flagNextChild = False
            cbLeft, cbTop, cbWidth, cbHeight = (0,
             0,
             self.displayWidth,
             self.displayHeight)
            for each in self.children:
                if each.destroyed:
                    continue
                isPushAligned = each.isPushAligned
                if isPushAligned and each._displayDirty:
                    flagNextChild = True
                if each.display:
                    if not each._alignmentDirty:
                        if displayDirty:
                            each._displayDirty = displayDirty
                        elif sizeChange:
                            each._alignmentDirty = True
                        elif flagNextChild and each.isAffectedByPushAlignment:
                            each._alignmentDirty = True
                    if getattr(each, '_childrenAlignmentDirty', False) or each._alignmentDirty or each._displayDirty or isPushAligned:
                        preDisplayX = each.displayX
                        preDisplayY = each.displayY
                        cbLeft, cbTop, cbWidth, cbHeight, changedSize = each.UpdateAlignment(cbLeft, cbTop, cbWidth, cbHeight)
                        if not flagNextChild and isPushAligned:
                            flagNextChild = changedSize or preDisplayX != each.displayX or preDisplayY != each.displayY

        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight,
         sizeChange)

    def GetChildrenList(self):
        """ Can be overwritten if we need custom children lists """
        return PyChildrenList(self)

    def GetOpacity(self):
        """ Accessor function for the opacity property, for backwards compatability"""
        return self.opacity

    def SetOpacity(self, opacity):
        """ Accessor function for the opacity property, for backwards compatability"""
        self.opacity = opacity

    def AutoFitToContent(self):
        if self.isAffectedByPushAlignment:
            raise RuntimeError('AutoFitToContent: invalid alignment')
        minWidth = 0
        minHeight = 0
        totalAutoVertical = 0
        totalAutoHorizontal = 0
        for each in self.children:
            if not each.isAffectedByPushAlignment:
                minWidth = max(minWidth, each.left + each.width)
                minHeight = max(minHeight, each.top + each.height)
            elif each.align in (uiconst.TOTOP, uiconst.TOBOTTOM):
                totalAutoVertical += each.padTop + each.height + each.padBottom
            elif each.align in (uiconst.TOLEFT, uiconst.TORIGHT):
                totalAutoHorizontal += each.padLeft + each.width + each.padRight

        self.width = max(minWidth, totalAutoHorizontal)
        self.height = max(minHeight, totalAutoVertical)

    def Flush(self):
        """
        Close and remove all children
        """
        for child in self.children[:]:
            child.Close()

    def FindChild(self, *names, **kwds):
        """
        Find children by their names. If you need to use this method, you're probably doing it wrong ...
        """
        if self.destroyed:
            return
        ret = None
        searchFrom = self
        for name in names:
            ret = searchFrom._FindChildByName(name)
            if hasattr(ret, 'children'):
                searchFrom = ret

        if not ret or ret.name != names[-1]:
            if kwds.get('raiseError', False):
                raise RuntimeError('ChildNotFound', (self.name, names))
            return
        return ret

    def _FindChildByName(self, name, lvl = 0):
        for child in self.children:
            if child.name == name:
                return child

        for child in self.children:
            if hasattr(child, 'children'):
                ret = child._FindChildByName(name, lvl + 1)
                if ret is not None:
                    return ret

    def Find(self, triTypeName):
        """ 
        Depreciated method that finds children by their __bluetype__
        """

        def FindType(under, typeName, addto):
            if under.__bluetype__ == typeName:
                addto.append(under)
            if hasattr(under, 'children'):
                for each in under.children:
                    FindType(each, typeName, addto)

        ret = []
        for child in self.children:
            FindType(child, triTypeName, ret)

        return ret

    def GetChild(self, *names):
        """
        Find children by their names. Raises an error if nothing is found.
        If you need to use this method, you're probably doing it wrong ...
        """
        return self.FindChild(*names, **{'raiseError': True})

    def IsChildClipped(self, child):
        """
        Determines whether an immediate child is clipped by this container. Note that
        this only looks at the relation between this container and the given child - there
        is no guarantee that the child is really visible (could be offscreen, or this container
        could be clipped).
        
        Returns True if 'child' lies outside of this container's clipping rectangle.
        Returns False if this container isn't set to clip, or if the child lies within
        the clipping rectangle.
        """
        if not self.clipChildren:
            return False
        cdx = child.displayX
        cdw = child.displayWidth
        sdx = self.displayX
        sdw = self.displayWidth
        if cdx >= sdx and cdx <= sdx + sdw or cdx + cdw >= sdx and cdx + cdw <= sdx + sdw:
            cdy = child.displayY
            cdh = child.displayHeight
            sdy = self.displayY
            sdh = self.displayHeight
            if cdy >= sdy and cdy <= sdy + sdh or cdy + cdh >= sdy and cdy + cdh <= sdy + sdh:
                return False
        return True

    @apply
    def background():
        doc = 'Background list of this container. READ-ONLY'

        def fget(self):
            if not self._backgroundlist:
                self._backgroundlist = BackgroundList(self)
            return self._backgroundlist

        def fset(self, value):
            pass

        return property(**locals())

    @apply
    def depthMin():
        doc = 'Minimum depth value'

        def fget(self):
            return self._depthMin

        def fset(self, value):
            self._depthMin = value
            ro = self.renderObject
            if ro and hasattr(ro, 'depthMin'):
                ro.depthMin = value or 0.0

        return property(**locals())

    @apply
    def depthMax():
        doc = 'Maximum depth value'

        def fget(self):
            return self._depthMax

        def fset(self, value):
            self._depthMax = value
            ro = self.renderObject
            if ro and hasattr(ro, 'depthMax'):
                ro.depthMax = value or 0.0

        return property(**locals())

    @apply
    def clipChildren():
        doc = 'Clip children?'

        def fget(self):
            return self._clipChildren

        def fset(self, value):
            self._clipChildren = value
            ro = self.renderObject
            if ro and hasattr(ro, 'clip'):
                ro.clip = value

        return property(**locals())

    @apply
    def opacity():
        doc = 'Opacity'

        def fget(self):
            return self._opacity

        def fset(self, value):
            if value != self._opacity:
                self._opacity = value
                ro = self.renderObject
                if ro and hasattr(ro, 'opacity'):
                    ro.opacity = value or 0.0
                for child in self.children:
                    childRenderObject = child.renderObject
                    if childRenderObject:
                        childRenderObject.isDirty = True

        return property(**locals())

    @apply
    def pickRadius():
        doc = 'Pick radius'

        def fget(self):
            return self._pickRadius

        def fset(self, value):
            self._pickRadius = value
            ro = self.renderObject
            if ro and hasattr(ro, 'pickRadius'):
                if value < 0:
                    ro.pickRadius = value
                else:
                    ro.pickRadius = uicore.ScaleDpi(value) or 0.0

        return property(**locals())

    @apply
    def displayWidth():
        doc = 'Width of container. Background objects are always assigned this width as well'
        fget = Base.displayWidth.fget

        def fset(self, value):
            Base.displayWidth.fset(self, value)
            if self._backgroundlist and len(self.background):
                self.UpdateBackgrounds()

        return property(**locals())

    @apply
    def displayHeight():
        doc = 'Height of container. Background objects are always assigned this height as well'
        fget = Base.displayHeight.fget

        def fset(self, value):
            Base.displayHeight.fset(self, value)
            if self._backgroundlist and len(self.background):
                self.UpdateBackgrounds()

        return property(**locals())

    @apply
    def displayRect():
        doc = ''
        fget = Base.displayRect.fget

        def fset(self, value):
            Base.displayRect.fset(self, value)
            if self._backgroundlist and len(self.background):
                self.UpdateBackgrounds()

        return property(**locals())

    def UpdateBackgrounds(self):
        for each in self.background:
            pl, pt, pr, pb = each.padding
            each.displayRect = (uicore.ScaleDpi(pl),
             uicore.ScaleDpi(pt),
             self._displayWidth - uicore.ScaleDpi(pl + pr),
             self._displayHeight - uicore.ScaleDpi(pt + pb))

    @apply
    def cacheContents():
        doc = '\n            Should contents of this container be cached? This can drastically improve\n            render performance of containers with static contents.\n            '

        def fget(self):
            return self._cacheContents

        def fset(self, value):
            self._cacheContents = value
            if self.renderObject:
                self.renderObject.cacheContents = value

        return property(**locals())

    def _AppendChildRO(self, child):
        try:
            self.renderObject.children.append(child.renderObject)
        except (AttributeError, TypeError):
            pass

    def _InsertChildRO(self, idx, child):
        try:
            self.renderObject.children.insert(idx, child.renderObject)
        except IndexError:
            self.renderObject.children.append(child.renderObject)
        except (AttributeError, TypeError):
            pass

    def _RemoveChildRO(self, child):
        try:
            self.renderObject.children.remove(child.renderObject)
        except (AttributeError,
         ValueError,
         RuntimeError,
         TypeError):
            pass

    def AppendBackgroundObject(self, child):
        try:
            self.renderObject.background.append(child.renderObject)
        except AttributeError:
            pass

    def InsertBackgroundObject(self, idx, child):
        try:
            self.renderObject.background.insert(idx, child.renderObject)
        except AttributeError:
            pass

    def RemoveBackgroundObject(self, child):
        try:
            self.renderObject.background.remove(child.renderObject)
        except (AttributeError,
         ValueError,
         RuntimeError,
         TypeError):
            pass
