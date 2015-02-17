#Embedded file name: eve/devtools/script\uiPerformanceTestWnd.py
from eve.client.script.ui.control.buttons import Button
from eve.client.script.ui.control.eveWindow import Window
import carbonui.const as uiconst
import blue
from eve.devtools.script.uiPerformanceTests import PerformanceTests

class UIPerformanceTestWnd(Window):
    default_caption = 'UI Performance Test Utility'
    default_windowID = 'UIPerformanceTestID'
    default_fixedWidth = 200
    default_fixedHeight = 60
    default_topParentHeight = 0

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.isTesting = False
        self.startBtn = Button(name='self.startBtn', parent=self.sr.main, align=uiconst.CENTER, label='Start Test', func=self.OnStartBtn)

    def OnStartBtn(self, *args):
        self.startBtn.Disable()
        self.RunAllTests()
        self.startBtn.Enable()

    def RunAllTests(self):
        self.HideScene()
        results = PerformanceTests().RunTests()
        self.ShowScene()
        self.DisplayResults(results)
        uicore.Message('CustomNotify', {'notify': 'All Tests successful. Results copied to clipboard'})

    def HideScene(self):
        scene = sm.GetService('sceneManager').GetActiveScene()
        scene.display = False
        scene.update = False

    def ShowScene(self):
        scene = sm.GetService('sceneManager').GetActiveScene()
        scene.display = True
        scene.update = True

    def DisplayResults(self, results):
        txt = ''
        for description, stats in results:
            txt += '%s:\n' % description
            for t, value in stats:
                txt += '%.1f\t%6.2f\n' % (t / float(const.SEC), value)

            txt += '\n'

        txt += 'SUMMARY'
        totalTime = 0
        for description, stats in results:
            txt += '\n%s:' % description
            values = [ value for t, value in stats ]
            txt += '\nMedian FPS: %s' % median(values)
            txt += '\nAverage FPS: %s' % (sum(values) / float(len(values)))
            txt += '\n'
            time = [ t for t, value in stats ]
            totalTime += time[-1]

        txt += '\nTotal time: %s' % (totalTime / float(const.SEC))
        print txt
        blue.pyos.SetClipboardData(txt)


def median(mylist):
    sorts = sorted(mylist)
    length = len(sorts)
    if not length % 2:
        return (sorts[length / 2] + sorts[length / 2 - 1]) / 2.0
    return sorts[length / 2]
