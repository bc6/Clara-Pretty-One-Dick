#Embedded file name: eve/devtools/script\bdqmonitor.py
import blue
import uicontrols
import carbonui.const as uiconst
from carbonui.primitives.container import Container
import remotefilecache
import uthread

class BackgroundDownloadQueueMonitor(uicontrols.Window):
    default_caption = 'Background Download Queue Monitor'
    default_minSize = (800, 500)

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.SetTopparentHeight(0)
        self.topPanel = Container(parent=self.sr.main, align=uiconst.TOTOP, height=30)
        uicontrols.Button(parent=self.topPanel, align=uiconst.TOLEFT, label='Pause', width=120, height=30, func=self.Pause)
        uicontrols.Button(parent=self.topPanel, align=uiconst.TOLEFT, label='Resume', width=120, height=30, func=self.Resume)
        self.mainQueue = uicontrols.Scroll(parent=self.sr.main, id='mainQueueScroll', align=uiconst.TOLEFT, width=300)
        self.subQueue = uicontrols.Scroll(parent=self.sr.main, id='subQueueScroll', align=uiconst.TOALL)
        self.queue = []
        uthread.new(self.PopulateMainQueueScrollTasklet)

    def PopulateMainQueueScrollTasklet(self):
        while not self.destroyed:
            self.PopulateMainQueueScroll()
            blue.synchro.Sleep(333)

    def PopulateMainQueueScroll(self, *args):
        self.queue = remotefilecache.get_queue()
        contentList = []
        index = 1
        for item in self.queue:
            label = '%d<t>%s<t>%d' % (index, item.key, len(item.fileset))
            listEntry = uicontrols.ScrollEntryNode(decoClass=uicontrols.SE_GenericCore, id=id, label=label)
            contentList.append(listEntry)
            index += 1

        self.mainQueue.Load(contentList=contentList, headers=['#', 'Key', 'Files'], noContentHint='Queue is empty')
        self.PopulateSubQueue(self.queue[0])

    def PopulateSubQueue(self, item):
        itemList = list(item.fileset)
        if len(itemList) > 50:
            itemList = itemList[0:49]
            itemList.append('...')
        contentList = []
        index = 1
        for each in itemList:
            label = '%d<t>%s' % (index, each)
            listEntry = uicontrols.ScrollEntryNode(decoClass=uicontrols.SE_GenericCore, id=id, label=label)
            contentList.append(listEntry)
            index += 1

        self.subQueue.Load(contentList=contentList, headers=['#', 'Resource file'], noContentHint='Queue is empty')

    def OnListEntryClicked(self, listEntry):
        node = listEntry.sr.node
        item = node.item
        self.selected_item = item
        self.PopulateSubQueue(item)

    def Pause(self, *args):
        remotefilecache.pause()

    def Resume(self, *args):
        remotefilecache.resume()
