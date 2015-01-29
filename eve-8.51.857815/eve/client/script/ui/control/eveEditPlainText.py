#Embedded file name: eve/client/script/ui/control\eveEditPlainText.py
import uicontrols
import uix
import util
import carbonui.const as uiconst
import uiutil
import localization
import searchUtil

class EditPlainText(uicontrols.EditPlainTextCore):
    """ Standard multi-line text edit. Use SingleLineEdit for simple, one-line text input """
    __guid__ = 'uicls.EditPlainText'
    default_align = uiconst.TOALL
    default_left = 0
    default_top = 0
    default_width = 0
    default_height = 0
    default_fontcolor = -1073741825
    allowPrivateDrops = 0

    def OnDropDataDelegate(self, node, nodes):
        """ 
            Handle the event when something is drag-dropped into the edit 
        """
        uicontrols.EditPlainTextCore.OnDropDataDelegate(self, node, nodes)
        if self.readonly:
            return
        uicore.registry.SetFocus(self)
        for entry in nodes:
            if entry.__guid__ in uiutil.AllUserEntries():
                link = 'showinfo:' + str(entry.info.typeID) + '//' + str(entry.charID)
                self.AddLink(entry.info.name, link)
            elif entry.__guid__ == 'listentry.PlaceEntry' and self.allowPrivateDrops:
                bookmarkID = entry.bm.bookmarkID
                bookmarkSvc = sm.GetService('bookmarkSvc')
                bms = bookmarkSvc.GetBookmarks()
                if bookmarkID in bms:
                    bookmark = bms[bookmarkID]
                    hint, comment = bookmarkSvc.UnzipMemo(bookmark.memo)
                link = 'showinfo:' + str(bms[bookmarkID].typeID) + '//' + str(bms[bookmarkID].itemID)
                self.AddLink(hint, link)
            elif entry.__guid__ == 'listentry.NoteItem' and self.allowPrivateDrops:
                link = 'note:' + str(entry.noteID)
                self.AddLink(entry.label, link)
            elif entry.__guid__ in ('listentry.InvItem', 'xtriui.InvItem', 'xtriui.ShipUIModule', 'listentry.InvAssetItem', 'listentry.ItemCheckbox'):
                if type(entry.rec.itemID) is tuple:
                    link = 'showinfo:' + str(entry.rec.typeID)
                else:
                    link = 'showinfo:' + str(entry.rec.typeID) + '//' + str(entry.rec.itemID)
                self.AddLink(entry.name, link)
            elif entry.__guid__ in ('listentry.VirtualAgentMissionEntry',):
                link = 'fleetmission:' + str(entry.agentID) + '//' + str(entry.charID)
                self.AddLink(entry.label, link)
            elif entry.__guid__ in ('listentry.CertEntry', 'listentry.CertEntryBasic'):
                link = 'CertEntry:%s//%s' % (entry.certID, entry.level)
                self.AddLink(entry.label, link)
            elif entry.__guid__.startswith('listentry.ContractEntry'):
                link = 'contract:' + str(entry.solarSystemID) + '//' + str(entry.contractID)
                self.AddLink(entry.name.replace('&gt;', '>'), link)
            elif entry.__guid__ in ('listentry.FleetFinderEntry',):
                link = 'fleet:%s' % entry.fleet.fleetID
                self.AddLink(entry.fleet.fleetName or localization.GetByLabel('UI/Common/Unknown'), link)
            elif entry.__guid__ in ('xtriui.ListSurroundingsBtn', 'listentry.LocationTextEntry', 'listentry.LabelLocationTextTop', 'listentry.LocationGroup', 'listentry.LocationSearchItem'):
                if not entry.typeID and not entry.itemID:
                    return
                link = 'showinfo:' + str(entry.typeID) + '//' + str(entry.itemID)
                displayLabel = getattr(entry, 'genericDisplayLabel', None) or entry.label
                self.AddLink(displayLabel, link)
            elif entry.__guid__ == 'listentry.FittingEntry':
                PADDING = 12
                link = 'fitting:' + sm.StartService('fittingSvc').GetStringForFitting(entry.fitting)
                roomLeft = self.RoomLeft()
                if roomLeft is not None:
                    roomLeft = roomLeft - PADDING
                    if len(link) >= roomLeft:
                        if roomLeft < 14:
                            raise UserError('LinkTooLong')
                        if eve.Message('ConfirmTruncateLink', {'numchar': len(link),
                         'maxchar': roomLeft}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
                            return
                        link = link[:roomLeft]
                self.AddLink(entry.fitting.name, link)
            elif entry.__guid__ in ('listentry.GenericMarketItem', 'listentry.QuickbarItem', 'uicls.GenericDraggableForTypeID', 'listentry.DroneEntry', 'listentry.SkillTreeEntry'):
                link = 'showinfo:' + str(entry.typeID)
                label = getattr(entry, 'label', None) or getattr(entry, 'text', '')
                self.AddLink(label, link)
            elif entry.__guid__ == 'TextLink':
                self.AddLink(entry.displayText, entry.url)
            elif entry.__guid__ == 'listentry.ChannelField':
                link = 'joinChannel:%s//%s//%s' % (entry.channel.channelID, None, None)
                label = getattr(entry, 'genericDisplayLabel', None) or entry.label
                self.AddLink(label, link)
            elif entry.__guid__ in ('listentry.KillMail', 'listentry.KillMailCondensed', 'listentry.WarKillEntry'):
                killmail = entry.mail
                hashValue = util.GetKillReportHashValue(killmail)
                if util.IsCharacter(killmail.victimCharacterID):
                    victimName = cfg.eveowners.Get(killmail.victimCharacterID).name
                    shipName = cfg.invtypes.Get(killmail.victimShipTypeID).typeName
                    label = localization.GetByLabel('UI/Corporations/Wars/Killmails/KillLinkCharacter', charName=victimName, typeName=shipName)
                else:
                    shipName = cfg.invtypes.Get(killmail.victimShipTypeID).typeName
                    label = localization.GetByLabel('UI/Corporations/Wars/Killmails/KillLinkStructure', typeName=shipName)
                link = 'killReport:%d:%s' % (entry.mail.killID, hashValue)
                self.AddLink(label, link)
            elif entry.__guid__ in 'listentry.WarEntry':
                warID = entry.war.warID
                attackerID = entry.war.declaredByID
                defenderID = entry.war.againstID
                attackerName = cfg.eveowners.Get(attackerID).name
                defenderName = cfg.eveowners.Get(defenderID).name
                label = localization.GetByLabel('UI/Corporations/Wars/WarReportLink', attackerName=attackerName, defenderName=defenderName)
                link = 'warReport:%d' % warID
                self.AddLink(label, link)
            elif entry.__guid__ in 'listentry.TutorialEntry':
                tutorialID = entry.tutorialID
                link = 'tutorial:%s' % tutorialID
                label = entry.label
                self.AddLink(label, link)
            elif entry.__guid__ in 'listentry.listentry.RecruitmentEntry':
                label = '%s - %s ' % (cfg.eveowners.Get(entry.advert.corporationID).name, entry.adTitle)
                link = 'recruitmentAd:' + str(entry.advert.corporationID) + '//' + str(entry.advert.adID)
                self.AddLink(label, link)
            elif entry.__guid__ in 'listentry.DirectionalScanResults':
                label = entry.typeName
                link = 'showinfo:' + str(entry.typeID) + '//' + str(entry.itemID)
                self.AddLink(label, link, addLineBreak=True)
            elif entry.__guid__ in ('listentry.SkillEntry', 'listentry.SkillQueueSkillEntry'):
                label = entry.invtype.typeName
                link = 'showinfo:' + str(entry.invtype.typeID)
                self.AddLink(label, link)
            elif entry.__guid__ in ('listentry.Item', 'listentry.ContractItemSelect', 'listentry.RedeemToken', 'listentry.FittingModuleEntry', 'listentry.KillItems'):
                label = cfg.invtypes.Get(entry.typeID).name
                link = 'showinfo:' + str(entry.typeID)
                self.AddLink(label, link)
            elif entry.__guid__ in ('listentry.PodGuideBrowseEntry',):
                label = entry.label
                link = 'podGuideLink:%s' % entry.termID
                self.AddLink(label, link)
            elif entry.__guid__ == 'fakeentry.OverviewProfile':
                progressText = localization.GetByLabel('UI/Overview/FetchingOverviewProfile')
                sm.GetService('loading').ProgressWnd(progressText, '', 1, 2)
                try:
                    presetKeyVal = sm.RemoteSvc('overviewPresetMgr').StoreLinkAndGetID(entry.data)
                    if presetKeyVal is None:
                        raise UserError('OverviewProfileLoadingError')
                    else:
                        presetKey = (presetKeyVal.hashvalue, presetKeyVal.sqID)
                finally:
                    sm.GetService('loading').ProgressWnd(progressText, '', 2, 2)

                link = 'overviewPreset:%s//%s' % presetKey
                label = entry.label
                self.AddLink(label, link)

    def ApplyGameSelection(self, what, data, changeObjs):
        if what == 6 and len(changeObjs):
            key = {}
            if data:
                key['link'] = data['link']
                t = self.DoSearch(key['link'], data['text'])
                if not t:
                    return
            else:
                format = [{'type': 'checkbox',
                  'label': '_hide',
                  'text': 'http://',
                  'key': 'http://',
                  'required': 1,
                  'setvalue': 1,
                  'frame': 1,
                  'group': 'link',
                  'onchange': self.OnLinkTypeChange},
                 {'type': 'btline'},
                 {'type': 'checkbox',
                  'label': '_hide',
                  'text': localization.GetByLabel('UI/Common/Character'),
                  'key': 'char',
                  'required': 1,
                  'setvalue': 0,
                  'frame': 1,
                  'group': 'link',
                  'onchange': self.OnLinkTypeChange},
                 {'type': 'checkbox',
                  'label': '_hide',
                  'text': localization.GetByLabel('UI/Common/Corporation'),
                  'key': 'corp',
                  'required': 1,
                  'setvalue': 0,
                  'frame': 1,
                  'group': 'link',
                  'onchange': self.OnLinkTypeChange},
                 {'type': 'btline'},
                 {'type': 'checkbox',
                  'label': '_hide',
                  'text': localization.GetByLabel('UI/Common/ItemType'),
                  'key': 'type',
                  'required': 1,
                  'setvalue': 0,
                  'frame': 1,
                  'group': 'link',
                  'onchange': self.OnLinkTypeChange},
                 {'type': 'btline'},
                 {'type': 'checkbox',
                  'label': '_hide',
                  'text': localization.GetByLabel('UI/Common/SolarSystem'),
                  'key': 'solarsystem',
                  'required': 1,
                  'setvalue': 0,
                  'frame': 1,
                  'group': 'link',
                  'onchange': self.OnLinkTypeChange},
                 {'type': 'checkbox',
                  'label': '_hide',
                  'text': localization.GetByLabel('UI/Common/Station'),
                  'key': 'station',
                  'required': 1,
                  'setvalue': 0,
                  'frame': 1,
                  'group': 'link',
                  'onchange': self.OnLinkTypeChange},
                 {'type': 'btline'},
                 {'type': 'edit',
                  'label': localization.GetByLabel('UI/Common/Link'),
                  'text': 'http://',
                  'width': 170,
                  'required': 1,
                  'key': 'txt',
                  'frame': 1}]
                key = self.AskLink(localization.GetByLabel('UI/Common/EnterLink'), format, width=400)
            anchor = -1
            if key:
                link = key['link']
                if link == None:
                    return
                if link in ('char', 'corp', 'solarsystem', 'station', 'type'):
                    if not self.typeID:
                        t = self.DoSearch(link, key['txt'])
                        if not t:
                            return
                    anchor = 'showinfo:' + str(self.typeID)
                    if self.itemID:
                        anchor += '//' + str(self.itemID)
                elif link == 'fleet':
                    anchor = 'fleet:' + str(self.itemID)
                elif link == 'http://':
                    if key['txt'].startswith(key['link']) or key['txt'].startswith('https://'):
                        anchor = ''
                    else:
                        anchor = key['link']
                    anchor += key['txt']
                else:
                    anchor = key['link'] + key['txt']
            return anchor
        return -1

    def OnLinkTypeChange(self, chkbox, *args):
        if chkbox.GetValue():
            self.itemID = self.typeID = 0
            self.key = chkbox.data['key']
            text = uiutil.GetChild(chkbox, 'text')
            wnd = chkbox.FindParentByName(localization.GetByLabel('UI/Common/GenerateLink'))
            if not wnd:
                return
            editParent = uiutil.FindChild(wnd, 'editField')
            if editParent is not None:
                label = uiutil.FindChild(editParent, 'label')
                label.text = text.text
                edit = uiutil.FindChild(editParent, 'edit_txt')
                edit.SetValue('')
                self.sr.searchbutt = uiutil.FindChild(editParent, 'button')
                if self.key in ('char', 'corp', 'type', 'solarsystem', 'station'):
                    if self.sr.searchbutt == None:
                        self.sr.searchbutt = uicontrols.Button(parent=editParent, label=localization.GetByLabel('UI/Common/Search'), func=self.OnSearch, btn_default=0, align=uiconst.TOPRIGHT)
                    else:
                        self.sr.searchbutt.state = uiconst.UI_NORMAL
                elif self.sr.searchbutt != None:
                    self.sr.searchbutt.state = uiconst.UI_HIDDEN

    def OnSearch(self, *args):
        wnd = self.sr.searchbutt.FindParentByName(localization.GetByLabel('UI/Common/GenerateLink'))
        if not wnd:
            return
        editParent = uiutil.FindChild(wnd, 'editField')
        edit = uiutil.FindChild(editParent, 'edit_txt')
        val = edit.GetValue().strip().lower()
        name = self.DoSearch(self.key, val)
        if name is not None:
            edit.SetValue(name)

    def DoSearch(self, key, val):
        self.itemID = None
        self.typeID = None
        id = None
        name = ''
        val = '%s*' % val
        if key == 'type':
            itemTypes = []
            results = searchUtil.QuickSearch(val, [const.searchResultInventoryType])
            if results is not None:
                for typeID in results:
                    typeRec = cfg.invtypes.Get(typeID)
                    itemTypes.append((typeRec.name, None, typeID))

            if not itemTypes:
                eve.Message('NoItemTypesFound')
                return
            id = uix.ListWnd(itemTypes, 'item', localization.GetByLabel('UI/Common/SelectItemType'), None, 1)
        else:
            group = None
            hideNPC = 0
            if key == 'solarsystem':
                group = const.groupSolarSystem
            elif key == 'station':
                group = const.groupStation
            elif key == 'char':
                group = const.groupCharacter
            elif key == 'corp':
                group = const.groupCorporation
            id = uix.Search(val, group, hideNPC=hideNPC, listType='Generic')
        name = ''
        if id:
            self.itemID = id
            self.typeID = 0
            if key in ('char', 'corp'):
                o = cfg.eveowners.Get(id)
                self.typeID = o.typeID
                name = o.name
            elif key == 'solarsystem':
                self.typeID = const.typeSolarSystem
                l = cfg.evelocations.Get(id)
                name = l.name
            elif key == 'station':
                self.typeID = sm.GetService('ui').GetStation(id).stationTypeID
                l = cfg.evelocations.Get(id)
                name = l.name
            elif key == 'type':
                self.typeID = id[2]
                self.itemID = None
                name = id[0]
        return name

    def AskLink(self, label = '', lines = [], width = 280):
        icon = uiconst.QUESTION
        format = [{'type': 'btline'}, {'type': 'text',
          'text': label,
          'frame': 1}] + lines + [{'type': 'bbline'}]
        btns = uiconst.OKCANCEL
        retval = uix.HybridWnd(format, localization.GetByLabel('UI/Common/GenerateLink'), 1, None, uiconst.OKCANCEL, minW=width, minH=110, icon=icon)
        if retval:
            return retval
        else:
            return

    def AddLink(self, text, link = None, addLineBreak = False):
        self.SetSelectionRange(None, None)
        node = self.GetActiveNode()
        if node is None:
            return
        text = uiutil.StripTags(text, stripOnly=['localized'])
        shiftCursor = len(text)
        stackCursorIndex = self.globalCursorPos - node.startCursorIndex + node.stackCursorIndex
        glyphString = node.glyphString
        glyphStringIndex = self.GetGlyphStringIndex(glyphString)
        shift = 0
        if stackCursorIndex != 0:
            currentParams = self._activeParams.Copy()
            self.InsertToGlyphString(glyphString, currentParams, u' ', stackCursorIndex)
            shift += 1
        currentParams = self._activeParams.Copy()
        currentParams.url = link
        self.InsertToGlyphString(glyphString, currentParams, text, stackCursorIndex + shift)
        shift += shiftCursor
        currentParams = self._activeParams.Copy()
        self.InsertToGlyphString(glyphString, currentParams, u' ', stackCursorIndex + shift)
        shift += 1
        self.UpdateGlyphString(glyphString, advance=shiftCursor, stackCursorIndex=stackCursorIndex)
        self.SetCursorPos(self.globalCursorPos + shift)
        self.UpdatePosition()
        cursorAdvance = 1
        if addLineBreak:
            self.Insert(uiconst.VK_RETURN)

    def GetMenuDelegate(self, node = None):
        m = uicontrols.EditPlainTextCore.GetMenuDelegate(self, node)
        if not self.readonly:
            m.append(None)
            linkmenu = [(uiutil.MenuLabel('UI/Common/Character'), self.LinkCharacter),
             (localization.GetByLabel('UI/Common/Corporation'), self.LinkCorp),
             (localization.GetByLabel('UI/Common/SolarSystem'), self.LinkSolarSystem),
             (localization.GetByLabel('UI/Common/Station'), self.LinkStation),
             (localization.GetByLabel('UI/Common/ItemType'), self.LinkItemType)]
            m.append((uiutil.MenuLabel('UI/Common/AutoLink'), linkmenu))
            if uicore.imeHandler:
                uicore.imeHandler.GetMenuDelegate(self, node, m)
        return m

    def LinkCharacter(self):
        if not self.HasSelection():
            self.SelectWordUnderCursor()
        txt = self.GetSelectedText()
        if txt:
            txt = txt.strip()
        self.ApplySelection(6, data={'text': txt,
         'link': 'char'})

    def LinkCorp(self):
        if not self.HasSelection():
            self.SelectWordUnderCursor()
        txt = self.GetSelectedText()
        if txt:
            txt = txt.strip()
        self.ApplySelection(6, data={'text': txt,
         'link': 'corp'})

    def LinkSolarSystem(self):
        if not self.HasSelection():
            self.SelectWordUnderCursor()
        txt = self.GetSelectedText()
        if txt:
            txt = txt.strip()
        self.ApplySelection(6, data={'text': txt,
         'link': 'solarsystem'})

    def LinkStation(self):
        if not self.HasSelection():
            self.SelectWordUnderCursor()
        txt = self.GetSelectedText()
        if txt:
            txt = txt.strip()
        self.ApplySelection(6, data={'text': txt,
         'link': 'station'})

    def LinkItemType(self):
        if not self.HasSelection():
            self.SelectWordUnderCursor()
        txt = self.GetSelectedText()
        if txt:
            txt = txt.strip()
        self.ApplySelection(6, data={'text': txt,
         'link': 'type'})


from carbonui.control.editPlainText import EditPlainTextCoreOverride
EditPlainTextCoreOverride.__bases__ = (EditPlainText,)
