#Embedded file name: evefleet\menu.py
import evefleet.const
from .const import fleetRoleMember, fleetRoleSquadCmdr, fleetRoleWingCmdr, fleetRoleLeader, fleetJobCreator
from collections import defaultdict

def SetLabel(role):
    return {fleetRoleLeader: 'UI/Fleet/Ranks/FleetCommander',
     fleetRoleWingCmdr: 'UI/Fleet/Ranks/WingCommander',
     fleetRoleSquadCmdr: 'UI/Fleet/Ranks/SquadCommander'}.get(role, 'UI/Fleet/Ranks/SquadMember')


class MemberMenu(object):
    """
    Populates the menusvc with positions for moving members of a fleet or inviting new members.
    """

    def __init__(self, targetCharID, wings, members, callback, isFreeMove, isMove, MenuLabel, GetByLabel):
        self.targetCharID = targetCharID
        self.wings = wings
        self.members = members
        self.isFreeMove = isFreeMove
        self.isMove = isMove
        self.MenuLabel = MenuLabel
        self.GetByLabel = GetByLabel
        self.callback = callback
        self._SetRoles()
        self._SetFleet()
        self.fleetMenu = []

    def _SetRoles(self):
        self.selfMember = self.members[session.charid]
        self.targetMember = self.members.get(self.targetCharID, None)
        self.isSquadCmdr = self.selfMember.role == fleetRoleSquadCmdr
        self.isWingCmdr = self.selfMember.role == fleetRoleWingCmdr
        self.isFleetLeader = self.selfMember.role == fleetRoleLeader or self.selfMember.job & fleetJobCreator

    def _SetFleet(self):
        self.sortedWings = sorted(self.wings.iteritems())
        self.squads = defaultdict(list)
        for fleetMember in self.members.itervalues():
            if fleetMember.squadID not in (None, -1):
                self.squads[fleetMember.squadID].append(fleetMember)

        self.sortedSquads = []
        for w in self.wings.itervalues():
            self.sortedSquads.extend(w.squads.iterkeys())

        self.sortedSquads.sort()

    def Get(self):
        if session.fleetid is None:
            return []
        if self.isFleetLeader:
            self.SetValidFleetLeaderMoves()
        if self.IsFreeMove():
            self.SetValidFreeMoves()
        if self.IsInviteToFleet():
            self.fleetMenu.append([self.MenuLabel(SetLabel(fleetRoleMember)), self.callback, (self.targetCharID,
              None,
              None,
              None)])
        if self.isFleetLeader or self.isWingCmdr or self.isSquadCmdr or self.IsFreeMove():
            self.SetValidWingAndSquadMoves()
        return self.fleetMenu

    def GetMenuEntry(self, role, wingID, squadID):
        return [self.MenuLabel(SetLabel(role)), self.callback, (self.targetCharID,
          wingID,
          squadID,
          role)]

    def SetValidFleetLeaderMoves(self):
        if self.HasEmptyFleetCmdrPosition():
            self.fleetMenu.append(self.GetMenuEntry(fleetRoleLeader, None, None))
        if not self.targetMember:
            return
        if self.targetMember.role in [fleetRoleMember, fleetRoleSquadCmdr] and self.targetMember.wingID not in self.WingsWithCmdrs():
            self.fleetMenu.append(self.GetMenuEntry(fleetRoleWingCmdr, self.targetMember.wingID, None))

    def SetValidFreeMoves(self):
        if not self.targetMember:
            return
        if self.targetMember.role == fleetRoleMember and self.targetMember.squadID not in self.SquadsWithCmdrs():
            self.fleetMenu.append(self.GetMenuEntry(fleetRoleSquadCmdr, self.targetMember.wingID, self.targetMember.squadID))
        if self.targetMember.role == fleetRoleSquadCmdr:
            self.fleetMenu.append(self.GetMenuEntry(fleetRoleMember, self.targetMember.wingID, self.targetMember.squadID))

    def HasEmptyFleetCmdrPosition(self):
        for member in self.members.itervalues():
            if member.role == fleetRoleLeader:
                return False

        return True

    def WingsWithCmdrs(self):
        return [ member.wingID for member in self.members.itervalues() if member.role == fleetRoleWingCmdr ]

    def SquadsWithCmdrs(self):
        return [ member.squadID for member in self.members.itervalues() if member.role == fleetRoleSquadCmdr ]

    def IsFreeMove(self):
        if self.isFreeMove and self.targetCharID == session.charid:
            return True
        else:
            return False

    def SetValidWingAndSquadMoves(self):
        for wingIndex, (wingID, wing) in enumerate(self.sortedWings):
            if self.isWingCmdr:
                if self.targetMember and self.targetMember.wingID != self.selfMember.wingID:
                    continue
            if not (self.isFleetLeader or self.IsFreeMove()) and wingID != self.selfMember.wingID:
                continue
            for name, subSquads in self.GetSquads(wingIndex, wingID, wing):
                self.fleetMenu.append([name, subSquads])

    def GetSquads(self, wingIndex, wingID, wing):
        squadMenus = []
        subSquads = self.GetSubSquads(wingID)
        for squadID, squad in wing.squads.iteritems():
            if self.isSquadCmdr and not self.isFleetLeader and not self.IsFreeMove() and not self.IsMySquad(squadID):
                continue
            squadSize = len(self.squads.get(squadID, ()))
            if self.IsSquadFull(squadID, squadSize):
                continue
            for label, subMembers in self.SetValidSquadMoves(wingID, squadID, squad, squadSize):
                subSquads.append([label, subMembers])

        if subSquads:
            name = wing.name
            if name == '':
                name = self.MenuLabel('UI/Fleet/FleetSubmenus/WingX', {'wingNumber': wingIndex + 1})
            squadMenus.append([name, subSquads])
        return squadMenus

    def SetValidSquadMoves(self, wingID, squadID, squad, squadSize):
        subSquads = []
        subMembers = []
        if squadID not in self.SquadsWithCmdrs():
            subMembers.append(self.GetMenuEntry(fleetRoleSquadCmdr, wingID, squadID))
        if self.targetMember is None or self.targetMember.squadID != squadID or self.targetMember.role == fleetRoleSquadCmdr:
            subMembers.append(self.GetMenuEntry(fleetRoleMember, wingID, squadID))
        if subMembers:
            subSquads.append([self.GetSquadLabel(squad.name, squadSize, squadID), subMembers])
        return subSquads

    def GetSquadLabel(self, squadName, squadSize, squadID):
        if squadName == '':
            squadName = self.GetByLabel('UI/Fleet/FleetSubmenus/SquadX', squadNumber=self.sortedSquads.index(squadID) + 1)
        label = self.MenuLabel('UI/Fleet/FleetSubmenus/SquadNameWithNumMembers', {'squadName': squadName,
         'numMembers': squadSize})
        return label

    def IsSquadFull(self, squadID, squadSize):
        if squadSize >= evefleet.const.MAX_MEMBERS_IN_SQUAD and (not self.targetMember or not self.IsTargetMemberSquad(squadID)):
            return True
        else:
            return False

    def GetSubSquads(self, wingID):
        if self.isFleetLeader and wingID not in self.WingsWithCmdrs():
            subSquads = [[self.MenuLabel('UI/Fleet/Ranks/WingCommander'), self.callback, (self.targetCharID,
               wingID,
               None,
               fleetRoleWingCmdr)]]
        else:
            subSquads = []
        return subSquads

    def IsMySquad(self, squadID):
        return squadID == self.selfMember.squadID

    def IsTargetMemberSquad(self, squadID):
        return squadID == self.targetMember.squadID

    def IsInviteToFleet(self):
        return not self.isMove
