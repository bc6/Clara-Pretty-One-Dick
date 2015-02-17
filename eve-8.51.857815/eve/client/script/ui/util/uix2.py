#Embedded file name: eve/client/script/ui/util\uix2.py
"""uix has circular imports, break them out here."""
import carbonui.const as uiconst
SEL_FILES = 0
SEL_FOLDERS = 1
SEL_BOTH = 2

def RefreshHeight(w):
    """ Refreshes the height of a parent window to be the sum of the heights of the visible children."""
    w.height = sum([ x.height for x in w.children if x.state != uiconst.UI_HIDDEN and x.align in (uiconst.TOBOTTOM, uiconst.TOTOP) ])


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('uix', locals())
