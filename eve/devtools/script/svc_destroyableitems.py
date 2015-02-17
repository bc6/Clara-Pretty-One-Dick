#Embedded file name: eve/devtools/script\svc_destroyableitems.py
import os
import sys
import blue
import util
import uiutil
import listentry
import menu
import uthread
import service
import carbonui.const as uiconst
import uicontrols
import uiprimitives
FILE_DESTROYABLES = 'Destroyables.txt'
FILE_POS_EXT = 'pos'

class InsiderDestroyables(listentry.Generic):
    __guid__ = 'listentry.InsiderDestroyables'

    def GetMenu(self, *args):
        node = self.sr.node
        selected = node.scroll.GetSelectedNodes(node)
        multiple = len(selected) > 1
        m = []
        if multiple:
            m += [('Destroy', [('Destroy all selected', self.HealZero, (selected,)), ('Unspawn all selected', self.Unspawn, (selected,))]), None]
            m += sm.GetService('menu').GetMenuFormItemIDTypeID(node.itemID, node.typeID)
            return m
        else:
            m += [('Destroy', [('Destroy this %s' % cfg.invtypes.Get(node.typeID).name, self.HealZero, (selected,)), ('Unspawn this %s' % cfg.invtypes.Get(node.typeID).name, self.Unspawn, (selected,))]), None]
            m += sm.GetService('menu').GetMenuFormItemIDTypeID(node.itemID, node.typeID)
            return m

    def Unspawn(self, nodes = None):
        if nodes is None:
            return
        if not settings.char.ui.Get('suppressDestroyableWarning', 0):
            if not eve.Message('CustomQuestion', {'header': 'Unspawn selected?',
             'question': 'Do you really want to unspawn these items?'}, uiconst.YESNO) == uiconst.ID_YES:
                return
        for node in nodes:
            sm.GetService('slash').SlashCmd('unspawn %d' % node.itemID)

    def HealZero(self, nodes = None):
        if nodes is None:
            return
        if not settings.char.ui.Get('suppressDestroyableWarning', 0):
            if not eve.Message('CustomQuestion', {'header': 'Destroy selected?',
             'question': 'Do you really want to destroy these items?'}, uiconst.YESNO) == uiconst.ID_YES:
                return
        for node in nodes:
            sm.GetService('slash').SlashCmd('heal %d 0' % node.itemID)


class DestroyableItemsWindow(uicontrols.Window):
    default_windowID = 'destroyableitems'


class destroyableItems(service.Service):
    __module__ = __name__
    __exportedcalls__ = {}
    __notifyevents__ = ['ProcessRestartUI', 'Update', 'DoBallRemove']
    __dependencies__ = []
    __guid__ = 'svc.destroyableItems'
    __servicename__ = 'destroyableItems'
    __displayname__ = 'destroyableItems'
    __neocommenuitem__ = (('Destroyable Items', None), 'Show', service.ROLE_GML)

    def Run(self, memStream = None):
        self.wnd = None

    def Stop(self, memStream = None):
        self.Hide()
        service.Service.Stop(self, memStream)

    def BallRemoveThread(self, ball, slimItem, terminal):
        if not hasattr(self, 'wnd') or not self.wnd or self.wnd.destroyed:
            return
        self.LogInfo('***destroyableItems::DoBallRemove Starting Long Run***', slimItem.itemID)
        if not hasattr(self, 'scroll') or not hasattr(self.scroll, 'GetNodes'):
            return
        nodes = self.scroll.GetNodes()
        for i in nodes:
            if i.itemID == slimItem.itemID:
                self.scroll.RemoveNodes([i])

    def DoBallRemove(self, ball, slimItem, terminal):
        uthread.worker('DestroyableItems::DoBallRemove', self.BallRemoveThread, ball, slimItem, terminal)

    def Show(self):
        if self.wnd:
            self.wnd.Maximize()
            return None
        self.wnd = wnd = DestroyableItemsWindow.Open()
        self.wnd._OnClose = self.Hide
        self.wnd.SetWndIcon('41_13')
        self.wnd.HideMainIcon()
        self.wnd.SetTopparentHeight(0)
        self.wnd.SetCaption('Destroyable Items')
        self.wnd.SetMinSize([370, 200])
        directionBox = uiprimitives.Container(name='direction', parent=uiutil.GetChild(wnd, 'main'), align=uiconst.TOALL, pos=(0, 0, 0, 0))
        directionSettingsBox = uiprimitives.Container(name='direction', parent=directionBox, align=uiconst.TOTOP, height=75)

        def Suppress(cb):
            checked = cb.GetValue()
            settings.char.ui.Set('suppressDestroyableWarning', checked)
            cb.state = uiconst.UI_HIDDEN
            cb.state = uiconst.UI_NORMAL

        def Verbose(cb):
            checked = cb.GetValue()
            settings.char.ui.Set('verboseDestroyables', checked)
            cb.state = uiconst.UI_HIDDEN
            cb.state = uiconst.UI_NORMAL

        self.suppress = uicontrols.Checkbox(text='Suppress warning messages', parent=directionSettingsBox, configName='', retval=0, checked=settings.char.ui.Get('suppressDestroyableWarning', 0), align=uiconst.TOPLEFT, callback=Suppress, pos=(5, 0, 200, 0))
        self.verbose = uicontrols.Checkbox(text='List all details', parent=directionSettingsBox, configName='', retval=0, checked=settings.char.ui.Get('verboseDestroyables', 0), align=uiconst.TOPLEFT, callback=Verbose, pos=(5, 15, 200, 0))
        uicontrols.Label(text=u'Range (km)', parent=directionSettingsBox, width=240, height=24, left=5, top=35, state=uiconst.UI_DISABLED)
        self.dir_rangeinput = uicontrols.SinglelineEdit(name='rangeedit', parent=directionSettingsBox, ints=(1, None), align=uiconst.TOPLEFT, width=78, top=55, left=5, maxLength=len(str(sys.maxint)) + 1)
        self.dir_rangeinput.SetValue('2147483647')

        def ExportMenu(*args):
            exportMenu = []
            exportMenu.append(('Generate List Dump', self.Dump))
            exportMenu.append(('Generate POSer', self.DumpPOSer))
            mv = menu.CreateMenuView(menu.CreateMenuFromList(exportMenu), None, None)
            anchorwindow = DestroyableItemsWindow.GetIfOpen()
            anchor = u'Export'
            anchoritem = uiutil.GetChild(anchorwindow, anchor)
            x, y, w, h = anchoritem.GetAbsolute()
            x = max(x, 0)
            y = y + h
            if y + mv.height > uicore.desktop.height:
                mv.top = anchoritem.GetAbsolute()[1] - mv.height
            else:
                mv.top = y
            mv.left = min(uicore.desktop.width - mv.width, x)
            uicontrols.Frame(parent=mv, color=(1.0, 1.0, 1.0, 0.2))
            uicore.layer.menu.children.insert(0, mv)

        uicontrols.Button(parent=directionSettingsBox, name=u'Scan', label=u'Scan', pos=(85, 55, 0, 0), func=self.Update)
        uicontrols.Button(parent=directionSettingsBox, name=u'Select All', label=u'Select All', pos=(130, 55, 0, 0), func=self.SelectAll)
        uicontrols.Button(parent=directionSettingsBox, name=u'Destroy', label=u'Destroy', pos=(204, 55, 0, 0), func=self.Pwn)
        uicontrols.Button(parent=directionSettingsBox, name=u'Export', label=u'Export', pos=(265, 55, 0, 0), func=ExportMenu)
        maincont = uiprimitives.Container(name='maincont', parent=directionBox, pos=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        self.scroll = uicontrols.Scroll(parent=maincont)
        self.scroll.sr.id = 'resultsscroll'
        self.scroll.Load(contentList=[])
        tabs = [[u'All items',
          self.scroll,
          self,
          'allitems'],
         [u'Drones',
          self.scroll,
          self,
          'drones'],
         [u'Container',
          self.scroll,
          self,
          'containers'],
         [u'Ships',
          self.scroll,
          self,
          'ships'],
         [u'Structures',
          self.scroll,
          self,
          'structures'],
         ['Deployables',
          self.scroll,
          self,
          'deployable'],
         ['%s/%s' % (u'NPC', u'Entity'),
          self.scroll,
          self,
          'npcs']]
        maintabs = uicontrols.TabGroup(name='tabparent', parent=maincont, idx=0)
        maintabs.Startup(tabs)
        self.width = 425

    def Hide(self, *args):
        if self.wnd:
            self.wnd = None

    def ProcessRestartUI(self):
        if self.wnd:
            self.Hide()
            self.Show()

    def Load(self, key, *args):
        if key == 'allitems':
            self.Search(group='all')
        elif key == 'drones':
            self.Search(group=const.categoryDrone)
        elif key == 'containers':
            self.Search(group=const.categoryCelestial)
        elif key == 'ships':
            self.Search(group=const.categoryShip)
        elif key == 'structures':
            self.Search(group=const.categoryStructure)
        elif key == 'deployable':
            self.Search(group=const.categoryDeployable)
        elif key == 'npcs':
            self.Search(group=const.categoryEntity)

    def Update(self, *args):
        wnd = DestroyableItemsWindow.GetIfOpen()
        if wnd and wnd.IsMinimized() == False:
            tabparent = uiutil.GetChild(wnd, 'tabparent')
            if uiutil.IsVisible(tabparent):
                tabparent.ReloadVisible()

    def SelectAll(self, *args):
        if not self.scroll.GetSelected():
            self.scroll.SelectAll()
        else:
            self.scroll.DeselectAll()

    def Pwn(self, *args):
        selected = self.scroll.GetSelected()
        multiple = len(selected) > 1
        if multiple:
            self.MultipleRemove(selected)
        elif selected:
            self.SingleRemove(selected)

    def DumpPOSer(self, *args):
        """
        Dumps the contents of the scroll window to a file for later review
        """
        if eve.Message('CustomQuestion', {'header': 'Save current data?',
         'question': 'This will save the current data entered in the window.<br><br>Are you sure that you want to save this?'}, uiconst.YESNO) == uiconst.ID_YES:
            filename = '%s.%s' % (self.GetTimestamp(), FILE_POS_EXT)
            wnd = DestroyableItemsWindow.GetIfOpen()
            if wnd:
                scroll = uiutil.GetChild(wnd, 'scroll')
                f = blue.classes.CreateInstance('blue.ResFile')
                TARGET = os.path.join(self.GetInsiderDir(), filename)
                if not f.Open(TARGET, 0):
                    f.Create(TARGET)
                scroll.SelectAll()
                data = scroll.GetSelected()
                scroll.DeselectAll()
                for entry in data:
                    if sm.GetService('michelle').GetBallpark().GetInvItem(entry.itemID).categoryID == const.categoryStructure:
                        f.Write('% 6d % 6d % 6d = %s' % (entry.x,
                         entry.y,
                         entry.z,
                         entry.typeID))
                        f.Write('\r\n')

            f.Close()

    def Dump(self, *args):
        """
        Dumps the contents of the scroll window to a file for later review
        """
        if eve.Message('CustomQuestion', {'header': 'Save current data?',
         'question': 'This will save the current data entered in the window.<br><br>Are you sure that you want to save this?'}, uiconst.YESNO) == uiconst.ID_YES:
            filename = '%s.%s' % (self.GetTimestamp(), FILE_DESTROYABLES)
            wnd = DestroyableItemsWindow.GetIfOpen()
            if wnd:
                scroll = uiutil.GetChild(wnd, 'scroll')
                f = blue.classes.CreateInstance('blue.ResFile')
                TARGET = os.path.join(self.GetInsiderDir(), filename)
                if not f.Open(TARGET, 0):
                    f.Create(TARGET)
                scroll.SelectAll()
                data = scroll.GetSelected()
                scroll.DeselectAll()
                headers = scroll.GetColumns()
                for header in headers:
                    f.Write('%s\t' % header)

                f.Write('\r\n')
                for entry in data:
                    f.Write('%s' % entry.label.replace('<t>', '\t').encode('utf8'))
                    f.Write('\r\n')

                f.Close()

    def SingleRemove(self, nodes = None):
        if not settings.char.ui.Get('suppressDestroyableWarning', 0):
            if eve.Message('CustomQuestion', {'header': 'Destroy selected?',
             'question': 'Do you really want to destroy this %s?' % cfg.invtypes.Get(nodes[0].typeID).name}, uiconst.YESNO) == uiconst.ID_YES:
                for node in nodes:
                    sm.GetService('slash').SlashCmd('heal %d 0' % node.itemID)

        else:
            for node in nodes:
                sm.GetService('slash').SlashCmd('heal %d 0' % node.itemID)

    def MultipleRemove(self, nodes = None):
        if not settings.char.ui.Get('suppressDestroyableWarning', 0):
            if eve.Message('CustomQuestion', {'header': 'Destroy selected?',
             'question': 'Do you really want to destroy these selected items?'}, uiconst.YESNO) == uiconst.ID_YES:
                if not nodes:
                    nodes = [self.sr.node]
                for node in nodes:
                    sm.GetService('slash').SlashCmd('heal %d 0' % node.itemID)

        else:
            if not nodes:
                nodes = [self.sr.node]
            for node in nodes:
                sm.GetService('slash').SlashCmd('heal %d 0' % node.itemID)

    def Collate(self, list, group = None, players = None, *args):
        m = []
        bp = sm.GetService('michelle').GetBallpark()
        you = bp.GetBall(session.shipid)
        if group.__class__ == int:
            group = [group]
        verbose = settings.char.ui.Get('verboseDestroyables', 0)
        for item in list:
            owner = cfg.eveowners.Get(item.ownerID)
            if verbose:
                ball = bp.GetBall(item.itemID)
                distance = ball.surfaceDist
                x = int(ball.x + 0.5 - (you.x + 0.5))
                y = int(ball.y + 0.5 - (you.y + 0.5))
                z = int(ball.z + 0.5 - (you.z + 0.5))
            else:
                distance = x = y = z = 0
                ball = bp.GetBall(item.itemID)
                if ball:
                    distance = ball.surfaceDist
            state = '-'
            for groups in group:
                if item.categoryID == groups and item.categoryID == const.categoryDrone:
                    if item.ownerID not in players:
                        m.append((u'Drones',
                         owner.Group().groupName,
                         item.typeID,
                         item.itemID,
                         owner.name,
                         distance,
                         'Abandoned',
                         x,
                         y,
                         z))
                elif item.categoryID == groups and item.categoryID == const.categoryCelestial and owner.IsNPC() == False and item.groupID != const.groupBeacon:
                    if cfg.invgroups.Get(item.groupID).name == 'Wreck':
                        if sm.GetService('state').CheckWreckEmpty(item):
                            state = u'Empty'
                        else:
                            state = 'Not Empty'
                        m.append((cfg.invgroups.Get(item.groupID).groupName,
                         owner.Group().groupName,
                         item.typeID,
                         item.itemID,
                         owner.name,
                         distance,
                         state,
                         x,
                         y,
                         z))
                    elif cfg.invgroups.Get(item.groupID).name == 'Biomass':
                        m.append((cfg.invgroups.Get(item.groupID).groupName,
                         owner.Group().groupName,
                         item.typeID,
                         item.itemID,
                         owner.name,
                         distance,
                         'Popsicle',
                         x,
                         y,
                         z))
                    else:
                        if cfg.invgroups.Get(item.groupID).anchorable:
                            if not bp.GetBall(item.itemID).isFree:
                                state = u'Anchored'
                            else:
                                state = u'Unanchored'
                        m.append((u'Container',
                         owner.Group().groupName,
                         item.typeID,
                         item.itemID,
                         owner.name,
                         distance,
                         state,
                         x,
                         y,
                         z))
                elif item.categoryID == groups and item.categoryID == const.categoryShip and not bp.GetBall(item.itemID).isInteractive:
                    m.append((u'Ships',
                     owner.Group().groupName,
                     item.typeID,
                     item.itemID,
                     owner.name,
                     distance,
                     u'Empty',
                     x,
                     y,
                     z))
                elif item.categoryID == groups and groups in (const.categoryStructure, const.categorySovereigntyStructure):
                    try:
                        state = sm.GetService('pwn').GetStructureState(item)[0].title()
                    except:
                        sys.exc_clear()

                    m.append((u'Structures',
                     owner.Group().groupName,
                     item.typeID,
                     item.itemID,
                     owner.name,
                     distance,
                     state,
                     x,
                     y,
                     z))
                elif item.categoryID == groups and groups == const.categoryDeployable:
                    if cfg.invgroups.Get(item.groupID).anchorable:
                        if not bp.GetBall(item.itemID).isFree:
                            state = u'Anchored'
                        else:
                            state = u'Unanchored'
                    m.append(('Deployables',
                     owner.Group().groupName,
                     item.typeID,
                     item.itemID,
                     owner.name,
                     distance,
                     state,
                     x,
                     y,
                     z))
                elif item.categoryID == groups and item.categoryID == const.categoryEntity:
                    m.append(('%s/%s' % (u'NPC', u'Entity'),
                     owner.Group().groupName,
                     item.typeID,
                     item.itemID,
                     owner.name,
                     distance,
                     state,
                     x,
                     y,
                     z))

        return m

    def Search(self, group = None, *args):
        ignoredGroups = [const.groupPlanet,
         const.groupMoon,
         const.groupAsteroidBelt,
         const.groupSun,
         const.groupSecondarySun,
         const.groupStargate,
         const.groupCapturePointTower,
         const.groupControlBunker,
         const.groupSentryGun,
         const.groupBillboard,
         const.groupDestructibleStationServices]
        wnd = DestroyableItemsWindow.GetIfOpen()
        bp = sm.GetService('michelle').GetBallpark()
        targets = []
        self.ballParkData = []
        playersPresent = []
        if util.IsSolarSystem(session.locationid):
            for ballID in bp.balls.keys():
                try:
                    item = bp.GetInvItem(ballID)
                    if item and item.groupID not in ignoredGroups:
                        self.ballParkData.append(item)
                        if item.categoryID == const.categoryShip and bp.GetBall(ballID).isInteractive:
                            playersPresent.append(item.charID)
                except:
                    sys.exc_clear()
                    continue

            if group == 'all':
                groups = [const.categoryDrone,
                 const.categoryCelestial,
                 const.categoryShip,
                 const.categoryStructure,
                 const.categoryDeployable,
                 const.categoryEntity,
                 const.categorySovereigntyStructure]
                targets += self.Collate(self.ballParkData, group=groups, players=playersPresent)
            else:
                targets += self.Collate(self.ballParkData, group=group, players=playersPresent)
        nodes = []
        verbose = settings.char.ui.Get('verboseDestroyables', 0)
        maxRange = self.dir_rangeinput.GetValue() * 1000
        if targets:
            for each in targets:
                ownertype = each[1]
                ownername = each[4]
                distance = each[5]
                if maxRange and maxRange < distance:
                    continue
                itemname = cfg.invtypes.Get(each[2]).name
                displayname = cfg.evelocations.Get(each[3]).name
                if not displayname:
                    displayname = '-'
                if verbose:
                    x = each[7]
                    y = each[8]
                    z = each[9]
                    label = u'%s<t>%s<t>%s<t>%s<t>%s<t>%s<t>%s<t>%s<t>%s<t>%s<t>%s' % (each[0],
                     each[6],
                     each[3],
                     util.FmtDist(distance, maxdemicals=1),
                     itemname,
                     displayname,
                     ownername,
                     ownertype,
                     x,
                     y,
                     z)
                    hint = u'Name: %s<br>Type: %s<br>Owner: %s<br>State: %s<br>Relative Position: [%s, %s, %s]' % (displayname,
                     itemname,
                     ownername,
                     each[6],
                     x,
                     y,
                     z)
                    entry = listentry.Get('InsiderDestroyables', {'label': label,
                     'hint': hint,
                     'entrytype': each[0],
                     'ownertype': ownertype,
                     'itemname': itemname,
                     'typeID': each[2],
                     'itemID': each[3],
                     'ownername': ownername,
                     'name': displayname,
                     u'Distance': util.FmtDist(distance, maxdemicals=1),
                     u'sort_Distance': distance,
                     'x': x,
                     'y': y,
                     'z': z})
                else:
                    label = u'%s<t>%s<t>%s' % (each[0], each[3], itemname)
                    hint = u'Name: %s<br>Type: %s<br>Owner: %s<br>State: %s' % (displayname,
                     itemname,
                     ownername,
                     each[6])
                    entry = listentry.Get('InsiderDestroyables', {'label': label,
                     'hint': hint,
                     'entrytype': each[0],
                     'ownertype': ownertype,
                     'itemname': itemname,
                     'typeID': each[2],
                     'itemID': each[3],
                     'ownername': ownername,
                     'name': displayname})
                nodes.append(entry)

        if verbose:
            self.scroll.Load(contentList=nodes, headers=['Entry Type',
             'State',
             'Item ID',
             'Distance',
             'Type',
             'Name',
             'Owner Name',
             'Owner Type',
             'x (m)',
             'y (m)',
             'z (m)'], fixedEntryHeight=18)
        else:
            self.scroll.Load(contentList=nodes, headers=['Entry Type', 'Item ID', 'Type'], fixedEntryHeight=18)
        if not nodes:
            self.scroll.ShowHint(u'No items found')
        else:
            self.scroll.ShowHint()

    exports = {'destroyableItems.Show': Show,
     'destroyableItems.Search': Search,
     'destroyableItems.Hide': Hide}
