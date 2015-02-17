#Embedded file name: carbon/common/script/localization\localizationUtil.py


class LocalizationSafeString(unicode):
    """
        Used to be baseclass for strings that were marked as "ok to be hardcoded"
        ### This needs to stay for the time being because Cerberus strings live in agent memory, and removing this breaks
        ### agent memory on test servers.. Can be removed sometime in the future but we'll have to fix agent memory
        ### on test servers first (or accept that old missions might be broken).
    """
    pass
