#Embedded file name: spacecomponents/common\componentclass.py


class ComponentClass(object):

    def __init__(self, componentName, factoryMethod):
        self.componentName = componentName
        self.factoryMethod = factoryMethod
