#Embedded file name: carbonui/primitives\area.py
"""
This class implements all the functionality a area should have by extending Container
"""
from carbonui.control.label import LabelOverride as Label
from carbonui.primitives.frame import FrameCoreOverride as Frame
from carbonui.primitives.container import Container
from carbonui.primitives.line import Line
from carbonui.util.various_unsorted import GetIndex
import carbonui.const as uiconst
import types
import telemetry
from carbonui.control.divider import Divider

class Area(Container):
    """
    Returns advanced container (Area) which has LoadFrame, LoadUnderlay and Split
    functions to work with
    
    frame
        __maincontainer; container for split areas. Splitarea is Frame as well
            subframe
                __submaincontainer; container for split areas. Splitarea is Area as well
                __subframe
                __subunderlay
                    ...
            ...
        __frame
        __underlay
    
    """
    __guid__ = 'uiprimitives.Area'
    default_name = 'Area'
    default_align = uiconst.TOALL
    default_state = uiconst.UI_PICKCHILDREN

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.sr.underlay = None
        self.sr.frame = None
        self.sr.splitareacontent = None
        self.sr.maincontainer = Container(parent=self, name='__maincontainer', align=uiconst.TOALL, state=uiconst.UI_PICKCHILDREN)
        self.Flush()

    def Width(self):
        w, h = self.GetAbsoluteSize()
        return w

    def Height(self):
        w, h = self.GetAbsoluteSize()
        return h

    def Flush(self, label = None):
        if self.sr.splitareacontent:
            self.sr.splitareacontent.Close()
            self.sr.splitareacontent = None
        elif self.sr.content:
            self.sr.content.Close()
            self.sr.content = None
        self.sr.content = Container(name='__content', align=uiconst.TOALL, parent=self.sr.maincontainer)

    def HideUnderlay(self):
        if self.sr.underlay:
            self.sr.underlay.state = uiconst.UI_HIDDEN

    def ShowUnderlay(self):
        if self.sr.underlay:
            self.sr.underlay.state = uiconst.UI_DISABLED

    def Split(self, splitConst, splitValue, adjustableID = False, line = 1, minSize = None):
        """
        Splits container into subcontainers;
        
        splitConst;     uiconst.SPLITTOP, uiconst.SPLITBOTTOM, uiconst.SPLITLEFT, uiconst.SPLITRIGHT
        splitValue;     if splitvalue is float it will split portionally and resize
                        when window is scaled. If it is int its considered pixelvalue.
        adjustableID;   If passed the splitter will be adjustable and the id is used to
                        register its position in prefs
        minSize         Minimum size if adjustable
        
        The areas are returned in same order as the splitlist + one area (remaining space)
        """
        if not self.sr.splitareacontent:
            self.sr.splitareacontent = Container(parent=self.sr.maincontainer, name='__splitareas_and_content', align=uiconst.TOALL, state=uiconst.UI_PICKCHILDREN)
            self.sr.content.SetParent(self.sr.splitareacontent)
        idx = 0
        for each in self.sr.splitareacontent.children:
            if each.name.endswith('_SplitArea'):
                idx = self.sr.splitareacontent.children.index(each) + 1

        if adjustableID:
            lastSize = settings.user.ui.Get('AreaSplitSize_%s' % adjustableID, None)
            if lastSize is not None:
                splitValue = lastSize
        w = h = 0
        if splitConst == uiconst.SPLITTOP:
            h = splitValue
            a = uiconst.TOTOP
            la = uiconst.TOBOTTOM
            s = 'top'
        elif splitConst == uiconst.SPLITBOTTOM:
            h = splitValue
            a = uiconst.TOBOTTOM
            la = uiconst.TOTOP
            s = 'bottom'
        elif splitConst == uiconst.SPLITLEFT:
            w = splitValue
            a = uiconst.TOLEFT
            la = uiconst.TORIGHT
            s = 'left'
        elif splitConst == uiconst.SPLITRIGHT:
            w = splitValue
            a = uiconst.TORIGHT
            la = uiconst.TOLEFT
            s = 'right'
        else:
            raise NotImplementedError
        newArea = Area(name=s + '_SplitArea', align=a, parent=self.sr.splitareacontent, idx=idx, clipChildren=1)
        newArea.isSplitArea = True
        newArea.Flush()
        newArea.isTabOrderGroup = True
        if type(splitValue) == types.FloatType:
            newArea.splitValue = splitValue
        else:
            newArea.width = w
            newArea.height = h
            newArea.splitValue = None
        if adjustableID:
            div = Divider(name='divider', align=a, pos=(0, 0, 5, 5), idx=idx + 1, parent=self.sr.splitareacontent)
            div.OnChangeStart_ = self.ScaleAreaStart
            div.OnChanged_ = self.ScaleAreaEnd
            div.OnChange_ = self.ScaleArea
            div.sr.area = newArea
            div.name = 'div_%s_SplitArea' % s
            if line:
                Line(name='line_%s_SplitArea' % s, parent=div, align=a)
                Line(name='line_%s_SplitArea' % s, parent=div, align=la)
        elif line:
            Line(name='line_%s_SplitArea' % s, parent=self.sr.splitareacontent, align=a, idx=idx + 1)
        newArea._adjustableData = (adjustableID, minSize)
        self._AdjustDividers(useSettings=True)
        return newArea

    def SetLabel(self, text):
        self.sr.label = Label(parent=self.sr.content, name='__caption', text=text, state=uiconst.UI_DISABLED, align=uiconst.TOPLEFT, idx=0, pos=(4, 2, 0, 0), uppercase=uiconst.WINHEADERUPPERCASE, fontsize=uiconst.WINHEADERFONTSIZE, letterspace=uiconst.WINHEADERLETTERSPACE)
        self.sr.label.affectWidth = 1
        self.sr.label.affectHeight = 1

    def OnContentResize(self, *args):
        self._AdjustDividers()

    def GetMinSize(self):
        return (0, 0)

    def _GetMinSize(self, container):
        mWidth = 0
        mHeight = 0
        tWidth = 0
        tHeight = 0
        cl, ct, cw, ch = container.GetAbsolute()
        for sizer in container.children:
            sl, st, sw, sh = sizer.GetAbsolute()
            dl, dt, dw, dh = (cl - sl,
             ct - st,
             cw - sw,
             ch - sh)
            check = 0
            if hasattr(sizer, 'affectWidth'):
                mWidth = max(mWidth, dl + sizer.width)
                check = 1
            if hasattr(sizer, 'affectHeight'):
                mHeight = max(mHeight, dt + sizer.height)
                check = 1
            if hasattr(sizer, 'GetMinSize'):
                w, h = sizer.GetMinSize()
                mHeight = max(mHeight, dt + h)
                mWidth = max(mWidth, dl + w)
                check = 1
            if check:
                if sizer.align in (uiconst.TOTOP, uiconst.TOBOTTOM):
                    tHeight += mHeight
                elif sizer.align in (uiconst.TOLEFT, uiconst.TORIGHT):
                    tWidth += mWidth
                elif sizer.align == uiconst.TOALL:
                    tWidth += mWidth
                    tHeight += mHeight
                else:
                    tWidth += mWidth
                    tHeight += mHeight

        return (tWidth, tHeight)

    def _OnResize(self, *args, **kw):
        Container._OnResize(self, *args, **kw)
        self._AdjustDividers()

    def Append(self, item):
        self.sr.content.children.append(item)

    def Insert(self, idx, item):
        self.sr.content.children.insert(idx, item)

    @telemetry.ZONE_METHOD
    def _AdjustDividers(self, useSettings = False):

        def Crawl(p):
            errorHeight = 0.0
            errorWidth = 0.0
            pl, pt, pw, ph = p.GetAbsolute()
            for each in p.children:
                if not getattr(each, 'isSplitArea', False):
                    continue
                sv = getattr(each, 'splitValue', None)
                if sv is not None:
                    mw, mh = each.GetMinSize()
                    adjustableID, minSize = getattr(each, '_adjustableData', (None, None))
                    if each.align in (uiconst.TOTOP, uiconst.TOBOTTOM):
                        lastSize = settings.user.ui.Get('AreaSplitSize_%s' % adjustableID, None)
                        if useSettings and adjustableID and lastSize is not None:
                            each.height = lastSize
                        else:
                            if mh:
                                desiredHeight = max(mh, sv * ph + errorHeight, minSize)
                            else:
                                desiredHeight = sv * ph + errorHeight
                            each.height = int(desiredHeight)
                            errorHeight = desiredHeight - each.height
                            if adjustableID:
                                settings.user.ui.Set('AreaSplitSize_%s' % adjustableID, each.height)
                    elif each.align in (uiconst.TOLEFT, uiconst.TORIGHT):
                        lastSize = settings.user.ui.Get('AreaSplitSize_%s' % adjustableID, None)
                        if useSettings and adjustableID and lastSize is not None:
                            each.width = lastSize
                        else:
                            if mw:
                                desiredWidth = max(mw, sv * pw + errorWidth, minSize)
                            else:
                                desiredWidth = sv * pw + errorWidth
                            each.width = int(desiredWidth)
                            errorWidth = desiredWidth - each.width
                            if adjustableID:
                                settings.user.ui.Set('AreaSplitSize_%s' % adjustableID, each.width)
                else:
                    adjustableID, minSize = getattr(each, '_adjustableData', (None, None))
                    if each.align in (uiconst.TOLEFT, uiconst.TORIGHT):
                        each.width = min(pw - 10, max(10, each.width))
                        if adjustableID:
                            settings.user.ui.Set('AreaSplitSize_%s' % adjustableID, each.width)
                    elif each.align in (uiconst.TOTOP, uiconst.TOBOTTOM):
                        each.height = min(ph - 10, max(10, each.height))
                        if adjustableID:
                            settings.user.ui.Set('AreaSplitSize_%s' % adjustableID, each.height)
                if hasattr(each, 'children'):
                    Crawl(each)

        if not self.destroyed and self.sr.splitareacontent:
            Crawl(self.sr.splitareacontent)

    def ScaleAreaStart(self, divider, *args):
        area = divider.sr.area
        self._initWH = area.width or area.height

    def ScaleArea(self, divider, x, y, *args):
        area = divider.sr.area
        if area.align == uiconst.TOTOP:
            area.height = self._initWH + y
        elif area.align == uiconst.TOBOTTOM:
            area.height = self._initWH - y
        elif area.align == uiconst.TOLEFT:
            area.width = self._initWH + x
        elif area.align == uiconst.TORIGHT:
            area.width = self._initWH - x
        else:
            raise NotImplementedError
        area.width = max(0, area.width)
        area.height = max(0, area.height)

    def ScaleAreaEnd(self, divider, *args):
        area = divider.sr.area
        al, at, aw, ah = area.GetAbsolute()
        pl, pt, pw, ph = area.parent.GetAbsolute()
        mn = 16 / float(pw)
        if area.splitValue:
            if area.align in (uiconst.TOLEFT, uiconst.TORIGHT):
                area.splitValue = min(1.0 - mn, max(mn, float(aw) / float(pw)))
            elif area.align in (uiconst.TOTOP, uiconst.TOBOTTOM):
                area.splitValue = min(1.0 - mn, max(mn, float(ah) / float(ph)))
        elif area.align in (uiconst.TOLEFT, uiconst.TORIGHT):
            area.width = min(pw - 10, max(10, area.width))
        elif area.align in (uiconst.TOTOP, uiconst.TOBOTTOM):
            area.height = min(ph - 10, max(10, area.height))
        self._AdjustDividers()

    def LoadFrame(self, color = None, offset = -2, iconPath = 'ui_1_16_209', cornerSize = 7):
        if not self.sr.frame:
            if self.sr.underlay:
                idx = GetIndex(self.sr.underlay)
            else:
                idx = -1
            self.sr.frame = Frame(name='__frame', color=color, frameConst=(iconPath, cornerSize, offset), parent=self, idx=idx)

    def LoadUnderlay(self, color = None, offset = -2, iconPath = 'ui_1_16_161', cornerSize = 7):
        if not self.sr.underlay:
            self.sr.underlay = Frame(name='__underlay', color=color, frameConst=(iconPath, cornerSize, offset), parent=self)
