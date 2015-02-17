#Embedded file name: eve/client/script/ui/podGuide\megaMenu.py
from carbonui.primitives.container import Container
from carbonui.primitives.frame import Frame
from carbonui.primitives.layoutGrid import LayoutGrid
from carbonui.util.mouseTargetObject import MouseTargetObject
from carbonui.util.various_unsorted import IsUnder
import uthread
from carbon.common.script.util.timerstuff import AutoTimer
from eve.client.script.ui.podGuide.megaMenuEntries import MegaMenuHeader, MegaMenuEntry
import carbonui.const as uiconst

class MegaMenu(Container):
    """
        megamenuOptions is a list of dictionaries, with the keys "headerInfo" and "entryInfoList". Each of these
        dictionaries will make one column in the mega menu
        the headerInfo value is a dict with info about the column header
        the entryInfoList value is a list of dictionaries with info about the column entries
        ex:
            [ {"headerInfo" : {"text": "MyHeader"}, "entryInfoList": [{"text": "1st entry"}, {"text": "2nd entry"}},
            ...
            ]
    """
    beingDestroyed = False

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        megaMenuOptions = attributes.megaMenuOptions
        self.categoryInfo = attributes.categoryInfo
        self.openingButtonClass = attributes.openingButtonClass
        buttonContainer = Container(parent=self, name='buttonContainer', align=uiconst.TOTOP, height=50)
        navigationButton = self.openingButtonClass(parent=buttonContainer, categoryInfo=self.categoryInfo, state=uiconst.UI_NORMAL)
        Frame(bgParent=navigationButton, frameConst=('res:/UI/Texture/Shared/menuButtonBackground_Top.png', 17, -16))
        buttonContainer.height = navigationButton.height
        layoutGridCont = Container(name='layoutGridCont', parent=self)
        numSubgroups = len(megaMenuOptions)
        myLayoutGrid = LayoutGrid(parent=layoutGridCont, columns=numSubgroups, state=uiconst.UI_NORMAL)
        MouseTargetObject(myLayoutGrid)
        Frame(bgParent=myLayoutGrid, frameConst=('res:/UI/Texture/Shared/menuBackground.png', 17, -16))
        for eachColumnInfo in megaMenuOptions:
            column = MegaMenuColumn(columnInfo=eachColumnInfo)
            myLayoutGrid.AddCell(cellObject=column)

        al, at, aw, ah = myLayoutGrid.GetAbsolute()
        self.height = myLayoutGrid.height + buttonContainer.height
        self.width = myLayoutGrid.width
        self.updateThread = AutoTimer(100, self.UpdateMegaMenu)
        uicore.uilib.RegisterForTriuiEvents(uiconst.UI_MOUSEUP, self.OnGlobalMouseUp)

    def Close(self, *args):
        Container.Close(self, *args)
        self.updateThread = None

    def UpdateMegaMenu(self, *args):
        if self.beingDestroyed:
            return
        isMouseOverMenu = self.IsMouseOverMenu()
        if not isMouseOverMenu:
            self.beingDestroyed = True
            uthread.new(self.FadeOut_thread)

    def FadeOut_thread(self):
        uicore.animations.FadeOut(self, duration=0.25, callback=self.Close, sleep=True)

    def IsMouseOverMenu(self):
        overMegaMenu = IsUnder(uicore.uilib.mouseOver, self)
        overNavigationButton = IsUnder(uicore.uilib.mouseOver, self)
        return overMegaMenu or overNavigationButton

    def OnGlobalMouseUp(self, *args):
        uthread.new(self.Close)


class MegaMenuColumn(LayoutGrid):
    default_columns = 1
    default_headerClass = MegaMenuHeader
    default_entryClass = MegaMenuEntry

    def ApplyAttributes(self, attributes):
        LayoutGrid.ApplyAttributes(self, attributes)
        headerClass = attributes.get('headerClass', self.default_headerClass)
        entryClass = attributes.get('entryClass', self.default_entryClass)
        columnInfo = attributes.columnInfo
        headerInfo = columnInfo['headerInfo']
        entryInfoList = columnInfo['entryInfoList']
        headerObject = headerClass(headerInfo=headerInfo)
        self.AddCell(cellObject=headerObject)
        for eachEntryInfo in entryInfoList:
            entryObject = entryClass(entryInfo=eachEntryInfo)
            self.AddCell(cellObject=entryObject)
