#Embedded file name: eve/devtools/script\svc_trainer.py
import uicontrols
import uiprimitives
import os
import itools
import param
import uix
import triui
import listentry
import uiutil
import carbonui.const as uiconst
import slash
from service import *
SERVICENAME = 'trainer'
Progress = lambda title, text, current, total: sm.GetService('loading').ProgressWnd(title, text, current, total)
Slash = lambda command: sm.RemoteSvc('slash').SlashCmd(command)
Message = lambda title, body, icon = triui.INFO: sm.GetService('gameui').MessageBox(body, title, buttons=uiconst.OK, icon=icon)

class TrainerService(Service):
    """Trainer"""
    __exportedcalls__ = {'Show': []}
    __notifyevents__ = ['ProcessRestartUI']
    __dependencies__ = []
    __guid__ = 'svc.trainer'
    __servicename__ = SERVICENAME
    __displayname__ = SERVICENAME
    __slashhook__ = True
    __neocommenuitem__ = (('Skill Tool', 'res:/ui/Texture/WindowIcons/browserbookmarks.png'), 'Show', ROLE_QA)

    def cmd_applyskills(self, p):
        """profileName charList_or_keyWord"""
        profileName, targetList = p.Parse('sr')
        targetList = [ x for x in param.ParamObject(targetList) ]
        confirmedTargets = []
        for target in targetList:
            if target.startswith('@'):
                target = target[1:].lower()
                if target == 'corp':
                    confirmedTargets += sm.GetService('corp').GetMemberIDs()
                else:
                    raise slash.Error('Unknown keyword @%s' % target)
            else:
                try:
                    confirmedTargets.append(sm.RemoteSvc('lookupSvc').LookupCharacters(target, 1)[0].characterID)
                except IndexError:
                    raise slash.Error("Can't find character: %s" % target)

        del targetList
        profile = self.Profile_LoadInternal(profileName)
        if not profile:
            raise slash.Error('No such skill profile: %s' % profileName)
        for charID in confirmedTargets:
            self.ApplyProfile(profile, charID)

        return 'Ok'

    def Run(self, memStream = None):
        self.wnd = None
        self.skillGroups = []
        self.skillsByGroupID = {}
        self.skillLevel = 5
        self.currentProfileName = None
        self.currentProfile = {}

    def Stop(self, memStream = None):
        self.Hide()
        Service.Stop(self, memStream)

    def InitSkills(self):
        if self.skillGroups:
            return
        self.skillGroups = [ g.id for g in cfg.invgroups if g.categoryID == const.categorySkill and g.groupName[0] != '*' and g.groupName != 'NOT USED SKILLS' and g.groupName != 'Fake Skills' ]
        for rec in cfg.invtypes:
            gid = rec.groupID
            if gid in self.skillGroups:
                if gid in self.skillsByGroupID:
                    self.skillsByGroupID[gid].append(rec.typeID)
                else:
                    self.skillsByGroupID[gid] = [rec.typeID]

    def Show(self):
        if not (hasattr(eve.session, 'solarsystemid') and eve.session.solarsystemid2):
            Message('Hold your horses!', 'The trainer UI requires you to be logged in.')
            return
        if self.wnd:
            self.wnd.Maximize()
            return
        self.InitSkills()
        self.wnd = wnd = uicontrols.Window.Open(windowID=SERVICENAME)
        wnd._OnClose = self.Hide
        wnd.SetWndIcon(None)
        wnd.SetTopparentHeight(0)
        wnd.SetCaption('Trainer')
        root = uiutil.GetChild(wnd, 'main')
        main = uiprimitives.Container(name='main2', parent=root, pos=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        SKILLWIDTH = 256
        CENTERWIDTH = 128
        wnd.sr.scroll = s = uicontrols.Scroll(name='left', parent=main, align=uiconst.TOLEFT, width=SKILLWIDTH)
        middle = uiprimitives.Container(name='middle', parent=main, align=uiconst.TOLEFT, width=CENTERWIDTH)
        for x, y, icon, func, hint in [(CENTERWIDTH / 8,
          CENTERWIDTH * 1 / 4,
          'ui_23_64_2',
          self.AddSelected,
          'Add skills selected in the left panel to the current profile with the selected default level'),
         (CENTERWIDTH * 3 / 8,
          CENTERWIDTH,
          'ui_23_64_1',
          self.DelSelected,
          'Remove skills selected in the right panel from the current profile'),
         (CENTERWIDTH * 3 / 8,
          CENTERWIDTH * 3 / 2,
          'ui_27_64_3',
          self.Profile_Fix,
          'For each skill in the current profile, modify or add all required skills with the selected default level or the required level, whichever is higher'),
         (CENTERWIDTH * 3 / 8,
          CENTERWIDTH * 4 / 2,
          'res:/ui/Texture/WindowIcons/augmentations.png',
          self.Profile_ToCurrentCharacter,
          'Give skills in the current profile to current character'),
         (CENTERWIDTH * 3 / 8,
          CENTERWIDTH * 5 / 2,
          'ui_25_64_9',
          lambda *args: self.Profile_ToCharacter(),
          'Give skills in the current profile to a different character')]:
            btn = uix.GetBigButton(CENTERWIDTH / 2, middle, left=x, top=y, hint=hint)
            btn.sr.icon.LoadIcon(icon)
            btn.OnClick = func

        uicontrols.Button(parent=middle, label='Level', pos=(CENTERWIDTH / 8,
         0,
         0,
         0), func=self.CycleDefaultLevel)
        wnd.sr.level = uicontrols.Label(text=str(self.skillLevel), parent=middle, color=None, left=CENTERWIDTH / 2 + 5, top=2, height=16, state=uiconst.UI_NORMAL)
        content = []
        for gid in self.skillGroups:
            node = {'label': cfg.invgroups.Get(gid).name,
             'iconMargin': 18,
             'showlen': True,
             'groupItems': self.skillsByGroupID[gid],
             'state': 0,
             'allowCopy': 0,
             'GetSubContent': self.GetSubContent,
             'selected': 0,
             'id': (str(gid), gid),
             'sublevel': 0,
             'open': 0}
            content.append(listentry.Get('Group', node))

        s.Startup()
        s.sr.sortBy = 'name'
        s.sr.id = 'TrainerSkillTree'
        s.Load(contentList=content, fixedEntryHeight=None, headers=['Name'])
        r = uiprimitives.Container(name='right', parent=main, align=uiconst.TOLEFT, width=SKILLWIDTH)
        top = uiprimitives.Container(name='top', parent=r, align=uiconst.TOTOP, height=24)
        arrow = uicontrols.MenuIcon(size=24, ignoreSize=True)
        arrow.align = uiconst.TOLEFT
        arrow.left = top.left
        arrow.GetMenu = self.Profile_GetMenu
        arrow.state = uiconst.UI_NORMAL
        top.children.append(arrow)
        uicontrols.Button(parent=top, label='Save', align=uiconst.TORIGHT, func=self.Profile_SaveCurrent)
        uicontrols.Button(parent=top, label='Clear', align=uiconst.TORIGHT, func=self.Profile_New)
        wnd.sr.profile = uicontrols.Label(text='', parent=top, color=None, left=20, top=5, height=16)
        wnd.sr.scroll2 = s = uicontrols.Scroll(name='profile', parent=r, align=uiconst.TOALL)
        s.Startup()
        s.sr.sortBy = 'name'
        s.sr.id = 'ProfileSkillTree'
        self.Profile_Refresh()
        wnd.fixedWidth = wnd.width = const.defaultPadding + SKILLWIDTH + CENTERWIDTH + SKILLWIDTH + const.defaultPadding
        wnd.SetMinSize((wnd.fixedWidth, 416))
        wnd.Maximize(1)

    def Hide(self, *args):
        if self.wnd:
            self.wnd.Close()
            self.wnd = None

    def ProcessRestartUI(self):
        if self.wnd:
            self.Hide()
            self.Show()

    def GetSubContent(self, node, *args):
        content = []
        for typeID in node.groupItems:
            content.append(listentry.Get('Generic', {'label': cfg.invtypes.Get(typeID).name,
             'typeID': typeID,
             'showinfo': True,
             'sublevel': 1}))

        return content

    def Profile_GetMenu(self, *args):
        m = []
        INSIDERDIR = sm.GetService('insider').GetInsiderDir()
        for f, file in itools.itertree(INSIDERDIR):
            if file.endswith('.skills'):
                p = os.path.basename(file)[:-7]
                m.append(['Load ' + p, self.Profile_SwitchTo, (p,)])

        return m

    def Profile_SwitchTo(self, profilename):
        self.Profile_Load(profilename)

    def Profile_LoadInternal(self, name):
        profile = {}
        INSIDERDIR = sm.GetService('insider').GetInsiderDir()
        try:
            for line in open(os.path.join(INSIDERDIR, '%s.skills' % name), 'r'):
                line = filter(lambda x: x in '0123456789. ', line).split()
                typeID = 0
                level = 5
                for part in line:
                    part = int(float(part))
                    if part < 6 and part > 0:
                        level = part
                    elif cfg.invtypes.GetIfExists(part):
                        typeID = part

                if typeID:
                    profile[typeID] = level

        except IOError:
            return None

        return profile

    def Profile_Load(self, name):
        self.currentProfile = self.Profile_LoadInternal(name) or {}
        self.currentProfileName = name
        self.Profile_Refresh()

    def Profile_Save(self, name):
        INSIDERDIR = sm.GetService('insider').GetInsiderDir()
        f = open(os.path.join(INSIDERDIR, '%s.skills' % name), 'wb')
        for typeID, level in self.currentProfile.iteritems():
            f.write('%s %s\r\n' % (typeID, level))

        f.close()

    def Profile_SaveCurrent(self, *args):
        ret = uiutil.NamePopup('Save skill sheet as...', 'Enter profile name', setvalue=self.currentProfileName or 'New Profile', maxLength=32)
        if ret:
            self.currentProfileName = ret
            self.Profile_Save(self.currentProfileName)
            self.Profile_Refresh()

    def Profile_New(self, filename):
        self.currentProfile = {}
        self.currentProfileName = None
        self.Profile_Refresh()

    def Profile_GetSubContent(self, node, *args):
        content = []
        for typeID in node.groupItems:
            content.append(listentry.Get('Generic', {'label': '%s Level %d' % (cfg.invtypes.Get(typeID).name, self.currentProfile[typeID]),
             'typeID': typeID,
             'showinfo': True,
             'sublevel': 1}))

        return content

    def Profile_Fix(self, *args):

        def Fix0r(typeID):
            for rTypeID, rLevel in sm.GetService('skills').GetRequiredSkills(typeID).iteritems():
                if rTypeID != typeID:
                    self.currentProfile[rTypeID] = int(max(max(self.currentProfile.get(rTypeID, 1), rLevel), self.skillLevel))
                    Fix0r(rTypeID)

        for typeID in self.currentProfile.keys():
            Fix0r(typeID)

        self.Profile_Refresh()

    def Profile_Refresh(self):
        content = []
        for gid in self.skillGroups:
            items = [ typeID for typeID in self.currentProfile.iterkeys() if cfg.invtypes.Get(typeID).groupID == gid ]
            if items:
                node = {'label': cfg.invgroups.Get(gid).name,
                 'iconMargin': 18,
                 'showlen': True,
                 'groupItems': items,
                 'state': 0,
                 'allowCopy': 0,
                 'GetSubContent': self.Profile_GetSubContent,
                 'selected': 0,
                 'id': ('p' + str(gid), gid),
                 'sublevel': 0}
                content.append(listentry.Get('Group', node))

        self.wnd.sr.scroll2.Load(contentList=content, fixedEntryHeight=None, headers=['Name'])
        self.wnd.sr.profile.text = self.currentProfileName or '&lt;New Profile&gt;'

    def Profile_ToCharacter(self, charID = None):
        if not charID:
            ret = uiutil.NamePopup('Give Skills', 'Name of character to give skills to', setvalue='', maxLength=37)
            if ret:
                sm.GetService('loading').Cycle('   Searching...', 'for owner with %s in its name' % ret)
                charID = uix.Search(ret.lower(), const.groupCharacter, const.categoryOwner, hideNPC=1)
                sm.GetService('loading').StopCycle()
        if not charID:
            return
        self.ApplyProfile(self.currentProfile, charID)

    def Profile_ToCurrentCharacter(self):
        self.ApplyProfile(self.currentProfile, 'me')

    def ApplyProfile(self, profile, target):
        total = len(profile)
        i = 1
        for typeID, level in profile.iteritems():
            Progress('Apply Skill Profile', '[%s/%s] %s' % (i, total, cfg.invtypes.Get(typeID).name), i, total)
            i += 1
            Slash('/giveskill %s %s %d' % (target, typeID, level))

        Progress('Apply Skill Profile', 'Done!', 1, 1)

    def AddSelected(self, *args):
        for node in self.wnd.sr.scroll.GetNodes():
            if node.Get('selected', 0) and node.Get('typeID'):
                self.currentProfile[node.typeID] = self.skillLevel

        self.Profile_Refresh()

    def DelSelected(self, *args):
        for node in self.wnd.sr.scroll2.GetNodes():
            if node.Get('selected', 0):
                del self.currentProfile[node.typeID]

        self.Profile_Refresh()

    def CycleDefaultLevel(self, *args):
        if self.skillLevel < 5:
            self.skillLevel += 1
        else:
            self.skillLevel = 1
        self.wnd.sr.level.text = str(self.skillLevel)
