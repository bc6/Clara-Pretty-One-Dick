#Embedded file name: eve/client/script/ui/shared\bookmarkLocationWindow.py
import uicls
import carbonui.const as uiconst
import localization
import uiprimitives
import uicontrols
import util

class BookmarkLocationWindow(uicontrols.Window):
    __guid__ = 'form.BookmarkLocationWindow'
    default_topParentHeight = 0
    default_windowID = 'bookmarkLocationWindow'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.locationID = attributes.get('locationID')
        locationName = attributes.get('locationName')
        note = attributes.get('note', '')
        self.typeID = attributes.get('typeID')
        self.scannerInfo = attributes.get('scannerInfo')
        self.parentID = attributes.get('parentID')
        self.bookmark = attributes.get('bookmark')
        if self.bookmark is None:
            self.SetCaption(localization.GetByLabel('UI/PeopleAndPlaces/NewBookmark'))
        else:
            self.SetCaption(localization.GetByLabel('UI/PeopleAndPlaces/EditLocation'))
        self.SetMinSize([280, 186])
        main = uiprimitives.Container(name='main', parent=self.sr.main, align=uiconst.TOALL, left=4, width=4)
        labelContainer = uiprimitives.Container(name='labelContainer', parent=main, align=uiconst.TOTOP, top=8, height=20, padding=(2, 2, 2, 2))
        uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/PeopleAndPlaces/Label'), parent=labelContainer, align=uiconst.TOLEFT, width=60)
        self.labelEdit = uicontrols.SinglelineEdit(name='labelEdit', setvalue=locationName, parent=labelContainer, align=uiconst.TOALL, width=0, autoselect=True)
        self.labelEdit.OnReturn = self.Confirm
        descriptionContainer = uiprimitives.Container(name='descriptionContainer', parent=main, align=uiconst.TOTOP, top=8, height=60, padding=(2, 2, 2, 2))
        uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/PeopleAndPlaces/Notes'), parent=descriptionContainer, align=uiconst.TOLEFT, width=60)
        self.notesEdit = uicls.EditPlainText(name='notesEdit', setvalue=note, parent=descriptionContainer, align=uiconst.TOALL)
        folderContainer = uiprimitives.Container(name='folderContainer', parent=main, align=uiconst.TOTOP, top=8, height=20, padding=(2, 2, 2, 2))
        uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/PeopleAndPlaces/Folder'), parent=folderContainer, align=uiconst.TOLEFT, width=60)
        options = self.GetFolderOptions()
        if self.bookmark is not None:
            ownerID, folderID = self.bookmark.ownerID, self.bookmark.folderID
        else:
            ownerID, folderID = settings.char.ui.Get('defaultBookmarkOwnerAndFolder', (session.charid, None))
        self.folderCombo = uicontrols.Combo(name='folderCombo', parent=folderContainer, align=uiconst.TOALL, select=(ownerID, folderID), options=options, width=0)
        buttons = self.GetButtons()
        buttonGroup = uicontrols.ButtonGroup(name='buttonGroup', parent=main, btns=buttons)
        submitButton = buttonGroup.GetBtnByIdx(0)
        submitButton.OnSetFocus()

    def GetFolderOptions(self):
        options = []
        locations = [(session.charid, localization.GetByLabel('UI/PeopleAndPlaces/PersonalLocations'))]
        if not util.IsNPCCorporation(session.corpid):
            locations.append((session.corpid, localization.GetByLabel('UI/PeopleAndPlaces/CorporationLocations')))
        for ownerID, label in locations:
            folders = sm.GetService('bookmarkSvc').GetFoldersForOwner(ownerID)
            options.append((label, (ownerID, None)))
            subFolders = [ ('  ' + folder.folderName, (ownerID, folder.folderID)) for folder in folders ]
            subFolders = localization.util.Sort(subFolders, key=lambda x: x[0])
            options.extend(subFolders)

        return options

    def GetButtons(self):
        return [(localization.GetByLabel('UI/Common/Submit'), self.Confirm, []), (localization.GetByLabel('UI/Common/Cancel'), self.Cancel, [])]

    def Confirm(self, *args):
        label = self.labelEdit.GetValue()
        if label.strip() == '':
            raise UserError('CustomInfo', {'info': localization.GetByLabel('UI/Map/MapPallet/msgPleaseTypeSomething')})
        label = label.replace('\t', ' ')
        note = self.notesEdit.GetValue()
        ownerID, folderID = self.folderCombo.GetValue()
        if self.bookmark is not None:
            sm.GetService('addressbook').UpdateBookmark(self.bookmark.bookmarkID, ownerID=ownerID, header=label, note=note, folderID=folderID)
        elif self.scannerInfo is not None:
            sm.GetService('bookmarkSvc').BookmarkScanResult(self.locationID, label, note, self.scannerInfo.id, ownerID, folderID=folderID)
        else:
            sm.GetService('bookmarkSvc').BookmarkLocation(self.locationID, ownerID, label, note, self.typeID, self.parentID, folderID=folderID)
        settings.char.ui.Set('defaultBookmarkOwnerAndFolder', (ownerID, folderID))
        self.Close()

    def Cancel(self, *args):
        self.Close()
