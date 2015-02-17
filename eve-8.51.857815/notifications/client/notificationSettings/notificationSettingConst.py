#Embedded file name: notifications/client/notificationSettings\notificationSettingConst.py


class ExperimentalConst(object):
    SERVER_EXPERIMENT_KEY = 'experimental_newnotifications'
    SERVER_EXPERIMENT_DESCRIPTION_KEY = 'experimental_newnotifications_desc'
    CLIENT_EXPERIMENT_ENABLED_KEY = 'experimental_newnotifications'
    EXPERIMENT_ENABLEDIALOG_LABEL = 'EnableExperimentalFeature'


class ExpandAlignmentConst(object):
    EXPAND_ALIGNMENT_HORIZONTAL_LEFT = 'left'
    EXPAND_ALIGNMENT_HORIZONTAL_RIGHT = 'right'
    EXPAND_ALIGNMENT_VERTICAL_UP = 'up'
    EXPAND_ALIGNMENT_VERTICAL_DOWN = 'down'
    EXPAND_ALIGNMENTS_HORIZONTAL = [EXPAND_ALIGNMENT_HORIZONTAL_LEFT, EXPAND_ALIGNMENT_HORIZONTAL_RIGHT]
    EXPAND_ALIGNMENTS_VERTICAL = [EXPAND_ALIGNMENT_VERTICAL_UP, EXPAND_ALIGNMENT_VERTICAL_DOWN]

    @staticmethod
    def OtherHorizontal(alignment):
        if alignment is ExpandAlignmentConst.EXPAND_ALIGNMENT_HORIZONTAL_LEFT:
            return ExpandAlignmentConst.EXPAND_ALIGNMENT_HORIZONTAL_RIGHT
        else:
            return ExpandAlignmentConst.EXPAND_ALIGNMENT_HORIZONTAL_LEFT

    @staticmethod
    def OtherVertical(alignment):
        if alignment is ExpandAlignmentConst.EXPAND_ALIGNMENT_VERTICAL_UP:
            return ExpandAlignmentConst.EXPAND_ALIGNMENT_VERTICAL_DOWN
        else:
            return ExpandAlignmentConst.EXPAND_ALIGNMENT_VERTICAL_UP
