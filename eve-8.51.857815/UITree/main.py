#Embedded file name: UITree\main.py
__author__ = 'fridrik'
import blue
import trinity
import uicls
import uthread
import base
import weakref
import os
import carbonui.const as uiconst
from carbonui.primitives.base import Base
from carbonui.primitives.desktop import UIRoot
from carbonui.control.layer import LayerCore
from carbonui.primitives.container import Container
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.frame import Frame
from carbonui.primitives.fill import Fill
from carbonui.primitives.sprite import Sprite
from carbonui.control.divider import Divider
from carbonui.util.various_unsorted import *
from carbonui.control.scrollentries import SE_BaseClassCore
from carbonui.control.scrollentries import ScrollEntryNode
from eve.client.script.ui.control.eveWindow import Window
from eve.client.script.ui.control.eveLabel import EveLabelMedium as Label
from eve.client.script.ui.control.eveScroll import Scroll
from eve.client.script.ui.control.utilMenu import UtilMenu
from eve.client.script.ui.control.buttons import Button
from eve.client.script.ui.control.eveSinglelineEdit import SinglelineEdit
RESROOT = os.path.dirname(__file__) + '\\res\\'
VALUEOFFSET = 160
IGNORE_PROPERTIES = ['dead']
ALIGNMENTNAMES = {uiconst.NOALIGN: 'NOALIGN',
 uiconst.TOLEFT: 'TOLEFT',
 uiconst.TORIGHT: 'TORIGHT',
 uiconst.TOTOP: 'TOTOP',
 uiconst.TOBOTTOM: 'TOBOTTOM',
 uiconst.TOLEFT_NOPUSH: 'TOLEFT_NOPUSH',
 uiconst.TORIGHT_NOPUSH: 'TORIGHT_NOPUSH',
 uiconst.TOTOP_NOPUSH: 'TOTOP_NOPUSH',
 uiconst.TOBOTTOM_NOPUSH: 'TOBOTTOM_NOPUSH',
 uiconst.TOLEFT_PROP: 'TOLEFT_PROP',
 uiconst.TORIGHT_PROP: 'TORIGHT_PROP',
 uiconst.TOTOP_PROP: 'TOTOP_PROP',
 uiconst.TOBOTTOM_PROP: 'TOBOTTOM_PROP',
 uiconst.TOALL: 'TOALL',
 uiconst.ABSOLUTE: 'ABSOLUTE',
 uiconst.TOPLEFT: 'TOPLEFT',
 uiconst.TOPLEFT_PROP: 'TOPLEFT_PROP',
 uiconst.TOPRIGHT: 'TOPRIGHT',
 uiconst.BOTTOMRIGHT: 'BOTTOMRIGHT',
 uiconst.BOTTOMLEFT: 'BOTTOMLEFT',
 uiconst.CENTER: 'CENTER',
 uiconst.CENTERBOTTOM: 'CENTERBOTTOM',
 uiconst.CENTERTOP: 'CENTERTOP',
 uiconst.CENTERLEFT: 'CENTERLEFT',
 uiconst.CENTERRIGHT: 'CENTERRIGHT',
 uiconst.ATTACHED: 'ATTACHED'}
PICKSTATENAMES = {}
for k, v in uiconst.__dict__.iteritems():
    if k.startswith('TR2_SPS'):
        PICKSTATENAMES[v] = k

SPRITEEFFECTNAMES = {}
BLENDMODENAMES = {}
for k, v in trinity.__dict__.iteritems():
    if k.startswith('TR2_SFX'):
        SPRITEEFFECTNAMES[v] = k
    if k.startswith('TR2_SBM'):
        BLENDMODENAMES[v] = k

COMBOPROPERTIES = {'align': ALIGNMENTNAMES,
 'pickState': PICKSTATENAMES,
 'spriteEffect': SPRITEEFFECTNAMES,
 'blendMode': BLENDMODENAMES}
COMBOPROPERTIES_NAMESPACE = {'align': 'uiconst',
 'pickState': 'uiconst',
 'spriteEffect': 'trinity',
 'blendMode': 'trinity'}
PROPERTYCAPS = {'opacity': (0.0, 5.0),
 'glowColor': (0.0, 1.0),
 'color.r': (0.0, 5.0),
 'color.g': (0.0, 5.0),
 'color.b': (0.0, 5.0),
 'color.a': (0.0, 5.0),
 'color': (0.0, 5.0),
 'pickRadius': (-1, sys.maxint)}
PYOBJECT_SUBLISTS = ('children', 'background')
PYOBJECT_SUBDICTS = ()

class UITree(Window):
    default_windowID = 'uitree'
    default_caption = 'UI Roots'
    default_width = 300
    default_height = 400
    default_minSize = (default_width, default_height)
    default_left = '__center__'
    default_top = '__center__'
    filterString = None

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        mainArea = self.GetMainArea()
        mainArea.padding = 6
        self._selectedObject = None
        self.SetTopparentHeight(0)
        self._infoContainer = Container(parent=mainArea, align=uiconst.TOTOP, height=72)
        self.searchInput = SinglelineEdit(parent=self._infoContainer, align=uiconst.BOTTOMRIGHT, left=4, top=8, width=100, OnChange=self.OnSearchInputChange, hinttext='Search')
        self.searchInput.SetHistoryVisibility(False)
        self.searchInput.ShowClearButton()
        m = UtilMenu(menuAlign=uiconst.TOPRIGHT, parent=self._infoContainer, align=uiconst.TOPRIGHT, GetUtilMenu=self.SettingMenu)
        self._infoLabel = Label(parent=self._infoContainer, state=uiconst.UI_DISABLED, color=(1.0, 1.0, 1.0, 0.75), left=2)
        self.searchResultParent = ContainerAutoSize(parent=mainArea, align=uiconst.TOTOP_NOPUSH, padding=(26, -6, 4, 0), bgColor=(0.5, 0.5, 0.5, 1))
        self.attributeScroll = Scroll(parent=mainArea, align=uiconst.TOBOTTOM, name='attributeScroll')
        self.attributeScroll.height = min(self.height / 2, max(72, settings.user.ui.Get('uitree_attributeScroll_height', 200)))
        settings.user.ui.Set('uitree_attributeScroll_height', self.attributeScroll.height)
        self.divider = Divider(align=uiconst.TOBOTTOM, parent=mainArea, height=11, state=uiconst.UI_NORMAL)
        self.divider.OnChange_ = self.OnDividerMove
        self.divider.OnChangeStart_ = self.OnDividerMoveStart
        Fill(parent=self.divider, align=uiconst.CENTER, pos=(0, 0, 20, 1))
        self.scroll = Scroll(parent=mainArea, name='treeScroll')
        self._hiliteFrame = Fill(parent=uicore.desktop, align=uiconst.ABSOLUTE, color=(0, 1, 0, 0.3), idx=0, state=uiconst.UI_DISABLED)
        self._selectedFrame = Frame(parent=uicore.desktop, align=uiconst.ABSOLUTE, color=(0, 1, 0, 0.3), idx=0, state=uiconst.UI_DISABLED)
        self.ReloadUIRoots()
        uthread.new(self.UpdateInfo)
        self._keyDownCookie = uicore.uilib.RegisterForTriuiEvents([uiconst.UI_KEYDOWN], self.OnGlobalKeyDown)

    def OnSearchInputChange(self, *args):
        self.searchThread = base.AutoTimer(250, self.SearchTree)

    def SearchTree(self):
        self.searchThread = None
        self.filterString = self.searchInput.GetValue()
        if not self.filterString:
            self.searchResultParent.Hide()
            self.searchResultParent.Flush()
            return
        self.searchResultParent.Flush()
        res = []
        searchFor = self.filterString.lower()

        def Crawl(obj, path):
            if obj is self:
                return
            if searchFor in obj.name.lower():
                if path:
                    res.append((obj, path + '/ <b>' + obj.name + '</b>'))
                else:
                    res.append((obj, '<b>' + obj.name + '</b>'))
            if hasattr(obj, 'children'):
                for each in obj.children:
                    if path:
                        Crawl(each, path + '/' + obj.name)
                    else:
                        Crawl(each, obj.name)

        for root in uicore.uilib.rootObjects:
            Crawl(root, '')

        if res:
            for obj, path in res[:20]:
                label = Label(parent=self.searchResultParent, align=uiconst.TOTOP, text=path, state=uiconst.UI_NORMAL, padding=(10, 2, 10, 2))
                label._searchObj = obj
                label.hint = path
                label.OnClick = (self.OnSearchResultClick, obj)

            if len(res) > 20:
                Label(parent=self.searchResultParent, align=uiconst.TOTOP, text='and even more... (%s found)' % len(res), padding=(10, 2, 10, 2))
        else:
            Label(parent=self.searchResultParent, align=uiconst.TOTOP, text='No Match!', padding=(10, 3, 10, 3))
        self.searchResultParent.Show()

    def OnSearchResultClick(self, obj):
        self.searchResultParent.Hide()
        self.ShowUIObject(obj)

    def _OnSizeChange_NoBlock(self, *args, **kwds):
        Window._OnSizeChange_NoBlock(self, *args, **kwds)
        self.attributeScroll.height = min(self.height / 2, max(72, settings.user.ui.Get('uitree_attributeScroll_height', 200)))
        settings.user.ui.Set('uitree_attributeScroll_height', self.attributeScroll.height)

    def OnDividerMove(self, divider, dx, dy):
        self.attributeScroll.height = min(self.height / 2, max(72, self._initAttributeScrollHeight - dy))
        settings.user.ui.Set('uitree_attributeScroll_height', self.attributeScroll.height)

    def OnDividerMoveStart(self, *args):
        self._initAttributeScrollHeight = self.attributeScroll.height

    def SettingMenu(self, menuParent, *args):
        checked = settings.user.ui.Get('uitreeShowPickHilite', True)
        menuParent.AddCheckBox(text='Show pick hilite', checked=checked, callback=(self.ToggleCheckboxSetting, 'ShowPickHilite'))
        checked = settings.user.ui.Get('uitreeIgnoreFullScreenPick', False)
        menuParent.AddCheckBox(text='Ignore fullscreen hilite', checked=checked, callback=(self.ToggleCheckboxSetting, 'IgnoreFullScreenPick'))
        menuParent.AddIconEntry(icon=None, text='Move To Desktop', callback=self.MoveToDesktop)
        menuParent.AddIconEntry(icon=None, text='Reload Textures', callback=self.ReloadTextures)

    def ReloadTextures(self):
        import blue
        for resPath in blue.motherLode.GetNonCachedKeys() + blue.motherLode.GetCachedKeys():
            if resPath.lower().startswith('res:/ui'):
                res = blue.motherLode.Lookup(resPath)
                if res:
                    if hasattr(res, 'Reload'):
                        res.Reload()

    def MoveToDesktop(self):
        self.SetParent(uicore.desktop, idx=0)

    def ToggleCheckboxSetting(self, settingName, *args):
        checked = settings.user.ui.Get('uitree' + settingName, True)
        settings.user.ui.Set('uitree' + settingName, not checked)

    def Close(self, *args, **kwds):
        frame = getattr(self, '_hiliteFrame', None)
        if frame:
            frame.Close()
        if getattr(self, '_selectedFrame', None):
            self._selectedFrame.Close()
        Window.Close(self, *args, **kwds)

    def OnGlobalKeyDown(self, *args, **kwds):
        if self.destroyed:
            return False
        ctrl = uicore.uilib.Key(uiconst.VK_CONTROL)
        alt = uicore.uilib.Key(uiconst.VK_MENU)
        if ctrl and not (IsUnder(uicore.uilib.mouseOver, self) or uicore.uilib.mouseOver is self):
            self.ShowUIObject(uicore.uilib.mouseOver)
        return True

    def UpdateInfo(self):
        while not self.destroyed:
            mo = uicore.uilib.mouseOver
            if mo:
                infoText = 'MouseOver: %s' % mo.name
            else:
                infoText = 'MouseOver: None'
            active = uicore.registry.GetActive()
            if active:
                infoText += '<br>Active: %s' % active.name
            else:
                infoText += '<br>Active: None'
            focus = uicore.registry.GetFocus()
            if focus:
                infoText += '<br>Focus: %s' % (focus.name or focus.__guid__)
            else:
                infoText += '<br>Focus: None'
            capture = uicore.uilib.GetMouseCapture()
            if capture:
                infoText += '<br>Capture: %s' % (capture.name or capture.__guid__)
            else:
                infoText += '<br>Capture: None'
            infoText += '<br>MouseX/Y: %s, %s' % (uicore.uilib.x, uicore.uilib.y)
            showHilite = settings.user.ui.Get('uitreeShowPickHilite', True)
            ignoreFullScreenPick = settings.user.ui.Get('uitreeIgnoreFullScreenPick', False)
            hiliteUIObject = None
            if showHilite:
                if IsUnder(mo, self):
                    if IsUnder(mo, self.scroll):
                        uiObjectGetAbs = GetAttrs(mo, 'sr', 'node', 'uiObject', 'GetAbsolute')
                        if uiObjectGetAbs:
                            hiliteUIObject = GetAttrs(mo, 'sr', 'node', 'uiObject')
                elif mo is not uicore.desktop and mo is not self and not IsUnder(mo, self) and self.state == uiconst.UI_NORMAL:
                    hiliteUIObject = mo
            if hiliteUIObject and ignoreFullScreenPick and isinstance(hiliteUIObject, (LayerCore, UIRoot)):
                hiliteUIObject = None
            self.ShowHilitedObjectInUI(hiliteUIObject)
            selectedObject = None
            if self._selectedObject:
                selectedObject = self._selectedObject()
                if getattr(selectedObject, 'destroyed', False):
                    selectedObject = None
            for node in self.scroll.sr.nodes:
                if node.panel:
                    node.panel.UpdateSelected(selectedObject)
                    node.panel.UpdatePickHilite(hiliteUIObject)
                    if getattr(node.uiObject, 'destroyed', False):
                        node.panel.CheckDestroyed()

            self.ShowSelectedObjectInUI(selectedObject)
            self._infoLabel.text = infoText
            self._infoContainer.height = self._infoLabel.textheight + 5
            blue.pyos.synchro.SleepWallclock(100)

    def ShowSelectedObjectInUI(self, uiObject):
        if uiObject and hasattr(uiObject, 'GetAbsolute'):
            self._selectedFrame.pos = uiObject.GetAbsolute()
            self._selectedFrame.display = True
        else:
            self._selectedFrame.display = False

    def ShowHilitedObjectInUI(self, uiObject):
        if self.destroyed:
            return
        if uiObject:
            self._hiliteFrame.pos = uiObject.GetAbsolute()
            self._hiliteFrame.display = True
        else:
            self._hiliteFrame.display = False

    def ReloadUIRoots(self, *args):
        startRoot = uicore.uilib.rootObjects
        scrollNodes = []
        for root in startRoot:
            self._CrawlUIObject(root, scrollNodes, 0)

        self.scroll.LoadContent(contentList=scrollNodes)

    def _AddUIObject(self, uiObject, scrollList, lvl, isExpanded = False, objectLabel = None, isExpandable = False):
        if len(scrollList) > 1 and lvl:
            for i in xrange(1, len(scrollList) - 1):
                last = scrollList[-i]
                if last.level < lvl:
                    break
                if lvl not in last.connectLevels:
                    last.connectLevels.append(lvl)

        node = ScrollEntryNode(decoClass=UITreeEntry, uiObject=uiObject, level=lvl, isExpanded=isExpanded, objectLabel=objectLabel, isExpandable=isExpandable, connectLevels=[lvl])
        scrollList.append(node)

    def IsExpanded(self, uiObject):
        desktopObjectID = id(uicore.desktop)
        allPrefs = settings.user.ui.Get('UITreeExpandedObjects', {})
        if desktopObjectID not in allPrefs:
            return False
        uiObjectID = id(uiObject)
        if getattr(uiObject, 'parent', None):
            uiObjectID = (id(uiObject.parent), uiObjectID)
        return uiObjectID in allPrefs[desktopObjectID]

    def ExpandUIObject(self, uiObject):
        uiObjectID = id(uiObject)
        if getattr(uiObject, 'parent', None):
            uiObjectID = (id(uiObject.parent), uiObjectID)
        desktopObjectID = id(uicore.desktop)
        allPrefs = settings.user.ui.Get('UITreeExpandedObjects', {})
        if desktopObjectID not in allPrefs:
            allPrefs[desktopObjectID] = []
        if uiObjectID not in allPrefs[desktopObjectID]:
            allPrefs[desktopObjectID].append(uiObjectID)
        settings.user.ui.Set('UITreeExpandedObjects', allPrefs)

    def ToggleExpandedObject(self, uiObject):
        uiObjectID = id(uiObject)
        if getattr(uiObject, 'parent', None):
            uiObjectID = (id(uiObject.parent), uiObjectID)
        desktopObjectID = id(uicore.desktop)
        allPrefs = settings.user.ui.Get('UITreeExpandedObjects', {})
        if desktopObjectID not in allPrefs:
            allPrefs[desktopObjectID] = []
        if uiObjectID in allPrefs[desktopObjectID]:
            allPrefs[desktopObjectID].remove(uiObjectID)
        else:
            allPrefs[desktopObjectID].append(uiObjectID)
        settings.user.ui.Set('UITreeExpandedObjects', allPrefs)
        self.ReloadUIRoots()

    def _CrawlUIObject(self, uiObject, scrollNodes, lvl, objectLabel = None):
        """Defines what to show in the tree"""
        isExpandable = UITree._IsExpandable(uiObject)
        if isExpandable:
            isExpanded = self.IsExpanded(uiObject)
        else:
            isExpanded = False
        self._AddUIObject(uiObject, scrollNodes, lvl, isExpanded, objectLabel=objectLabel, isExpandable=isExpandable)
        if isExpanded:
            if isinstance(uiObject, Base):
                allPy = dir(uiObject)
                for propertyName in allPy:
                    if propertyName.startswith('_') or propertyName in IGNORE_PROPERTIES:
                        continue
                    try:
                        prop = getattr(uiObject, propertyName, None)
                    except:
                        print 'Failed on property', propertyName
                        continue

                    try:
                        if getattr(prop, 'TypeInfo', None):
                            self._CrawlUIObject(prop, scrollNodes, lvl + 1, objectLabel=propertyName)
                    except (KeyError, RuntimeError):
                        pass

                for dictName in PYOBJECT_SUBDICTS:
                    dct = getattr(uiObject, dictName, {})
                    if dct:
                        for k, v in dct.iteritems():
                            self._CrawlUIObject(v, scrollNodes, lvl + 1, objectLabel='%s: %s' % (dictName.lstrip('_'), k))

                for listName in PYOBJECT_SUBLISTS:
                    lst = getattr(uiObject, listName, [])
                    if lst:
                        for objChild in lst:
                            if listName == 'background':
                                self._CrawlUIObject(objChild, scrollNodes, lvl + 1, objectLabel=listName)
                            else:
                                self._CrawlUIObject(objChild, scrollNodes, lvl + 1)

            else:
                allC = dir(uiObject)
                for propertyName in allC:
                    if propertyName.startswith('_'):
                        continue
                    prop = getattr(uiObject, propertyName, None)
                    if callable(prop):
                        continue
                    if getattr(prop, '__bluetype__', None) == 'blue.List':
                        isExpanded = self.IsExpanded(prop)
                        self._AddUIObject(prop, scrollNodes, lvl + 1, isExpanded, isExpandable=True, objectLabel='%s (%s)' % (propertyName, len(prop)))
                        if isExpanded:
                            for each in prop:
                                self._CrawlUIObject(each, scrollNodes, lvl + 2)

                        continue
                    elif getattr(prop, '__bluetype__', None) == 'blue.Dict':
                        isExpanded = self.IsExpanded(prop)
                        self._AddUIObject(prop, scrollNodes, lvl + 1, isExpanded, isExpandable=True, objectLabel=propertyName)
                        if isExpanded:
                            for k, v in prop.items():
                                self._CrawlUIObject(v, scrollNodes, lvl + 2, objectLabel=k)

                        continue
                    elif hasattr(prop, 'TypeInfo'):
                        self._CrawlUIObject(prop, scrollNodes, lvl + 1, objectLabel=propertyName)

    @classmethod
    def _IsExpandable(cls, uiObject):
        if isinstance(uiObject, Base):
            return True
        allC = dir(uiObject)
        for propertyName in allC:
            if propertyName.startswith('_'):
                continue
            prop = getattr(uiObject, propertyName, None)
            if getattr(prop, '__bluetype__', None) in ('blue.List', 'blue.Dict'):
                return True
            if hasattr(prop, 'TypeInfo'):
                return True

        return False

    def ShowUIObject(self, uiObject):
        traceUp = [uiObject]
        parent = uiObject.parent
        while parent:
            traceUp.insert(0, parent)
            parent = parent.parent

        for each in traceUp:
            self.ExpandUIObject(each)

        self.ShowPropertiesForObject(uiObject)
        for node in self.scroll.sr.nodes:
            if node.uiObject is uiObject:
                self.scroll.ShowNodeIdx(node.idx)
                break

    def ShowPropertiesForObject(self, uiObject):
        if uiObject is None:
            return
        try:
            len(uiObject)
            self.attributeScroll.LoadContent(contentList=[])
            return
        except:
            pass

        self._selectedObject = weakref.ref(uiObject)
        level = 0
        newNodes = []
        if isinstance(uiObject, Base):
            combined = []
            if hasattr(uiObject, 'color'):
                combined.append(('color', ('color.r', 'color.g', 'color.b', 'color.a')))
            for propertyName, subs in combined:
                propertyNode = ScrollEntryNode(decoClass=UITreePropertyEntry, uiObject=uiObject, level=level, propertyName=propertyName, combineProperties=subs)
                newNodes.append(propertyNode)

            basics = ['name',
             'pos',
             'opacity',
             'padding',
             'displayRect',
             'display',
             'pickState',
             'align',
             'clipChildren',
             'pickRadius',
             'absoluteCoordinates',
             'cacheContents',
             'text',
             'blendMode',
             'spriteEffect',
             'effectAmount',
             'effectAmount2',
             'glowColor',
             'glowFactor',
             'glowExpand',
             'useSizeFromTexture',
             'rotation',
             'rotationCenter',
             'scale',
             'scalingCenter',
             'scalingRotation',
             '',
             '__guid__',
             '__class__']
            for propertyName in basics:
                prop = getattr(uiObject, propertyName, '_!_')
                if prop == '_!_':
                    continue
                propertyNode = ScrollEntryNode(decoClass=UITreePropertyEntry, uiObject=uiObject, level=level, propertyName=propertyName)
                newNodes.append(propertyNode)

        else:
            for attr in dir(uiObject):
                if attr[0] == attr[0].upper():
                    continue
                if attr[0] == '_':
                    continue
                if attr in ('children', 'background'):
                    continue
                propertyNode = ScrollEntryNode(decoClass=UITreePropertyEntry, uiObject=uiObject, level=level, propertyName=attr)
                newNodes.append((attr, propertyNode))

            newNodes = SortListOfTuples(newNodes)
        self.ReloadUIRoots()
        self.attributeScroll.LoadContent(contentList=newNodes)


class UITreeNumberInput(Container):
    default_state = uiconst.UI_NORMAL
    _downPos = 0

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self._value = attributes.value
        self._propertyName = attributes.propertyName
        self._propertyIndex = attributes.propertyIndex
        self._uiObject = attributes.uiObject
        self._editType = type(self._value)
        self._label = Label(parent=self, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT, color=(1.0, 1.0, 1.0, 0.75), text=str(self._value))
        if self._propertyName in COMBOPROPERTIES:
            self._label.text = COMBOPROPERTIES[self._propertyName].get(self._value, 'Unknown value!')
            self.expandOnLeft = True
            self.GetMenu = self.GetComboOptions
        elif self._editType == float:
            self.hint = 'MouseDown and Drag to change value<br>ALT for 1/100, ALT-SHIFT for 1/1000'
            if -1 <= self._value <= 1:
                self._label.text = '%.3f' % self._value
        elif self._editType == int:
            self.hint = 'MouseDown and Drag to change value'
        elif self._editType == type:
            try:
                text = repr(self._value).replace("<class '", '').replace("'>", '')
                self._label.text = text
                print 'text', type(self._value), text
            except:
                pass

        self.UpdateSize()

    def GetComboOptions(self, *args):
        m = []
        for value, name in COMBOPROPERTIES[self._propertyName].iteritems():
            m.append((name, self.ChangeComboOption, (value,)))

        return m

    def ChangeComboOption(self, newValue, *args):
        self._value = newValue
        self._label.text = COMBOPROPERTIES[self._propertyName].get(self._value, 'Unknown value!')
        self.UpdateSize()
        self.SetPropertyValue(self._value)

    def UpdateSize(self):
        self.width = self._label.textwidth + 6

    def OnClick(self, *args):
        if self._propertyName in COMBOPROPERTIES:
            return
        if self._editType in (bool,):
            self._value = not self._value
            self.SetPropertyValue(self._value)
            self._label.text = str(self._value)
            self.UpdateSize()

    def OnMouseDown(self, *args):
        if self._propertyName in COMBOPROPERTIES:
            return
        if self._editType in (int, float):
            self._downPos = uicore.uilib.x
            self._updateValue = base.AutoTimer(10, self.ScrollValue)

    def OnMouseUp(self, *args):
        if self._propertyName in COMBOPROPERTIES:
            return
        if self._editType in (int, float):
            self._updateValue = None
            self.ScrollValue(register=True)

    def ScrollValue(self, register = False):
        posDiff = (uicore.uilib.x - self._downPos) / 2
        alt = uicore.uilib.Key(uiconst.VK_MENU)
        shift = uicore.uilib.Key(uiconst.VK_SHIFT)
        if self._editType == float:
            if shift:
                newValue = round(self._value + posDiff / 1000.0, 3)
            elif alt:
                newValue = round(self._value + posDiff / 100.0, 3)
            else:
                newValue = round(self._value + posDiff / 10.0, 3)
        elif shift:
            newValue = self._value + posDiff / 4
        elif alt:
            newValue = self._value + posDiff / 2
        else:
            newValue = self._value + posDiff
        PROPERTYCAPS = {'opacity': (0.0, 5.0),
         'glowColor': (0.0, 1.0),
         'color.r': (0.0, 5.0),
         'color.g': (0.0, 5.0),
         'color.b': (0.0, 5.0),
         'color.a': (0.0, 5.0),
         'color': (0.0, 5.0),
         'pickRadius': (-1, sys.maxint)}
        for capName, (mn, mx) in PROPERTYCAPS.iteritems():
            if capName.lower() in self._propertyName.lower():
                newValue = min(max(newValue, mn), mx)

        self.SetPropertyValue(newValue)
        if self._editType in (float,) and -1 <= newValue <= 1:
            self._label.text = '%.3f' % newValue
        else:
            self._label.text = str(newValue)
        self.UpdateSize()
        if register:
            self._value = newValue

    def SetPropertyValue(self, value):
        obj = self._uiObject
        propertyName = self._propertyName
        if '.' in self._propertyName:
            trace = self._propertyName.split('.')
            for each in trace[:-1]:
                obj = getattr(obj, each, None)
                if not obj:
                    return

            propertyName = trace[-1]
        if self._propertyIndex is not None:
            current = list(getattr(obj, propertyName))
            current[self._propertyIndex] = value
            value = tuple(current)
        try:
            setattr(obj, propertyName, value)
        except:
            pass


INDENTSIZE = 18

class UITreeEntry(SE_BaseClassCore):
    ENTRYHEIGHT = 18

    def ApplyAttributes(self, attributes):
        SE_BaseClassCore.ApplyAttributes(self, attributes)
        self._expandIcon = Sprite(parent=self, align=uiconst.CENTERLEFT, pos=(0, 0, 18, 18))
        self._expandIcon.OnClick = self.ExpandUIObject
        self._label = Label(parent=self, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT, left=20, color=(1.0, 1.0, 1.0, 1))
        self._pickHilite = Frame(name='_pickHilite', bgParent=self, texturePath=RESROOT + 'hiliteBackground.png', color=(0, 1, 0, 0.3), state=uiconst.UI_HIDDEN)
        self._hilite = Fill(name='_hilite', bgParent=self, color=(1, 1, 1, 0.125), state=uiconst.UI_HIDDEN)
        self.loaded = False

    def Load(self, node):
        self.CheckDestroyed()
        if self.loaded:
            return
        self.loaded = True
        if isinstance(node.uiObject, (Base,)):
            self._label.text = node.uiObject.name or node.uiObject.__class__
            if node.objectLabel:
                self._label.text = '%s: %s' % (node.objectLabel, self._label.text)
        else:
            self._label.italic = True
            if node.objectLabel:
                self._label.text = node.objectLabel
            elif getattr(node.uiObject, 'name', None):
                self._label.text = '%s (%s)' % (node.uiObject.name, node.uiObject.__typename__)
            else:
                self._label.text = node.uiObject.__typename__
            self._label.color = (1.0, 1.0, 1.0, 0.5)
        self._label.left = INDENTSIZE * node.level + 20
        if hasattr(node.uiObject, 'Reload') or 'Reload' in getattr(node.uiObject, '__methods__', []):
            reloadIcon = Sprite(texturePath=RESROOT + 'tinyReload.png', pos=(3, 0, 16, 16), parent=self, align=uiconst.CENTERRIGHT, idx=0)
            reloadIcon.OnClick = self.ReloadUIObject
        if node.isExpandable:
            if node.isExpanded:
                self._expandIcon.texturePath = RESROOT + 'containerExpanded_down.png'
            else:
                self._expandIcon.texturePath = RESROOT + 'containerCollapsed.png'
        else:
            self._expandIcon.texturePath = RESROOT + 'nonContainer.png'
            self._expandIcon.state = uiconst.UI_DISABLED
        self._expandIcon.left = INDENTSIZE * node.level
        nextNode = node.scroll.GetNode(node.idx + 1)
        if node.connectLevels is not None:
            for i, connectLevel in enumerate(node.connectLevels):
                if connectLevel == node.level:
                    if not nextNode or connectLevel not in nextNode.connectLevels:
                        texturePath = RESROOT + 'connectionL.png'
                    else:
                        texturePath = RESROOT + 'connectionT.png'
                else:
                    texturePath = RESROOT + 'connectionI.png'
                Sprite(parent=self, texturePath=texturePath, align=uiconst.CENTERLEFT, pos=((connectLevel - 1) * INDENTSIZE,
                 0,
                 INDENTSIZE,
                 INDENTSIZE))

    def ReloadUIObject(self, *args):
        if hasattr(self.sr.node.uiObject, 'Reload'):
            self.CallUIObjectAndReload('Reload')
        elif 'Reload' in self.sr.node.uiObject.__methods__:
            self.CallUIObjectAndReload('Reload')

    def CheckDestroyed(self):
        if isinstance(self.sr.node.uiObject, Base) and self.sr.node.uiObject.destroyed:
            if not getattr(self, '_destroyedIndicator', None):
                self._destroyedIndicator = Fill(parent=self, idx=0, color=(1, 0, 0, 0.3))
            self.state = uiconst.UI_DISABLED

    def UpdateSelected(self, selectedObject):
        if self.sr.node.uiObject and selectedObject is self.sr.node.uiObject:
            if not getattr(self, '_selectedSprite', None):
                self._selectedSprite = Frame(bgParent=self, color=(0, 1, 0, 0.3), padding=(1, 0, 1, 0))
            self._selectedSprite.display = True
        elif getattr(self, '_selectedSprite', None):
            self._selectedSprite.display = False

    def UpdatePickHilite(self, hilitedObject):
        if hilitedObject and self.sr.node.uiObject:
            wnd = UITree.GetIfOpen()
            if hilitedObject is self.sr.node.uiObject:
                self._pickHilite.display = True
                self._pickHilite.spriteEffect = trinity.TR2_SFX_FILL
            elif IsUnder(hilitedObject, self.sr.node.uiObject) and not (wnd and IsUnder(uicore.uilib.mouseOver, wnd.scroll)):
                self._pickHilite.display = True
                self._pickHilite.spriteEffect = trinity.TR2_SFX_COPY
            else:
                self._pickHilite.display = False
        else:
            self._pickHilite.display = False

    def GetMenu(self):
        m = []
        if isinstance(self.sr.node.uiObject, Base):
            if hasattr(self.sr.node.uiObject, 'Reload'):
                m.append(('Reload', self.CallUIObjectAndReload, ('Reload', True)))
            if hasattr(self.sr.node.uiObject, 'Play'):
                m.append(('Play', self.CallUIObjectAndReload, ('Play', True)))
            m.append(('Close', self.CallUIObjectAndReload, ('Close',)))
            if hasattr(self.sr.node.uiObject, 'Flush'):
                m.append(('Flush', self.CallUIObjectAndReload, ('Flush',)))
            m.append(('Move Up', self.MoveUIObject, (-1,)))
            m.append(('Move Down', self.MoveUIObject, (1,)))
            m.append(('Open In Jessica', self.OpenInJessica, (self.sr.node.uiObject,)))
        elif self.sr.node.uiObject:
            if 'Reload' in self.sr.node.uiObject.__methods__:
                m.append(('Reload', self.CallUIObjectAndReload, ('Reload',)))
            if hasattr(self.sr.node.uiObject, 'name') and self.sr.node.uiObject.name not in ('children', 'background'):
                m.append(('Open In Jessica', self.OpenInJessica, (self.sr.node.uiObject,)))
        return m

    def CallUIObjectAndReload(self, functionName, setFocus = False, *args):
        func = getattr(self.sr.node.uiObject, functionName, None)
        if func:
            returnValue = func()
            self.ReloadUITree()
            if setFocus and returnValue:
                wnd = UITree.GetIfOpen()
                if wnd:
                    uthread.new(wnd.ShowUIObject, returnValue)

    def MoveUIObject(self, direction):
        uiObject = self.sr.node.uiObject
        currentIndex = uiObject.parent.children.index(uiObject)
        uiObject.SetParent(uiObject.parent, direction + currentIndex)
        self.ReloadUITree()

    def ReloadUITree(self):
        wnd = GetWindowAbove(self)
        if wnd:
            wnd.ReloadUIRoots()

    def CopySourceToClipboard(self):
        uiObject = self.sr.node.uiObject
        objClass = uiObject.__class__
        wrap = '%s = %s(\n' % (uiObject.name, uiObject.__guid__)
        defaultAttrs = [ each for each in dir(objClass) if each.startswith('default_') ]
        for parentClass in objClass.__bases__:
            for each in dir(parentClass):
                if each.startswith('default_') and each not in defaultAttrs:
                    defaultAttrs.append(each)

        for defaultAttr in defaultAttrs:
            attr = defaultAttr[8:]
            defaultAttrValue = getattr(objClass, defaultAttr)
            objAttrValue = getattr(uiObject, attr, '__attr_notset__')
            if objAttrValue != '__attr_notset__' and objAttrValue != defaultAttrValue:
                if isinstance(objAttrValue, basestring):
                    wrap += '    %s="%s",\n' % (attr, objAttrValue)
                elif attr == 'color':
                    wrap += '    %s=%s,\n' % (attr, objAttrValue.GetRGBA())
                elif attr == 'parent':
                    wrap += '    %s=%s,\n' % (attr, objAttrValue.name)
                elif attr in ('state',):
                    continue
                elif attr in COMBOPROPERTIES:
                    objAttrValue = COMBOPROPERTIES[attr].get(objAttrValue, 'Unknown value!')
                    nameSpace = COMBOPROPERTIES_NAMESPACE.get(attr, 'Unknown namespace')
                    wrap += '    %s=%s.%s,\n' % (attr, nameSpace, objAttrValue)
                else:
                    wrap += '    %s=%s,\n' % (attr, objAttrValue)

        wrap += '    )'

    def ExpandUIObject(self, *args):
        wnd = GetWindowAbove(self)
        if wnd:
            wnd.ToggleExpandedObject(self.sr.node.uiObject)

    def OnClick(self, *args):
        wnd = GetWindowAbove(self)
        if wnd:
            wnd.ShowPropertiesForObject(self.sr.node.uiObject)

    def OpenInJessica(self, uiObjectOrRenderObject):
        try:
            import wx
            tree = wx.FindWindowByName('TreeView2')
            tree.AddUITree(uiObjectOrRenderObject.name, uiObjectOrRenderObject)
        except ImportError:
            pass

    def OnMouseExit(self, *args):
        self._hilite.display = False

    def OnMouseEnter(self, *args):
        self._hilite.display = True


class UITreePropertyEntry(SE_BaseClassCore):
    ENTRYHEIGHT = 16

    def ApplyAttributes(self, attributes):
        SE_BaseClassCore.ApplyAttributes(self, attributes)
        cnt = Container(parent=self, pos=(0, 0, 0, 0), state=uiconst.UI_PICKCHILDREN)
        self._label = Label(parent=cnt, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT, color=(1.0, 1.0, 1.0, 0.75))
        self._valueContainer = Container(parent=cnt, state=uiconst.UI_PICKCHILDREN, align=uiconst.TOALL, padLeft=VALUEOFFSET)
        self._hilite = Fill(bgParent=self, color=(1, 1, 1, 0.125), state=uiconst.UI_HIDDEN)
        self._mainContainer = cnt

    def Load(self, node):
        self._mainContainer.padLeft = 6 + 16 * node.level
        self._label.text = node.propertyName
        self._valueContainer.Flush()
        if node.combineProperties:
            for propertyName in node.combineProperties:
                currentValue = GetAttrs(node.uiObject, *tuple(propertyName.split('.')))
                inpt = UITreeNumberInput(parent=self._valueContainer, value=currentValue, uiObject=node.uiObject, propertyName=propertyName, align=uiconst.TOLEFT)

        else:
            currentValue = GetAttrs(node.uiObject, *tuple(node.propertyName.split('.')))
            if isinstance(currentValue, (tuple, list)):
                for i in xrange(len(currentValue)):
                    inpt = UITreeNumberInput(parent=self._valueContainer, value=currentValue[i], uiObject=node.uiObject, propertyName=node.propertyName, propertyIndex=i, align=uiconst.TOLEFT)

            else:
                inpt = UITreeNumberInput(parent=self._valueContainer, value=currentValue, uiObject=node.uiObject, propertyName=node.propertyName, align=uiconst.TOLEFT)

    def OnMouseExit(self, *args):
        self._hilite.display = False

    def OnMouseEnter(self, *args):
        self._hilite.display = True

    def GetMenu(self):
        m = []
        m.append(('Copy', self.CopyValue))
        m.append(('Copy All Properties', self.CopyAll))
        return m

    def CopyAll(self):
        allNodes = self.sr.node.scroll.sr.nodes
        allCopyStrings = []
        for node in allNodes:
            allCopyStrings.append(self._GetCopyString(node))

        blue.pyos.SetClipboardData('\n'.join(allCopyStrings))

    def CopyValue(self):
        blue.pyos.SetClipboardData(self._GetCopyString(self.sr.node))

    def _GetCopyString(self, node):
        propertyName = node.propertyName
        copyStr = '%s = ' % node.propertyName
        currentValue = getattr(node.uiObject, propertyName, '__notfound__')
        if propertyName in COMBOPROPERTIES:
            objAttrValue = COMBOPROPERTIES[propertyName].get(currentValue, 'Unknown value!')
            nameSpace = COMBOPROPERTIES_NAMESPACE.get(propertyName, 'Unknown namespace')
            currentValue = '%s.%s' % (nameSpace, objAttrValue)
        copyStr += repr(currentValue)
        return copyStr
