#Embedded file name: eve/client/script/ui/control\divider.py
import carbonui.const as uiconst
import uiprimitives

class Divider(uiprimitives.Container):
    __guid__ = 'xtriui.Divider'
    __nonpersistvars__ = []
    dragging = 0
    startvalue = None
    initx = None
    inity = None
    default_cursor = 18

    def _OnClose(self):
        uiprimitives.Container._OnClose(self)
        self.OnSizeChanged = None
        self.OnSizeChanging = None
        self.OnSizeChangeStarting = None

    def Startup(self, victim, attribute, xory, minValue = 1, maxValue = 1600):
        self.sr.victim = victim
        self.attribute = attribute
        self.xory = xory
        self.SetMinMax(minValue, maxValue)
        self.cursor = [11, 18][xory == 'x']

    def OnMouseDown(self, *args):
        self.dragging = 1
        self.OnSizeChangeStarting(self)
        self.initx = uicore.uilib.x
        self.inity = uicore.uilib.y
        self.initvalue = getattr(self.sr.victim, self.attribute, 0)

    def OnMouseUp(self, *args):
        self.dragging = 0
        self.OnSizeChanged()

    def SetMinMax(self, minValue = None, maxValue = None):
        if minValue is not None:
            self.min = minValue
        if maxValue is not None:
            self.max = maxValue

    def OnMouseMove(self, *args):
        if self.dragging:
            self.diffx = uicore.uilib.x - self.initx
            self.diffy = uicore.uilib.y - self.inity
            diff = getattr(self, 'diff%s' % self.xory, 0)
            if self.sr.victim.align in (uiconst.TOBOTTOM, uiconst.TORIGHT):
                diff = -diff
            newvalue = min(self.max, max(self.min, diff + self.initvalue))
            setattr(self.sr.victim, self.attribute, newvalue)
            self.OnSizeChanging()

    def OnSizeChangeStarting(self, *args):
        """ Overwriteable """
        pass

    def OnSizeChanged(self, *args):
        """ Overwriteable """
        pass

    def OnSizeChanging(self, *args):
        """ Overwriteable """
        pass


class DividedContainer(uiprimitives.Container):
    """
        This is a container that has 2 subcontainers, and a splitter between them.
        The 2 subcontainer can either be side by side, or top and bottom.
        There is one "victim" container, and that container takes up a certain percentage
        of the container, then the splitter is added, and the restCont fills up the rest.
        "victimlocation" specifies the alignment of the victim 
        (can be uiconst.TOTOP, uiconst.TOBOTTOM, uiconst.TORIGHT, uiconst.TOLEFT), 
        and that determines if the splitter is a vertical or horizontal.
    """
    __guid__ = 'uicls.DividedContainer'
    default_splitterSize = 4

    def ApplyAttributes(self, attributes):
        self.initx = None
        self.inity = None
        self.dragging = 0
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.settingName = attributes.settingName
        self.splitterSize = attributes.get('splitterSize', self.default_splitterSize)
        victimAlignment = attributes.victimAlignment or uiconst.TOTOP
        if victimAlignment in (uiconst.TOLEFT, uiconst.TORIGHT):
            self.isVertical = True
            self.totalValue = self.GetAbsoluteSize()[0]
        else:
            self.isVertical = False
            self.totalValue = self.GetAbsoluteSize()[1]
        self.minVictimValue = attributes.get('minVictimValue', 0)
        self.minRestValue = attributes.get('minRestValue', 0)
        self.maxVictimValue = attributes.get('maxVictimValue', const.maxBigint)
        self.victimRatio = ratio = attributes.victimValueRatio or settings.user.ui.Get(self.settingName, 0.5)
        startingVictimValue = int(ratio * self.totalValue)
        biggsetVictimAllowed = self.totalValue - self.splitterSize - self.minRestValue
        startingVictimValue = min(startingVictimValue, biggsetVictimAllowed)
        startingVictimValue = max(self.minVictimValue, startingVictimValue)
        self.victimValue = startingVictimValue
        if self.isVertical:
            self.victimCont = uiprimitives.Container(parent=self, name='victimCont', align=victimAlignment, width=startingVictimValue)
            splitter = uiprimitives.Container(parent=self, align=victimAlignment, width=self.splitterSize, state=uiconst.UI_NORMAL)
            splitter.cursor = 18
        else:
            self.victimCont = uiprimitives.Container(parent=self, name='victimCont', align=victimAlignment, height=startingVictimValue)
            splitter = uiprimitives.Container(parent=self, align=victimAlignment, height=self.splitterSize, state=uiconst.UI_NORMAL)
            splitter.cursor = 11
        self.restCont = uiprimitives.Container(parent=self, name='restCont', align=uiconst.TOALL)
        splitter.OnMouseDown = self.OnSplitterMouseDown
        splitter.OnMouseUp = self.OnSplitterMouseUp
        splitter.OnMouseMove = self.OnSplitterMouseMove
        self.splitter = splitter
        self.setupDone = True

    def OnSplitterMouseDown(self, *args):
        self.dragging = 1
        self.OnSizeChangeStarting(self)
        self.initx = uicore.uilib.x
        self.inity = uicore.uilib.y
        if self.isVertical:
            self.totalValue = self.GetAbsoluteSize()[0]
            self.victimInitvalue = self.victimCont.width
            self.restInitvalue = self.restCont.GetAbsoluteSize()[0]
        else:
            self.totalValue = self.GetAbsoluteSize()[1]
            self.victimInitvalue = self.victimCont.height
            self.restInitvalue = self.restCont.GetAbsoluteSize()[1]

    def OnSplitterMouseUp(self, *args):
        self.dragging = 0
        self.totalValue = None
        self.OnSizeChanged()

    def OnSplitterMouseMove(self, *args):
        if self.dragging:
            self.splitter.diffx = uicore.uilib.x - self.initx
            self.splitter.diffy = uicore.uilib.y - self.inity
            if self.isVertical:
                if self.totalValue is None:
                    self.totalValue = self.GetAbsoluteSize()[0]
                diff = self.splitter.diffx
            else:
                if self.totalValue is None:
                    self.totalValue = self.GetAbsoluteSize()[1]
                diff = self.splitter.diffy
            if self.victimCont.align in (uiconst.TOBOTTOM, uiconst.TORIGHT):
                diff = -diff
            mostDiffAllowed = self.restInitvalue - self.minRestValue
            diff = min(diff, mostDiffAllowed)
            newValue = max(self.minVictimValue, diff + self.victimInitvalue)
            newValue = min(self.maxVictimValue, newValue)
            if self.isVertical:
                self.victimCont.width = newValue
            else:
                self.victimCont.height = newValue
            self.victimValue = newValue
            self.victimRatio = float(newValue) / self.totalValue
            self.OnSizeChanging()

    def _OnResize(self, *args):
        uiprimitives.Container._OnResize(self)
        if not getattr(self, 'setupDone', False):
            return
        if self.isVertical:
            totalValue = self.displayWidth
            victimNewValue = max(int(totalValue * self.victimRatio), self.minVictimValue)
            biggsetVictimAllowed = totalValue - self.splitterSize - self.minRestValue
            biggsetVictimAllowed = min(self.maxVictimValue, biggsetVictimAllowed)
            victimNewValue = min(victimNewValue, biggsetVictimAllowed)
            self.victimCont.width = victimNewValue
        else:
            totalValue = self.displayHeight
            victimNewValue = max(int(totalValue * self.victimRatio), self.minVictimValue)
            biggsetVictimAllowed = totalValue - self.splitterSize - self.minRestValue
            biggsetVictimAllowed = min(self.maxVictimValue, biggsetVictimAllowed)
            victimNewValue = min(victimNewValue, biggsetVictimAllowed)
            self.victimCont.height = victimNewValue

    def OnSizeChangeStarting(self, *args):
        """ Overwriteable """
        pass

    def OnSizeChanged(self, *args):
        """ Overwriteable """
        pass

    def OnSizeChanging(self, *args):
        """ Overwriteable """
        pass

    def _OnClose(self):
        if self.settingName:
            if self.isVertical:
                totalValue = self.displayWidth
            else:
                totalValue = self.displayHeight
            settingValue = min(float(self.victimValue) / totalValue, 1.0)
            settings.user.ui.Set(self.settingName, settingValue)
        uiprimitives.Container._OnClose(self)
        self.OnSizeChanged = None
        self.OnSizeChanging = None
        self.OnSizeChangeStarting = None
