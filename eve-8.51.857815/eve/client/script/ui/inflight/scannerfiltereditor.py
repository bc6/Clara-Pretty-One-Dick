#Embedded file name: eve/client/script/ui/inflight\scannerfiltereditor.py
import uiprimitives
import uicontrols
import uiutil
import util
from eve.client.script.ui.control import entries as listentry
import carbonui.const as uiconst
import localization

class ScannerFilterEditor(uicontrols.Window):
    __guid__ = 'form.ScannerFilterEditor'
    default_windowID = 'probeScannerFilterEditor'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.specialGroups = util.GetNPCGroups()
        self.filterID = None
        self.scope = 'inflight'
        self.SetCaption(localization.GetByLabel('UI/Inflight/Scanner/ScannerFilterEditor'))
        self.SetMinSize([300, 250])
        self.SetWndIcon()
        self.SetTopparentHeight(0)
        self.sr.main = uiutil.GetChild(self, 'main')
        topParent = uiprimitives.Container(name='topParent', parent=self.sr.main, height=64, align=uiconst.TOTOP)
        topParent.padRight = 6
        topParent.padLeft = 6
        uicontrols.EveHeaderSmall(text=localization.GetByLabel('UI/Inflight/Scanner/FilterName'), parent=topParent, state=uiconst.UI_DISABLED, idx=0, top=2)
        nameEdit = uicontrols.SinglelineEdit(name='name', parent=topParent, setvalue=None, align=uiconst.TOTOP, maxLength=64)
        nameEdit.top = 16
        self.sr.nameEdit = nameEdit
        hint = uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Inflight/Scanner/SelectGroupsToFilter'), parent=topParent, align=uiconst.TOTOP)
        hint.top = 4
        self.sr.topParent = topParent
        self.sr.scroll = uicontrols.Scroll(parent=self.sr.main, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        self.sr.scroll.multiSelect = 0
        self.DefineButtons(uiconst.OKCANCEL, okLabel=localization.GetByLabel('UI/Common/Buttons/Save'), okFunc=self.SaveChanges, cancelFunc=self.Close)
        self.scanGroupsNames = {const.probeScanGroupSignatures: localization.GetByLabel('UI/Inflight/Scanner/CosmicSignature'),
         const.probeScanGroupShips: localization.GetByLabel('UI/Inflight/Scanner/Ship'),
         const.probeScanGroupStructures: localization.GetByLabel('UI/Inflight/Scanner/Structure'),
         const.probeScanGroupDronesAndProbes: cfg.invcategories.Get(const.categoryDrone).categoryName}
        self.Maximize()
        self.OnResizeUpdate()

    def LoadData(self, filterID):
        self.tempState = {}
        self.filterID = filterID
        if filterID is None:
            filterName = ''
        else:
            filterName, userSettings = sm.GetService('scanSvc').GetResultFilter(filterID)
            self.sr.nameEdit.SetValue(filterName)
            for each in userSettings:
                self.tempState[each] = True

        self._originalName = filterName
        self.LoadTypes()

    def OnResizeUpdate(self, *args):
        self.sr.topParent.height = sum([ each.height + each.top + each.padTop + each.padBottom for each in self.sr.topParent.children if each.align == uiconst.TOTOP ])

    def SaveChanges(self, *args):
        name = self.sr.nameEdit.GetValue()
        if name is None or name == '':
            eve.Message('CustomNotify', {'notify': localization.GetByLabel('UI/Inflight/Scanner/PleaseNameFilter')})
            self.sr.nameEdit.SetFocus()
            return
        if name.lower() == localization.GetByLabel('UI/Common/Show all').lower():
            eve.Message('CustomNotify', {'notify': localization.GetByLabel('UI/Inflight/Scanner/CannotNameFilter')})
            return
        groups = [ key for key, value in self.tempState.iteritems() if bool(value) ]
        if not groups:
            eve.Message('CustomNotify', {'notify': localization.GetByLabel('UI/Inflight/Scanner/SelectGroupsForFilter')})
            self.sr.scroll.SetFocus()
            return
        current = settings.user.ui.Get('probeScannerFilters', {})
        if name in current:
            if eve.Message('OverwriteFilter', {'filter': name}, uiconst.YESNO) != uiconst.ID_YES:
                return
        if name != self._originalName and self._originalName in current:
            del current[self._originalName]
        if self.filterID is None:
            sm.GetService('scanSvc').CreateResultFilter(name, groups)
        else:
            sm.GetService('scanSvc').EditResultFilter(self.filterID, name, groups)
        current[name] = groups
        settings.user.ui.Set('probeScannerFilters', current)
        settings.user.ui.Set('activeProbeScannerFilter', name)
        sm.ScatterEvent('OnNewScannerFilterSet', name, current[name])
        self.Close()

    def LoadTypes(self):
        categoryList = {}
        for scanGroupID, groupSet in const.probeScanGroups.iteritems():
            if scanGroupID not in self.scanGroupsNames:
                continue
            catName = self.scanGroupsNames[scanGroupID]
            for groupID in groupSet:
                if groupID == const.groupCosmicSignature:
                    for signatureType in [const.attributeScanGravimetricStrength,
                     const.attributeScanLadarStrength,
                     const.attributeScanMagnetometricStrength,
                     const.attributeScanRadarStrength,
                     const.attributeScanWormholeStrength,
                     const.attributeScanAllStrength]:
                        if catName not in categoryList:
                            categoryList[catName] = [(groupID, signatureType)]
                        elif (groupID, signatureType) not in categoryList[catName]:
                            categoryList[catName].append((groupID, signatureType))

                else:
                    name = cfg.invgroups.Get(groupID).name
                    if catName not in categoryList:
                        categoryList[catName] = [(groupID, name)]
                    elif (groupID, name) not in categoryList[catName]:
                        categoryList[catName].append((groupID, name))

        sortCat = categoryList.keys()
        sortCat.sort()
        scrolllist = []
        for catName in sortCat:
            data = {'GetSubContent': self.GetCatSubContent,
             'MenuFunction': self.GetSubFolderMenu,
             'label': catName,
             'id': ('ProberScannerGroupSel', catName),
             'groupItems': categoryList[catName],
             'showlen': 1,
             'showicon': 'hide',
             'sublevel': 0,
             'state': 'locked',
             'BlockOpenWindow': 1}
            scrolllist.append(listentry.Get('Group', data))

        self.cachedScrollPos = self.sr.scroll.GetScrollProportion()
        self.sr.scroll.Load(contentList=scrolllist, scrolltotop=0, scrollTo=getattr(self, 'cachedScrollPos', 0.0))

    def GetSubFolderMenu(self, node):
        m = [None, (localization.GetByLabel('UI/Common/SelectAll'), self.SelectGroup, (node, True)), (localization.GetByLabel('UI/Common/DeselectAll'), self.SelectGroup, (node, False))]
        return m

    def SelectGroup(self, node, isSelect):
        for groupID, label in node.groupItems:
            if groupID == const.groupCosmicSignature:
                for signatureType in [const.attributeScanGravimetricStrength,
                 const.attributeScanLadarStrength,
                 const.attributeScanMagnetometricStrength,
                 const.attributeScanRadarStrength,
                 const.attributeScanWormholeStrength,
                 const.attributeScanAllStrength]:
                    self.tempState[groupID, signatureType] = isSelect

            else:
                self.tempState[groupID] = isSelect

        self.LoadTypes()

    def GetCatSubContent(self, nodedata, newitems = 0):
        scrolllist = []
        for groupID, groupName in nodedata.groupItems:
            if groupID == const.groupCosmicSignature:
                signatureType = groupName
                name = localization.GetByLabel(const.EXPLORATION_SITE_TYPES[signatureType])
                checked = self.tempState.get((groupID, signatureType), 0)
                retval = (groupID, signatureType)
            else:
                name = groupName
                checked = self.tempState.get(groupID, 0)
                retval = groupID
            data = util.KeyVal()
            data.label = name
            data.checked = checked
            data.cfgname = 'probeScannerFilters'
            data.retval = retval
            data.OnChange = self.CheckBoxChange
            data.sublevel = 0
            scrolllist.append(listentry.Get('Checkbox', data=data))

        return localization.util.Sort(scrolllist, key=lambda x: x.label)

    def CheckBoxChange(self, checkbox, *args):
        self.tempState[checkbox.data['retval']] = checkbox.checked
