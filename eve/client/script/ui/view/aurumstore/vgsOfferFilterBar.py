#Embedded file name: eve/client/script/ui/view/aurumstore\vgsOfferFilterBar.py
from carbonui.primitives.container import Container
from eve.client.script.ui.util.uiComponents import Component, ToggleButtonEffect
from eve.client.script.ui.view.aurumstore.vgsUiConst import TAG_TEXT_COLOR, TAG_TEXT_OFF_COLOR
from eve.client.script.ui.view.aurumstore.vgsUiPrimitives import VgsLabelSubCategories, TAG_TEXT_PADDING
import localization
import uthread
from carbonui import const as uiconst
TAG_SORT_ORDER = [15,
 16,
 20,
 19,
 17,
 18]

def BiasedSortKey(tag):
    if tag.id in TAG_SORT_ORDER:
        return unicode(TAG_SORT_ORDER.index(tag.id))


@Component(ToggleButtonEffect(bgElementFunc=lambda parent, _: parent.label, opacityHover=0.7, opacityMouseDown=1.0, opacityIdle=0.0, audioOnEntry='store_menuhover', audioOnClick='store_click'))

class FilterButton(Container):
    default_state = uiconst.UI_NORMAL
    default_padding = (0, 2, 0, 4)

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.tagId = attributes.tagId
        self.label = VgsLabelSubCategories(text=attributes.label, parent=self, align=uiconst.CENTER, state=uiconst.UI_DISABLED, color=TAG_TEXT_COLOR)
        VgsLabelSubCategories(text=attributes.label, parent=self, align=uiconst.CENTER, state=uiconst.UI_DISABLED, color=TAG_TEXT_OFF_COLOR)
        self.width = self.label.actualTextWidth + 2 * TAG_TEXT_PADDING
        self.onClick = attributes.onClick

    def OnClick(self):
        self.onClick(self.tagId)


def SortTags(tags):
    return localization.util.Sort(tags, key=BiasedSortKey)


class VgsOfferFilterBar(Container):
    default_name = 'VgsOfferFilterBar'
    default_align = uiconst.TOALL
    default_padding = (0, 2, 0, 4)

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.onFilterChanged = attributes.onFilterChanged
        self.filterButtons = []

    def SetTags(self, tags, activeTags = set()):
        self.Flush()
        self.filterButtons = []
        tags = localization.util.Sort(tags, key=BiasedSortKey, reverse=True)
        for tag in tags:
            button = FilterButton(parent=self, label=tag.name, tagId=tag.id, align=uiconst.TORIGHT, onClick=self.OnClickTagFilter, isActive=tag.id in activeTags, top=-1)
            self.filterButtons.append(button)

    def OnClickTagFilter(self, tagId):
        for button in self.filterButtons:
            if button.tagId != tagId:
                button.SetActive(False)

        uthread.new(self.onFilterChanged)

    def GetSelectedFilterTagIds(self):
        return {button.tagId for button in self.filterButtons if button.isActive}
