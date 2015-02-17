#Embedded file name: eve/devtools/script\svc_invtools.py
import sys
import blue
import service
import random
import types
import time
from service import *
import uix
import uiutil
import carbonui.const as uiconst
import util
import uicontrols
import uiprimitives
MAX_VOLUME = 1000000
Progress = lambda title, text, current, total: sm.GetService('loading').ProgressWnd(title, text, current, total)

class InvTools(service.Service):
    __module__ = __name__
    __exportedcalls__ = {}
    __notifyevents__ = []
    __dependencies__ = []
    __servicename__ = 'invtools'
    __displayname__ = 'invtools'
    __guid__ = 'svc.invtools'

    def __init__(self):
        Service.__init__(self)
        self.inv = sm.GetService('invCache').GetInventory

    def Run(self, memStream = None):
        self.state = SERVICE_START_PENDING
        Service.Run(self, memStream)
        self.wnd = None
        self.state = SERVICE_RUNNING

    def Stop(self, memStream = None):
        self.state = SERVICE_STOP_PENDING
        Service.Stop(self, memStream)
        self.state = SERVICE_STOPPED

    def Startup(self, *args):
        pass

    def GetShip(self, *args):
        """
            Returns the inventory instance for the current ship.
        """
        if not hasattr(eve.session, 'shipid'):
            return
        return self.inv(eve.session.shipid)

    def GetSelf(self, *args):
        """
            Returns the inventory instance for the current character
            Used to access skills and such that are stored 'in' the character.
        """
        if not hasattr(eve.session, 'charid'):
            return
        return self.inv(eve.session.charid)

    def GetSpecial(self, loc = None, *args):
        """
            Returns the inventory instance for a specified container
        """
        if loc is None:
            return
        return self.inv(loc)

    def GetTypes(self, want, categories = True, onlyPublished = True, onlyUnpublished = False, volume = None, *args):
        """
            This function resolves a list of categoryIDs or groupIDs into the typeIDs
            that comprise it by choosing which method to use as determined by the
            category and group variables passed to it.
        
            The function makes use of the getattr method to attach to the needed functions
        
            Usage:
                GetTypes(want=[x,y,z], categories=False)
                 - where x, y and z are groupIDs
                GetTypes([a,b,c])
                 - where a, b and c are categoryIDs
            Note:
                - 'want' _must_ be a list of IDs e.g.: [943,]
                - onlyPublished overrides onlyUnpublished. To use onlyUnpublished, you must
                  set onlyPublished=False
        """
        if volume is None:
            volume = float(MAX_VOLUME)
        listOfTypes = []
        fieldType = ['groupID', 'categoryID'][categories]
        queryType = ['invtypes', 'invgroups'][categories]
        cfgQuery = getattr(cfg, queryType)
        if onlyPublished:
            onlyUnpublished = False
        for item in cfg.invtypes:
            if onlyPublished:
                if item.published:
                    lookup = [item.typeID, item.groupID]
                    use = lookup[categories]
                    if getattr(cfgQuery.Get(use), fieldType) in want:
                        if item.volume < volume:
                            listOfTypes.append(lookup[0])
            elif onlyUnpublished:
                if not item.published:
                    lookup = [item.typeID, item.groupID]
                    use = lookup[categories]
                    if getattr(cfgQuery.Get(use), fieldType) in want:
                        if item.volume < volume:
                            listOfTypes.append(lookup[0])
            else:
                lookup = [item.typeID, item.groupID]
                use = lookup[categories]
                if getattr(cfgQuery.Get(use), fieldType) in want:
                    if item.volume < volume:
                        listOfTypes.append(lookup[0])

        return listOfTypes

    def SpawnRandom(self, loc = None, flag = None, minQty = None, maxQty = None, iterations = None, categories = True, groups = False, want = None, onlyPublished = True, onlyUnpublished = False, useMultiMove = True, volume = None, *args):
        """
            Spawns random items to the current ship and then transfers them to the specified hangar
            args:
                loc         = location to move items to after spawning
                maxQty      = maximum stack size for each item
                minQty      = minimum stack size for each item
                iterations  = number of items to spawn
                categories  = specifies 'want' is a categoryID
                groups      = specifies 'want' is a groupID
                NOTE:
                    setting categories=True overrides groups=True
                want        = list of categoryIDs/groupIDs of items you want to spawn
                onlyPublished and onlyUnpublished are to specify the published flag for 
                    the items being spawned
        """
        if loc is None:
            return
        if loc == util.GetActiveShip() and sm.GetService('clientDogmaIM').GetDogmaLocation().GetItem(loc).groupID == const.groupCapsule:
            eve.Message('CustomNotify', {'notify': 'You cannot spawn items into capsule.'})
            return
        if minQty is None:
            minQty = 1
        if maxQty is None:
            maxQty = 10
        if iterations is None:
            iterations = 10
        if minQty > maxQty:
            eve.Message('CustomNotify', {'notify': 'Min stack size is greater than max stack size.'})
            return
        if minQty > iterations:
            eve.Message('CustomNotify', {'notify': 'Min stack size is greater than number of items.'})
            return
        if categories and groups:
            groups = False
        if not categories:
            groups = True
        if want is None:
            categories = True
            groups = False
            want = [const.categoryCharge, const.categoryCommodity, const.categoryModule]
        if type(want) is types.IntType:
            want = [want]
        if type(want) is not types.ListType:
            return
        possibleTypes = []
        selectedTypesAndQty = []
        mustMove = []
        spawntype = ['groupID', 'categoryID'][categories]
        cfgtype = ['invtypes', 'invgroups'][categories]
        cfgquery = getattr(cfg, cfgtype)
        possibleTypes = self.GetTypes(want, categories=categories, onlyPublished=onlyPublished, onlyUnpublished=onlyUnpublished, volume=volume)
        if len(possibleTypes) == 0:
            return
        for i in xrange(1, iterations + 1):
            selectedTypesAndQty.append((random.choice(possibleTypes), random.choice(xrange(minQty, maxQty + 1))))

        title = 'Spawning...'
        idx = int()
        qty = len(selectedTypesAndQty)
        Progress(title, 'Processing', 0, qty)
        for t, q in selectedTypesAndQty:
            idx += 1
            msg = 'Processing %d of %d' % (idx, qty)
            Progress(title, msg, idx, qty)
            if q == 0:
                q = 1
            if eve.session.role & service.ROLE_WORLDMOD:
                itemID = sm.RemoteSvc('slash').SlashCmd('/createitem %d %d' % (t, q))
            elif eve.session.role & service.ROLE_GML:
                try:
                    itemID = sm.RemoteSvc('slash').SlashCmd('/load me %d %d' % (t, q))[0]
                except UserError:
                    sys.exc_clear()

            else:
                return
            mustMove.append(itemID)

        Progress(title, 'Complete', 1, 1)
        if session.stationid is not None and loc != const.containerHangar:
            self.MoveItems(items=mustMove, source=session.locationid, destination=loc, flag=flag, multi=useMultiMove, suppress=True)

    def GetFlags(self, *args):
        """
            This function returns a list of the flags in const that start with flag*
            This is to help the discovery of location flags for the uninitiated.
        """
        flagList = []
        for key in const.__dict__:
            if key.lower().startswith('flag'):
                flagList.append(key)

        flagList.sort()
        return flagList

    def GetItemFromContainer(self, itemID = None, container = None, *args):
        """
            Returns the inventory record for an item in a particular container or None if
            the item is not found in the specified location.
            args:
                itemID      =   the itemID of the item you want to query
                container   =   containerID of the location of the item
        """
        if itemID is None:
            return
        if container is None:
            return
        inv = [ item for item in self.inv(container).List() ]
        for item in inv:
            if item.itemID == itemID:
                return item

    def MoveItems(self, items = None, source = None, destination = None, flag = None, multi = True, suppress = False, **kwargs):
        """
            Moves items from one container to another using either single move or multimove. Also prints out a
            summary of the findings to the console.
            args:
                items       =   a list of itemID's relating to the items to be moved.
                source      =   the originating container
                destination =   the destination container id
                flag        =   used to send items to corp hangars and specific locations
                multi       =   True/False flag for using multimove (or not)
                suppress    =   flag to suppress the console output
        
            usage:
                items = [1234, 2345, 3456, 4567,]
                self.MoveItems(items=items, source=eve.session.shipid,
                    destination=const.containerHangar, flag=None, multi=False, suppress=True)
        
                This would then move the items in the items list, from the cargo on the 
                current ship, to the hangar at the current station, without using multimove
                and suppressing the console output.
        
                For sending to an office division, you must have the officeID:
        
                items  = [1234, 2345, 3456, 4567,]
                office = sm.StartService("corp").GetOffice()
                self.MoveItems(items=items, source=eve.session.shipid,
                    destination=office.itemID, flag=const.flagCorpSAG2, 
                    multi=True, suppress=True)
        
                This moves 'items' from the ship, to the second division of the corp hangar
                present at the current location. Some logic would need to be inserted,
                because if the GetOffice() calls does not find an office, it will return None
                and the subsequent MoveItems call will fail.
        """
        if None in (items, source, destination):
            return
        if not suppress:
            destinationCargo = {}
            postDestinationCargo = {}
            sourceCargo = {}
            postSourceCargo = {}
            cargoDict = {}
            for rec in self.inv(destination).List():
                destinationCargo[rec.itemID] = rec.stacksize

            for rec in self.inv(source).List():
                sourceCargo[rec.itemID] = rec.stacksize

            for each in items:
                cargoDict[each] = self.GetItemFromContainer(each, source).stacksize

        title = 'Moving...'
        Progress(title, 'Telling Scotty the docking manager what to do...', 0, 1)
        if multi:
            if flag is not None:
                self.inv(destination).MultiAdd(items, source, flag=flag, **kwargs)
            else:
                self.inv(destination).MultiAdd(items, source, **kwargs)
        else:
            idx = int()
            all = len(items)
            for itemID in items:
                idx += 1
                msg = 'Processing %d of %d' % (idx, all)
                Progress(title, msg, idx, all)
                self.inv(destination).Add(itemID, source, **kwargs)

        Progress(title, "All done, don't forget to pay the man!", 1, 1)
        if not suppress:
            blue.pyos.synchro.SleepWallclock(5000)
            for rec in self.inv(destination).List():
                postDestinationCargo[rec.itemID] = rec.stacksize

            for rec in self.inv(source).List():
                postSourceCargo[rec.itemID] = rec.stacksize

            for k in cargoDict.iterkeys():
                if k in postDestinationCargo:
                    qtyCargo = cargoDict[k]
                    qtyDest = postDestinationCargo[k]
                    if qtyCargo == qtyDest:
                        pass
                    else:
                        print k, ' is in destination and qty is different!'
                else:
                    print '\t%s is not in destination', k
                    print '\tsrc inv rec', self.GetItemFromContainer(k, source)
                    print '\tdest inv rec:', self.GetItemFromContainer(k, destination)

            postSourceCopy = postSourceCargo.copy()
            postSourceCopy.update(cargoDict)
            print '\tsrc ok?\t', ['No', 'Yes'][postSourceCopy == sourceCargo]
            destinationCopy = destinationCargo.copy()
            destinationCopy.update(cargoDict)
            print '\tdest ok?\t', ['No', 'Yes'][destinationCopy == postDestinationCargo]

    def InvMoveLoop(self, loop = None, noSpawn = True, *args):
        """
            Inventory Move Loop
            Moves items between the current ship, station hangar and office divisions if
            present. Does the moving with both the single move and multimove code paths
            by invoking self.MoveItems(...) and specifying multi=True/False
            args:
                loop    =   determines the number of iterations to loop through
                noSpawn =   if enabled, does not spawn a random selection of items to move
                            or, if disabled, will not spawn, and will simply use the
                            contents of the source hangar (ship cargo)
        """
        if loop is None:
            loop = 10
        _loop = loop
        if not noSpawn:
            self.SpawnRandom(eve.session.shipid, iterations=10)
        items = self.GetShip().ListCargo()
        if len(items) == 0:
            return
        itemIDs = [ rec.itemID for rec in items ]
        moveCommands = [(eve.session.shipid,
          const.containerHangar,
          const.flagHangar,
          False),
         (const.containerHangar,
          eve.session.shipid,
          const.flagCargo,
          False),
         (eve.session.shipid,
          const.containerHangar,
          const.flagHangar,
          True),
         (const.containerHangar,
          eve.session.shipid,
          const.flagCargo,
          True)]
        lookup = {util.GetActiveShip(): 'Ship',
         const.containerHangar: 'Hangar Floor',
         const.flagCargo: 'Cargo Bay',
         const.flagHangar: 'Corp Hangar, Division 1',
         const.flagCorpSAG2: 'Corp Hangar, Division 2',
         const.flagCorpSAG3: 'Corp Hangar, Division 3',
         const.flagCorpSAG4: 'Corp Hangar, Division 4',
         const.flagCorpSAG5: 'Corp Hangar, Division 5',
         const.flagCorpSAG6: 'Corp Hangar, Division 6',
         const.flagCorpSAG7: 'Corp Hangar, Division 7'}
        usecase = {True: 'multimove',
         False: 'single move'}
        office = sm.StartService('corp').GetOffice()
        if office is not None:
            office = office.itemID
        if office is not None:
            moveCommands.extend([(eve.session.shipid,
              office,
              const.flagHangar,
              False),
             (office,
              office,
              const.flagCorpSAG2,
              False),
             (office,
              office,
              const.flagCorpSAG3,
              False),
             (office,
              office,
              const.flagCorpSAG4,
              False),
             (office,
              office,
              const.flagCorpSAG5,
              False),
             (office,
              office,
              const.flagCorpSAG6,
              False),
             (office,
              office,
              const.flagCorpSAG7,
              False),
             (office,
              eve.session.shipid,
              const.flagCargo,
              False),
             (eve.session.shipid,
              office,
              const.flagHangar,
              True),
             (office,
              office,
              const.flagCorpSAG2,
              True),
             (office,
              office,
              const.flagCorpSAG3,
              True),
             (office,
              office,
              const.flagCorpSAG4,
              True),
             (office,
              office,
              const.flagCorpSAG5,
              True),
             (office,
              office,
              const.flagCorpSAG6,
              True),
             (office,
              office,
              const.flagCorpSAG7,
              True),
             (office,
              eve.session.shipid,
              const.flagCargo,
              True)])
            lookup[office] = 'Office'
        start = time.time()
        while loop:
            for src, dest, f, m in moveCommands:
                if f is not None:
                    print "Moving from %s to %s's %s using %s:" % (lookup[src],
                     lookup[dest],
                     lookup[f],
                     usecase[m])
                else:
                    print 'Moving from %s to %s using %s:' % (lookup[src], lookup[dest], usecase[m])
                t = time.time()
                self.MoveItems(itemIDs, src, dest, f, m)
                duration = time.time() - t
                print 'Move took %d:%.2d to move %s items\n' % (duration / 60, duration % 60, len(items))

            loop -= 1

        finish = time.time() - start
        print 'Move test complete, total time: %d:%.2d for %s iteration(s)' % (finish / 60, finish % 60, _loop)
        print '%s items were moved %s times' % (len(items), len(moveCommands) * _loop)


class InvToolsWnd(uicontrols.Window):
    __guid__ = 'form.invTools'
    __neocommenuitem__ = (('Inventory Tools', 'invTools'), True, ROLE_GMH)
    __notifyevents__ = ['OnSessionChanged']
    RANDOM_COMBO = ('Random', 'random')
    PUBLISHED_LIST = ['<color=0xffff0000>Not Published<color=0xffffffff>', '<color=0xff00ff00>Published<color=0xffffffff>']
    default_windowID = 'InvTools'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.SetMinSize([200, 290])
        self.SetWndIcon(None)
        self.SetCaption('Inventory Tools')
        self.MakeUnResizeable()
        self.SetTopparentHeight(0)
        self.cats = None
        self.grps = None
        self.locs = None
        self.DoSetup()
        self.Begin()

    def OnSessionChanged(self, isRemote, session, change):
        """
            Called when a session change occurs, to update the location combo dialog options.
        """
        self.location.entries = self.locs = self.GetLocations()
        self.location.SetValue('ship')

    def DoSetup(self):
        """
            Setup routine that populates the category combo, ans sets up the default
            configuration.
        """
        self.cats = [ ('%s [%s]' % (c.name, self.PUBLISHED_LIST[c.published]), c.categoryID) for c in cfg.invcategories if c.categoryID is not 0 ]
        self.cats.sort()
        self.cats.insert(0, self.RANDOM_COMBO)
        self.grps = [self.RANDOM_COMBO]
        self.default = {'categoryID': 'random',
         'groupID': 'random',
         'published': 1,
         'multimove': 1,
         'minQty': 1,
         'maxQty': 10,
         'number': 10,
         'volume': MAX_VOLUME,
         'location': 'ship'}
        self.config = self.default.copy()
        self.locs = self.GetLocations()
        self.spawnlocation = (util.GetActiveShip(), const.flagCargo)
        self.prepCorpHangar = False

    def Begin(self):
        """
            Main UI creation and layout.
        """
        margin = const.defaultPadding
        self.main = main = uiprimitives.Container(name='main', parent=self.sr.main, padding=margin)
        uicontrols.Frame(parent=main, color=(1.0, 1.0, 1.0, 0.2))
        uix.GetContainerHeader('Random Item Spawn', main, bothlines=0)
        COMBOPADDING = 120
        self.categories = uicontrols.Combo(parent=main, options=self.cats, select=self.config['categoryID'], name='category', align=uiconst.TOTOP, callback=self.DoCategoryChange, padding=(COMBOPADDING,
         margin,
         margin,
         0))
        txt = uicontrols.Label(text='Category', parent=self.categories, align=uiconst.CENTERLEFT, left=-COMBOPADDING + margin, fontsize=10)
        self.groups = uicontrols.Combo(parent=main, options=self.grps, select=self.config['groupID'], name='group', align=uiconst.TOTOP, callback=self.DoGroupChange, padding=(COMBOPADDING,
         margin,
         margin,
         0))
        txt = uicontrols.Label(text='Group', parent=self.groups, align=uiconst.CENTERLEFT, left=-COMBOPADDING + margin, fontsize=10)
        self.pub = uicontrols.Checkbox(text='use only published items', parent=main, configName='pub', retval=0, checked=bool(self.config['published'] == 1), groupname='published', align=uiconst.TOTOP, callback=self.DoPublishChange, padding=(margin,
         0,
         margin,
         0))
        uiprimitives.Line(parent=main, align=uiconst.TOTOP)
        self.unpub = uicontrols.Checkbox(text='use only unpublished items', parent=main, configName='unpub', retval=0, checked=bool(self.config['published'] == 0), groupname='published', align=uiconst.TOTOP, callback=self.DoPublishChange, padding=(margin,
         0,
         margin,
         0))
        self.all = uicontrols.Checkbox(text='use all items', parent=main, configName='all', retval=0, checked=bool(self.config['published'] == -1), groupname='published', align=uiconst.TOTOP, callback=self.DoPublishChange, padding=(margin,
         0,
         margin,
         0))
        uiprimitives.Line(parent=main, align=uiconst.TOTOP)
        self.multimove = uicontrols.Checkbox(text='use multimove', parent=main, configName='multimove', retval=0, checked=self.config['multimove'], groupname=None, align=uiconst.TOTOP, callback=self.DoMoveChange, padding=(margin,
         0,
         margin,
         0))
        uiprimitives.Line(parent=main, align=uiconst.TOTOP)
        for checkbox in [self.pub,
         self.unpub,
         self.all,
         self.multimove]:
            checkbox.hint = 'Changing this is <color=0xffff0000>not advised<color=0xffffffff>.<br>Proceed with caution!'

        INPUTPADDING = 170
        self.min = uicontrols.SinglelineEdit(name='minQty', setvalue=str(self.config['minQty']), ints=(1, 100), parent=main, align=uiconst.TOTOP, padding=(INPUTPADDING,
         margin,
         margin,
         0))
        txt = uicontrols.Label(text='Minimum stack size', parent=self.min, align=uiconst.CENTERLEFT, left=-INPUTPADDING + margin, fontsize=10)
        self.max = uicontrols.SinglelineEdit(name='maxQty', setvalue=str(self.config['maxQty']), ints=(1, 1000), parent=main, align=uiconst.TOTOP, padding=(INPUTPADDING,
         margin,
         margin,
         0))
        txt = uicontrols.Label(text='Maximum stack size', parent=self.max, align=uiconst.CENTERLEFT, left=-INPUTPADDING + margin, fontsize=10)
        self.number = uicontrols.SinglelineEdit(name='number', setvalue=str(self.config['number']), ints=(1, 1000), parent=main, align=uiconst.TOTOP, padding=(INPUTPADDING,
         margin,
         margin,
         0))
        txt = uicontrols.Label(text='Number of Items', parent=self.number, align=uiconst.CENTERLEFT, left=-INPUTPADDING + margin, fontsize=10)
        self.volume = uicontrols.SinglelineEdit(name='volume', setvalue=str(self.config['volume']), floats=(0, MAX_VOLUME), parent=main, align=uiconst.TOTOP, padding=(INPUTPADDING,
         margin,
         margin,
         0))
        txt = uicontrols.Label(text='Maximum item volume', parent=self.volume, align=uiconst.CENTERLEFT, left=-INPUTPADDING + margin, fontsize=10)
        self.location = uicontrols.Combo(parent=main, options=self.locs, select=self.config['location'], name='location', align=uiconst.TOTOP, callback=self.DoLocationChange, padding=(COMBOPADDING,
         margin,
         margin,
         0))
        txt = uicontrols.Label(text='Location', parent=self.location, align=uiconst.CENTERLEFT, left=-COMBOPADDING + margin, fontsize=10)
        buttons = [['Spawn',
          self.DoFormSubmit,
          None,
          81]]
        btns = uicontrols.ButtonGroup(btns=buttons, line=1, parent=main, padTop=margin)
        btn = uiutil.GetChild(btns, 'Spawn_Btn')
        if eve.session.role & service.ROLE_WORLDMOD:
            btn.hint = 'Spawn using /createitem...'
        elif eve.session.role & service.ROLE_GML:
            btn.hint = 'Spawn using /load...'
        else:
            btn.hint = 'No <b>WORLDMOD</b> or <b>GML</b> role present.'
        self.SetHeight(sum([ each.height + each.padTop + each.padBottom + each.top for each in main.children ]) + self.GetHeaderHeight() + margin * 4)

    def DoCategoryChange(self, combo, text, value):
        """
            This sets the categoryID and updates the groupID combo at the same time.
            If the user has set the categoryID combo to "Random", then the groupID combo 
            is blanked and populated with one entry listing, "Random".
        """
        self.config['categoryID'] = value
        if value == 'random':
            self.grps = [self.RANDOM_COMBO]
        else:
            self.grps = [ ('%s [%s]' % (g.name, self.PUBLISHED_LIST[g.published]), g.groupID) for g in cfg.invgroups if g.categoryID == value ]
            self.grps.sort()
            self.grps.insert(0, self.RANDOM_COMBO)
        self.groups.SetValue('random')
        self.groups.entries = self.grps

    def DoGroupChange(self, combo, text, value):
        """
            This sets the groupID value in the config dictionary to be the selected group.
        """
        self.config['groupID'] = value

    def DoLocationChange(self, combo, text, value):
        """
            Spawn location combo callback function. Configures the self.location value
            as specified by the selected value of the combo dialog.
        """
        self.prepCorpHangar = False
        officeFlags = [const.flagHangar,
         const.flagCorpSAG2,
         const.flagCorpSAG3,
         const.flagCorpSAG4,
         const.flagCorpSAG5,
         const.flagCorpSAG6,
         const.flagCorpSAG7]
        self.config['location'] = value
        if value in officeFlags:
            self.prepCorpHangar = True
            self.spawnlocation = (self.office, value)
        elif value == 'ship':
            self.spawnlocation = (util.GetActiveShip(), const.flagCargo)
        elif value == 'hangar':
            self.spawnlocation = const.containerHangar

    def DoPublishChange(self, cb):
        """
            This function provides a simple lookup routine to parse the selected value into
            the config dictionary. Used on the publish checkboxes for callback.
            It sets flags for each unique selection:
                published only   =  1
                unpublished only =  0
                all items        = -1
        """
        lookup = {'pub': 1,
         'unpub': 0,
         'all': -1}
        self.config['published'] = lookup[cb.name]

    def DoMoveChange(self, cb):
        """
            Multimove checkbox callback function.
        """
        self.config['multimove'] = cb.GetValue()

    def DoFormSubmit(self, *args):
        """
            Main submit function.
            Ths parses the data and enforces some validation, before passing it onto the
            service.
        """
        for formField in [self.min,
         self.max,
         self.number,
         self.volume]:
            configFieldName = formField.name
            self.config[configFieldName] = formField.GetValue()

        loc = self.spawnlocation
        if isinstance(loc, types.TupleType):
            loc, flag = loc
        else:
            flag = None
        if self.config['categoryID'] == 'random':
            ids = set([ c.categoryID for c in cfg.invgroups ])
            want = list(ids)
            categories = True
            groups = False
        elif self.config['groupID'] == 'random':
            ids = set([ g.groupID for g in cfg.invgroups if g.categoryID == self.config['categoryID'] ])
            want = list(ids)
            categories = False
            groups = True
        else:
            want = [self.config['groupID']]
            categories = False
            groups = True
        publishedFlags = {0: (False, True),
         1: (True, False),
         -1: (False, False)}
        onlyPublished, onlyUnpublished = publishedFlags[self.config['published']]
        if self.prepCorpHangar is True:
            sm.GetService('window').OpenCorpHangar(None, None, 1)
        sm.StartService('invtools').SpawnRandom(loc=loc, flag=flag, minQty=self.config['minQty'], maxQty=self.config['maxQty'], iterations=self.config['number'], categories=categories, groups=groups, want=want, onlyPublished=onlyPublished, onlyUnpublished=onlyUnpublished, useMultiMove=self.config['multimove'], volume=self.config['volume'])

    def GetLocations(self):
        """
            Invoked from the 'OnSessionChanged' event and for the initial population of the 
            location combo options. Parses the available options into a list, and sets it
            as the options for the drop down combo.
        """
        ret = [('Current Ship', 'ship')]
        if eve.session.stationid is not None:
            ret.append(('Hangar Floor', 'hangar'))
            office = sm.StartService('corp').GetOffice()
            if office is not None:
                office = office.itemID
            if office is not None:
                self.office = office
                for flag, text in [(const.flagHangar, 'Corp Hangar, Division 1'),
                 (const.flagCorpSAG2, 'Corp Hangar, Division 2'),
                 (const.flagCorpSAG3, 'Corp Hangar, Division 3'),
                 (const.flagCorpSAG4, 'Corp Hangar, Division 4'),
                 (const.flagCorpSAG5, 'Corp Hangar, Division 5'),
                 (const.flagCorpSAG6, 'Corp Hangar, Division 6'),
                 (const.flagCorpSAG7, 'Corp Hangar, Division 7')]:
                    ret.append((text, flag))

        else:
            self.office = None
        return ret
