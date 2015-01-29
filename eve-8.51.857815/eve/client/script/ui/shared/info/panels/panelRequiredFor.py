#Embedded file name: eve/client/script/ui/shared/info/panels\panelRequiredFor.py
from carbonui.primitives.container import Container
from eve.client.script.ui.control.buttons import ToggleButtonGroup
import carbonui.const as uiconst
import localization
import uiutil
from eve.client.script.ui.control.eveScroll import Scroll
import const
import listentry
from eve.client.script.ui.control.listgroup import ListGroup
import uix

class PanelRequiredFor(Container):

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.typeID = attributes.typeID

    def Load(self):
        self.Flush()
        toggleButtonCont = Container(name='btnGroupCont', parent=self, align=uiconst.TOTOP, height=35)
        btnGroup = ToggleButtonGroup(parent=toggleButtonCont, align=uiconst.CENTER, height=toggleButtonCont.height, width=300, padding=(10, 4, 10, 3), callback=self.LoadRequiredForLevel)
        for level in xrange(1, 6):
            hint = localization.GetByLabel('UI/InfoWindow/RequiredForLevelButtonHint', skillName=cfg.invtypes.Get(self.typeID).name, level=level)
            isDisabled = not bool(cfg.GetTypesRequiredBySkill(self.typeID).get(level, None))
            btnGroup.AddButton(btnID=level, label=uiutil.IntToRoman(level), hint=hint, isDisabled=isDisabled)

        self.scroll = Scroll(name='scroll', parent=self, padding=const.defaultPadding)
        btnGroup.SelectFirst()

    def LoadRequiredForLevel(self, level):
        scrolllist = self.GetRequiredForLevelSubContent(self.typeID, level)
        self.scroll.Load(fixedEntryHeight=27, contentList=scrolllist)

    def GetRequiredForLevelSubContent(self, typeID, skillLevel):
        scrolllist = []
        requiredFor = cfg.GetTypesRequiredBySkill(typeID)[skillLevel]
        for marketGroupID in requiredFor:
            marketGroup = cfg.GetMarketGroup(marketGroupID)
            data = {'GetSubContent': self.GetRequiredForLevelGroupSubContent,
             'label': marketGroup.marketGroupName,
             'skillLevel': int(skillLevel),
             'sublevel': 0,
             'showlen': False,
             'typeID': typeID,
             'marketGroupID': marketGroupID,
             'id': ('skillGroups_group', marketGroupID),
             'state': 'locked',
             'iconID': marketGroup.iconID,
             'openByDefault': True}
            scrolllist.append(listentry.Get(decoClass=ListGroup, data=data))

        return scrolllist

    def GetRequiredForLevelGroupSubContent(self, data, *args):
        scrolllist = []
        skillTypeID = data['typeID']
        skillLevel = data['skillLevel']
        skillMarketGroup = data['marketGroupID']
        requiredFor = cfg.GetTypesRequiredBySkill(skillTypeID)[skillLevel][skillMarketGroup]
        if const.metaGroupUnused in requiredFor:
            for typeID in requiredFor[const.metaGroupUnused]:
                typeRec = cfg.invtypes.Get(typeID)
                data = {'label': typeRec.name,
                 'sublevel': 1,
                 'typeID': typeID,
                 'showinfo': True,
                 'getIcon': True}
                scrolllist.append(listentry.Get('Item', data))

        for metaLevel in requiredFor.keys():
            if metaLevel == const.metaGroupUnused:
                continue
            data = {'GetSubContent': self.GetRequiredForLevelGroupMetaSubContent,
             'id': ('skillGroups_Meta', metaLevel),
             'label': cfg.invmetagroups.Get(metaLevel).metaGroupName,
             'groupItems': requiredFor[metaLevel],
             'state': 'locked',
             'sublevel': 1,
             'showicon': uix.GetTechLevelIconID(metaLevel),
             'metaLevel': metaLevel,
             'BlockOpenWindow': True,
             'typeID': skillTypeID,
             'skillLevel': skillLevel,
             'marketGroupID': skillMarketGroup,
             'typeIDs': requiredFor[metaLevel],
             'showlen': False}
            scrolllist.append(listentry.Get('MarketMetaGroupEntry', data))

        return scrolllist

    def GetRequiredForLevelGroupMetaSubContent(self, data):
        skillTypeID = data['typeID']
        skillLevel = data['skillLevel']
        skillMarketGroup = data['marketGroupID']
        metaLevel = data['metaLevel']
        scrolllist = []
        reqFor = cfg.GetTypesRequiredBySkill(skillTypeID)[skillLevel][skillMarketGroup][metaLevel]
        for typeID in reqFor:
            typeRec = cfg.invtypes.Get(typeID)
            data = {'label': typeRec.name,
             'sublevel': 3,
             'typeID': typeID,
             'showinfo': True,
             'getIcon': True}
            scrolllist.append(listentry.Get('Item', data))

        return scrolllist
