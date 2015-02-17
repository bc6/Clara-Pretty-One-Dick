#Embedded file name: carbonui/control\xposeCoreClasses.py
import log
from carbonui.primitives.base import Base

def ExposeCoreClassesWithOutCorePostfix():
    import uicls
    for className, classInstance in uicls.__dict__.items():
        if not className.endswith('Core'):
            continue
        if not issubclass(classInstance, Base):
            continue
        nocore = className[:-4]
        if nocore not in uicls.__dict__:
            uicls.__dict__[nocore] = classInstance
            print 'Added %s into uicls namespace as %s' % (className, nocore)
            log.LogInfo('Added %s into uicls namespace as %s' % (className, nocore))
