#Embedded file name: eve/client/script/ui/shared\export.py
"""
Contains a base class for importing and exporting window as well as subclasses to import
and export overview and fittings.
"""
import uiprimitives
import uicontrols
import util
from eve.client.script.ui.control import entries as listentry
import os
import blue
import codecs
import sys
import carbonui.const as uiconst
import localization
import uiutil
import operator
import yaml
from eve.client.script.ui.inflight.overview import OverView, DraggableShareContainer
from xml.dom.minidom import getDOMImplementation, parse
from overviewPresets.overviewPresetUtil import GetDeterministicListFromDict, GetDictFromList, ReplaceInnerListsWithDicts, MAX_SHARED_PRESETS

class ImportBaseWindow(uicontrols.Window):
    """
    This is a base for creating an import window. We should never use this window
    directly but rather create a new windwow that inherits from it and overwrite
    import function and other functions. ImportFittingsWindow should give you some
    idea about how
    """
    __guid__ = 'form.ImportBaseWindow'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.SetMinSize([450, 250])
        self.minWidth = 225
        self.SetTopparentHeight(0)
        self.SetWndIcon(None)
        self.scrollWidth = 0
        dirpath = attributes.get('dirpath', None)
        if dirpath:
            self.dirpath = dirpath
        else:
            self.dirpath = os.path.join(blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL), 'EVE', 'Overview')
        self.ConstructLayout()

    def ConstructLayout(self, *args):
        self.sr.fileContainer = uiprimitives.Container(name='fileContainer', align=uiconst.TOLEFT, parent=self.sr.main, padTop=const.defaultPadding, width=256)
        self.sr.profilesContainer = uiprimitives.Container(name='profilesContainer', align=uiconst.TOALL, parent=self.sr.main, pos=(0, 0, 0, 0))
        self.sr.fileHeader = uicontrols.CaptionLabel(text=localization.GetByLabel('UI/Common/Files/FileName'), parent=self.sr.fileContainer, left=const.defaultPadding, align=uiconst.TOTOP, fontsize=14)
        fileScrollCont = uiprimitives.Container(name='fileScrollCont', parent=self.sr.fileContainer, align=uiconst.TOALL)
        self.sr.fileScroll = uicontrols.Scroll(name='fileScroll', parent=fileScrollCont, padding=(const.defaultPadding,
         0,
         const.defaultPadding,
         const.defaultPadding))
        self.sr.refreshFileListBtn = uicontrols.ButtonGroup(btns=[[localization.GetByLabel('UI/Commands/Refresh'),
          self.RefreshFileList,
          (),
          None]], parent=self.sr.fileContainer, idx=0)
        profilesTopCont = uiprimitives.Container(name='fileTopCont', parent=self.sr.profilesContainer, align=uiconst.TOTOP, height=40)
        profilesScrollCont = uiprimitives.Container(name='fileScrollCont', parent=self.sr.profilesContainer, align=uiconst.TOALL)
        self.sr.profilesHeader = uicontrols.CaptionLabel(text=localization.GetByLabel('UI/Common/PleaseSelect'), parent=profilesTopCont, align=uiconst.TOPLEFT, left=4)
        self.sr.profilesHeader.fontsize = 14
        self.checkAllCB = uicontrols.Checkbox(text=localization.GetByLabel('UI/Shared/CheckAllOn'), parent=profilesTopCont, align=uiconst.TOBOTTOM, height=16, padLeft=const.defaultPadding, callback=self.CheckAll, checked=True)
        self.sr.profilesScroll = uicontrols.Scroll(name='profilesScroll', parent=profilesScrollCont, padding=(const.defaultPadding,
         0,
         const.defaultPadding,
         const.defaultPadding))
        self.sr.importProfilesBtn = uicontrols.ButtonGroup(btns=[[localization.GetByLabel('UI/Commands/Import'),
          self.Import,
          (),
          None]], parent=self.sr.profilesContainer, idx=0)
        self.sr.importProfilesBtn.state = uiconst.UI_HIDDEN
        self.RefreshFileList()

    def RefreshFileList(self, *args):
        fileList = self.GetFilesByExt('.xml')
        contentList = []
        for fileName in fileList:
            contentList.append(listentry.Get('Generic', {'label': fileName,
             'OnClick': self.OnFileSelected}))

        self.sr.fileScroll.Load(contentList=contentList)

    def GetFilesByExt(self, ext):
        fileList = []
        if os.path.exists(self.dirpath):
            for file in os.listdir(self.dirpath):
                if file.endswith(ext):
                    fileList.append(file[:-len(ext)])

        return fileList

    def OnChange(self, *args):
        self.ChangeImportButtonState()

    def ChangeImportButtonState(self):
        anySelected = self.IsAnyEntrySelected()
        if anySelected:
            self.sr.importProfilesBtn.state = uiconst.UI_NORMAL
        else:
            self.sr.importProfilesBtn.state = uiconst.UI_HIDDEN

    def IsAnyEntrySelected(self):
        for entry in self.sr.profilesScroll.GetNodes():
            if entry.checked:
                return True

        return False

    def Import(self, *args):
        raise NotImplementedError('')

    def OnFileSelected(self, entry):
        raise NotImplementedError('')

    def CheckAll(self, *args):
        for entry in self.sr.profilesScroll.GetNodes():
            if entry.__guid__ == 'listentry.Checkbox':
                entry.checked = self.checkAllCB.checked
                if entry.panel:
                    entry.panel.Load(entry)

        self.ChangeImportButtonState()


class ExportBaseWindow(uicontrols.Window):
    """
    This is a base for creating an export window. We should never use this window
    directly but rather create a new windwow that inherits from it and overwrite
    export function and other functions. ImportFittingsWindow should give you some
    idea about how
    """
    __guid__ = 'form.ExportBaseWindow'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        dirpath = attributes.get('dirpath', None)
        if dirpath:
            self.dirpath = dirpath
        else:
            self.dirpath = os.path.join(blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL), 'EVE', 'Overview')
        self.SetTopparentHeight(0)
        self.SetWndIcon(None)
        self.SetMinSize([370, 270])
        self.ConstructLayout()

    def ConstructLayout(self, *args):
        self.topCont = uiprimitives.Container(name='topCont', align=uiconst.TOTOP, height=14, parent=self.sr.main)
        left = const.defaultPadding
        self.sr.buttonContainer = uiprimitives.Container(name='buttonContainer', align=uiconst.TOBOTTOM, parent=self.sr.main)
        self.checkAllCB = uicontrols.Checkbox(text=localization.GetByLabel('UI/Shared/CheckAllOn'), parent=self.topCont, align=uiconst.TOPLEFT, pos=(left,
         0,
         100,
         0), callback=self.CheckAll, checked=True)
        left = const.defaultPadding
        self.sr.filenameLabel = uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Common/Files/FileName'), parent=self.sr.buttonContainer, top=const.defaultPadding, left=left, state=uiconst.UI_NORMAL)
        left += self.sr.filenameLabel.width + const.defaultPadding
        self.sr.filename = uicontrols.SinglelineEdit(name='filename', parent=self.sr.buttonContainer, pos=(left,
         const.defaultPadding,
         150,
         0), align=uiconst.TOPLEFT)
        self.sr.filename.SetMaxLength(32)
        left += self.sr.filename.width + const.defaultPadding
        self.sr.exportBtn = uicontrols.Button(parent=self.sr.buttonContainer, label=localization.GetByLabel('UI/Commands/Export'), func=self.Export, btn_default=1, idx=0, pos=(left,
         const.defaultPadding,
         0,
         0))
        self.sr.buttonContainer.height = self.sr.filename.height + 10
        self.sr.scrolllistcontainer = uiprimitives.Container(name='scrolllistcontainer', align=uiconst.TOALL, parent=self.sr.main, pos=(0, 0, 0, 0))
        self.sr.scroll = uicontrols.Scroll(name='scroll', parent=self.sr.scrolllistcontainer, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        self.ConstructScrollList()

    def CheckAll(self, *args):
        for entry in self.sr.scroll.GetNodes():
            if entry.__guid__ == 'listentry.Checkbox':
                entry.checked = self.checkAllCB.checked
                if entry.panel:
                    entry.panel.Load(entry)

        self.ChangeExportButtonState()

    def OnSelectionChanged(self, c):
        self.ChangeExportButtonState()

    def ChangeExportButtonState(self):
        anySelected = self.IsAnyEntrySelected()
        if anySelected:
            self.sr.exportBtn.state = uiconst.UI_NORMAL
        else:
            self.sr.exportBtn.state = uiconst.UI_HIDDEN

    def IsAnyEntrySelected(self):
        for entry in self.sr.scroll.GetNodes():
            if entry.checked:
                return True

        return False


class ExportFittingsWindow(ExportBaseWindow):
    __guid__ = 'form.ExportFittingsWindow'
    default_windowID = 'ExportFittingsWindow'
    default_iconNum = 'res:/ui/Texture/WindowIcons/fitting.png'

    def ApplyAttributes(self, attributes):
        self.isCorp = attributes.isCorp
        self.fittingSvc = sm.StartService('fittingSvc')
        dirpath = os.path.join(blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL), 'EVE', 'Overview')
        attributes.dirpath = dirpath
        ExportBaseWindow.ApplyAttributes(self, attributes)
        self.SetCaption(localization.GetByLabel('UI/Fitting/ExportFittings'))

    def ConstructScrollList(self):
        fittings = self.fittingSvc.GetAllFittings()
        scrolllist = []
        fittingList = []
        for fittingID, fitting in fittings.iteritems():
            if self.isCorp:
                if fitting.ownerID == session.corpid:
                    fittingList.append((fitting.name, fitting))
            elif fitting.ownerID == session.charid:
                fittingList.append((fitting.name, fitting))

        fittingList.sort()
        for fittingName, fitting in fittingList:
            data = util.KeyVal()
            data.label = fittingName
            data.checked = True
            data.cfgname = 'groups'
            data.retval = True
            data.report = False
            data.OnChange = self.OnSelectionChanged
            data.fitting = fitting
            scrolllist.append(listentry.Get('Checkbox', data=data))

        self.sr.scroll.Load(contentList=scrolllist)

    def Export(self, *args):
        if self.sr.filename.GetValue().strip() == '':
            raise UserError('NameInvalid')
        impl = getDOMImplementation()
        newdoc = impl.createDocument(None, 'fittings', None)
        try:
            docEl = newdoc.documentElement
            export = {}
            for entry in self.sr.scroll.GetNodes():
                if not entry.checked:
                    continue
                profile = newdoc.createElement('fitting')
                docEl.appendChild(profile)
                profile.attributes['name'] = entry.fitting.name
                element = newdoc.createElement('description')
                element.attributes['value'] = entry.fitting.Get('description')
                profile.appendChild(element)
                element = newdoc.createElement('shipType')
                shipType = cfg.invtypes.Get(entry.fitting.Get('shipTypeID')).typeName
                element.attributes['value'] = shipType
                profile.appendChild(element)
                for typeID, flag, qty in entry.fitting.fitData:
                    typeName = cfg.invtypes.Get(typeID).typeName
                    hardWareElement = newdoc.createElement('hardware')
                    hardWareElement.attributes['type'] = typeName
                    slot = self.GetSlotFromFlag(flag)
                    hardWareElement.attributes['slot'] = slot
                    if flag in (const.flagDroneBay, const.flagCargo):
                        hardWareElement.attributes['qty'] = str(qty)
                    profile.appendChild(hardWareElement)

            filename = self.sr.filename.GetValue()
            illegalFileNameChars = ['?',
             '*',
             ':',
             ';',
             '~',
             '\\',
             '/',
             '"',
             '|']
            for char in illegalFileNameChars:
                if char in filename:
                    eve.Message('IllegalFilename')
                    return

            self.dirpath = os.path.join(blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL), 'EVE', 'fittings')
            filepath = os.path.join(self.dirpath, self.sr.filename.GetValue() + '.xml')
            if not os.path.exists(self.dirpath):
                os.makedirs(self.dirpath)
            if os.path.exists(filepath):
                if eve.Message('FileExists', {}, uiconst.YESNO) == uiconst.ID_NO:
                    return
            outfile = codecs.open(filepath, 'w', 'utf-8')
            newdoc.writexml(outfile, indent='\t', addindent='\t', newl='\n')
            self.CloseByUser()
            eve.Message('FittingExportDone', {'filename': filepath})
        finally:
            newdoc.unlink()

    def GetSlotFromFlag(self, flag):
        if flag >= const.flagHiSlot0 and flag <= const.flagHiSlot7:
            return 'hi slot ' + str(flag - const.flagHiSlot0)
        if flag >= const.flagMedSlot0 and flag <= const.flagMedSlot7:
            return 'med slot ' + str(flag - const.flagMedSlot0)
        if flag >= const.flagLoSlot0 and flag <= const.flagLoSlot7:
            return 'low slot ' + str(flag - const.flagLoSlot0)
        if flag >= const.flagRigSlot0 and flag <= const.flagRigSlot7:
            return 'rig slot ' + str(flag - const.flagRigSlot0)
        if flag >= const.flagSubSystemSlot0 and flag <= const.flagSubSystemSlot7:
            return 'subsystem slot ' + str(flag - const.flagSubSystemSlot0)
        if flag == const.flagCargo:
            return 'cargo'
        if flag == const.flagDroneBay:
            return 'drone bay'


class ImportFittingsWindow(ImportBaseWindow):
    __guid__ = 'form.ImportFittingsWindow'
    default_windowID = 'ImportFittingsWindow'
    default_iconNum = 'res:/ui/Texture/WindowIcons/fitting.png'

    def ApplyAttributes(self, attributes):
        dirpath = os.path.join(blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL), 'EVE', 'Fittings')
        attributes.dirpath = dirpath
        ImportBaseWindow.ApplyAttributes(self, attributes)
        self.SetCaption(localization.GetByLabel('UI/Fitting/ImportFittings'))
        self.fittingSvc = sm.StartService('fittingSvc')
        uicontrols.WndCaptionLabel(text=localization.GetByLabel('UI/Fitting/ImportFittings'), parent=self.sr.topParent)

    def OnFileSelected(self, entry):
        filepath = os.path.join(self.dirpath, entry.sr.node.label + '.xml')
        self.sr.selectedFileName = entry.sr.node.label
        profileCheckboxes = []
        try:
            doc = parse(filepath)
            try:
                profiles = doc.documentElement.getElementsByTagName('fitting')
                for x in profiles:
                    fitting = util.KeyVal()
                    fitting.label = x.attributes['name'].value
                    fitting.checked = True
                    fitting.cfgname = 'profiles'
                    fitting.retval = True
                    fitting.OnChange = self.OnChange
                    profileCheckboxes.append(listentry.Get('Checkbox', data=fitting))

                self.sr.importProfilesBtn.state = uiconst.UI_NORMAL
            finally:
                doc.unlink()

        except Exception as e:
            raise
            profileCheckboxes = [listentry.Get('Generic', {'label': localization.GetByLabel('UI/Common/Files/FileNotValid')})]
            self.sr.importProfilesBtn.state = uiconst.UI_HIDDEN

        self.sr.profilesScroll.Load(contentList=profileCheckboxes)
        self.OnChange()

    def Import(self, *args):
        filepath = os.path.join(self.dirpath, self.sr.selectedFileName + '.xml')
        godma = sm.GetService('godma')
        doc = parse(filepath)
        try:
            fittings = doc.documentElement.getElementsByTagName('fitting')
            fittingsDict = {}
            borkedTypeNames = set()
            borkedFlags = set()
            for checkbox in self.sr.profilesScroll.GetNodes():
                if not checkbox.checked:
                    continue
                fittingName = checkbox.label
                kv = util.KeyVal()
                for fitting in fittings:
                    if fitting.attributes['name'].value != fittingName:
                        continue
                    descriptionElements = fitting.getElementsByTagName('description')
                    if descriptionElements > 0:
                        description = descriptionElements[0].attributes['value'].value
                    else:
                        description = ''
                    shipTypeName = fitting.getElementsByTagName('shipType')[0].attributes['value'].value
                    try:
                        shipTypeID = godma.GetTypeFromName(shipTypeName).typeID
                    except KeyError:
                        sys.exc_clear()
                        borkedTypeNames.add(shipTypeName)
                        continue

                    shipTypeID = int(shipTypeID)
                    fitData = {}
                    for hardwareElement in fitting.getElementsByTagName('hardware'):
                        typeName = hardwareElement.attributes['type'].value
                        try:
                            typeID = godma.GetTypeFromName(typeName).typeID
                        except KeyError:
                            borkedTypeNames.add(typeName)
                            sys.exc_clear()
                            continue

                        slot = hardwareElement.attributes['slot'].value
                        flag = self.GetFlagFromSlot(slot)
                        if flag is None:
                            borkedFlags.add(typeName)
                            continue
                        categoryID = cfg.invtypes.Get(typeID).categoryID
                        if categoryID in [const.categoryModule, const.categorySubSystem]:
                            qty = 1
                        else:
                            qty = hardwareElement.attributes['qty'].value
                            qty = int(qty)
                        fitData[typeID, flag] = (typeID, flag, qty)

                    kv.name = fittingName
                    kv.description = description
                    kv.shipTypeID = shipTypeID
                    kv.fitData = fitData.values()
                    kv.ownerID = None
                    kv.fittingID = fittingName
                    fittingsDict[fittingName] = kv

            text = ''
            if len(borkedTypeNames) > 0:
                text += localization.GetByLabel('UI/Fitting/MalformedXML')
                text += '<br><br>'
                for typeName in borkedTypeNames:
                    text += typeName + '<br>'

            if len(borkedFlags) > 0:
                if len(text) > 0:
                    text += '<br><br>'
                text += localization.GetByLabel('UI/Fitting/MalformedFlagInformation')
                text += '<br><br>'
                for typeName in borkedTypeNames:
                    text += typeName + '<br>'

            if len(text) > 0:
                eve.Message('CustomInfo', {'info': text})
            self.fittingSvc.PersistManyFittings(session.charid, fittingsDict.values())
            self.CloseByUser()
        finally:
            doc.unlink()

    def GetFlagFromSlot(self, slot):
        if slot == 'drone bay':
            return const.flagDroneBay
        if slot == 'cargo':
            return const.flagCargo
        if slot.startswith('hi slot'):
            offset = int(slot[-1])
            return const.flagHiSlot0 + offset
        if slot.startswith('med slot'):
            offset = int(slot[-1])
            return const.flagMedSlot0 + offset
        if slot.startswith('low slot'):
            offset = int(slot[-1])
            return const.flagLoSlot0 + offset
        if slot.startswith('rig slot'):
            offset = int(slot[-1])
            return const.flagRigSlot0 + offset
        if slot.startswith('subsystem slot'):
            offset = int(slot[-1])
            return const.flagSubSystemSlot0 + offset


class ImportOverviewWindow(ImportBaseWindow):
    __guid__ = 'form.ImportOverviewWindow'
    default_windowID = 'ImportOverviewWindow'

    def ApplyAttributes(self, attributes):
        dirpath = os.path.join(blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL), 'EVE', 'Overview')
        attributesdirpath = dirpath
        self.presetsSelected = set()
        ImportBaseWindow.ApplyAttributes(self, attributes)
        self.SetCaption(localization.GetByLabel('UI/Overview/ImportOverviewSettings'))
        uicontrols.WndCaptionLabel(text=localization.GetByLabel('UI/Overview/ImportOverviewSettings'), parent=self.sr.topParent)
        self.sr.fileScroll.multiSelect = False
        self.fileType = ''
        self.yamlSettingsDict = {}

    def RefreshFileList(self, *args):
        legacyPresets = self.GetLegacyPresets()
        fileList = self.GetFilesByExt('.yaml')
        contentList = []
        for fileName in fileList:
            contentList.append(listentry.Get('Generic', {'label': fileName,
             'OnClick': self.OnFileSelected,
             'ext': 'yaml'}))

        contentList += legacyPresets
        self.sr.fileScroll.Load(contentList=contentList)

    def GetLegacyPresets(self):
        filelist = self.GetFilesByExt('.xml')
        if not filelist:
            return []
        data = {'GetSubContent': self.GetOldPresetSubContent,
         'label': localization.GetByLabel('UI/Overview/OldOverviewSettings'),
         'id': ('importOverview', 'oldPresets'),
         'groupItems': filelist,
         'showlen': 1,
         'sublevel': 0,
         'showicon': 'hide',
         'state': 'locked'}
        return [listentry.Get('Group', data)]

    def GetOldPresetSubContent(self, nodedata):
        fileList = []
        for fileName in nodedata.groupItems:
            fileList.append(listentry.Get('Generic', {'label': fileName,
             'OnClick': self.OnFileSelected,
             'sublevel': 1,
             'ext': 'xml'}))

        return fileList

    def OnFileSelected(self, entry):
        if entry.sr.node.ext == 'xml':
            self.ShowXmlSettings(entry)
        else:
            self.yamlSettingsDict = {}
            self.ShowYamlSettings(entry)

    def ShowXmlSettings(self, entry):
        self.fileType = 'xml'
        filepath = os.path.join(self.dirpath, entry.sr.node.label + '.xml')
        self.sr.selectedFileName = entry.sr.node.label
        profileCheckboxes = []
        try:
            doc = parse(filepath)
            try:
                profiles = doc.documentElement.getElementsByTagName('profile')
                for x in profiles:
                    globalSettings = util.KeyVal()
                    globalSettings.label = x.attributes['name'].value
                    globalSettings.checked = True
                    globalSettings.cfgname = 'profiles'
                    globalSettings.retval = True
                    globalSettings.OnChange = self.OnChange
                    profileCheckboxes.append(listentry.Get('Checkbox', data=globalSettings))

                if len(doc.documentElement.getElementsByTagName('globalSettings')):
                    globalSettings = util.KeyVal()
                    globalSettings.label = localization.GetByLabel('UI/Overview/GlobalOverviewSettings')
                    globalSettings.checked = True
                    globalSettings.cfgname = 'profiles'
                    globalSettings.retval = True
                    globalSettings.OnChange = self.OnChange
                    profileCheckboxes.append(listentry.Get('Checkbox', data=globalSettings))
                self.sr.importProfilesBtn.state = uiconst.UI_NORMAL
            finally:
                doc.unlink()

        except Exception as e:
            profileCheckboxes = [listentry.Get('Generic', {'label': localization.GetByLabel('UI/Common/Files/FileNotValid')})]
            self.sr.importProfilesBtn.state = uiconst.UI_HIDDEN

        self.sr.profilesScroll.Load(contentList=profileCheckboxes)
        self.ChangeImportButtonState()

    def ShowYamlSettings(self, entry):
        self.fileType = 'yaml'
        filepath = os.path.join(self.dirpath, entry.sr.node.label + '.yaml')
        filestream = open(filepath)
        settingDict = yaml.safe_load(filestream)
        self.yamlSettingsDict = settingDict
        self.ConstructScrollList(initPresetsSelected=True)

    def ConstructScrollList(self, initPresetsSelected = False):
        if self.fileType != 'yaml':
            return
        allChecked = True
        settingDict = self.yamlSettingsDict
        tabPresets = GetDictFromList(settingDict.get('presets', []))
        tabPresets = ReplaceInnerListsWithDicts(tabPresets)
        tabSetup = sm.GetService('overviewPresetSvc').GetTabSetupToLoad(settingDict)
        presetsInUseDict = sm.GetService('overviewPresetSvc').GetPresetsInUseFromTabSettings(tabSetup, tabPresets)
        if initPresetsSelected:
            self.InitPresetsSelected(presetsInUseDict)
        checked = 'generalSettings' in self.presetsSelected
        scrolllist = [GetGeneralOverviewSettingsEntry(onChangeFunc=self.OnChange, checked=checked)]
        allChecked = allChecked and checked
        checked = 'overviewProfile' in self.presetsSelected
        profileEntry = GetOverviewProfileEntry(onChangeFunc=self.OnChange, checked=checked)
        scrolllist.append(profileEntry)
        allChecked = allChecked and checked
        presetsInUseList = []
        for eachPresetName in presetsInUseDict:
            lowerDisplayName = eachPresetName.lower()
            presetsInUseList.append((lowerDisplayName, eachPresetName))

        presetsInUseList = [ x[1] for x in localization.util.Sort(presetsInUseList, key=operator.itemgetter(0)) ]
        for eachPresetName in presetsInUseList:
            checked = eachPresetName in self.presetsSelected
            entry = GetTabPresetEntry(eachPresetName, onChangeFunc=self.OnChange, checked=checked)
            scrolllist.append(entry)
            allChecked = allChecked and checked

        restOfPresets = []
        for eachPresetName in tabPresets:
            if eachPresetName in presetsInUseList:
                continue
            lowerDisplayName = eachPresetName.lower()
            restOfPresets.append((lowerDisplayName, eachPresetName))

        if restOfPresets:
            restOfPresets = [ x[1] for x in localization.util.Sort(restOfPresets, key=operator.itemgetter(0)) ]
            posttext, allSubPresetsChecked = GetPresetPostText(restOfPresets, self.presetsSelected)
            allChecked = allChecked and allSubPresetsChecked
            data = {'GetSubContent': self.GetPresetSubContent,
             'label': localization.GetByLabel('UI/Overview/OtherTabPresets'),
             'id': ('importOverview', 'restOfPresets'),
             'groupItems': restOfPresets,
             'showlen': 0,
             'sublevel': 0,
             'showicon': 'hide',
             'state': 'locked',
             'posttext': posttext}
            scrolllist.append(listentry.Get('Group', data))
        self.sr.profilesScroll.Load(contentList=scrolllist)
        self.ChangeImportButtonState()
        self.checkAllCB.SetChecked(allChecked, report=False)

    def InitPresetsSelected(self, presetsInUseDict):
        self.presetsSelected = set(['generalSettings', 'overviewProfile'])
        for eachPresetName in presetsInUseDict:
            self.presetsSelected.add(eachPresetName)

    def OnChange(self, c, *args):
        OnOverviewCheckboxChange(c, self.presetsSelected)
        if self.fileType == 'yaml':
            self.ConstructScrollList()
        ImportBaseWindow.OnChange(self, c)

    def CheckAll(self, *args):
        if self.fileType == 'xml':
            return ImportBaseWindow.CheckAll(self)
        if self.fileType == 'yaml':
            checkAll = self.checkAllCB.checked
            ModifyPresetSelectedDict(checkAll, self.sr.profilesScroll, self.presetsSelected)
            self.ConstructScrollList()
        self.ChangeImportButtonState()

    def IsAnyEntrySelected(self):
        if self.fileType == 'xml':
            return ImportBaseWindow.IsAnyEntrySelected(self)
        else:
            return bool(self.presetsSelected)

    def GetPresetSubContent(self, nodedata):
        scrolllist = []
        for eachPresetName in nodedata.groupItems:
            checked = eachPresetName in self.presetsSelected
            entry = GetTabPresetEntry(eachPresetName, onChangeFunc=self.OnChange, checked=checked)
            scrolllist.append(entry)

        return scrolllist

    def AddProfilesToSettings(self, profileName, profiles):
        for profile in profiles:
            groups = []
            filteredStates = []
            if profile.attributes['name'].value != profileName:
                continue
            for groupElement in profile.getElementsByTagName('groups')[0].getElementsByTagName('group'):
                groups.append(int(groupElement.attributes['id'].value))

            for el in profile.getElementsByTagName('filteredStates')[0].getElementsByTagName('state'):
                filteredStates.append(int(el.attributes['state'].value))

            profileValues = {'groups': groups,
             'filteredStates': filteredStates}
            return (profileName, profileValues)

        return (None, None)

    def ImportGlobalSettings(self, doc, miscSettings):
        settingsElement = doc.documentElement.getElementsByTagName('globalSettings')[0]
        for setting in ['useSmallColorTags',
         'applyOnlyToShips',
         'hideCorpTicker',
         'overviewBroadcastsToTop']:
            element = settingsElement.getElementsByTagName(setting)[0]
            value = bool(element.attributes['value'])
            miscSettings[setting] = value

        overviewColumns = []
        columnsElement = settingsElement.getElementsByTagName('columns')[0]
        for columnElement in columnsElement.getElementsByTagName('column'):
            overviewColumns.append(columnElement.attributes['id'].value)

        shipLabels = []
        if len(settingsElement.getElementsByTagName('shipLabels')):
            shipLabelsElement = settingsElement.getElementsByTagName('shipLabels')[0]
            shipLabelElements = shipLabelsElement.getElementsByTagName('label')
            for sle in shipLabelElements:
                d = {}
                for shipLabelPartElement in sle.getElementsByTagName('part'):
                    n = shipLabelPartElement.attributes['name'].value
                    v = shipLabelPartElement.attributes['value'].value
                    if n == 'state':
                        v = int(v)
                    if v == 'None':
                        v = None
                    d[n] = v

                shipLabels.append(d)

        stateService = sm.StartService('state')
        if hasattr(stateService, 'shipLabels'):
            delattr(stateService, 'shipLabels')
        return (overviewColumns, shipLabels)

    def GetTabData(self, selectedProfiles, tabElement):
        overviewProfileName = tabElement.attributes['overview'].value
        bracketProfileName = tabElement.attributes['bracket'].value
        tabdata = {}
        if overviewProfileName in selectedProfiles and bracketProfileName in selectedProfiles:
            for attributeName in ('name', 'overview', 'showNone', 'showSpecials', 'showAll', 'bracket'):
                attribute = tabElement.getAttribute(attributeName)
                if attribute:
                    if attribute in ('showNone', 'showSpecials', 'showAll'):
                        attribute = bool(attribute)
                    tabdata[attributeName] = attribute

        return tabdata

    def Import(self, *args):
        if self.fileType == 'xml':
            return self.ImportXml()
        else:
            return self.ImportYaml()

    def ImportXml(self, *args):
        dirpath = os.path.join(blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL), 'EVE', 'Overview')
        filepath = os.path.join(dirpath, self.sr.selectedFileName + '.xml')
        doc = parse(filepath)
        try:
            profiles = doc.documentElement.getElementsByTagName('profile')
            ov = settings.user.overview.Get('overviewProfilePresets', {})
            miscSettings = {}
            selectedProfiles = []
            shipLabels = None
            overviewColumns = None
            newTabSettings = None
            closeWindow = True
            profileUpdateDict = {}
            for checkbox in self.sr.profilesScroll.GetNodes():
                if not checkbox.checked:
                    continue
                profileName = checkbox.label
                if profileName in ov and eve.Message('OverviewProfileExists', {'name': profileName}, uiconst.YESNO) != uiconst.ID_YES:
                    closeWindow = False
                    continue
                if profileName == localization.GetByLabel('UI/Overview/GlobalOverviewSettings'):
                    overviewColumns, shipLabels = self.ImportGlobalSettings(doc, miscSettings)
                    continue
                selectedProfiles.append(profileName)
                profileName, profileValues = self.AddProfilesToSettings(profileName, profiles)
                if profileValues:
                    profileUpdateDict[profileName] = profileValues

            sm.GetService('overviewPresetSvc').UpdateAllPresets(profileUpdateDict)
            oldTabSettings = settings.user.overview.Get('tabsettings', {})
            tabsChanged = False
            tabsData = {}
            tabIndex = 0
            for tabElement in doc.documentElement.getElementsByTagName('tab'):
                if tabIndex >= 5:
                    eve.Message('TooManyTabsImported')
                    break
                dataForTab = self.GetTabData(selectedProfiles, tabElement)
                if dataForTab:
                    tabsData[tabIndex] = dataForTab
                    tabIndex += 1
                    tabsChanged = True

            if overviewColumns:
                settings.user.overview.Set('overviewColumns', overviewColumns)
            if shipLabels:
                settings.user.overview.Set('shipLabels', shipLabels)
            for k, v in miscSettings.items():
                settings.user.overview.Set(k, v)

            sm.GetService('overviewPresetSvc').LoadPresetsFromUserSettings()
            overviewWindow = OverView.GetIfOpen()
            if overviewWindow:
                if tabsChanged:
                    overviewWindow.OnOverviewTabChanged(tabsData, oldTabSettings)
                else:
                    overviewWindow.FullReload()
            if closeWindow:
                self.CloseByUser()
        finally:
            doc.unlink()

    def ImportYaml(self):
        tabPresetNamesToImport = []
        tabsChanged = False
        for checkboxConfig in self.presetsSelected:
            if checkboxConfig == 'generalSettings':
                sm.GetService('overviewPresetSvc').LoadGeneralSettings(self.yamlSettingsDict)
            elif checkboxConfig == 'overviewProfile':
                tabSetup = sm.GetService('overviewPresetSvc').GetTabSetupToLoad(self.yamlSettingsDict)
                oldTabSetup = sm.GetService('overviewPresetSvc').GetTabSettingsForOverview()
                sm.GetService('overviewPresetSvc').SetTabSettingsForOverview(tabSetup)
                tabsChanged = True
            else:
                tabPresetNamesToImport.append(checkboxConfig)

        presetsDict = GetDictFromList(self.yamlSettingsDict.get('presets', []))
        presetsDict = ReplaceInnerListsWithDicts(presetsDict)
        myPresets = {presetName:presetValue for presetName, presetValue in presetsDict.iteritems() if presetName in tabPresetNamesToImport}
        sm.GetService('overviewPresetSvc').UpdateAllPresets(myPresets)
        if tabsChanged:
            sm.ScatterEvent('OnOverviewTabChanged', tabSetup, oldTabSetup)
        sm.ScatterEvent('OnReloadingOverviewProfile')
        self.CloseByUser()


class ImportLegacyFittingsWindow(ExportBaseWindow):
    __guid__ = 'form.ImportLegacyFittingsWindow'
    default_windowID = 'ImportLegacyFittingsWindow'
    default_iconNum = 'res:/ui/Texture/WindowIcons/fitting.png'

    def OnSelectionChanged(self, c):
        checkedCount = 0
        for entry in self.sr.scroll.GetNodes():
            if entry.checked:
                checkedCount += 1

        text = localization.GetByLabel('UI/Fitting/MovingCount', count=checkedCount, total=self.totalLocalFittings)
        if self.fittingCount > 0:
            text += ' (' + localization.GetByLabel('UI/Fitting/CurrentlySaved', count=self.fittingCount) + ')'
        self.sr.countSelectedTextLabel.text = text
        if not self.okBtn.disabled and self.fittingCount + checkedCount > const.maxCharFittings:
            self.okBtn.Disable()
        elif self.okBtn.disabled and self.fittingCount + checkedCount <= const.maxCharFittings:
            self.okBtn.Enable()

    def ApplyAttributes(self, attributes):
        self.fittingSvc = sm.StartService('fittingSvc')
        self.fittingCount = len(self.fittingSvc.GetFittingMgr(session.charid).GetFittings(session.charid))
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.SetTopparentHeight(0)
        self.SetWndIcon(None)
        self.SetMinSize([370, 270])
        self.SetCaption(localization.GetByLabel('UI/Fitting/MoveToServer'))
        self.ConstructLayout()

    def ConstructLayout(self, *args):
        self.countSelectedText = ''
        self.sr.textContainer = uiprimitives.Container(name='textContainer', align=uiconst.TOTOP, parent=self.sr.main, height=65, padding=const.defaultPadding)
        self.sr.textLabel = uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Fitting/LegacyImport', maxFittings=const.maxCharFittings), align=uiconst.TOTOP, parent=self.sr.textContainer)
        self.sr.textContainer2 = uiprimitives.Container(name='textContainer', align=uiconst.TOTOP, parent=self.sr.main, height=15, padding=const.defaultPadding)
        self.sr.countSelectedTextLabel = uicontrols.EveLabelMedium(text=self.countSelectedText, align=uiconst.TOALL, parent=self.sr.textContainer2)
        self.sr.buttonContainer = uiprimitives.Container(name='buttonContainer', align=uiconst.TOBOTTOM, parent=self.sr.main)
        btns = [[localization.GetByLabel('UI/Generic/Cancel'),
          self.CloseByUser,
          None,
          81], [localization.GetByLabel('UI/Generic/OK'),
          self.Import,
          None,
          81]]
        self.buttonGroup = uicontrols.ButtonGroup(btns=btns, parent=self.sr.buttonContainer)
        self.okBtn = self.buttonGroup.children[0].children[1]
        self.sr.buttonContainer.height = 23
        self.sr.scrolllistcontainer = uiprimitives.Container(name='scrolllistcontainer', align=uiconst.TOALL, parent=self.sr.main, pos=(0, 0, 0, 0))
        self.sr.scroll = uicontrols.Scroll(name='scroll', parent=self.sr.scrolllistcontainer, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        self.ConstructScrollList()

    def ConstructScrollList(self):
        fittings = self.fittingSvc.GetLegacyClientFittings()
        scrolllist = []
        fittingList = []
        for fittingID, fitting in fittings.iteritems():
            fittingList.append((fitting.name, fitting))

        fittingList.sort()
        self.emptyFittings = []
        for fittingName, fitting in fittingList:
            if len(fitting.fitData) == 0:
                self.emptyFittings.append(fitting)
                continue
            typeFlag = set()
            for typeID, flag, qty in fitting.fitData[:]:
                if (typeID, flag) in typeFlag:
                    fitting.fitData.remove((typeID, flag, qty))
                else:
                    typeFlag.add((typeID, flag))

            data = util.KeyVal()
            data.label = fittingName
            data.checked = False
            data.OnChange = self.OnSelectionChanged
            data.cfgname = 'groups'
            data.retval = True
            data.report = False
            data.fitting = fitting
            scrolllist.append(listentry.Get('Checkbox', data=data))

        self.sr.scroll.Load(contentList=scrolllist)
        self.totalLocalFittings = len(fittingList)
        self.OnSelectionChanged(None)

    def Import(self, *args):
        impl = getDOMImplementation()
        newdoc = impl.createDocument(None, 'fittings', None)
        try:
            docEl = newdoc.documentElement
            fittings = []
            saveSomeToFile = False
            for entry in self.sr.scroll.GetNodes():
                if entry.checked:
                    fittings.append(entry.fitting)
                else:
                    saveSomeToFile = True
                    profile = newdoc.createElement('fitting')
                    docEl.appendChild(profile)
                    profile.attributes['name'] = entry.fitting.name
                    element = newdoc.createElement('description')
                    element.attributes['value'] = entry.fitting.Get('description')
                    profile.appendChild(element)
                    element = newdoc.createElement('shipType')
                    try:
                        shipType = cfg.invtypes.Get(entry.fitting.Get('shipTypeID')).typeName
                    except KeyError:
                        shipType = 'unknown type'

                    element.attributes['value'] = shipType
                    profile.appendChild(element)
                    for typeID, flag, qty in entry.fitting.fitData:
                        try:
                            typeName = cfg.invtypes.Get(typeID).typeName
                        except KeyError:
                            typeName = 'unknown type'

                        hardWareElement = newdoc.createElement('hardware')
                        hardWareElement.attributes['type'] = typeName
                        slot = self.GetSlotFromFlag(flag)
                        if slot is None:
                            slot = 'unknown slot'
                        hardWareElement.attributes['slot'] = slot
                        if flag == const.flagDroneBay:
                            hardWareElement.attributes['qty'] = str(qty)
                        profile.appendChild(hardWareElement)

            for emptyFitting in self.emptyFittings:
                saveSomeToFile = True
                profile = newdoc.createElement('fitting')
                docEl.appendChild(profile)
                profile.attributes['name'] = entry.fitting.name
                element = newdoc.createElement('description')
                element.attributes['value'] = entry.fitting.Get('description')
                profile.appendChild(element)
                element = newdoc.createElement('shipType')
                try:
                    shipType = cfg.invtypes.Get(entry.fitting.Get('shipTypeID')).typeName
                except KeyError:
                    shipType = 'unknown type'

                element.attributes['value'] = shipType
                profile.appendChild(element)

            if len(fittings) > 0:
                self.fittingSvc.PersistManyFittings(session.charid, fittings)
            if saveSomeToFile:
                self.dirpath = os.path.join(blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL), 'EVE', 'fittings')
                filename = cfg.eveowners.Get(session.charid).ownerName
                filename = filename.replace(' ', '')
                filename = uiutil.SanitizeFilename(filename)
                dirpath = os.path.join(blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL), 'EVE', 'fittings')
                filename = os.path.join(dirpath, filename)
                extraEnding = ''
                while os.path.exists(filename + str(extraEnding) + '.xml'):
                    if not isinstance(extraEnding, int):
                        extraEnding = 1
                    extraEnding += 1

                filename += str(extraEnding) + '.xml'
                if not os.path.exists(self.dirpath):
                    os.makedirs(self.dirpath)
                outfile = codecs.open(filename, 'w', 'utf-8')
                newdoc.writexml(outfile, indent='\t', addindent='\t', newl='\n')
                eve.Message('LegacyFittingExportDone', {'filename': filename})
            self.fittingSvc.DeleteLegacyClientFittings()
            self.CloseByUser()
        finally:
            newdoc.unlink()

    def GetSlotFromFlag(self, flag):
        if flag >= const.flagHiSlot0 and flag <= const.flagHiSlot7:
            return 'hi slot ' + str(flag - const.flagHiSlot0)
        if flag >= const.flagMedSlot0 and flag <= const.flagMedSlot7:
            return 'med slot ' + str(flag - const.flagMedSlot0)
        if flag >= const.flagLoSlot0 and flag <= const.flagLoSlot7:
            return 'low slot ' + str(flag - const.flagLoSlot0)
        if flag >= const.flagRigSlot0 and flag <= const.flagRigSlot7:
            return 'rig slot ' + str(flag - const.flagRigSlot0)
        if flag >= const.flagSubSystemSlot0 and flag <= const.flagSubSystemSlot7:
            return 'subsystem slot ' + str(flag - const.flagSubSystemSlot0)
        if flag == const.flagDroneBay:
            return 'drone bay'


class ExportOverviewWindow(ExportBaseWindow):
    __guid__ = 'form.ExportOverviewWindow'
    default_windowID = 'ExportOverviewWindow'
    __notifyevents__ = ['OnOverviewPresetSaved']

    def ApplyAttributes(self, attributes):
        self.overviewPresetSvc = sm.StartService('overviewPresetSvc')
        dirpath = os.path.join(blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL), 'EVE', 'Overview')
        attributes.dirpath = dirpath
        self.InitPresetsSelected()
        ExportBaseWindow.ApplyAttributes(self, attributes)
        self.SetCaption(localization.GetByLabel('UI/Commands/ExportOverviewSettings'))
        currentText = self.overviewPresetSvc.GetOverviewName()
        defaultText = localization.GetByLabel('UI/Overview/DefaultOverviewName', charID=session.charid)
        configName = 'overviewProfileNameInExport'
        getDragDataFunc = self.GetShareData
        shareContainer = DraggableShareContainer(parent=self.topCont, currentText=currentText, defaultText=defaultText, configName=configName, getDragDataFunc=getDragDataFunc, hintText=localization.GetByLabel('UI/Overview/SharableOverviewIconExportHint'), idx=0)
        self.topCont.height = shareContainer.sharedNameLabel.height + 10

    def GetShareData(self, text):
        selected = self.presetsSelected.copy()
        for x in ('generalSettings', 'overviewProfile'):
            if x in selected:
                selected.remove(x)

        if len(selected) > MAX_SHARED_PRESETS:
            eve.Message('CustomNotify', {'notify': localization.GetByLabel('UI/Overview/TryingToShareTooManyPresets')})
            return []
        return self.overviewPresetSvc.GetShareData(text=text, presetsToUse=selected)

    def InitPresetsSelected(self):
        self.presetsSelected = set(['generalSettings', 'overviewProfile'])
        presetsInUse = self.overviewPresetSvc.GetPresetsInUse()
        for eachPresetName in presetsInUse:
            lowerDisplayName = eachPresetName.lower()
            self.presetsSelected.add(eachPresetName)

    def ConstructScrollList(self):
        allChecked = True
        scrolllist = []
        checked = 'generalSettings' in self.presetsSelected
        generalSettingsEntry = GetGeneralOverviewSettingsEntry(onChangeFunc=self.OnSelectionChanged, checked=checked)
        scrolllist.append(generalSettingsEntry)
        allChecked = allChecked and checked
        checked = 'overviewProfile' in self.presetsSelected
        profileEntry = GetOverviewProfileEntry(onChangeFunc=self.OnSelectionChanged, checked=checked)
        scrolllist.append(profileEntry)
        allChecked = allChecked and checked
        presetsInUse = self.overviewPresetSvc.GetPresetsInUse()
        presetsInUseList = []
        for eachPresetName in presetsInUse:
            lowerDisplayName = eachPresetName.lower()
            presetsInUseList.append((lowerDisplayName, eachPresetName))

        presetsInUseList = [ x[1] for x in localization.util.Sort(presetsInUseList, key=operator.itemgetter(0)) ]
        for eachPresetName in presetsInUseList:
            checked = eachPresetName in self.presetsSelected
            entry = GetTabPresetEntry(eachPresetName, onChangeFunc=self.OnSelectionChanged, checked=checked)
            scrolllist.append(entry)
            allChecked = allChecked and checked

        allPresets = self.overviewPresetSvc.GetAllPresets()
        restOfPresets = []
        defaultProfileNames = self.overviewPresetSvc.GetDefaultOverviewNameList()
        for eachPresetName in allPresets:
            if eachPresetName in presetsInUse or eachPresetName in defaultProfileNames:
                continue
            lowerDisplayName = eachPresetName.lower()
            restOfPresets.append((lowerDisplayName, eachPresetName))

        if restOfPresets:
            restOfPresets = [ x[1] for x in localization.util.Sort(restOfPresets, key=operator.itemgetter(0)) ]
            posttext, allSubPresetsChecked = GetPresetPostText(restOfPresets, self.presetsSelected)
            allChecked = allChecked and allSubPresetsChecked
            data = {'GetSubContent': self.GetPresetSubContent,
             'label': localization.GetByLabel('UI/Overview/OtherTabPresets'),
             'id': ('exportOverview', 'restOfPresets'),
             'groupItems': restOfPresets,
             'showlen': 0,
             'sublevel': 0,
             'showicon': 'hide',
             'state': 'locked',
             'posttext': posttext}
            scrolllist.append(listentry.Get('Group', data))
        self.sr.scroll.Load(contentList=scrolllist)
        self.checkAllCB.SetChecked(allChecked, report=False)

    def GetPresetSubContent(self, nodedata):
        scrolllist = []
        for eachPresetName in nodedata.groupItems:
            checked = eachPresetName in self.presetsSelected
            entry = GetTabPresetEntry(eachPresetName, onChangeFunc=self.OnSelectionChanged, checked=checked)
            scrolllist.append(entry)

        return scrolllist

    def Export(self, *args):
        if self.sr.filename.GetValue().strip() == '':
            raise UserError('NameInvalid')
        exportData = {}
        presetList = []
        allPresets = self.overviewPresetSvc.GetAllPresets()
        defaultProfileNames = self.overviewPresetSvc.GetDefaultOverviewNameList()
        for checkboxConfig in self.presetsSelected:
            if checkboxConfig == 'generalSettings':
                generalSettings = self.GetGeneralSettings()
                exportData.update(generalSettings)
            elif checkboxConfig == 'overviewProfile':
                overviewProfile = self.GetOverviewProfile()
                exportData['tabSetup'] = overviewProfile
            else:
                presetName = checkboxConfig
                if presetName in allPresets and presetName not in defaultProfileNames:
                    presetAsList = GetDeterministicListFromDict(allPresets[presetName])
                    presetList.append((presetName, presetAsList))

        if presetList:
            exportData['presets'] = presetList
        dirpath = os.path.join(blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL), 'EVE', 'Overview')
        filepath = os.path.join(dirpath, self.sr.filename.GetValue().strip() + '.yaml')
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        if os.path.exists(filepath):
            if eve.Message('FileExists', {}, uiconst.YESNO) != uiconst.ID_YES:
                return
        with open(filepath, 'w') as yamlFile:
            yaml.safe_dump(exportData, yamlFile, default_flow_style=False, allow_unicode=True)
        self.CloseByUser()
        eve.Message('OverviewExportDone', {'filename': filepath})

    def GetGeneralSettings(self):
        return self.overviewPresetSvc.GetGeneralSettings()

    def GetOverviewProfile(self):
        return self.overviewPresetSvc.GetTabSettingsForSaving()

    def OnSelectionChanged(self, c):
        OnOverviewCheckboxChange(c, self.presetsSelected)
        self.ConstructScrollList()
        ExportBaseWindow.OnSelectionChanged(self, c)

    def CheckAll(self, *args):
        checkAll = self.checkAllCB.checked
        ModifyPresetSelectedDict(checkAll, self.sr.scroll, self.presetsSelected)
        self.ConstructScrollList()
        self.ChangeExportButtonState()

    def IsAnyEntrySelected(self):
        return bool(self.presetsSelected)

    def OnOverviewPresetSaved(self, *args):
        self.ConstructScrollList()


def GetGeneralOverviewSettingsEntry(onChangeFunc, checked = True):
    data = util.KeyVal()
    data.label = localization.GetByLabel('UI/Overview/GeneralOverviewSettings')
    data.checked = checked
    data.cfgname = 'generalSettings'
    data.retval = checked
    data.OnChange = onChangeFunc
    return listentry.Get('Checkbox', data=data)


def GetOverviewProfileEntry(onChangeFunc, checked = True):
    data = util.KeyVal()
    data.label = localization.GetByLabel('UI/Overview/OverviewProfile')
    data.checked = checked
    data.cfgname = 'overviewProfile'
    data.retval = checked
    data.OnChange = onChangeFunc
    data.hint = localization.GetByLabel('UI/Overview/OverviewProfileHint')
    return listentry.Get('Checkbox', data=data)


def GetTabPresetEntry(eachProfileName, onChangeFunc, checked = True):
    data = util.KeyVal()
    data.label = localization.GetByLabel('UI/Overview/TabPresetName', presetName=eachProfileName)
    data.checked = checked
    data.cfgname = eachProfileName
    data.presetName = eachProfileName
    data.retval = checked
    data.sublevel = 1
    data.OnChange = onChangeFunc
    return listentry.Get('Checkbox', data=data)


def ModifyPresetSelectedDict(checkAll, scroll, presetSelectedDict):
    if checkAll:
        for entry in scroll.GetNodes():
            guid = entry.__guid__
            if guid == 'listentry.Checkbox':
                presetSelectedDict.add(entry.cfgname)
            elif guid == 'listentry.Group':
                for each in entry.groupItems:
                    presetSelectedDict.add(each)

    else:
        presetSelectedDict.clear()


def OnOverviewCheckboxChange(c, presetSelectedDict):
    key = c.data['key']
    if c.checked:
        presetSelectedDict.add(key)
    elif c.data['key'] in presetSelectedDict:
        presetSelectedDict.remove(key)


def GetPresetPostText(presetsList, presetSelectedDict):
    checkedPresets = [ p for p in presetsList if p in presetSelectedDict ]
    allChecked = len(checkedPresets) == len(presetsList)
    return ('[%s/%s]' % (len(checkedPresets), len(presetsList)), allChecked)
