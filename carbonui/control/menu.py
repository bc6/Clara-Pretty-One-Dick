#Embedded file name: carbonui/control\menu.py
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.frame import FrameCoreOverride as Frame
from carbonui.control.label import LabelOverride as Label
from carbonui.primitives.container import Container
from carbonui.primitives.sprite import Sprite
from carbonui.util.bunch import Bunch
from eve.client.script.ui.control.eveWindowUnderlay import ListEntryUnderlay
from eve.client.script.ui.control.glowSprite import GlowSprite
from eve.client.script.ui.control.themeColored import LineThemeColored
import uthread
import types
import log
import weakref
import eve.client.script.ui.menuUtil as menuUtil
import carbonui.const as uiconst
import localization
from carbon.common.script.util.timerstuff import AutoTimer
from carbonui.control.menuLabel import MenuLabel
DISABLED_ENTRY0 = -1
DISABLED_ENTRY = [-1]
DISABLED_ENTRY2 = [[-1]]

class Menu(object):
    """Data structure for a menu, irrespective of its graphic representation."""

    def __init__(self):
        self.entrylist = []
        self.iconSize = 0

    def AddEntry(self, name, value, icon, identifier, enabled = 1, menuClass = None):
        m = Bunch()
        m.caption = name
        m.value = value
        m.enabled = enabled
        m.icon = icon
        m.id = identifier
        m.menuClass = menuClass
        if not m.value:
            m.enabled = False
        self.entrylist.append(m)

    def AddSeparator(self):
        self.entrylist.append(None)

    def ActivateEntry(self, name):
        entry = self._GetEntry(name)
        if not entry.enabled:
            return
        uicore.Message('MenuActivate')
        if callable(entry.value):
            uthread.new(entry.value)
        uthread.new(CloseContextMenus)

    def GetEntries(self):
        return self.entrylist

    def _GetEntry(self, name):
        for each in self.entrylist:
            if getattr(each, 'id', None) == name:
                return each
        else:
            raise RuntimeError('Entry not found!', name)


class DropDownMenuCore(ContainerAutoSize):
    """One graphic representation of a menu."""
    __guid__ = 'uicls.DropDownMenuCore'
    default_alignMode = uiconst.TOTOP
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        ContainerAutoSize.ApplyAttributes(self, attributes)
        self.sr.entries = ContainerAutoSize(parent=self, name='_entries', align=uiconst.TOTOP, padding=(0, 1, 0, 1))
        self.Prepare_()

    def Prepare_(self, *args):
        self.SetAlign(uiconst.TOPLEFT)
        self.Prepare_Background_()

    def Prepare_Background_(self, *args):
        Frame(name='__underlay', color=(0.5, 0.5, 0.5, 0.95), frameConst=uiconst.FRAME_FILLED_SHADOW_CORNER1, bgParent=self)

    def _OnClose(self):
        Container._OnClose(self)
        for each in self.sr.entries.children[:]:
            if hasattr(each, 'Collapse'):
                each.Collapse()

        self.menu = None

    def Setup(self, menu, parent = None, minwidth = None):
        log.LogInfo('Menu.Setup', id(self))
        entries = menu.GetEntries()
        wasLine = 0
        idNo = 0
        for i, entry in enumerate(entries):
            if entry is None:
                if not len(self.sr.entries.children) or i == len(entries) - 1 or wasLine:
                    continue
                item = LineThemeColored(align=uiconst.TOTOP, parent=self.sr.entries, opacity=0.15, padding=(0, 2, 0, 1))
                wasLine = 1
            else:
                size = settings.user.ui.Get('cmenufontsize', 10)
                from carbonui.control.menu import MenuEntryViewCoreOverride as MenuEntryView
                menuEntryViewClass = entry.menuClass or MenuEntryView
                item = menuEntryViewClass(name='entry', align=uiconst.TOTOP, state=uiconst.UI_NORMAL, parent=self.sr.entries)
                item.Setup(entry, size, menu, idNo)
                idNo += 1
                wasLine = 0

        if len(self.sr.entries.children):
            self.width = max(max([ each.width for each in self.sr.entries.children ]) + 8, minwidth or 0) + self.sr.entries.left + self.sr.entries.width
        else:
            self.width = 100
        self.sr.entries.SetSizeAutomatically()
        self.SetSizeAutomatically()
        self.menu = menu
        log.LogInfo('Menu.Setup Completed', id(self))

    def ActivateEntry(self, name):
        error = self.menu.ActivateEntry(name)
        if error:
            apply(uicore.Message, error)

    def Collapse(self):
        if not self.destroyed:
            for each in self.sr.entries.children:
                if hasattr(each, 'Collapse'):
                    each.Collapse()

            self.Close()

    def Next(self):
        found = None
        for each in self.sr.entries.children:
            if not isinstance(each, MenuEntryViewCore):
                continue
            if found:
                each.OnMouseEnter()
                return
            if each.sr.hilite:
                each.OnMouseExit()
                found = each

        self.sr.entries.children[0].OnMouseEnter()

    def Prev(self):
        found = None
        lst = [ each for each in self.sr.entries.children ]
        lst.reverse()
        for each in lst:
            if not isinstance(each, MenuEntryViewCore):
                continue
            if found:
                each.OnMouseEnter()
                return
            if each.sr.hilite:
                each.OnMouseExit()
                found = each

        self.sr.entries.children[-1].OnMouseEnter()

    def ChooseHilited(self):
        for each in self.sr.entries.children:
            if not isinstance(each, MenuEntryViewCore):
                continue
            if each.sr.hilite:
                self.ActivateEntry(each.id)
                return


class MenuEntryViewCore(Container):
    __guid__ = 'uicls.MenuEntryViewCore'
    LABELVERTICALPADDING = 2
    LABELHORIZONTALPADDING = 8
    default_fontsize = 10
    default_fontStyle = None
    default_fontFamily = None
    default_fontPath = None

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.fontStyle = attributes.get('fontStyle', self.default_fontStyle)
        self.fontFamily = attributes.get('fontFamily', self.default_fontFamily)
        self.fontPath = attributes.get('fontPath', self.default_fontPath)
        self.fontsize = attributes.get('fontsize', self.default_fontsize)
        self.cursor = 1
        self.clicked = 0
        self.submenu = None
        self.submenuview = None
        self.sr.hilite = None
        self.Prepare()

    def Prepare(self, *args):
        self.Prepare_Triangle_()
        self.Prepare_Label_()
        self.sr.label.OnMouseDown = self.OnMouseDown
        self.sr.label.OnMouseUp = self.OnMouseUp

    def Prepare_Triangle_(self, *args):
        self.triangle = GlowSprite(parent=self, align=uiconst.CENTERRIGHT, state=uiconst.UI_HIDDEN, idx=0, texturePath='res:/UI/Texture/Icons/1_16_14.png', pos=(0, 0, 16, 16))

    def Prepare_Label_(self, *args):
        label = Label(parent=self, pos=(8, 1, 0, 0), align=uiconst.CENTERLEFT, letterspace=1, fontStyle=self.fontStyle, fontFamily=self.fontFamily, fontPath=self.fontPath, fontsize=self.fontsize, state=uiconst.UI_DISABLED)
        self.sr.label = label

    def Prepare_Hilite_(self, *args):
        self.sr.hilite = ListEntryUnderlay(parent=self)

    def Setup(self, entry, size, menu, identifier):
        text = entry.caption
        self.sr.label.fontsize = size
        self.sr.label.text = text
        self.menu = menu
        menuIconSize = menu.iconSize
        icon = None
        if menuIconSize:
            icon = Sprite(parent=self, pos=(0,
             0,
             menuIconSize,
             menuIconSize), align=uiconst.RELATIVE, idx=0, state=uiconst.UI_DISABLED, name='icon')
            icon.LoadIcon(entry.icon or 'ui_1_16_101', ignoreSize=True)
            self.sr.label.left += menuIconSize
        self.id = identifier
        if not entry.enabled:
            if icon:
                icon.SetAlpha(0.5)
            self.sr.label.SetRGB(1.0, 1.0, 1.0, 0.5)
            if isinstance(entry.value, basestring):
                self.sr.label.text += ' (' + entry.value + ')'
        self.width = self.sr.label.textwidth + self.sr.label.left + self.LABELHORIZONTALPADDING
        self.height = max(menuIconSize, self.sr.label.textheight + self.LABELVERTICALPADDING)
        if not entry.enabled:
            self.state = uiconst.UI_DISABLED
        if isinstance(entry.value, (list, tuple)):
            self.triangle.state = uiconst.UI_DISABLED
            self.submenu = entry.value

    def _OnClose(self):
        if self.submenuview is not None and not self.submenuview.destroyed:
            self.submenuview.Close()
            self.submenuview = None
        self.menu = None
        self.submenu = None
        self.expandTimer = None
        self.collapseTimer = None
        Container._OnClose(self)

    def OnMouseDown(self, *etc):
        uthread.new(self.MouseDown)

    def MouseDown(self):
        if not self.destroyed and self.submenu:
            self.Expand()

    def OnMouseUp(self, *etc):
        if not self.submenu and uicore.uilib.mouseOver in (self, self.sr.label):
            self.menu.ActivateEntry(self.id)
            uthread.new(CloseContextMenus)

    def OnMouseEnter(self, *args):
        uicore.Message('ContextMenuEnter')
        if self.sr.hilite is None:
            self.Prepare_Hilite_()
        self.sr.hilite.ShowHilite()
        self.expandTimer = AutoTimer(10, self.ExpandMenu)
        if self.triangle.display:
            self.triangle.OnMouseEnter()

    def ExpandMenu(self):
        for each in self.parent.children:
            if each != self and getattr(each, 'submenuview', None):
                each.Collapse()

        self.expandTimer = None
        if uicore.uilib.mouseOver in (self, self.sr.label) and self.submenu:
            self.Expand()

    def OnMouseExit(self, *args):
        if self.sr.hilite:
            self.sr.hilite.HideHilite()
        if self.triangle.display:
            self.triangle.OnMouseExit()

    def toggle(self):
        if self.submenuview:
            self.Collapse()
        else:
            self.Expand()

    def Collapse(self):
        self.collapseTimer = None
        if self.submenuview and self.submenuview.destroyed:
            self.submenuview = None
        elif self.submenuview:
            self.submenuview.Collapse()
            self.submenuview = None

    def Expand(self):
        if not self.submenuview:
            for each in self.parent.children:
                if each != self and getattr(each, 'submenuview', None):
                    each.Collapse()

            if self.submenu[0] == 'isDynamic':
                menu = CreateMenuView(CreateMenuFromList(apply(self.submenu[1], self.submenu[2])), self.parent)
            else:
                menu = CreateMenuView(CreateMenuFromList(self.submenu), self.parent)
            if not menu:
                return
            w = uicore.desktop.width
            h = uicore.desktop.height
            aL, aT, aW, aH = self.GetAbsolute()
            menu.top = max(0, min(h - menu.height, aT))
            if aL + aW + menu.width <= w:
                menu.left = aL + aW + 2
            else:
                aL, aT, aW, aH = self.GetAbsolute()
                menu.left = aL - menu.width + 5
            uicore.layer.menu.children.insert(0, menu)
            if self.destroyed:
                CloseContextMenus()
                return
            self.submenuview = menu


def CreateMenuView(menu, parent = None, minwidth = None):
    if menu is None:
        return
    if not parent:
        CloseContextMenus()
    from carbonui.control.menu import DropDownMenuCoreOverride as DropDownMenu
    m = DropDownMenu(name='menuview', align=uiconst.TOPLEFT, parent=None)
    m.Setup(menu, parent, minwidth)
    return m


def CreateMenuFromList(lst):
    while lst and lst[0] is None:
        lst = lst[1:]

    while lst and lst[-1] is None:
        lst = lst[:-1]

    if not lst:
        return
    iconSize = None
    m = Menu()
    ignoreMenuGrouping = prefs.GetValue('ignoreMenuGrouping', 0)
    allEntries = []
    for each in lst:
        if each is None:
            allEntries.append((None, None))
        else:
            groupID = None
            menuLabel, value = each[:2]
            if isinstance(menuLabel, MenuLabel):
                labelPath, keywords = menuLabel
                labelPath = labelPath.strip()
                groupID = menuUtil.GetMenuGroup(labelPath)
                caption = localization.GetByLabel(labelPath, **keywords)
            else:
                label = menuLabel
                keywords = {}
                if isinstance(label, basestring):
                    groupID = menuUtil.GetMenuGroup(label.lower())
                caption = label
            if ignoreMenuGrouping:
                groupID = None
            if len(each) > 2:
                args = each[2]
                if args not in (DISABLED_ENTRY, DISABLED_ENTRY2):
                    value = lambda f = value, args = args: f(*args)
                else:
                    value = None
                if len(args) == 2 and type(args[1]) == list and len(args[1]) > 1:
                    t = 0
                    for eacharg in args[1]:
                        t1 = None
                        if hasattr(eacharg, 'stacksize'):
                            t1 = eacharg.stacksize
                        if t1 is None and hasattr(eacharg, 'quantity'):
                            t1 = eacharg.quantity
                        if t1 is not None:
                            t += t1
                        else:
                            t += 1

                    caption += ' (%s)' % t
            icon = None
            if len(each) > 3:
                icon = each[3]
                if icon is not None:
                    thisIconSize = 16
                    if type(icon) == types.TupleType:
                        icon, thisIconSize = icon
                    iconSize = max(iconSize, thisIconSize)
            menuClass = None
            if len(each) > 4:
                menuClass = each[4]
            isCallableOrSubmenu = isinstance(value, types.MethodType) or isinstance(value, types.FunctionType) or isinstance(value, types.ListType) or isinstance(value, types.TupleType)
            allEntries.append((groupID, (caption,
              value,
              icon,
              isCallableOrSubmenu,
              menuClass)))

    m.iconSize = iconSize
    idNo = 0
    allEntries = SortMenuEntries(allEntries)
    lastGroupID = None
    for groupID, each in allEntries:
        if groupID is None:
            if each is None:
                m.AddSeparator()
                lastGroupID = groupID
                continue
        if groupID != lastGroupID:
            if isinstance(groupID, tuple) and isinstance(lastGroupID, tuple):
                if groupID[0] != lastGroupID[0]:
                    m.AddSeparator()
            else:
                m.AddSeparator()
        lastGroupID = groupID
        caption, value, icon, isCallableOrSubmenu, menuClass = each
        m.AddEntry(caption, value, icon, idNo, isCallableOrSubmenu, menuClass)
        idNo += 1

    return m


def SortMenuEntries(entryList, *args):
    entryList.sort(cmp=CompareGroups)
    return entryList


def CompareGroups(x, y):
    groupX = x[0]
    groupY = y[0]
    if groupX in menuUtil.menuHierarchy:
        priorityX = menuUtil.menuHierarchy.index(groupX)
    else:
        priorityX = -1
    if groupY in menuUtil.menuHierarchy:
        priorityY = menuUtil.menuHierarchy.index(groupY)
    else:
        priorityY = -1
    if priorityX < priorityY:
        return -1
    elif priorityX == priorityY:
        return 0
    else:
        return 1


def ShowMenu(object, auxObject = None):
    CloseContextMenus()
    m = None
    menuFunc = getattr(object, 'GetMenu', None)
    if menuFunc:
        if type(menuFunc) == types.TupleType:
            func, args = menuFunc
            m = func(args)
        else:
            m = menuFunc()
    if not m or not filter(None, m):
        if auxObject and hasattr(auxObject, 'GetAuxiliaryMenuOptions'):
            m = auxObject.GetAuxiliaryMenuOptions()
        else:
            log.LogInfo('menu', 'ShowMenu: No Menu!')
            return
    elif auxObject and hasattr(auxObject, 'GetAuxiliaryMenuOptions'):
        m = m + auxObject.GetAuxiliaryMenuOptions()
    if getattr(object, 'showingMenu', 0):
        log.LogInfo('menu', 'ShowMenu: Already showing a menu')
        return
    object.showingMenu = 1
    uicore.contextMenuOwner = weakref.ref(object)
    try:
        d = uicore.desktop
        mv = CreateMenuView(CreateMenuFromList(m), None, getattr(object, 'minwidth', None))
        object.menuObject_weakref = weakref.ref(mv)
        topLeft = 1
        func = getattr(object, 'GetMenuPosition', None)
        if func is not None:
            ret = func(object)
            if len(ret) == 2:
                x, y = ret
            else:
                x, y, topLeft = ret
        else:
            x, y = uicore.uilib.x + 10, uicore.uilib.y
        if topLeft:
            x, y = min(d.width - mv.width, x), min(d.height - mv.height, y)
        else:
            x, y = min(d.width - mv.width, x - mv.width), min(d.height - mv.height, y)
        mv.left, mv.top = x, y
        uicore.layer.menu.children.insert(0, mv)
    finally:
        object.showingMenu = 0

    log.LogInfo('menu', 'ShowMenu finished OK')


def ObjectHasMenu(uiObject):
    if hasattr(uiObject, 'menuObject_weakref'):
        mo = uiObject.menuObject_weakref
        if mo and mo():
            return True
    return False


def GetContextMenuOwner():
    contextMenuOwner = getattr(uicore, 'contextMenuOwner', None)
    if contextMenuOwner:
        menuOwner = contextMenuOwner()
        if menuOwner and not menuOwner.destroyed and ObjectHasMenu(menuOwner):
            return menuOwner


def CloseContextMenus():
    from carbonui.control.menu import DropDownMenuCoreOverride as DropDownMenu
    closedMenu = False
    for each in uicore.layer.menu.children[:]:
        if isinstance(each, DropDownMenu):
            each.Close()
            closedMenu = True

    return closedMenu


def HasContextMenu():
    from carbonui.control.menu import DropDownMenuCoreOverride as DropDownMenu
    for each in uicore.layer.menu.children:
        if isinstance(each, DropDownMenu):
            return True

    return False


def ClearMenuLayer():
    """
    Will destroy all menus using standard menu layer as its parent,
    this can include, standard context menus, tooltip menus, edit menus,
    Use CloseContextMenus if your intention is to close current
    context menu
    """
    uicore.layer.menu.Flush()


class MenuEntryViewCoreOverride(MenuEntryViewCore):
    pass


class DropDownMenuCoreOverride(DropDownMenuCore):
    pass


exports = {'menu.ShowMenu': ShowMenu,
 'menu.CreateMenuView': CreateMenuView,
 'menu.CreateMenuFromList': CreateMenuFromList,
 'menu.DISABLED_ENTRY': DISABLED_ENTRY}
