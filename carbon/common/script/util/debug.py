#Embedded file name: carbon/common/script/util\debug.py
"""
Base debugging class
"""
import sys, pdb

def startDebugging():
    pdb.post_mortem(sys.exc_info()[2])


exports = {'debug.startDebugging': startDebugging}
