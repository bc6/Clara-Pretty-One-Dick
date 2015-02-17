#Embedded file name: gatekeeper\__init__.py
"""
    Common functionality for A/B/n testing
"""
from gatekeeper.gatekeeperClass import Gatekeeper
from gatekeeper.gatekeeperConst import *
character = Gatekeeper(ignoreMultipleTeardowns=True, allowMultipleInits=True)
user = Gatekeeper()
