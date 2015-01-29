#Embedded file name: carbon/common/lib\ztree.py
"""
Constants for the tree system.
"""
import zactionConst
import carbon.common.lib.ai as ai
import batma
TREE_SCHEMA = 'ztree'
_TREE_PREFIX = TREE_SCHEMA + '.'
TREE_NODES_TABLE_NAME = 'nodes'
TREE_NODES_TABLE_FULL_PATH = _TREE_PREFIX + TREE_NODES_TABLE_NAME
TREE_LINKS_TABLE_NAME = 'links'
TREE_LINKS_TABLE_FULL_PATH = _TREE_PREFIX + TREE_LINKS_TABLE_NAME
TREE_LINKS_PARENT_ID_FOR_CHILDREN_WHO_ARE_ROOTS = 0
TREE_NODE_PROPERTIES_TABLE_NAME = 'nodeProperties'
TREE_NODE_PROPERTIES_TABLE_FULL_PATH = _TREE_PREFIX + TREE_NODE_PROPERTIES_TABLE_NAME
TREE_SYSTEM_ID_DICT = {zactionConst.ACTION_SCHEMA: 1,
 ai.AI_SCHEMA: 2,
 batma.BUFF_SYSTEM: 3}
NODE_FOLDER = 2
NODE_NORMAL = 3
ACTION_NODE_TYPES = [NODE_FOLDER, NODE_NORMAL]
DECISION_NODE_TYPES = [NODE_FOLDER, NODE_NORMAL]
ACTION_NODE_TYPE_NAMES = {'Normal': NODE_NORMAL,
 'Folder': NODE_FOLDER}
DECISION_NODE_TYPE_NAMES = {'Normal2': NODE_NORMAL,
 'Folder2': NODE_FOLDER}
NODE_TYPES = {TREE_SYSTEM_ID_DICT[zactionConst.ACTION_SCHEMA]: ACTION_NODE_TYPES,
 TREE_SYSTEM_ID_DICT[ai.AI_SCHEMA]: DECISION_NODE_TYPES,
 TREE_SYSTEM_ID_DICT[batma.BUFF_SYSTEM]: ACTION_NODE_TYPES}
NODE_TYPE_NAMES = {TREE_SYSTEM_ID_DICT[zactionConst.ACTION_SCHEMA]: ACTION_NODE_TYPE_NAMES,
 TREE_SYSTEM_ID_DICT[ai.AI_SCHEMA]: DECISION_NODE_TYPE_NAMES,
 TREE_SYSTEM_ID_DICT[batma.BUFF_SYSTEM]: ACTION_NODE_TYPE_NAMES}
GENERATE_TREE_INSTANCE_ID = 0
ACTION_PROPERTY = -1
