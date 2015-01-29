#Embedded file name: eve/client/script/ui/control/browser\eveEditBookMarksWindow.py
"""
Extending EditBookmarksWindowCore
"""
from carbonui.control.browser.browserEditBookMarksWindow import EditBookmarksWindowCore, EditBookmarksWindowCoreOverride

class EditBookmarksWindow(EditBookmarksWindowCore):
    __guid__ = 'uicls.EditBookmarksWindow'

    def ApplyAttributes(self, attributes):
        EditBookmarksWindowCore.ApplyAttributes(self, attributes)
        self.SetWndIcon()
        self.SetTopparentHeight(0)
        self.MakeUnpinable()


EditBookmarksWindowCoreOverride.__bases__ = (EditBookmarksWindow,)
