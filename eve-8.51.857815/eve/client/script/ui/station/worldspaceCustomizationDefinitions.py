#Embedded file name: eve/client/script/ui/station\worldspaceCustomizationDefinitions.py
"""
Contains definitions for worldspace color themes, currently includes and example of Gallente-normal and Gallente-Quafe
The definitions are broken down into races and corporations.
"""
DEFAULT_GALLENTE = 1000168
QUAFE_OWNER = 1000100
themeSettings = {const.raceAmarr: {},
 const.raceMinmatar: {},
 const.raceCaldari: {},
 const.raceJove: {},
 const.raceGallente: {}}
import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('worldspaceCustomization', locals())
