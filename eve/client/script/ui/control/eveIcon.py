#Embedded file name: eve/client/script/ui/control\eveIcon.py
import types
from carbonui.primitives.container import Container
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.control.eveFrame import Frame
import uiprimitives
import carbonui.const as uiconst
import log
import util
import trinity
import uthread
from utillib import KeyVal
IN_ICONS = {500001: 'ui_19_128_1',
 500002: 'ui_19_128_2',
 500004: 'ui_19_128_3',
 500003: 'ui_19_128_4'}
IN_CORP_ICONS = {500005: 'corps_39_128_3',
 500006: 'corps_26_128_3',
 500007: 'corps_44_128_4',
 500008: 'corps_45_128_3',
 500009: 'corps_27_128_2',
 500010: 'corps_28_128_3',
 500011: 'corps_45_128_2',
 500012: 'corps_19_128_3',
 500013: 'corps_3_128_2',
 500014: 'corps_27_128_4',
 500015: 'corps_44_128_3',
 500016: 'corps_14_128_1',
 500017: 'corps_36_128_2',
 500018: 'corps_34_128_2',
 500019: 'corps_44_128_2',
 500020: 'corps_45_128_1',
 500024: 'corps_48_128_1'}
IN_SMALL_ICONS = {500001: 'ui_75_32_1',
 500002: 'ui_75_32_2',
 500004: 'ui_75_32_3',
 500003: 'ui_75_32_4',
 500005: 'ui_75_32_5',
 500006: 'ui_75_32_6',
 500007: 'ui_75_32_7',
 500008: 'ui_75_32_8',
 500009: 'ui_75_32_9',
 500010: 'ui_75_32_10',
 500011: 'ui_75_32_11',
 500012: 'ui_75_32_20',
 500013: 'ui_75_32_12',
 500014: 'ui_75_32_13',
 500015: 'ui_75_32_14',
 500016: 'ui_75_32_15',
 500017: 'ui_75_32_16',
 500018: 'ui_75_32_17',
 500019: 'ui_75_32_18',
 500020: 'ui_75_32_19'}
RACE_ICONS = {const.raceCaldari: 'ui_88_128_1',
 const.raceMinmatar: 'ui_88_128_2',
 const.raceAmarr: 'ui_88_128_4',
 const.raceGallente: 'ui_88_128_3'}
CORP_ICONS = {1000002: 'corps_7_128_4',
 1000050: 'corps_41_128_3',
 1000051: 'corps_22_128_2',
 1000052: 'corps_22_128_1',
 1000053: 'corps_23_128_1',
 1000054: 'corps_22_128_4',
 1000055: 'corps_21_128_2',
 1000056: 'corps_23_128_2',
 1000057: 'corps_21_128_3',
 1000058: 'corps_23_128_3',
 1000059: 'corps_21_128_4',
 1000068: 'corps_18_128_3',
 1000060: 'corps_22_128_3',
 1000061: 'corps_23_128_4',
 1000062: 'corps_21_128_1',
 1000063: 'corps_14_128_3',
 1000064: 'corps_15_128_2',
 1000065: 'corps_14_128_2',
 1000066: 'corps_19_128_4',
 1000067: 'corps_16_128_1',
 1000069: 'corps_17_128_2',
 1000070: 'corps_19_128_1',
 1000079: 'corps_14_128_4',
 1000080: 'corps_17_128_1',
 1000071: 'corps_17_128_4',
 1000072: 'corps_16_128_2',
 1000073: 'corps_13_128_2',
 1000074: 'corps_15_128_4',
 1000075: 'corps_17_128_3',
 1000076: 'corps_13_128_3',
 1000077: 'corps_39_128_4',
 1000078: 'corps_18_128_4',
 1000082: 'corps_16_128_3',
 1000083: 'corps_15_128_1',
 1000084: 'corps_16_128_4',
 1000085: 'corps_18_128_1',
 1000086: 'corps_12_128_1',
 1000087: 'corps_13_128_1',
 1000088: 'corps_12_128_3',
 1000089: 'corps_12_128_2',
 1000090: 'corps_12_128_4',
 1000091: 'corps_15_128_3',
 1000092: 'corps_13_128_4',
 1000081: 'corps_18_128_2',
 1000093: 'corps_19_128_2',
 1000094: 'corps_33_128_1',
 1000095: 'corps_33_128_3',
 1000096: 'corps_26_128_1',
 1000097: 'corps_31_128_3',
 1000098: 'corps_28_128_2',
 1000099: 'corps_27_128_3',
 1000100: 'corps_34_128_3',
 1000101: 'corps_32_128_3',
 1000102: 'corps_29_128_4',
 1000103: 'corps_25_128_4',
 1000114: 'corps_25_128_1',
 1000104: 'corps_25_128_2',
 1000105: 'corps_38_128_2',
 1000106: 'corps_25_128_3',
 1000107: 'corps_31_128_2',
 1000108: 'corps_32_128_1',
 1000109: 'corps_32_128_4',
 1000110: 'corps_33_128_2',
 1000111: 'corps_30_128_1',
 1000112: 'corps_31_128_4',
 1000113: 'corps_32_128_2',
 1000124: 'corps_24_128_3',
 1000125: 'corps_26_128_3',
 1000115: 'corps_39_128_1',
 1000116: 'corps_30_128_2',
 1000117: 'corps_30_128_4',
 1000118: 'corps_29_128_1',
 1000119: 'corps_29_128_2',
 1000120: 'corps_29_128_3',
 1000121: 'corps_30_128_3',
 1000122: 'corps_31_128_1',
 1000123: 'corps_35_128_2',
 1000134: 'corps_19_128_3',
 1000135: 'corps_38_128_1',
 1000136: 'corps_24_128_2',
 1000126: 'corps_35_128_3',
 1000127: 'corps_28_128_3',
 1000128: 'corps_34_128_2',
 1000129: 'corps_27_128_4',
 1000130: 'corps_14_128_1',
 1000131: 'corps_36_128_2',
 1000132: 'corps_3_128_4',
 1000133: 'corps_24_128_1',
 1000137: 'corps_4_128_1',
 1000138: 'corps_24_128_4',
 1000139: 'corps_35_128_4',
 1000140: 'corps_40_128_2',
 1000141: 'corps_28_128_4',
 1000142: 'corps_40_128_4',
 1000143: 'corps_26_128_4',
 1000144: 'corps_26_128_2',
 1000145: 'corps_27_128_1',
 1000146: 'corps_28_128_1',
 1000147: 'corps_27_128_2',
 1000148: 'corps_3_128_2',
 1000149: 'corps_40_128_3',
 1000150: 'corps_39_128_3',
 1000151: 'corps_11_128_4',
 1000152: 'corps_11_128_2',
 1000153: 'corps_11_128_3',
 1000154: 'corps_35_128_1',
 1000155: 'corps_41_128_1',
 1000156: 'corps_11_128_1',
 1000157: 'corps_33_128_4',
 1000158: 'corps_40_128_1',
 1000159: 'corps_36_128_3',
 1000160: 'corps_36_128_1',
 1000161: 'corps_34_128_4',
 1000162: 'corps_34_128_1',
 1000163: 'corps_36_128_4',
 1000164: 'corps_41_128_2',
 1000003: 'corps_1_128_3',
 1000004: 'corps_8_128_1',
 1000005: 'corps_1_128_4',
 1000006: 'corps_4_128_4',
 1000007: 'corps_38_128_3',
 1000008: 'corps_39_128_2',
 1000009: 'corps_3_128_3',
 1000010: 'corps_3_128_1',
 1000011: 'corps_6_128_2',
 1000012: 'corps_10_128_4',
 1000013: 'corps_9_128_4',
 1000014: 'corps_7_128_2',
 1000015: 'corps_1_128_1',
 1000016: 'corps_5_128_4',
 1000017: 'corps_2_128_4',
 1000018: 'corps_5_128_3',
 1000019: 'corps_6_128_1',
 1000020: 'corps_2_128_1',
 1000021: 'corps_2_128_3',
 1000022: 'corps_5_128_2',
 1000023: 'corps_9_128_1',
 1000024: 'corps_7_128_3',
 1000025: 'corps_10_128_3',
 1000026: 'corps_8_128_4',
 1000027: 'corps_9_128_2',
 1000028: 'corps_9_128_3',
 1000029: 'corps_4_128_2',
 1000030: 'corps_5_128_1',
 1000031: 'corps_8_128_2',
 1000032: 'corps_7_128_1',
 1000033: 'corps_8_128_3',
 1000034: 'corps_4_128_3',
 1000035: 'corps_37_128_3',
 1000036: 'corps_1_128_2',
 1000037: 'corps_2_128_2',
 1000038: 'corps_6_128_3',
 1000039: 'corps_37_128_2',
 1000040: 'corps_37_128_1',
 1000041: 'corps_38_128_4',
 1000042: 'corps_6_128_4',
 1000043: 'corps_37_128_4',
 1000044: 'corps_10_128_1',
 1000045: 'corps_10_128_2',
 1000046: 'corps_20_128_3',
 1000047: 'corps_20_128_1',
 1000048: 'corps_20_128_4',
 1000049: 'corps_20_128_2',
 1000165: 'corps_43_128_1',
 1000166: 'corps_42_128_3',
 1000167: 'corps_42_128_1',
 1000168: 'corps_42_128_4',
 1000169: 'corps_41_128_4',
 1000170: 'corps_43_128_2',
 1000171: 'corps_43_128_3',
 1000172: 'corps_43_128_4',
 1000173: 'corps_44_128_1',
 1000178: 'corps_45_128_4',
 1000179: 'corps_47_128_1',
 1000180: 'corps_47_128_2',
 1000181: 'corps_47_128_3',
 1000182: 'corps_47_128_4',
 109299958: 'corps_46_128_1',
 1000177: 'corps_45_128_4',
 1000193: 'res:/ui/texture/Corps/arkombine.png',
 1000197: 'res:/UI/Texture/Corps/templis_dragonaurs.png',
 1000198: 'res:/UI/Texture/Corps/imperial_guard.png',
 1000205: 'res:/ui/texture/Corps/amarr_templars.png',
 1000206: 'res:/UI/Texture/Corps/royal_uhlans.png',
 1000207: 'res:/UI/Texture/Corps/bragian_order.png',
 1000208: 'res:/UI/Texture/Corps/zumari_force_projection.png',
 1000213: 'res:/UI/Texture/Corps/osmon_surveillance.png',
 1000214: 'res:/UI/Texture/Corps/seituoda_taskforce.png',
 1000215: 'res:/ui/texture/Corps/algintal_core.png',
 1000216: 'res:/UI/Texture/Corps/crux_special_tasks_group.png',
 1000217: 'res:/UI/Texture/Corps/villore_sec_ops.png',
 1000218: 'res:/UI/Texture/Corps/circle_of_huskarl.png',
 1000219: 'res:/UI/Texture/Corps/tronhadar_free_guard.png',
 1000220: 'res:/UI/Texture/Corps/sanmatar_kelkoons.png',
 1000270: 'res:/UI/Texture/Corps/outer_ring_development.png',
 1000271: 'res:/UI/Texture/Corps/outer_ring_prospecting.png',
 1000222: 'res:/UI/Texture/Corps/default.png',
 1000223: 'res:/UI/Texture/Corps/default.png',
 1000224: 'res:/UI/Texture/Corps/default.png',
 1000225: 'res:/UI/Texture/Corps/default.png',
 1000226: 'res:/UI/Texture/Corps/default.png',
 1000227: 'res:/UI/Texture/Corps/default.png',
 1000228: 'res:/UI/Texture/Corps/default.png',
 1000229: 'res:/UI/Texture/Corps/default.png',
 1000230: 'res:/UI/Texture/Corps/default.png',
 1000231: 'res:/UI/Texture/Corps/default.png',
 1000232: 'res:/UI/Texture/Corps/default.png',
 1000233: 'res:/UI/Texture/Corps/default.png',
 1000234: 'res:/UI/Texture/Corps/default.png',
 1000235: 'res:/UI/Texture/Corps/default.png',
 1000236: 'res:/UI/Texture/Corps/default.png',
 1000237: 'res:/UI/Texture/Corps/default.png',
 1000238: 'res:/UI/Texture/Corps/default.png',
 1000239: 'res:/UI/Texture/Corps/default.png',
 1000240: 'res:/UI/Texture/Corps/default.png',
 1000243: 'res:/UI/Texture/Corps/default.png',
 1000244: 'res:/UI/Texture/Corps/default.png',
 1000245: 'res:/UI/Texture/Corps/default.png',
 1000246: 'res:/UI/Texture/Corps/default.png',
 1000247: 'res:/UI/Texture/Corps/default.png',
 1000248: 'res:/UI/Texture/Corps/default.png',
 1000249: 'res:/UI/Texture/Corps/default.png',
 1000250: 'res:/UI/Texture/Corps/default.png',
 1000251: 'res:/UI/Texture/Corps/default.png',
 1000252: 'res:/UI/Texture/Corps/default.png',
 1000253: 'res:/UI/Texture/Corps/default.png',
 1000254: 'res:/UI/Texture/Corps/default.png',
 1000255: 'res:/UI/Texture/Corps/default.png',
 1000256: 'res:/UI/Texture/Corps/default.png',
 1000257: 'res:/UI/Texture/Corps/default.png',
 1000258: 'res:/UI/Texture/Corps/default.png',
 1000259: 'res:/UI/Texture/Corps/default.png',
 1000261: 'res:/UI/Texture/Corps/state_peacekeepers.png',
 1000262: 'res:/UI/Texture/Corps/federal_marines.png',
 1000263: 'res:/UI/Texture/Corps/republic_command.png',
 1000274: 'res:/UI/Texture/Corps/48_128_1.png'}

class Icon(uiprimitives.Sprite):
    """
    DEPRICATED: Use Sprite instead with full texture path
    Eve specific icon that knows how to deal with silly icon paths.
    Evaluated in the following order:
    icon or typeID or graphicID 
    """
    __guid__ = 'uicontrols.Icon'
    size_doc = 'Optional icon pixel size. Will override width and height with size.'
    typeID_doc = 'Optional param to override the icon path.  Will get a type based icon instead.'
    itemID_doc = "Optional param for char portraits or 'location' icons. Used with typeID."
    graphicID_doc = 'Optional param to get icon based on standard graphic record.'
    default_size = None
    default_typeID = None
    default_graphicID = None
    default_itemID = None
    default_icon = None
    default_ignoreSize = 0
    default_rect = None
    default_name = 'icon'
    default_left = 0
    default_top = 0
    default_width = 0
    default_height = 0

    def ApplyAttributes(self, attributes):
        """
        add in special cases for non-core icon path types
        supports:
        - nu style ui_44_16_2
        - oldstyle iconpath: 44_2
        - corp, alliance, icons roots
        """
        if attributes.__gotShape__ and len(attributes.keys()) == 1:
            return
        for each in ('iconID', 'path'):
            if each in attributes:
                log.LogInfo('Someone creating icon with', each, 'as keyword', attributes.Get(each, 'None'))

        size = attributes.get('size', self.default_size)
        if attributes.get('align', self.default_align) != uiconst.TOALL:
            if size:
                attributes.width = attributes.height = size
        else:
            attributes.pos = (0, 0, 0, 0)
            attributes.width = attributes.height = 0
        icon = attributes.get('icon', self.default_icon)
        if 'icon' in attributes:
            del attributes['icon']
        uiprimitives.Sprite.ApplyAttributes(self, attributes)
        ignoreSize = attributes.get('ignoreSize', self.default_ignoreSize)
        self.typeID = attributes.get('typeID', self.default_typeID)
        self.itemID = attributes.get('itemID', self.default_itemID)
        graphicID = attributes.get('graphicID', self.default_graphicID)
        isCopy = attributes.get('isCopy', False)
        if icon:
            self.LoadIcon(icon, ignoreSize=ignoreSize)
        elif self.typeID:
            self.LoadIconByTypeID(self.typeID, itemID=self.itemID, size=size, ignoreSize=ignoreSize, isCopy=isCopy)
        elif graphicID:
            self.LoadIconByGraphicID(graphicID, ignoreSize=ignoreSize)
        else:
            self.LoadTexture('res:/UI/Texture/None.dds')
        onClick = attributes.get('OnClick', None)
        if onClick:
            self.OnClick = onClick

    def LoadIconByGraphicID(self, graphicID, ignoreSize = False):
        graphic = cfg.icons.Get(graphicID)
        if graphic and graphic.iconFile:
            iconFile = graphic.iconFile.strip()
            self.LoadIcon(iconFile, ignoreSize)

    def LoadIcon(self, icon, ignoreSize = False):
        if not icon:
            return
        if type(icon) == types.IntType:
            return self.LoadIconByGraphicID(icon, ignoreSize=ignoreSize)
        icon = uiprimitives.Sprite.LoadIcon(self, icon, ignoreSize)
        if icon is not None:
            fullPathData = self.ConvertIconNoToResPath(icon)
            if fullPathData:
                resPath, iconSize = fullPathData
                self.LoadTexture(resPath)
                if not ignoreSize and self.GetAlign() != uiconst.TOALL and self.texture.atlasTexture:
                    self.width = iconSize
                    self.height = iconSize

    def LoadIconByTypeID(self, typeID, itemID = None, size = None, ignoreSize = False, isCopy = False):
        self.typeID = typeID
        sm.GetService('photo').GetIconByType(self, typeID, itemID=itemID, size=size, ignoreSize=ignoreSize, isCopy=isCopy)

    @staticmethod
    def ConvertIconNoToResPath(iconNo):
        resPath = None
        if iconNo.startswith('res:'):
            return (iconNo, 0)
        parts = iconNo.split('_')
        if len(parts) == 2:
            sheet, iconNum = parts
            iconSize = GetIconSize(sheet)
            resPath = 'res:/ui/texture/icons/%s_%s_%s.png' % (int(sheet), int(iconSize), int(iconNum))
        elif iconNo.startswith('ui_'):
            u, sheet, iconSize, iconNum = parts
            iconSize = int(iconSize)
            resPath = 'res:/ui/texture/icons/%s_%s_%s.png' % (int(sheet), int(iconSize), int(iconNum))
        elif iconNo.startswith('corps_'):
            resPath = 'res:/ui/texture/corps/' + iconNo[6:] + '.png'
            iconSize = 128
        elif iconNo.startswith('alliance_'):
            resPath = 'res:/ui/texture/alliance/' + iconNo[9:] + '.png'
            iconSize = 128
        elif iconNo.startswith('c_'):
            c, sheet, iconNum = parts
            resPath = 'res:/ui/texture/corps/%s_128_%s.png' % (int(sheet), int(iconNum))
            iconSize = 128
        elif iconNo.startswith('a_'):
            a, sheet, iconNum = parts
            resPath = 'res:/ui/texture/alliance/%s_128_%s.png' % (int(sheet), int(iconNum))
            iconSize = 128
        if resPath:
            return (resPath, iconSize)
        log.LogWarn('Icon: MISSING CONVERSION HANDLING FOR', iconNo)


class DraggableIcon(uiprimitives.Container):
    """
    The same as a normal eve Icon except based on icon_draggable.blue template
    This is a bit of a hack where we throw out the old icon element and replace it
    with an eve Icon.
    
    all the parameters except for pos are passed to the eve icon
    """
    __guid__ = 'uicls.DraggableIcon'
    default_name = 'draggableIcon'
    default_opacity = 1.0

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.sr.dot = Frame(parent=self, name='baseFrame', state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/Shared/buttonDOT.png', color=(1.0, 1.0, 1.0, 1.0), cornerSize=8, spriteEffect=trinity.TR2_SFX_DOT, blendMode=trinity.TR2_SBM_ADD)
        self.sr.icon = Icon(parent=self, name='icon', align=uiconst.TOALL)
        self.sr.shadow = Frame(parent=self, offset=-9, cornerSize=13, name='shadow', state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/Shared/bigButtonShadow.png')
        self.ChangeIcon(**attributes)

    def ChangeIcon(self, typeID = None, itemID = None, icon = None, isCopy = False, **kw):
        if icon:
            self.sr.icon.LoadIcon(icon, ignoreSize=True)
        elif typeID:
            self.sr.icon.LoadIconByTypeID(typeID, itemID=itemID, ignoreSize=True, isCopy=isCopy)

    def LoadIcon(self, icon, *args, **kwds):
        self.ChangeIcon(icon=icon)

    def LoadIconByTypeID(self, typeID, itemID = None, isCopy = False, *args, **kwds):
        self.ChangeIcon(typeID=typeID, itemID=itemID, isCopy=isCopy)


class LogoIcon(Icon):
    """
    Knows how to figure out logos for factions, corps and alliances
    """
    __guid__ = 'uicls.LogoIcon'
    default_isSmall = None
    default_isSmall_doc = 'Should we use the small version for faction icons.'
    default_align = uiconst.RELATIVE

    def ApplyAttributes(self, attributes):
        itemID = attributes.get('itemID', None)
        icon = None
        if itemID is not None:
            if util.IsCorporation(itemID):
                if CheckCorpID(itemID):
                    icon = CORP_ICONS[itemID]
                else:
                    raise ValueError, 'LogoIcon class does not support custom corp icons.  Use CorpIcon for that'
            elif util.IsAlliance(itemID):
                raise ValueError, 'LogoIcon class does not support Alliance Logos.  Use GetLogoIcon or GetOwnerIcon'
            elif util.IsFaction(itemID):
                isSmall = attributes.get('isSmall', self.default_isSmall)
                icon = self.GetFactionIconID(itemID, isSmall)
            elif itemID in RACE_ICONS:
                icon = RACE_ICONS[itemID]
        if icon is None:
            icon = 'ui_1_16_256'
        attributes['icon'] = icon
        Icon.ApplyAttributes(self, attributes)

    @staticmethod
    def GetFactionIconID(factionID, isSmall = default_isSmall):
        """Get the iconID for a specifice factionID and size (small or not)"""
        if isSmall and factionID in IN_SMALL_ICONS:
            return IN_SMALL_ICONS.get(factionID)
        elif factionID in IN_ICONS:
            return IN_ICONS.get(factionID)
        elif factionID in IN_CORP_ICONS:
            return IN_CORP_ICONS.get(factionID)
        else:
            return None

    @staticmethod
    def GetFactionIconTexturePath(factionID, isSmall = True):
        iconNo = LogoIcon.GetFactionIconID(factionID, isSmall)
        texturePath, _ = Icon.ConvertIconNoToResPath(iconNo)
        return texturePath


class CorpIcon(uiprimitives.Container):
    __guid__ = 'uicls.CorpIcon'
    isDragObject = True
    default_left = 0
    default_top = 0
    default_width = 128
    default_height = 128
    default_size = None
    size_doc = 'Optional icon pixel size. Will override width and height with size.'
    default_name = 'corplogo'
    default_state = uiconst.UI_DISABLED
    default_align = uiconst.TOPLEFT

    def ApplyAttributes(self, attributes):
        if attributes.get('align', self.default_align) != uiconst.TOALL:
            size = attributes.get('size', self.default_size)
            if size:
                attributes.width = attributes.height = size
        else:
            attributes.pos = (0, 0, 0, 0)
            attributes.width = attributes.height = 0
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.colorIDs = [None, None, None]
        self.shapeIDs = [None, None, None]
        sprite1 = uiprimitives.Sprite(parent=self, name='layerTopSampl', align=uiconst.TOALL, state=uiconst.UI_DISABLED, color=(1.0, 1.0, 1.0, 0.0))
        sprite2 = uiprimitives.Sprite(parent=self, name='layerTopSampl', align=uiconst.TOALL, state=uiconst.UI_DISABLED, color=(1.0, 1.0, 1.0, 0.0))
        sprite3 = uiprimitives.Sprite(parent=self, name='layerTopSampl', align=uiconst.TOALL, state=uiconst.UI_DISABLED, color=(1.0, 1.0, 1.0, 0.0))
        corpID = attributes.get('corpID', None)
        if attributes.dontUseThread:
            self.DoLayout(corpID, attributes)
        else:
            uthread.new(self.DoLayout, corpID, attributes)

    def DoLayout(self, corpID, attributes):
        big = attributes.get('big', False)
        onlyValid = attributes.get('onlyValid', False)
        logoData = attributes.get('logoData', None)
        if corpID in CORP_ICONS:
            return CORP_ICONS[corpID]
        if logoData is None:
            if not corpID:
                return
            logoData = cfg.corptickernames.Get(corpID)
        if logoData:
            log.LogInfo('LogoIcon.GetCorpIconID', 'corpID:', corpID, 'shape1:', logoData.shape1, 'shape2:', logoData.shape2, 'shape3:', logoData.shape3, 'color1:', logoData.color1, 'color2:', logoData.color2, 'color3:', logoData.color3)
            shapeIDs = (logoData.shape1, logoData.shape2, logoData.shape3)
            colorIDs = (logoData.color1, logoData.color2, logoData.color3)
            for i in xrange(3):
                shapeID = shapeIDs[i]
                colorID = colorIDs[i]
                if shapeID is not None and shapeID == int(shapeID):
                    self.SetLayerShapeAndColor(i, shapeID, colorID, big)

        elif onlyValid:
            raise RuntimeError('not valid corpID')

    def SetLayerShapeAndColor(self, layerNum, shapeID = None, colorID = None, isBig = False):
        """
            layerNum: [0,2], shapeID: [415, 577], colorID: [671, 685]
        """
        if self.destroyed:
            return
        layer = self.children[layerNum]
        if shapeID is None:
            shapeID = self.shapeIDs[layerNum]
        else:
            self.shapeIDs[layerNum] = shapeID
        if colorID is None:
            colorID = self.colorIDs[layerNum]
        else:
            self.colorIDs[layerNum] = colorID
        texturePath = const.graphicCorpLogoLibShapes.get(shapeID, const.graphicCorpLogoLibShapes[const.graphicCorpLogoLibNoShape])
        if isBig:
            texturePath = '%s/large/%s' % tuple(texturePath.rsplit('/', 1))
        if colorID is not None and colorID == int(colorID):
            color, blendMode = const.graphicCorpLogoLibColors.get(colorID, (1.0, 1.0, 1.0, 1.0))
        else:
            color, blendMode = (1.0, 1.0, 1.0, 1.0), const.CORPLOGO_BLEND
        if blendMode == const.CORPLOGO_BLEND:
            layer.SetTexturePath(texturePath)
            layer.SetSecondaryTexturePath(None)
            layer.spriteEffect = trinity.TR2_SFX_COPY
            layer.SetRGB(*color)
        elif blendMode == const.CORPLOGO_SOLID:
            layer.SetTexturePath('res:/UI/Texture/fill.dds')
            layer.SetSecondaryTexturePath(texturePath)
            layer.spriteEffect = trinity.TR2_SFX_MASK
            layer.SetRGB(*color)
        elif blendMode == const.CORPLOGO_GRADIENT:
            layer.SetTexturePath('res:/UI/Texture/corpLogoLibs/%s.png' % colorID)
            layer.SetSecondaryTexturePath(texturePath)
            layer.spriteEffect = trinity.TR2_SFX_MASK
            layer.SetRGB(1.0, 1.0, 1.0, 1.0)


def CheckCorpID(corpID):
    return corpID in CORP_ICONS


def GetLogoIcon(itemID = None, **kw):
    if util.IsAlliance(itemID):
        logo = Icon(icon=None, **kw)
        sm.GetService('photo').GetAllianceLogo(itemID, 128, logo)
        return logo
    elif not util.IsCorporation(itemID) or CheckCorpID(itemID):
        return LogoIcon(itemID=itemID, **kw)
    else:
        return CorpIcon(corpID=itemID, **kw)


def GetOwnerLogo(parent, ownerID, size = 64, noServerCall = False, callback = False, orderIfMissing = True):
    """
        Get the logo of an owner (character/corp/alliance/faction)
    """
    if util.IsCharacter(ownerID) or util.IsAlliance(ownerID):
        logo = Icon(icon=None, parent=parent, pos=(0,
         0,
         size,
         size), ignoreSize=True)
        if util.IsAlliance(ownerID):
            path = sm.GetService('photo').GetAllianceLogo(ownerID, 128, logo, callback=callback, orderIfMissing=orderIfMissing)
        else:
            path = sm.GetService('photo').GetPortrait(ownerID, size, logo, callback=callback, orderIfMissing=orderIfMissing)
        return path is not None
    if util.IsCorporation(ownerID) or util.IsFaction(ownerID):
        GetLogoIcon(itemID=ownerID, parent=parent, pos=(0,
         0,
         size,
         size), ignoreSize=True)
    else:
        raise RuntimeError('ownerID %d is not of an owner type!!' % ownerID)
    return True


class PreviewIcon(Icon):
    """Preview icon with a build in preview linky
       arguments:
       - typeID (required)
    """
    __guid__ = 'uicls.PreviewIcon'
    default_size = 16
    default_typeID = None

    def ApplyAttributes(self, attributes):
        typeID = attributes.get('typeID', self.default_typeID)
        icon = 'ui_38_16_89'
        attributes['icon'] = icon
        Icon.ApplyAttributes(self, attributes)
        self.OnClick = (self.Preview, typeID)

    def Preview(self, typeID, *args):
        sm.GetService('preview').PreviewType(typeID)


class MenuIcon(Icon):
    """MenuIcon for the menu options
    """
    __guid__ = 'uicontrols.MenuIcon'
    default_size = 16

    def ApplyAttributes(self, attributes):
        size = attributes.get('size', self.default_size)
        if size <= 16:
            icon = 'ui_73_16_50'
        else:
            icon = 'ui_77_32_49'
        attributes['icon'] = icon
        Icon.ApplyAttributes(self, attributes)
        self.SetAlpha(0.8)
        self.expandOnLeft = 1

    def OnMouseEnter(self, *args):
        self.SetAlpha(1.0)

    def OnMouseExit(self, *args):
        self.SetAlpha(0.8)


class ItemIcon(Container):
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_NORMAL
    default_width = 32
    default_height = 32
    isDragObject = True

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.typeID = attributes.typeID
        self.itemID = attributes.Get('itemID', None)
        self.bpData = attributes.Get('bpData', False)
        self.techIcon = Sprite(name='techIcon', parent=self, width=16, height=16)
        self.icon = Icon(parent=self, align=uiconst.TOALL, state=uiconst.UI_DISABLED)
        self.SetTypeID(self.typeID, self.bpData)

    def SetTypeID(self, typeID, bpData = None):
        self.typeID = typeID
        self.bpData = bpData
        self.icon.LoadIconByTypeID(typeID, ignoreSize=True, isCopy=self.IsBlueprintCopy())
        from eve.client.script.ui.util.uix import GetTechLevelIconPathAndHint
        texturePath, hint = GetTechLevelIconPathAndHint(typeID)
        if texturePath:
            self.techIcon.texturePath = texturePath
            self.techIcon.hint = hint
            self.techIcon.Show()
        else:
            self.techIcon.Hide()

    def IsBlueprintCopy(self):
        if not self.bpData:
            return False
        return not self.bpData.original

    def GetMenu(self):
        return sm.GetService('menu').GetMenuFormItemIDTypeID(self.itemID, self.typeID, ignoreMarketDetails=0, abstractInfo=KeyVal(bpData=self.bpData))

    def OnClick(self):
        sm.GetService('info').ShowInfo(self.typeID, self.itemID, abstractinfo=KeyVal(bpData=self.bpData))

    def GetHint(self):
        return cfg.invtypes.Get(self.typeID).description

    def GetDragData(self):
        return [KeyVal(__guid__='uicls.GenericDraggableForTypeID', typeID=self.typeID, label=cfg.invtypes.Get(self.typeID).name, bpData=self.bpData)]


def GetIconSize(sheetNum):
    sheetNum = int(sheetNum)
    one = [90,
     91,
     92,
     93]
    two = [17,
     18,
     19,
     28,
     29,
     32,
     33,
     59,
     60,
     61,
     65,
     66,
     67,
     80,
     85,
     86,
     87,
     88,
     89,
     102,
     103,
     104]
    eight = [22,
     44,
     75,
     77,
     105,
     112]
    sixteen = [38, 73]
    if sheetNum in one:
        return 256
    if sheetNum in two:
        return 128
    if sheetNum in eight:
        return 32
    if sheetNum in sixteen:
        return 16
    return 64


exports = {'uiutil.GetLogoIcon': GetLogoIcon,
 'uiutil.CheckCorpID': CheckCorpID,
 'uiutil.GetOwnerLogo': GetOwnerLogo,
 'uix.GetIconSize': GetIconSize}
