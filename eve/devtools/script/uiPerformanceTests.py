#Embedded file name: eve/devtools/script\uiPerformanceTests.py
from eve.client.script.ui.control.eveWindow import Window
import random
import blue
import inspect

class PerformanceTests:

    def __init__(self):
        self.results = []
        self.wnds = []

    def RunTests(self):
        for testMethod in self.GetTestMethods():
            self.RunTest(testMethod)

        return self.results

    def GetTestMethods(self):
        """
        Returns a list of all the methods in this class whose name starts with "Test"
        """
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        return (method for name, method in methods if name.startswith('Test'))

    def RunTest(self, test):
        fpsSvc = sm.GetService('fpsMonitorSvc')
        fpsSvc.StartCollectingData()
        test()
        result = fpsSvc.StopCollectingData()
        self.results.append((test.__doc__.strip(), result))

    def Test1(self):
        """
        Test 1: Open 50 windows
        """
        for i in xrange(50):
            wnd = self.CreateBlankWindow(i)
            blue.synchro.Yield()
            self.wnds.append(wnd)

    def Test2(self):
        """
        Test 2: Move top window around
        """
        wnd = self.wnds[-1]
        for i in xrange(100):
            wnd.left = wnd.top = 5 * i
            blue.synchro.Yield()

    def Test3(self):
        """
        Test 3: Close 50 windows
        """
        for wnd in self.wnds:
            wnd.Close()
            blue.synchro.Yield()

    def CreateBlankWindow(self, i):
        wnd = TestWindow.Open(windowID='testWindow%s' % i)
        wnd.left = random.randint(0, uicore.desktop.width - wnd.width)
        wnd.top = random.randint(0, uicore.desktop.height - wnd.height)
        return wnd


class TestWindow(Window):
    default_caption = 'Test Window'
    default_windowID = 'TestWindowID'
    default_width = 600
    default_height = 400
    default_topParentHeight = 0

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
