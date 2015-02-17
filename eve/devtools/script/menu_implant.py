#Embedded file name: eve/devtools/script\menu_implant.py
import os
import sys
import blue
import uix
import uiutil
import uthread
import service
from service import *
IMPLANTFILE = 'implants.ini'
Progress = lambda text, current, total: sm.GetService('loading').ProgressWnd('Messing with your head!', text, current, total)

class ImplantService(Service):
    __module__ = __name__
    __doc__ = 'Insider Implant'
    __exportedcalls__ = {}
    __guid__ = 'svc.implant'
    __servicename__ = 'implant'
    __displayname__ = 'Insider Implant Service'

    def Run(self, *args):
        self.state = SERVICE_START_PENDING
        self.LogInfo('Implant Service starting.')
        self.state = SERVICE_RUNNING
        self.LogInfo('Implant service running.')

    def Load(self, fileName):
        d = {}
        if os.path.exists(fileName):
            lines = blue.win32.AtomicFileRead(fileName)[0].replace('\r', '').replace('\x00', '').split('\n')
            for line in lines:
                impName, key = line.split('=', 1)
                impName = impName.strip()
                d[impName.lower()] = (impName, key.strip())

        return d

    def Save(self, thisDict, fileName):
        text = '\r\n'.join([ '%s=%s' % (name, key) for name, key in thisDict.itervalues() ])
        blue.win32.AtomicFileWrite(fileName, text)

    def ImplantEntry(dgm, typeID):
        rec = dgm.GetType(typeID)
        return {'label': rec.name,
         'height': 16,
         'iconmap': rec.iconID,
         'action': PlugEmIn,
         'args': ([typeID],)}

    def ImplantName(self, typeID):
        dgm = sm.GetService('godma')
        rec = dgm.GetType(typeID)
        return rec.name

    def ImplantMenu(self, *args):
        m = []
        try:
            INSIDERDIR = sm.GetService('insider').GetInsiderDir()
            TARGET = os.path.join(INSIDERDIR, IMPLANTFILE)
            self.implants = self.Load(TARGET)
        except:
            sys.exc_clear()
            self.implants = []

        if len(self.implants) == 0:
            self.implants = {'armor tank': ('Armor Tank', 'IMP:20499:20501:20507:20503:20505:20509:19685:21606'),
             'speed demon': ('Speed Demon', 'IMP:19540:19551:19553:19554:19555:19556:24669:24663:16006:16009'),
             'shield tank': ('Shield Tank', 'IMP:20121:20157:20158:20159:20160:20161:16246:16248:21888'),
             'low-grade centurion': ('Low-grade Centurion', 'IMP:28790:28791:28794:28792:28793:28795'),
             'low-grade crystal': ('Low-grade Crystal', 'IMP:22107:22108:22111:22109:22110:22112'),
             'low-grade edge': ('Low-grade Edge', 'IMP:28814:28815:28818:28816:28817:28819'),
             'low-grade halo': ('Low-grade Halo', 'IMP:22113:22114:22117:22115:22116:22118'),
             'low-grade harvest': ('Low-grade Harvest', 'IMP:28802:28803:28806:28804:28805:28807'),
             'low-grade nomad': ('Low-grade Nomad', 'IMP:28796:28797:28800:28798:28799:28801'),
             'low-grade slave': ('Low-grade Slave', 'IMP:22119:22120:22123:22121:22122:22124'),
             'low-grade snake': ('Low-grade Snake', 'IMP:22125:22126:22129:22127:22128:22130'),
             'low-grade talisman': ('Low-grade Talisman', 'IMP:22131:22133:22136:22134:22135:22137'),
             'low-grade virtue': ('Low-grade Virtue', 'IMP:28808:28809:28812:28810:28811:28813'),
             'low-grade ascendancy': ('Low-grade Ascendancy', 'IMP:33555:33557:33559:33561:33563:33565'),
             'high-grade crystal': ('High-grade Crystal', 'IMP:20121:20157:20158:20159:20160:20161'),
             'high-grade halo': ('High-grade Halo', 'IMP:20498:20500:20506:20502:20504:20508'),
             'high-grade slave': ('High-grade Slave', 'IMP:20499:20501:20507:20503:20505:20509'),
             'high-grade snake': ('High-grade Snake', 'IMP:19540:19551:19553:19554:19555:19556'),
             'high-grade talisman': ('High-grade Talisman', 'IMP:19534:19535:19536:19537:19538:19539'),
             'high-grade ascendancy': ('High-Grade Ascendancy', 'IMP:33516:33525:33526:33527:33528:33529'),
             'qa tools': ('QA Tools', 'IMP:33486:33512:33068'),
             'aurora set': ('Aurora Set', 'IMP:24343:24344:24345:24346:24347')}
        items = self.implants.values()
        items.sort()
        for name, key in items:
            m.append((name, ('isDynamic', self.ImplantSubMenu, (name,))))

        m.append(None)
        m.append(('Unplug all implants', self.FullFrontalLobotomy))
        m.append(None)
        m.append(('Store current set', self.StoreImplants))
        return m

    def ImplantSubMenu(self, name):
        m = []

        def _IsValidImplant(typeID):
            rec = cfg.invtypes.GetIfExists(typeID)
            return rec and rec.categoryID == const.categoryImplant

        keys = map(int, self.implants[name.lower()][1].split(':')[1:])
        keys = [ typeID for typeID in keys if _IsValidImplant(typeID) ]
        m.append(('Plug in %s [%s]' % (name, len(keys)), self.PlugEmIn, (keys,)))
        m.append(None)
        dgm = sm.GetService('godma')
        for key in keys:
            m.append(('%s' % self.ImplantName(key), self.PlugEmIn, ([key],)))

        m.append(None)
        m.append(('<color=0xffff8080>Delete this set', self.Delete, (name,)))
        return m

    def Delete(self, name):
        ret = sm.GetService('gameui').MessageBox(title='Delete set?', text="You are about to delete the implant set '%s'<br><br>Click OK to delete this set." % name, buttons=uiconst.OKCANCEL, icon=uiconst.WARNING)
        if ret[0] != uiconst.ID_OK:
            return
        del self.implants[name.lower()]
        INSIDERDIR = sm.GetService('insider').GetInsiderDir()
        TARGET = os.path.join(INSIDERDIR, IMPLANTFILE)
        self.Save(self.implants, TARGET)

    def PlugEmIn(self, typeIDs):
        if len(typeIDs) <= 1:
            p = lambda *x: None
        else:
            p = Progress
        p('Evaluating state of mind...', 0, 1)
        dgm = sm.GetService('godma')
        sh = dgm.GetSkillHandler()
        sh.CharStopTrainingSkill()
        head = {}
        for typeID in typeIDs:
            rec = dgm.GetType(typeID)
            head[rec.implantness] = typeID

        removeCalls = []
        for implant in dgm.GetItem(eve.session.charid).implants:
            rec = dgm.GetType(implant.typeID)
            if rec.implantness in head:
                if rec.typeID == head[rec.implantness]:
                    del head[rec.implantness]
                else:
                    removeCalls.append((sh.RemoveImplantFromCharacter, (implant.itemID,)))

        pluginCalls = []
        t = len(head)
        c = 1
        slash = sm.GetService('slash')
        for typeID in head.itervalues():
            p('[%d/%d] Creating implants...' % (c, t), c, t * 2)
            c += 1
            if eve.session.role & service.ROLE_WORLDMOD:
                itemID = slash.SlashCmd('/create %d 1' % (typeID,))
            else:
                itemID = slash.SlashCmd('/load me %d' % typeID)[0]
            pluginCalls.append((sh.CharAddImplant, (itemID,)))

        if removeCalls:
            p('Ripping old hardware out...', 1, 2)
            uthread.parallel(removeCalls)
        if pluginCalls:
            p('Plugging you up...', 3, 4)
            uthread.parallel(pluginCalls)
        p('All done...', 1, 1)

    def FullFrontalLobotomy(*args):
        Progress('Performing lobotomy...', 0, 1)
        dgm = sm.GetService('godma')
        sh = dgm.GetSkillHandler()
        sh.CharStopTrainingSkill()
        parallelCalls = [ (sh.RemoveImplantFromCharacter, (implant.itemID,)) for implant in dgm.GetItem(eve.session.charid).implants ]
        uthread.parallel(parallelCalls)
        Progress('All done!', 1, 1)

    def StoreImplants(self, *args):
        INSIDERDIR = sm.GetService('insider').GetInsiderDir()
        TARGET = os.path.join(INSIDERDIR, IMPLANTFILE)
        godma = sm.GetService('godma')
        mygodma = godma.GetItem(eve.session.charid)
        if not mygodma:
            return
        imps = uiutil.SortListOfTuples([ (getattr(godma.GetType(implant.typeID), 'implantness', None), implant) for implant in mygodma.implants ])
        ret = uix.NamePopup('Save Implant Set', 'Enter name for set', setvalue='New', maxLength=32)
        if not ret:
            return
        name = ret['name']
        if name.lower() in self.implants:
            ret = sm.GetService('gameui').MessageBox(title='Overwrite set?', text="An implant set named '%s' already exists.<br><br>Click OK to overwrite the old set." % name, buttons=uiconst.OKCANCEL, icon=uiconst.WARNING)
            if ret[0] != uiconst.ID_OK:
                return
        key = 'IMP:' + ':'.join([ str(row.typeID) for row in imps ])
        self.implants[name.lower()] = (name, key)
        self.Save(self.implants, TARGET)

    exports = {'insider.ImplantMenu': ImplantMenu}
