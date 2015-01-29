#Embedded file name: eve/client/script/ui/hacking\hackingWindow.py
import uicls
import carbonui.const as uiconst
import localization
import uiprimitives
import uicontrols
import util
import random
import uthread
import trinity
import hackingcommon.hackingConstants as hackingConst
import hackingui as hackingUI
import hackingUIConst

class hackingWindow(uicontrols.Window):
    __guid__ = 'form.HackingWindow'
    __notifyevents__ = ['OnHackingNewTurn',
     'OnHackingWon',
     'OnHackingLost',
     'OnDefenseSoftwareUnveiled',
     'OnCoreUnveiled',
     'OnHackingTileCreated',
     'OnHackingTileChanged',
     'OnHackingStart',
     'OnHackingUEInventoryConstructed']
    default_windowID = 'HackingWindow'
    default_caption = 'Hacking'
    default_width = 898
    default_height = 631
    default_fixedWidth = default_width
    default_fixedHeight = default_height
    default_topParentHeight = 0
    default_isCollapseable = False
    default_isStackable = False

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.tilesByTileCoord = {}
        self.linesByTileCoords = {}
        self.utilityElements = []
        self.accessibleTiles = []
        self.hasGameEnded = False
        self.bottomCont = uiprimitives.Container(name='bottomCont', parent=self.sr.main, align=uiconst.TOBOTTOM, height=110)
        self.tileHintLabel = uicontrols.Label(name='tileHintLabel', parent=self.bottomCont, align=uiconst.BOTTOMRIGHT, pos=(15, 15, 220, 0), fontsize=10)
        self.utilityElementContainer = uicontrols.ContainerAutoSize(name='utilityElementContainer', parent=self.bottomCont, align=uiconst.CENTERBOTTOM, state=uiconst.UI_PICKCHILDREN, opacity=1.0, height=50, top=10)
        self.virusInfo = hackingUI.VirusInfo(parent=self.bottomCont, left=15, top=10, opacity=0.0)
        self.boardTransform = uiprimitives.Transform(name='boardTransform', parent=self.sr.main, align=uiconst.TOALL, state=uiconst.UI_NORMAL, scalingCenter=(0.5, 0.5))
        self.boardContainer = uiprimitives.Container(name='boardContainer', parent=self.boardTransform, align=uiconst.TOPLEFT, opacity=0.0)
        self.backgroundVideo = uiprimitives.VideoSprite(bgParent=self.sr.maincontainer, videoPath='res:/video/hacking/bgLoop_alpha.bik', videoLoop=True, spriteEffect=trinity.TR2_SFX_COPY, color=hackingUIConst.COLOR_WINDOW_BG, opacity=0.0)
        sm.GetService('audio').SendUIEvent('minigame_start')

    def Close(self, *args, **kw):
        uicontrols.Window.Close(self, *args, **kw)
        sm.GetService('audio').SendUIEvent('minigame_stop')

    def CloseByUser(self, *args):
        uthread.new(sm.GetService('hackingUI').QuitHackingAttempt)

    def EntryAnimation(self):
        uicore.animations.Tr2DScaleTo(self.boardTransform, startScale=(0.99, 0.99), endScale=(1.0, 1.0), duration=0.8)
        uicore.animations.FadeTo(self.backgroundVideo, 0.0, hackingUIConst.COLOR_WINDOW_BG[3], duration=1.6)
        uicore.animations.FadeIn(self.boardContainer, duration=0.8)
        uicore.animations.FadeIn(self.virusInfo, duration=0.8, timeOffset=0.3)
        uicore.animations.FadeIn(self.utilityElementContainer, duration=0.8, timeOffset=0.6)

    def OnHackingWon(self):
        self.EndGame(True)

    def OnHackingLost(self):
        self.EndGame(False)

    def OnHackingTileChanged(self, eventID, tileData):
        self.tilesByTileCoord[tileData.coord].UpdateTileState(eventID, tileData)
        self.UpdateLineColors()
        for neighbour in tileData.GetNeighbours():
            if neighbour.coord in self.tilesByTileCoord:
                self.tilesByTileCoord[neighbour.coord].UpdateTileState(hackingConst.EVENT_TILE_REACHABLE, tileData)

    def OnHackingTileCreated(self, tileData, objectData):
        if tileData.coord in self.tilesByTileCoord:
            self.OnHackingTileChanged(hackingConst.EVENT_TILE_CREATED, tileData)
        else:
            left, top = tileData.GetXY()
            tile = hackingUI.Tile(parent=self.boardContainer, left=left, top=top, tileData=tileData)
            self.tilesByTileCoord[tileData.coord] = tile

    def OnHackingUEInventoryConstructed(self, inventoryContents):
        for i, elementData in enumerate(inventoryContents):
            elementUI = hackingUI.UtilityElement(parent=self.utilityElementContainer, utilityElementData=elementData, index=i)
            self.utilityElements.append(elementUI)

    def OnHackingStart(self, eventData):
        self.SetBoardSize()
        if eventData['moduleTypeID']:
            self.SetCaption(cfg.invtypes.Get(eventData['moduleTypeID']).typeName)
        for tile in self.tilesByTileCoord.values():
            self.ConstructLinesForTile(tile.tileData)

        self.EntryAnimation()

    def SetBoardSize(self):
        x = y = 0
        for tile in self.tilesByTileCoord.values():
            hexX, hexY = tile.tileData.GetHexXY()
            if hexX > x:
                x = hexX
            if hexY > y:
                y = hexY

        self.boardContainer.width = x * hackingUIConst.GRID_X + hackingUIConst.TILE_SIZE
        self.boardContainer.height = y * hackingUIConst.GRID_Y + hackingUIConst.TILE_SIZE
        offsetY = int(hackingUIConst.GRID_MAX_ROWS - y - 1) / 2
        self.boardContainer.top = 16 + offsetY * hackingUIConst.GRID_Y
        offsetX = int(hackingUIConst.GRID_MAX_COLUMNS - x + 0.5) / 2
        if offsetY % 2 == 1:
            offsetX -= 0.5
        self.boardContainer.left = 15 + offsetX * hackingUIConst.GRID_X

    def OnDefenseSoftwareUnveiled(self, coord):
        uicore.animations.SpColorMorphTo(self.backgroundVideo, hackingUIConst.COLOR_WINDOW_BG_BLINK, hackingUIConst.COLOR_WINDOW_BG, duration=0.6)

    def OnCoreUnveiled(self, coord):
        uicore.animations.SpColorMorphTo(self.backgroundVideo, hackingUIConst.COLOR_WINDOW_BG_BLINK, hackingUIConst.COLOR_WINDOW_BG, duration=0.15, loops=3)

    def EndGame(self, won):
        self.boardContainer.Disable()
        text = localization.GetByLabel('UI/Hacking/HackSuccess') if won else localization.GetByLabel('UI/Hacking/HackFailed')
        label = uicontrols.Label(parent=self.sr.main, align=uiconst.CENTER, text=text, bold=True, fontsize=30, idx=0, color=util.Color.WHITE)
        uicore.animations.FadeTo(self.boardContainer, 1.0, 0.5, duration=1.0)
        uicore.animations.FadeOut(self.utilityElementContainer, duration=0.6)
        uicore.animations.FadeOut(self.virusInfo, duration=0.6, timeOffset=0.3)
        uicore.animations.FadeTo(label, 0.0, 1.0, duration=0.6, timeOffset=0.2)
        color = hackingUIConst.COLOR_EXPLORED if won else hackingUIConst.COLOR_UNEXPLORED
        lines = self.linesByTileCoords.values()
        random.shuffle(lines)
        for i, line in enumerate(lines):
            line.AnimExit(i)

        tiles = self.tilesByTileCoord.values()
        random.shuffle(tiles)
        for i, tile in enumerate(tiles):
            uicore.animations.FadeTo(tile, tile.opacity, 0.0, timeOffset=0.2 + i * 0.01, duration=0.2)

        uicore.animations.Tr2DScaleOut(self.boardTransform, endScale=(0.99, 0.99), duration=10.0)
        uicore.animations.FadeOut(self, duration=1.6, callback=self.Close)

    def UpdateLineColors(self):
        for line in self.linesByTileCoords.values():
            line.UpdateState()

    def ConstructLinesForTile(self, tileData):
        for neighbour in tileData.GetNeighbours():
            lineID = [tileData.coord, neighbour.coord]
            lineID.sort()
            lineID = tuple(lineID)
            tile1 = self.tilesByTileCoord[lineID[0]]
            tile2 = self.tilesByTileCoord[lineID[1]]
            if lineID in self.linesByTileCoords:
                continue
            line = hackingUI.Line(tileFrom=tile1, tileTo=tile2, parent=self.boardContainer)
            self.linesByTileCoords[lineID] = line

    def OnKeyDown(self, key, *args):
        if key == uiconst.VK_1:
            self.utilityElements[0].OnClick()
        elif key == uiconst.VK_2:
            self.utilityElements[1].OnClick()
        elif key == uiconst.VK_3:
            self.utilityElements[2].OnClick()

    def SetTileHint(self, hint):
        if hint:
            self.tileHintLabel.text = '<right>' + hint + '</right>'
            if self.tileHintLabel.opacity < 0.01:
                uicore.animations.FadeTo(self.tileHintLabel, self.tileHintLabel.opacity, 1.0, duration=0.3, timeOffset=0.6)
            else:
                uicore.animations.FadeTo(self.tileHintLabel, self.tileHintLabel.opacity, 1.0, duration=0.3)
        else:
            uicore.animations.FadeOut(self.tileHintLabel, duration=0.1)
