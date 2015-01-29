#Embedded file name: eve/client/script/sys\evePatchService.py
"""
    evePatchService.py

    Authors:   Freyr Magn\xfasson (corification)
    Created:   Corified May 2009
    Project:   EVE Client

    Description:

    This file contains the app specific implementation of a patching service.
    Where we provide an URL opener which overrides the core one to provide an appName.
    In addition we supply key/value pairs for the URL dictionaries used by the patcher
"""
appName = 'EVE'
patchInfoURLs = {'optic': 'http://www.eve-online.com.cn/patches/',
 'ccp': 'http://client.eveonline.com/patches/'}
optionalPatchInfoURLs = {'optic': 'http://www.eve-online.com.cn/patches/optional/',
 'ccp': 'http://client.eveonline.com/patches/optional/'}
