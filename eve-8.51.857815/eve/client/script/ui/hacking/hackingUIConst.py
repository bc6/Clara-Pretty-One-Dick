#Embedded file name: eve/client/script/ui/hacking\hackingUIConst.py
"""
UI Constants and util functions for profession minigame 
"""
import util
import hackingcommon.hackingConstants as hackingConst
GRID_X = 86
GRID_Y = 53
GRID_MAX_ROWS = 9
GRID_MAX_COLUMNS = 10
TILE_SIZE = 48
TILE_ICON_SIZE = 64
NEIGHBOR_OFFSETS1 = ((0, -1),
 (1, -1),
 (-1, 0),
 (1, 0),
 (0, 1),
 (1, 1))
NEIGHBOR_OFFSETS2 = ((-1, -1),
 (0, -1),
 (-1, 0),
 (1, 0),
 (-1, 1),
 (0, 1))
EVENTS_SLEEP = {hackingConst.EVENT_HONEYPOT_HEALING: 300}
HINTS_BY_TILE_TYPE = {hackingConst.TYPE_NONE: 'UI/Hacking/UnknownNode',
 hackingConst.TYPE_SEGMENT: 'UI/Hacking/SegmentNode',
 hackingConst.TYPE_VIRUS: 'UI/Hacking/Virus',
 hackingConst.TYPE_CORE: 'UI/Hacking/CoreNode',
 hackingConst.TYPE_DEFENSESOFTWARE: 'UI/Hacking/DefenseNode',
 hackingConst.TYPE_UTILITYELEMENTTILE: 'UI/Hacking/UtilityNode',
 hackingConst.TYPE_DATACACHE: 'UI/Hacking/DataCacheNode'}
DS_HINTS_BY_SUBTYPE = {hackingConst.SUBTYPE_DS_FIREWALL: 'UI/Hacking/FirewallNode',
 hackingConst.SUBTYPE_DS_ANTIVIRUS: 'UI/Hacking/AntiVirusNode',
 hackingConst.SUBTYPE_DS_HONEYPOT_STRENGTH: 'UI/Hacking/HoneyPotStrength',
 hackingConst.SUBTYPE_DS_HONEYPOT_HEALING: 'UI/Hacking/HoneyPotHealing',
 hackingConst.SUBTYPE_DS_DISRUPTOR: '/UI/Hacking/DisruptorNode'}
UE_HINTS_BY_SUBTYPE = {hackingConst.SUBTYPE_UE_KERNALROT: 'UI/Hacking/UtilityKernalRot',
 hackingConst.SUBTYPE_UE_SELFREPAIR: 'UI/Hacking/UtilitySelfRepair',
 hackingConst.SUBTYPE_UE_SECONDARYVECTOR: 'UI/Hacking/UtilitySecondaryVector',
 hackingConst.SUBTYPE_UE_POLYMORPHICSHIELD: 'UI/Hacking/UtilityPolymorphicShield'}
ICONPATH_BY_SUBTYPE = {hackingConst.SUBTYPE_UE_SELFREPAIR: 'res:/UI/Texture/classes/hacking/utilSelfRepair.png',
 hackingConst.SUBTYPE_UE_KERNALROT: 'res:/UI/Texture/classes/hacking/utilKernalRot.png',
 hackingConst.SUBTYPE_UE_SECONDARYVECTOR: 'res:/UI/Texture/classes/hacking/utilSecondVector.png',
 hackingConst.SUBTYPE_UE_POLYMORPHICSHIELD: 'res:/UI/Texture/classes/hacking/utilPolymorphShield.png',
 hackingConst.SUBTYPE_DS_FIREWALL: 'res:/UI/Texture/classes/hacking/defSoftFirewall.png',
 hackingConst.SUBTYPE_DS_ANTIVIRUS: 'res:/UI/Texture/classes/hacking/defSoftAntiVirus.png',
 hackingConst.SUBTYPE_DS_HONEYPOT_STRENGTH: 'res:/UI/Texture/classes/hacking/defSoftHoneyPotStrength.png',
 hackingConst.SUBTYPE_DS_HONEYPOT_HEALING: 'res:/UI/Texture/classes/hacking/defSoftHoneyPotHealing.png',
 hackingConst.SUBTYPE_DS_DISRUPTOR: 'res:/UI/Texture/classes/hacking/defSoftIds.png',
 hackingConst.SUBTYPE_CORE_LOW: 'res:/UI/Texture/classes/hacking/coreLow.png',
 hackingConst.SUBTYPE_CORE_MEDIUM: 'res:/UI/Texture/classes/hacking/coreMedium.png',
 hackingConst.SUBTYPE_CORE_HIGH: 'res:/UI/Texture/classes/hacking/coreHigh.png'}
ICONPATHS_INFECTED = ('res:/UI/Texture/classes/hacking/infected1.png', 'res:/UI/Texture/classes/hacking/infected2.png', 'res:/UI/Texture/classes/hacking/infected3.png', 'res:/UI/Texture/classes/hacking/infected4.png')
LOW_COHERENCE_WARN_LEVEL = 50
COLOR_EXPLORED = (0.588, 0.247, 0.039, 1.0)
COLOR_UNEXPLORED = (0.523, 0.8, 0.758, 1.0)
COLOR_BLOCKED = (0.2, 0.2, 0.2, 1.0)
COlOR_UNREACHABLE = (1.0, 1.0, 1.0, 0.75)
COLOR_UNREACHABLE = (1.0, 1.0, 1.0, 1.0)
COLOR_DEFENSE = (0.298, 0.455, 0.431, 1.0)
COLOR_DEFENSEICON = (0.678, 0.894, 0.847, 1.0)
COLOR_DATACACHE = (1.0, 0.8, 0.3, 1.0)
COLOR_UTILITYELEMENT = (0.953, 0.502, 0.067, 1.0)
COLOR_UTILITYELEMENTICON = (1.0, 0.737, 0.592, 1.0)
COLOR_UEEMPTY_SLOT = (0.8, 0.8, 0.8, 1.0)
COLOR_BG_SPRITE = (0.1, 0.1, 0.1, 1.0)
COLOR_WINDOW_BG = (1.0, 1.0, 1.0, 1.0)
COLOR_WINDOW_BG_BLINK = (1.0, 1.0, 1.0, 2.5)
COLOR_BY_SUBTYPE = {hackingConst.SUBTYPE_CORE_LOW: (0.357, 0.718, 0.561, 1.0),
 hackingConst.SUBTYPE_CORE_MEDIUM: (1.0, 0.675, 0.0, 1.0),
 hackingConst.SUBTYPE_CORE_HIGH: util.Color.RED}
COLOR_TILE_ICON_BY_TYPE = {hackingConst.TYPE_DEFENSESOFTWARE: COLOR_DEFENSEICON,
 hackingConst.TYPE_UTILITYELEMENTTILE: COLOR_UTILITYELEMENTICON}
COLOR_TILE_BG_BY_TYPE = {hackingConst.TYPE_DEFENSESOFTWARE: COLOR_DEFENSE}
COLOR_HUD_BAR_BG = (0.12, 0.12, 0.12, 0.4)
COLOR_HUD_BAR_STRIPES = (0.0, 0.0, 0.0, 0.3)
COLOR_HUD_BAR_STRENGTH = (0.592, 0.102, 0.102, 1.0)
COLOR_HUD_BAR_COHERENCE = (0.588, 0.247, 0.039, 1.0)
COLOR_HUD_TEXT = (0.412, 0.51, 0.482, 1.0)
WIDTH_LINE = 1.0
LINETYPE_HORIZONTAL = 1
LINETYPE_INCLINE = 2
LINETYPE_DECLINE = 3
LINEBLEED_TEXTUREPATHS_HORIZONTAL = ('res:/UI/Texture/classes/hacking/lineBleed/horiz01.png', 'res:/UI/Texture/classes/hacking/lineBleed/horiz02.png', 'res:/UI/Texture/classes/hacking/lineBleed/horiz03.png', 'res:/UI/Texture/classes/hacking/lineBleed/horiz04.png', 'res:/UI/Texture/classes/hacking/lineBleed/horiz05.png', 'res:/UI/Texture/classes/hacking/lineBleed/horiz06.png', 'res:/UI/Texture/classes/hacking/lineBleed/horiz07.png', 'res:/UI/Texture/classes/hacking/lineBleed/horiz08.png', 'res:/UI/Texture/classes/hacking/lineBleed/horiz09.png', 'res:/UI/Texture/classes/hacking/lineBleed/horiz10.png', 'res:/UI/Texture/classes/hacking/lineBleed/horiz11.png', 'res:/UI/Texture/classes/hacking/lineBleed/horiz12.png', 'res:/UI/Texture/classes/hacking/lineBleed/horiz13.png', 'res:/UI/Texture/classes/hacking/lineBleed/horiz14.png', 'res:/UI/Texture/classes/hacking/lineBleed/horiz15.png', 'res:/UI/Texture/classes/hacking/lineBleed/horiz16.png', 'res:/UI/Texture/classes/hacking/lineBleed/horiz17.png')
LINEBLEED_TEXTUREPATHS_DIAGONAL = ('res:/UI/Texture/classes/hacking/lineBleed/diag01.png', 'res:/UI/Texture/classes/hacking/lineBleed/diag02.png', 'res:/UI/Texture/classes/hacking/lineBleed/diag03.png', 'res:/UI/Texture/classes/hacking/lineBleed/diag04.png', 'res:/UI/Texture/classes/hacking/lineBleed/diag05.png', 'res:/UI/Texture/classes/hacking/lineBleed/diag06.png', 'res:/UI/Texture/classes/hacking/lineBleed/diag07.png', 'res:/UI/Texture/classes/hacking/lineBleed/diag08.png', 'res:/UI/Texture/classes/hacking/lineBleed/diag09.png', 'res:/UI/Texture/classes/hacking/lineBleed/diag10.png', 'res:/UI/Texture/classes/hacking/lineBleed/diag11.png')
LINEBLEED_SIZE_BY_LINETYPE = {LINETYPE_HORIZONTAL: (96, 50),
 LINETYPE_INCLINE: (64, 75),
 LINETYPE_DECLINE: (64, 75)}
STAT_COHERENCE = 1
STAT_STRENGTH = 2
UTILITYELEMENT_SPACING = 34
import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('hackingUIConst', locals())
