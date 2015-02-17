#Embedded file name: eve/client/script/ui/shared/neocom\attributes.py
"""
This file contains the UI needed to view and respec your attributes
independently from the character sheet
"""
import blue
import uiprimitives
import uicontrols
import util
import form
from carbonui.primitives.container import Container
from carbonui.primitives.layoutGrid import LayoutGrid
from carbonui.primitives.line import Line
from eve.client.script.ui.control.buttons import Button
from eve.client.script.ui.control.eveLabel import EveLabelMedium
import uthread
import uicls
import carbonui.const as uiconst
import localization

class AttributeRespecWindow(uicontrols.Window):
    __guid__ = 'form.attributeRespecWindow'
    __notifyevents__ = ['OnSessionChanged']
    default_windowID = 'attributerespecification'
    default_iconNum = 'res:/ui/Texture/WindowIcons/attributes.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.readOnly = attributes.readOnly
        self.MakeUnResizeable()
        self.SetCaption(localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/NavScroll/Attributes'))
        self.SetWndIcon(self.iconNum)
        self.godma = sm.StartService('godma')
        self.skillHandler = self.godma.GetSkillHandler()
        uicontrols.WndCaptionLabel(text=localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/Attributes/NeuralRemapping'), subcaption=localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/Attributes/NeuralRemappingTagline'), parent=self.sr.topParent, align=uiconst.RELATIVE)
        self.attributes = [const.attributePerception,
         const.attributeMemory,
         const.attributeWillpower,
         const.attributeIntelligence,
         const.attributeCharisma]
        self.implantTypes = [19540,
         19551,
         19553,
         19554,
         19555]
        self.attributeIcons = ['ui_22_32_5',
         'ui_22_32_4',
         'ui_22_32_2',
         'ui_22_32_3',
         'ui_22_32_1']
        self.attributeLabels = [localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/Attributes/AttributePerception'),
         localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/Attributes/AttributeMemory'),
         localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/Attributes/AttributeWillpower'),
         localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/Attributes/AttributeIntelligence'),
         localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/Attributes/AttributeCharisma')]
        self.currentAttributes = {}
        self.implantModifier = {}
        self.unspentPts = 0
        self.ConstructLayout()
        self.Load()

    def OnSessionChanged(self, isRemote, session, change):
        self.skillHandler = self.godma.GetSkillHandler()

    def Load(self, *args):
        """
            Performs the initialization of the window's data by loading
            the current session's character's base attributes, clamping them to
            conform to basic business rules (for the player's convenience),
            and setting up the UI's initial display data.
        """
        if not eve.session.charid or self.destroyed:
            return
        dogmaLM = self.godma.GetDogmaLM()
        attrDict = dogmaLM.GetCharacterBaseAttributes()
        unspentPts = const.respecTotalRespecPoints
        for x in xrange(0, 5):
            attr = self.attributes[x]
            if attr in attrDict:
                attrValue = attrDict[attr]
                if attrValue > const.respecMaximumAttributeValue:
                    attrValue = const.respecMaximumAttributeValue
                if attrValue < const.respecMinimumAttributeValue:
                    attrValue = const.respecMinimumAttributeValue
                self.currentAttributes[attr] = attrValue
                self.respecBar[x].SetValue(attrValue - const.respecMinimumAttributeValue)
                unspentPts -= attrValue
            modifiers = self.skillHandler.GetCharacterAttributeModifiers(attr)
            implantBonus = 0
            for itemID, typeID, operation, value in modifiers:
                categoryID = cfg.invtypes.Get(typeID).categoryID
                if categoryID == const.categoryImplant:
                    implantBonus += value

            totalAttributesText = localization.formatters.FormatNumeric(int(self.currentAttributes[attr]) + implantBonus, decimalPlaces=0)
            self.totalLabels[x].text = totalAttributesText
            self.implantModifier[x] = implantBonus
            label, icon = self.implantLabels[x]
            if implantBonus == 0:
                icon.SetAlpha(0.5)
                label.text = localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/Attributes/ImplantBonusZero')
                label.SetAlpha(0.5)
            else:
                label.text = localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/Attributes/ImplantBonus', implantBonus=int(implantBonus))

        if not self.readOnly:
            self.unspentPts = unspentPts
            self.sr.unassignedBar.SetValue(unspentPts)
            unspentPtsText = localization.formatters.FormatNumeric(self.unspentPts, decimalPlaces=0)
            self.availableLabel.text = unspentPtsText
            if self.unspentPts <= 0:
                self.sr.saveWarningText.state = uiconst.UI_HIDDEN
            else:
                self.sr.saveWarningText.state = uiconst.UI_DISABLED

    def ConstructLayout(self):
        """
            This method lays out the elements that comprise the respecification window,
            assigning them initial display values that make sense in the case that
            Load() later fails.
            Performs no data initialization.
        """
        self.implantLabels = []
        self.respecBar = []
        self.totalLabels = []
        iconsize = 32
        buttonSize = 24
        boxWidth = 6
        boxHeight = 12
        boxMargin = 1
        boxSpacing = 1
        numBoxes = const.respecMaximumAttributeValue - const.respecMinimumAttributeValue
        barWidth = numBoxes * boxSpacing + 2 * boxMargin + numBoxes * boxWidth - 1
        barHeight = boxHeight + 2 * boxMargin
        backgroundColor = (0.0, 0.0, 0.0, 0.0)
        colorDict = {uicls.ClickableBoxBar.COLOR_UNSELECTED: (0.2, 0.2, 0.2, 1.0),
         uicls.ClickableBoxBar.COLOR_SELECTED: (0.2, 0.8, 0.2, 1.0)}
        headerText = EveLabelMedium(parent=self.sr.main, text=localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/Attributes/CharacterRespecMessage'), state=uiconst.UI_NORMAL, align=uiconst.TOTOP, padding=8)
        self.headerText = headerText
        if self.readOnly:
            columns = 7
        else:
            columns = 9
        mainGrid = LayoutGrid(parent=self.sr.main, columns=columns, cellPadding=4, left=6, top=6, OnGridSizeChanged=self.OnMainGridSizeChanged)
        self.mainGrid = mainGrid
        for labelPath, colSpan in (('UI/CharacterSheet/CharacterSheetWindow/NavScroll/Attributes', 2),
         ('UI/CharacterSheet/CharacterSheetWindow/Attributes/BaseStatPoints', 1),
         ('UI/CharacterSheet/CharacterSheetWindow/Attributes/CharacterImplants', 2),
         ('UI/CharacterSheet/CharacterSheetWindow/Attributes/RemappableStat', 1 if self.readOnly else 3),
         ('UI/CharacterSheet/CharacterSheetWindow/Attributes/StatTotal', 1)):
            label = EveLabelMedium(text=localization.GetByLabel(labelPath), align=uiconst.CENTER)
            mainGrid.AddCell(cellObject=label, colSpan=colSpan, cellPadding=(10, 2, 10, 2))

        line = Line(align=uiconst.TOTOP)
        mainGrid.AddCell(cellObject=line, colSpan=mainGrid.columns)
        for x in xrange(5):
            uicontrols.Icon(parent=mainGrid, width=iconsize, height=iconsize, size=iconsize, icon=self.attributeIcons[x], align=uiconst.TOPLEFT)
            EveLabelMedium(text=self.attributeLabels[x], parent=mainGrid, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT)
            minText = localization.formatters.FormatNumeric(const.respecMinimumAttributeValue, decimalPlaces=0)
            EveLabelMedium(text=minText, parent=mainGrid, state=uiconst.UI_DISABLED, align=uiconst.CENTER, bold=True)
            icon = uicontrols.Icon(parent=mainGrid, width=32, height=32, size=32, icon=util.IconFile(cfg.invtypes.Get(self.implantTypes[x]).iconID), align=uiconst.TOPLEFT, ignoreSize=True)
            implantLabel = EveLabelMedium(text='0', parent=mainGrid, align=uiconst.CENTERLEFT)
            self.implantLabels.append((implantLabel, icon))
            if not self.readOnly:
                minusText = localization.GetByLabel('UI/Common/Buttons/Minus')
                Button(parent=mainGrid, label=minusText, fixedwidth=buttonSize, func=self.DecreaseAttribute, args=(x,), align=uiconst.CENTERRIGHT)
            bar = Container(parent=mainGrid, align=uiconst.CENTER, width=barWidth, height=barHeight, state=uiconst.UI_PICKCHILDREN)
            bar = uicls.ClickableBoxBar(parent=bar, numBoxes=numBoxes, boxWidth=boxWidth, boxHeight=boxHeight, boxMargin=boxMargin, boxSpacing=boxSpacing, backgroundColor=backgroundColor, colorDict=colorDict)
            bar.OnValueChanged = self.OnMemberBoxClick
            bar.OnAttemptBoxClicked = self.ValidateBoxClick
            self.respecBar.append(bar)
            if not self.readOnly:
                plusText = localization.GetByLabel('UI/Common/Buttons/Plus')
                Button(parent=mainGrid, label=plusText, fixedwidth=buttonSize, func=self.IncreaseAttribute, args=(x,), align=uiconst.CENTERLEFT)
            totalLabel = EveLabelMedium(text='0', parent=mainGrid, left=8, align=uiconst.CENTERRIGHT, bold=True)
            self.totalLabels.append(totalLabel)

        if not self.readOnly:
            line = Line(align=uiconst.TOTOP)
            mainGrid.AddCell(cellObject=line, colSpan=mainGrid.columns)
            textObj = EveLabelMedium(text=localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/Attributes/UnassignedAttributePoints'))
            mainGrid.AddCell(cellObject=textObj, colSpan=6)
            numBoxes = const.respecTotalRespecPoints - const.respecMinimumAttributeValue * 5
            barWidth = numBoxes * boxSpacing + 2 * boxMargin + numBoxes * boxWidth - 1
            unassignedBarParent = Container(align=uiconst.TOPLEFT, width=barWidth, height=barHeight, state=uiconst.UI_PICKCHILDREN)
            mainGrid.AddCell(cellObject=unassignedBarParent, colSpan=2)
            self.sr.unassignedBar = uicls.ClickableBoxBar(parent=unassignedBarParent, numBoxes=numBoxes, boxWidth=boxWidth, boxHeight=boxHeight, boxMargin=boxMargin, boxSpacing=boxSpacing, backgroundColor=backgroundColor, colorDict=colorDict, readonly=True, hintFormat='UI/CharacterSheet/CharacterSheetWindow/Attributes/UnassignedPointsHint')
            self.availableLabel = EveLabelMedium(parent=mainGrid, align=uiconst.CENTERRIGHT, left=8)
            mainGrid.FillRow()
            self.sr.saveWarningText = EveLabelMedium(text=localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/Attributes/CannotSaveUnassignedPoints'), color=(1.0, 0.0, 0.0, 0.9))
            mainGrid.AddCell(cellObject=self.sr.saveWarningText, colSpan=mainGrid.columns)
        if not self.readOnly:
            uicontrols.ButtonGroup(btns=[[localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/Attributes/SaveStatChanges'),
              self.SaveChanges,
              (),
              None], [localization.GetByLabel('UI/Common/Buttons/Cancel'),
              self.CloseByUser,
              (),
              None]], parent=self.sr.main, idx=0)

    def OnMainGridSizeChanged(self, width, height, *args, **kwds):
        self.mainGrid.top = self.headerText.height + self.headerText.padTop + self.headerText.padBottom
        self.SetMinSize([width + 12, self.mainGrid.top + height + 110], refresh=1)

    def SaveChanges(self, *args):
        """
            This method is called when the user clicks the "Save Changes" button in the UI.
            It performs basic sanity checks (primarily on the ranges of the user's desired
            attribute values) and then forwards the request to the server.
            
            It also forces the UI to no-op if the user didn't change anything, so the user
            doesn't waste a respec by doing nothing.
        """
        totalAttrs = 0
        newAttributes = {}
        for x in xrange(0, 5):
            newAttributes[self.attributes[x]] = const.respecMinimumAttributeValue + self.respecBar[x].GetValue()

        for attrValue in newAttributes.itervalues():
            if attrValue < const.respecMinimumAttributeValue:
                raise UserError('RespecAttributesTooLow')
            elif attrValue > const.respecMaximumAttributeValue:
                raise UserError('RespecAttributesTooHigh')
            totalAttrs += attrValue

        if totalAttrs != const.respecTotalRespecPoints or self.sr.unassignedBar.GetValue() > 0:
            self.sr.saveWarningText.state = uiconst.UI_DISABLED
            raise UserError('RespecAttributesMisallocated')
        allSame = True
        for attr in self.attributes:
            if int(self.currentAttributes[attr]) != int(newAttributes[attr]):
                allSame = False
                break

        if not allSame:
            respecInfo = sm.GetService('skills').GetRespecInfo()
            freeRespecs = respecInfo['freeRespecs']
            if respecInfo['nextTimedRespec'] is None or respecInfo['nextTimedRespec'] <= blue.os.GetWallclockTime():
                if eve.Message('ConfirmRespec2', {'months': int(const.respecTimeInterval / const.MONTH30)}, uiconst.YESNO) != uiconst.ID_YES:
                    return
            elif freeRespecs > 0:
                if eve.Message('ConfirmRespecFree', {'freerespecs': int(respecInfo['freeRespecs']) - 1}, uiconst.YESNO) != uiconst.ID_YES:
                    return
            else:
                raise UserError('RespecTooSoon', {'nextTime': respecInfo['nextTimedRespec']})
            self.skillHandler.RespecCharacter(newAttributes[const.attributeCharisma], newAttributes[const.attributeIntelligence], newAttributes[const.attributeMemory], newAttributes[const.attributePerception], newAttributes[const.attributeWillpower])
        self.CloseByUser()

    def IncreaseAttribute(self, attribute, *args):
        """
            This method is called when the user clicks on one of the "+" buttons to increase
            an attribute. It ensures that the user has a point to spend and won't exceed the
            maximum permissible value, then modifies the remaining points and updates the UI.
            
            The ID of the attribute to increase is passed in as an argument.
        """
        if self.respecBar[attribute].GetValue() >= const.respecMaximumAttributeValue - const.respecMinimumAttributeValue:
            return
        if self.unspentPts <= 0:
            raise UserError('RespecCannotIncrementNotEnoughPoints')
        if not self.respecBar[attribute].Increment():
            raise UserError('RespecAttributesTooHigh')

    def DecreaseAttribute(self, attribute, *args):
        """
            This method is called when the user clicks on one of the "-" buttons to decrease
            an attribute. It ensures that the user has a point to spend and won't fall below the
            minimum permissible value, then modifies the remaining points and updates the UI.
            
            The ID of the attribute to decrease is passed in as an argument.
        
        """
        if self.respecBar[attribute].GetValue() <= 0:
            return
        if not self.respecBar[attribute].Decrement():
            raise UserError('RespecAttributesTooLow')

    def ValidateBoxClick(self, oldValue, newValue):
        """
            This is an override of a method used in the clickableboxbar.
            A CBB calls this method before attempting to change a value,
            allowing us to perform business logic related to changing
            the value of the bar.
            
            Here, we use it for validation.
        """
        if self.readOnly:
            return False
        if oldValue >= newValue:
            return True
        if self.unspentPts < newValue - oldValue:
            return False
        return True

    def OnMemberBoxClick(self, oldValue, newValue):
        """
            This is an override of a method on a clickableboxbar.
            It is called whenever the value of a clickableboxbar changes.
        """
        if oldValue is None or oldValue == newValue:
            return
        if self.readOnly:
            return
        self.unspentPts -= newValue - oldValue
        self.sr.unassignedBar.SetValue(self.unspentPts)
        unspentPtsText = localization.formatters.FormatNumeric(self.unspentPts, decimalPlaces=0)
        self.availableLabel.text = unspentPtsText
        for x in xrange(0, 5):
            totalPts = const.respecMinimumAttributeValue + self.respecBar[x].GetValue() + self.implantModifier[x]
            totalPtsText = localization.formatters.FormatNumeric(int(totalPts), decimalPlaces=0)
            self.totalLabels[x].text = totalPtsText

        if self.unspentPts <= 0:
            self.sr.saveWarningText.state = uiconst.UI_HIDDEN


class AttributeRespecEntry(uicontrols.SE_BaseClassCore):
    __guid__ = 'listentry.AttributeRespec'
    default_showHilite = False
    ENTRYHEIGHT = 44

    def Startup(self, *args):
        """
            This method lays out the elements used to display a character's next respec time.
        """
        self.OnSelectCallback = None
        self.sr.label = uicontrols.EveLabelSmall(text=localization.GetByLabel('UI/Neocom/NextDNAModification'), parent=self, left=8, top=4, maxLines=1)
        self.sr.respecTime = uicontrols.EveLabelMedium(text='', parent=self, left=8, top=18, maxLines=1)
        self.sr.numberOfRemaps = uicontrols.EveLabelMedium(text='', parent=self, left=8, top=38, maxLines=1, state=uiconst.UI_HIDDEN)
        self.sr.respecButton = uicontrols.Button(parent=self, label=localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/Attributes/RemapStatsNow'), align=uiconst.TOPRIGHT, pos=(2, 16, 0, 0), func=self.OpenRespecWindow, args=(False,))
        self.hint = localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/Attributes/CharacterSheetHint')

    def Load(self, node):
        """
            This method loads in the data needed to display a character's next respec time
            and sets the UI's display data as a result of checking the loaded data.
            It also launches the UI refresh thread in the case that the character cannot
            respec yet.
            
            Node must contain:
                nextTimedRespec - A bluetime indicating when the next respec is available.
                freeRespecs - An integer indicating how many free/bonus respecs the character has.
        """
        self.sr.node = node
        freeRespecs = node.Get('freeRespecs', 0)
        nextRespecTime = node.Get('nextTimedRespec', None)
        canRemap = False
        if nextRespecTime is None or nextRespecTime <= blue.os.GetWallclockTime():
            self.sr.respecTime.text = localization.GetByLabel('UI/Generic/Now')
            canRemap = True
        else:
            self.sr.respecTime.text = util.FmtDate(node.nextTimedRespec)
            self.refreshThread = uthread.new(self.RefreshThread)
        if freeRespecs > 0:
            canRemap = True
            lbl = localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/Attributes/BonusRemapsAvailable', remapsAvailable=freeRespecs)
            self.sr.numberOfRemaps.text = lbl
            if nextRespecTime is not None and nextRespecTime > blue.os.GetWallclockTime():
                self.hint = localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/Attributes/CharacterSheetHintFree')
            else:
                self.hint = localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/Attributes/CharacterSheetHintFreeTimed')
            self.sr.numberOfRemaps.state = uiconst.UI_DISABLED
        if not canRemap:
            self.sr.respecButton.SetLabel(localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/Attributes/AttributesOverview'))
            self.sr.respecButton.args = (True,)

    def OpenRespecWindow(self, readOnly, *args):
        """
            This method is called when a user clicks the "Respec Now" (currently "Modify DNA") button.
            It maximizes/foregrounds the attribute respec window if it's already open; otherwise,
            it creates and displays the window.
        """
        wnd = form.attributeRespecWindow.GetIfOpen()
        if wnd is not None and not wnd.destroyed:
            wnd.Maximize()
        else:
            form.attributeRespecWindow.Open(readOnly=readOnly)

    def RefreshThread(self):
        """
            This thread is launched when the UI opens and the character cannot yet respec.
            It loops, sleeping for a second before checking if the respec time has passed.
            If it has passed, it displays the Respec button, updates the UI text to "now"
            and halts.
            If the respec time is still in the future, it continues sleeping.
        """
        if not self or self.destroyed:
            return
        sleepMsec = max(self.sr.node.nextTimedRespec - blue.os.GetWallclockTime(), 0) / 10000L
        sleepMsec = min(sleepMsec, 60000)
        while sleepMsec > 0:
            blue.pyos.synchro.SleepWallclock(sleepMsec)
            if not self or self.destroyed:
                return
            sleepMsec = max(self.sr.node.nextTimedRespec - blue.os.GetWallclockTime(), 0) / 10000L
            sleepMsec = min(sleepMsec, 60000)

        if not self or self.destroyed:
            return
        self.sr.respecButton.state = uiconst.UI_NORMAL
        self.sr.respecTime.text = localization.GetByLabel('UI/Generic/Now')
