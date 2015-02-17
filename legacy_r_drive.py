#Embedded file name: legacy_r_drive.py
"""
This module is to help minimize fallout from removing blue.rot.loadFromContent and
blue.rot.loadFromTmp flags. I needed somewhere to put those flags so I could rename
them wholesale - the tech artists will then deal with deleting them altogether.
These flags have been defunct in Blue for a while.
"""
loadFromContent = False
loadFromTmp = False
