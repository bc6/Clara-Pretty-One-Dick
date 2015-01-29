#Embedded file name: eve/devtools/script\svc_dgmattr.py
import sys
import uiutil
import triui
import listentry
import util
import carbonui.const as uiconst
import uicontrols
import uiprimitives
from service import ROLE_GMH, ROLE_PROGRAMMER

class AttrEntry(listentry.Generic):
    __guid__ = 'listentry.DgmAttrEntry'

    def OnDblClick(self, *args):
        self.ShowAttribute()

    def GetMenu(self):
        n = self.sr.node
        ret = [('View Details', self.ShowAttribute, ())]
        if eve.session.role & ROLE_PROGRAMMER:
            ret.append(('Change Attribute', sm.StartService('menu').SetDogmaAttribute, (n.itemID, n.attributeName, n.actualValue)))
        return ret

    def ShowAttribute(self):
        n = self.sr.node
        n.ShowAttribute(n.attributeID)


class AttributeInspector(uicontrols.Window):
    __guid__ = 'form.AttributeInspector'
    default_windowID = 'AttributeInspector'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        itemID = attributes.itemID
        typeID = attributes.typeID
        self.itemID = itemID
        self.typeID = typeID
        self.stateManager = sm.GetService('godma').GetStateManager()
        self.SetCaption('Attribute Inspector')
        self.SetWndIcon(None)
        self.SetTopparentHeight(0)
        main = uiprimitives.Container(name='main', parent=uiutil.GetChild(self, 'main'), pos=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        top = uiprimitives.Container(name='top', parent=main, height=20, align=uiconst.TOTOP)
        btn = uicontrols.Button(parent=top, label='Refresh', align=uiconst.TORIGHT, func=self.Refresh)

        def _OnChange(text):
            ntext = filter('0123456789'.__contains__, text)
            if ntext != text:
                self.input.SetValue(ntext)

        self.input = uicontrols.SinglelineEdit(name='itemID', parent=top, width=-1, height=-1, align=uiconst.TOALL)
        self.input.readonly = not eve.session.role & ROLE_GMH
        self.input.OnReturn = self.Refresh
        self.input.OnChange = _OnChange
        self.input.SetValue(str(self.itemID))
        uiprimitives.Container(name='div', parent=main, height=5, align=uiconst.TOTOP)
        self.scroll = uicontrols.Scroll(parent=main)
        self.Refresh()

    def Refresh(self, *args):
        itemID = int(self.input.GetValue())
        if itemID != self.itemID or not self.typeID:
            self.itemID = itemID
            self.typeID = None
            if eve.session.stationid:
                m = util.Moniker('i2', (eve.session.stationid, const.groupStation))
            else:
                m = util.Moniker('i2', (eve.session.solarsystemid2, const.groupSolarSystem))
            if m.IsPrimed(self.itemID):
                self.typeID = m.GetItem(self.itemID).typeID
        contentList = []
        if self.typeID:
            d = sm.GetService('info').GetAttributeDictForType(self.typeID)
            a = self.stateManager.attributesByID
            for id, baseValue in d.iteritems():
                attrName = a[id].attributeName
                try:
                    actualValue = self.stateManager.GetAttribute(self.itemID, attrName)
                except:
                    sys.exc_clear()
                    actualValue = 'Unknown'

                contentList.append(listentry.Get('DgmAttrEntry', {'label': u'%s<t>%s<t>%s<t>%s' % (id,
                           attrName,
                           actualValue,
                           baseValue),
                 'attributeID': id,
                 'attributeName': attrName,
                 'actualValue': actualValue,
                 'baseValue': baseValue,
                 'ShowAttribute': self.ShowAttribute,
                 'itemID': self.itemID}))

        self.scroll.Load(contentList=contentList, headers=['ID',
         'Name',
         'Client',
         'Base'], fixedEntryHeight=18)
        self.scroll.Sort('Name')

    def GetDogmaLM(self):
        return self.stateManager.GetDogmaLM()

    def ShowAttribute(self, attributeID):
        attrName = self.stateManager.attributesByID[attributeID].attributeName
        try:
            val = self.stateManager.GetAttribute(self.itemID, attrName)
        except:
            sys.exc_clear()
            val = 'Unknown'

        x = self.GetDogmaLM().LogAttribute(self.itemID, attributeID, 'Value on client was %s.' % val)
        x = ['Base value: %s' % x[3].split(':')[1],
         'Client value: %s' % val,
         'Server value: %s' % x[2].split(':')[1],
         ''] + x[4:]
        sm.GetService('gameui').MessageBox('<br>'.join(x), 'Attribute Info: %s' % attrName, buttons=uiconst.OK, icon=triui.INFO)
