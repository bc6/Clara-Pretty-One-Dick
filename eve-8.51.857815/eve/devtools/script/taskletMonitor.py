#Embedded file name: eve/devtools/script\taskletMonitor.py
import traceback
__author__ = 'snorri.sturluson'
import uiprimitives
import uicontrols
import carbonui.const as uiconst
import bluepy
import blue
from eve.client.script.ui.control.tabGroup import TabGroup
from carbonui.primitives.container import Container

class RunningTasklets(Container):

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.settingsContainer = uiprimitives.Container(parent=self, align=uiconst.TOTOP, height=30)
        self.countLabel = uicontrols.Label(parent=self.settingsContainer, align=uiconst.TOLEFT, text='', height=30, padLeft=2, padTop=2)
        uicontrols.Button(parent=self.settingsContainer, align=uiconst.TORIGHT, label='Refresh', width=120, height=30, func=self.PopulateScroll)
        self.scroll = uicontrols.Scroll(parent=self, id='taskletsScroll', align=uiconst.TOTOP, height=350)
        self.callstack = uicontrols.Scroll(parent=self, align=uiconst.TOALL)
        self.PopulateScroll()

    def PopulateScroll(self, *args):
        contentList = []
        for t in bluepy.tasklets.keys():
            if not t.alive:
                continue
            callstack = traceback.extract_stack(t.frame)
            ctx = getattr(t, 'context', '(unknown)')
            runtime = getattr(t, 'runTime', 0)
            label = '%d<t>%f<t>%s' % (t.tasklet_id, runtime, ctx)
            listEntry = uicontrols.ScrollEntryNode(decoClass=uicontrols.SE_GenericCore, id=id, taskletId=t.tasklet_id, context=ctx, callstack=callstack, runTime=runtime, label=label, OnClick=self.OnListEntryClicked)
            contentList.append(listEntry)

        self.scroll.Load(contentList=contentList, headers=['ID', 'Runtime', 'Context'], noContentHint='No Data available')
        self.countLabel.text = '%d tasklets' % len(contentList)

    def OnListEntryClicked(self, listEntry):
        node = listEntry.sr.node
        contentList = []
        entryNo = 1
        for each in node.callstack:
            filename, line, function_name, code = each
            label = '%d<t>%s<t>%d<t>%s<t>%s' % (entryNo,
             filename,
             line,
             function_name,
             code)
            listEntry = uicontrols.ScrollEntryNode(decoClass=uicontrols.SE_GenericCore, id=id, entryNo=entryNo, filename=filename, line=line, function_name=function_name, code=code, label=label)
            contentList.append(listEntry)
            entryNo += 1

        self.callstack.Load(contentList=contentList, headers=['Entry',
         'File name',
         'Line',
         'Function name',
         'Code'], noContentHint='No Data available')


class TimesliceWarnings(Container):

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.settingsContainer = uiprimitives.Container(parent=self, align=uiconst.TOTOP, height=30)
        self.countLabel = uicontrols.Label(parent=self.settingsContainer, align=uiconst.TOLEFT, text='', height=30, padLeft=2, padTop=2)
        uicontrols.Button(parent=self.settingsContainer, align=uiconst.TORIGHT, label='Refresh', width=120, height=30, func=self.PopulateScroll)
        self.scroll = uicontrols.Scroll(parent=self, id='timesliceWarningsScroll', align=uiconst.TOALL)
        self.PopulateScroll()

    def PopulateScroll(self, *args):
        totalWarnings = 0
        contentList = []
        for ctx, v in blue.pyos.taskletTimer.taskletWarnings.iteritems():
            maxValue, count = v
            label = '%d<t>%d<t>%s' % (maxValue, count, ctx)
            listEntry = uicontrols.ScrollEntryNode(decoClass=uicontrols.SE_GenericCore, id=id, maxValue=maxValue, count=count, context=ctx, label=label)
            contentList.append(listEntry)
            totalWarnings += count

        self.scroll.Load(contentList=contentList, headers=['Max value', 'Count', 'Context'], noContentHint='No Data available')
        self.countLabel.text = '%d warnings' % totalWarnings


class TaskletMonitor(uicontrols.Window):
    default_caption = 'Tasklet Monitor'
    default_minSize = (800, 500)

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.SetTopparentHeight(0)
        runningTaskletsPanel = RunningTasklets(parent=self.sr.main)
        timesliceWarningsPanel = TimesliceWarnings(parent=self.sr.main)
        TabGroup(parent=self.sr.main, groupID='TaskletsGroupID', idx=0, tabs=(('Running tasklets',
          runningTaskletsPanel,
          self.sr.main,
          'taskletsID1'), ('Timeslice warnings',
          timesliceWarningsPanel,
          self.sr.main,
          'taskletsID2')))
