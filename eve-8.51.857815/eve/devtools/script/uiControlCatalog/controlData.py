#Embedded file name: eve/devtools/script/uiControlCatalog\controlData.py
from eve.client.script.ui.control.treeData import TreeData
import tokenize
import StringIO
import blue
import os

def GetControlData():
    ret = []
    path = os.path.dirname(__file__)
    path += '\\controls'
    for groupName in os.listdir(path):
        children = []
        groupPath = path + '\\' + groupName
        for fileName in os.listdir(groupPath):
            filePath = groupPath + '\\' + fileName
            children.append(ControlData(filePath))

        ret.append(TreeData(groupName, children=children))

    return ret


def BrowseControls():
    blue.os.ShellExecute(os.path.dirname(__file__) + '\\controls')


def GetNumSamples(text):
    num = 0
    f = StringIO.StringIO(text)
    isMethodName = False
    tokens = tokenize.generate_tokens(f.readline)
    for tokType, tokVal, _, _, _ in tokens:
        if isMethodName and tokVal.startswith('Sample'):
            num += 1
        isMethodName = tokType == tokenize.NAME and tokVal == 'def'

    return num


class ControlData(TreeData):

    def __init__(self, label, parent = None, children = None):
        TreeData.__init__(self, label, parent, children)

    def GetLabel(self):
        fileName = os.path.basename(self.GetFilePath())
        return fileName.replace('.py', '')

    def GetFilePath(self):
        return self._label

    def GetBaseClass(self):
        f = StringIO.StringIO(self.GetCode())
        line = f.readline()
        try:
            clsName = line.split(' ')[-1]
            cls = None
            exec line + '\ncls = %s' % clsName
        except:
            sm.GetService('gameui').Say('Unable to determine class. Please make sure the first line of code sample is importing the class like so:\n\n from carbonui.primitives.sprite import Sprite')
            raise

        return cls

    def GetClassPath(self):
        ret = None
        module = self.GetBaseClass().__module__
        exec ('import %s' % module, globals())
        exec 'ret = %s.__file__' % module
        return ret

    def OpenModuleCodeInEditor(self):
        blue.os.ShellExecute(self.GetClassPath(), 'edit')

    def GetCode(self):
        return open(self.GetFilePath()).read()

    def OpenSampleCodeInEditor(self):
        blue.os.ShellExecute(self.GetFilePath())
