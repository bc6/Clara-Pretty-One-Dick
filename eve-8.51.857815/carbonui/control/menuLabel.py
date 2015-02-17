#Embedded file name: carbonui/control\menuLabel.py


class MenuLabel(tuple):
    """
        This class is used when adding options to menu, it is the label part of the option.
        MenuLabels are always of this format:
            (labelPath, tokenDictionary)
        where 
            labelPath       = cerberus label path
            tokenDictionary = tokens used by the cerberus label (empty dictionary if there are no tokens) 
    """

    def __new__(cls, text, kw = None):
        if kw is None:
            kw = {}
        return tuple.__new__(cls, (text, kw))


exports = {'uiutil.MenuLabel': MenuLabel}
