#Embedded file name: eve/client/script/ui/station/missions\missionentry.py
import localization
import uiprimitives
import uicontrols
import uix
import util
import uicls
import carbonui.const as uiconst
import uiutil

class VirtualBaseMissionEntry(uicontrols.SE_BaseClassCore):
    __guid__ = 'listentry.VirtualBaseMissionEntry'
    OnSelectCallback = None

    def Startup(self, *etc):
        self.sr.label = uicontrols.EveLabelMedium(text='', parent=self, left=5, state=uiconst.UI_DISABLED, color=None, maxLines=1, align=uiconst.CENTERLEFT)
        self.sr.line = uiprimitives.Container(name='lineparent', align=uiconst.TOBOTTOM, parent=self, height=1)
        uiprimitives.Line(parent=self.sr.line, align=uiconst.TOALL, color=uiconst.ENTRY_LINE_COLOR)

    def GetHeight(_self, *args):
        node, width = args
        node.height = uix.GetTextHeight(node.label, maxLines=1) + 4
        return node.height

    def OnSelect(self, *args):
        if getattr(self, 'OnSelectCallback', None):
            apply(self.OnSelectCallback, args)

    def OnClick(self, *args):
        self.sr.node.scroll.SelectNode(self.sr.node)
        self.OnSelect(self)

    def NoEvent(self, *args):
        pass

    @classmethod
    def GetCopyData(cls, node):
        return node.label


class VirtualAgentMissionEntry(VirtualBaseMissionEntry):
    __guid__ = 'listentry.VirtualAgentMissionEntry'
    isDragObject = True

    def Load(self, node):
        self.sr.node = node
        self.sr.label.text = node.label
        self.sr.iconList = []
        textOffset = 1
        for iconID, hintText in node.missionIconData:
            self.sr.iconList.append(uicontrols.Icon(icon=iconID, parent=self, pos=(textOffset,
             1,
             16,
             16), align=uiconst.TOPLEFT, idx=0))
            self.sr.iconList[-1].hint = hintText
            textOffset += self.sr.iconList[-1].width

        self.sr.label.left = textOffset + 4
        self.rightClickMenu = []
        self.rightClickMenu.append((uiutil.MenuLabel('UI/Agents/Commands/ReadDetails'), self.OpenDetails))
        self.rightClickMenu.append((uiutil.MenuLabel('UI/Agents/Commands/StartConversationWith', {'agentID': self.sr.node.agentID}), self.Convo))
        if node.missionState == const.agentMissionStateOffered:
            self.rightClickMenu.append((uiutil.MenuLabel('UI/Agents/Commands/RemoveOffer'), self.RemoveOffer))

    def OpenDetails(self):
        sm.GetService('agents').PopupMissionJournal(self.sr.node.agentID)

    def RemoveOffer(self):
        sm.StartService('agents').RemoveOfferFromJournal(self.sr.node.agentID)

    def OnDblClick(self, *args):
        self.OpenDetails()

    def Convo(self):
        sm.GetService('agents').InteractWith(self.sr.node.agentID)

    def GetMenu(self):
        return self.rightClickMenu

    def GetDragData(self, *args):
        fakeNode = []
        if session.fleetid:
            _fakeNode = util.KeyVal()
            _fakeNode.__guid__ = 'listentry.VirtualAgentMissionEntry'
            _fakeNode.agentID = self.sr.node.agentID
            _fakeNode.charID = session.charid
            _fakeNode.label = localization.GetByLabel('UI/Agents/MissionJournal')
            fakeNode = [_fakeNode]
        return fakeNode


class VirtualAgentOfferEntry(VirtualBaseMissionEntry):
    __guid__ = 'listentry.VirtualAgentOfferEntry'

    def Load(self, node):
        self.sr.node = node
        self.sr.label.text = node.label

    def OpenDetails(self):
        sm.GetService('agents').PopupOfferJournal(self.sr.node.agentID)

    def OnDblClick(self, *args):
        self.OpenDetails()

    def Convo(self):
        sm.GetService('agents').InteractWith(self.sr.node.agentID)

    def GetMenu(self):
        return [(uiutil.MenuLabel('UI/Agents/Commands/ReadDetails'), self.OpenDetails), (uiutil.MenuLabel('UI/Agents/Commands/StartConversationWith', {'agentID': self.sr.node.agentID}), self.Convo)]


class VirtualResearchEntry(VirtualBaseMissionEntry):
    __guid__ = 'listentry.VirtualResearchEntry'

    def Load(self, node):
        self.sr.node = node
        self.sr.label.text = node.label

    def ShowInfo(self):
        sm.GetService('info').ShowInfo(cfg.eveowners.Get(self.sr.node.agentID).typeID, self.sr.node.agentID)

    def Convo(self):
        sm.GetService('agents').InteractWith(self.sr.node.agentID)

    def GetMenu(self):
        return sm.GetService('menu').CharacterMenu(self.sr.node.agentID)
