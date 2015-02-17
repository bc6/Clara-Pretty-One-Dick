#Embedded file name: eve/common/script/util\notificationconst.py
"""
Contains functions and mappings for the notification system that are used both on the client and on the server (or in ESP)
"""
notificationTypeOldLscMessages = 1
notificationTypeCharTerminationMsg = 2
notificationTypeCharMedalMsg = 3
notificationTypeAllMaintenanceBillMsg = 4
notificationTypeAllWarDeclaredMsg = 5
notificationTypeAllWarSurrenderMsg = 6
notificationTypeAllWarRetractedMsg = 7
notificationTypeAllWarInvalidatedMsg = 8
notificationTypeCharBillMsg = 9
notificationTypeCorpAllBillMsg = 10
notificationTypeBillOutOfMoneyMsg = 11
notificationTypeBillPaidCharMsg = 12
notificationTypeBillPaidCorpAllMsg = 13
notificationTypeBountyClaimMsg = 14
notificationTypeCloneActivationMsg = 15
notificationTypeCorpAppNewMsg = 16
notificationTypeCorpAppRejectMsg = 17
notificationTypeCorpAppAcceptMsg = 18
notificationTypeCorpTaxChangeMsg = 19
notificationTypeCorpNewsMsg = 20
notificationTypeCharLeftCorpMsg = 21
notificationTypeCorpNewCEOMsg = 22
notificationTypeCorpDividendMsg = 23
notificationTypeCorpVoteMsg = 25
notificationTypeCorpVoteCEORevokedMsg = 26
notificationTypeCorpWarDeclaredMsg = 27
notificationTypeCorpWarFightingLegalMsg = 28
notificationTypeCorpWarSurrenderMsg = 29
notificationTypeCorpWarRetractedMsg = 30
notificationTypeCorpWarInvalidatedMsg = 31
notificationTypeContainerPasswordMsg = 32
notificationTypeCustomsMsg = 33
notificationTypeInsuranceFirstShipMsg = 34
notificationTypeInsurancePayoutMsg = 35
notificationTypeInsuranceInvalidatedMsg = 36
notificationTypeSovAllClaimFailMsg = 37
notificationTypeSovCorpClaimFailMsg = 38
notificationTypeSovAllBillLateMsg = 39
notificationTypeSovCorpBillLateMsg = 40
notificationTypeSovAllClaimLostMsg = 41
notificationTypeSovCorpClaimLostMsg = 42
notificationTypeSovAllClaimAquiredMsg = 43
notificationTypeSovCorpClaimAquiredMsg = 44
notificationTypeAllAnchoringMsg = 45
notificationTypeAllStructVulnerableMsg = 46
notificationTypeAllStrucInvulnerableMsg = 47
notificationTypeSovDisruptorMsg = 48
notificationTypeCorpStructLostMsg = 49
notificationTypeCorpOfficeExpirationMsg = 50
notificationTypeCloneRevokedMsg1 = 51
notificationTypeCloneMovedMsg = 52
notificationTypeCloneRevokedMsg2 = 53
notificationTypeInsuranceExpirationMsg = 54
notificationTypeInsuranceIssuedMsg = 55
notificationTypeJumpCloneDeletedMsg1 = 56
notificationTypeJumpCloneDeletedMsg2 = 57
notificationTypeFWCorpJoinMsg = 58
notificationTypeFWCorpLeaveMsg = 59
notificationTypeFWCorpKickMsg = 60
notificationTypeFWCharKickMsg = 61
notificationTypeFWCorpWarningMsg = 62
notificationTypeFWCharWarningMsg = 63
notificationTypeFWCharRankLossMsg = 64
notificationTypeFWCharRankGainMsg = 65
notificationTypeAgentMoveMsg = 66
notificationTypeTransactionReversalMsg = 67
notificationTypeReimbursementMsg = 68
notificationTypeLocateCharMsg = 69
notificationTypeResearchMissionAvailableMsg = 70
notificationTypeMissionOfferExpirationMsg = 71
notificationTypeMissionTimeoutMsg = 72
notificationTypeStoryLineMissionAvailableMsg = 73
notificationTypeTutorialMsg = 74
notificationTypeTowerAlertMsg = 75
notificationTypeTowerResourceAlertMsg = 76
notificationTypeStationAggressionMsg1 = 77
notificationTypeStationStateChangeMsg = 78
notificationTypeStationConquerMsg = 79
notificationTypeStationAggressionMsg2 = 80
notificationTypeFacWarCorpJoinRequestMsg = 81
notificationTypeFacWarCorpLeaveRequestMsg = 82
notificationTypeFacWarCorpJoinWithdrawMsg = 83
notificationTypeFacWarCorpLeaveWithdrawMsg = 84
notificationTypeCorpLiquidationMsg = 85
notificationTypeSovereigntyTCUDamageMsg = 86
notificationTypeSovereigntySBUDamageMsg = 87
notificationTypeSovereigntyIHDamageMsg = 88
notificationTypeContactAdd = 89
notificationTypeContactEdit = 90
notificationTypeIncursionCompletedMsg = 91
notificationTypeCorpKicked = 92
notificationTypeOrbitalAttacked = 93
notificationTypeOrbitalReinforced = 94
notificationTypeOwnershipTransferred = 95
notificationTypeFWAllianceWarningMsg = 96
notificationTypeFWAllianceKickMsg = 97
notificationTypeAllWarCorpJoinedAllianceMsg = 98
notificationTypeAllyJoinedWarDefenderMsg = 99
notificationTypeAllyJoinedWarAggressorMsg = 100
notificationTypeAllyJoinedWarAllyMsg = 101
notificationTypeMercOfferedNegotiationMsg = 102
notificationTypeWarSurrenderOfferMsg = 103
notificationTypeWarSurrenderDeclinedMsg = 104
notificationTypeFacWarLPPayoutKill = 105
notificationTypeFacWarLPPayoutEvent = 106
notificationTypeFacWarLPDisqualifiedEvent = 107
notificationTypeFacWarLPDisqualifiedKill = 108
notificationTypeAllyContractCancelled = 109
notificationTypeWarAllyOfferDeclinedMsg = 110
notificationTypeBountyYourBountyClaimed = 111
notificationTypeBountyPlacedChar = 112
notificationTypeBountyPlacedCorp = 113
notificationTypeBountyPlacedAlliance = 114
notificationTypeKillRightAvailable = 115
notificationTypeKillRightAvailableOpen = 116
notificationTypeKillRightEarned = 117
notificationTypeKillRightUsed = 118
notificationTypeKillRightUnavailable = 119
notificationTypeKillRightUnavailableOpen = 120
notificationTypeDeclareWar = 121
notificationTypeOfferedSurrender = 122
notificationTypeAcceptedSurrender = 123
notificationTypeMadeWarMutual = 124
notificationTypeRetractsWar = 125
notificationTypeOfferedToAlly = 126
notificationTypeAcceptedAlly = 127
notificationTypeCharAppAcceptMsg = 128
notificationTypeCharAppRejectMsg = 129
notificationTypeCharAppWithdrawMsg = 130
notificationTypeDustAppAcceptedMsg = 131
notificationTypeDistrictAttacked = 132
notificationTypeBattlePunishFriendlyFire = 133
notificationTypeBountyESSTaken = 134
notificationTypeBountyESSShared = 135
notificationTypeIndustryTeamAuctionWon = 136
notificationTypeIndustryTeamAuctionLost = 137
notificationTypeCloneActivationMsg2 = 138
notificationTypeCorpAppInvitedMsg = 139
notificationTypeKillReportVictim = 140
notificationTypeKillReportFinalBlow = 141
notificationTypeCorpAppRejectCustomMsg = 142
notificationTypeCorpFriendlyFireEnableTimerStarted = 143
notificationTypeCorpFriendlyFireDisableTimerStarted = 144
notificationTypeCorpFriendlyFireEnableTimerCompleted = 145
notificationTypeCorpFriendlyFireDisableTimerCompleted = 146
notificationTypeSkillEmptyQueue = 1002
notificationTypeSkillFinished = 1000
notificationTypeMailSummary = 1003
notificationTypeNewMailFrom = 1004
notificationTypeUnusedSkillPoints = 1005
notificationTypeContractAssigned = 1006
notificationTypeContractNeedsAttention = 1007
notificationTypeContactSignedOn = 2001
notificationTypeContactSignedOff = 2002
notificationTypeAchievementTaskFinished = 1010
notificationTypeOpportunityFinished = 1011
notificationToSettingDescription = {notificationTypeContactSignedOn: 'Notifications/NotificationNames/WatchedContactOnline',
 notificationTypeContactSignedOff: 'Notifications/NotificationNames/WatchedContactOffline',
 notificationTypeSkillFinished: 'Notifications/NotificationNames/SkillTrainingComplete',
 notificationTypeSkillEmptyQueue: 'Notifications/NotificationNames/SkillQueueEmpty',
 notificationTypeOldLscMessages: 'Notifications/NotificationNames/OldNotifications',
 notificationTypeCharTerminationMsg: 'Notifications/NotificationNames/MemberBiomassed',
 notificationTypeCharMedalMsg: 'Notifications/NotificationNames/MedalAwarded',
 notificationTypeAllMaintenanceBillMsg: 'Notifications/NotificationNames/AllianceMaintenanceBill',
 notificationTypeAllWarDeclaredMsg: 'Notifications/NotificationNames/AllianceWarDeclared',
 notificationTypeAllWarSurrenderMsg: 'Notifications/NotificationNames/AllianceWarSurrender',
 notificationTypeAllWarRetractedMsg: 'Notifications/NotificationNames/AllianceWarRetracted',
 notificationTypeAllWarInvalidatedMsg: 'Notifications/NotificationNames/AllianceWarInvalidated',
 notificationTypeCharBillMsg: 'Notifications/NotificationNames/PilotBilled',
 notificationTypeCorpAllBillMsg: 'Notifications/NotificationNames/OrganizationBilled',
 notificationTypeBillOutOfMoneyMsg: 'Notifications/NotificationNames/InsufficientFundsToPayBill',
 notificationTypeBillPaidCharMsg: 'Notifications/NotificationNames/BillPaidByPilot',
 notificationTypeBillPaidCorpAllMsg: 'Notifications/NotificationNames/BillPaidByOrganization',
 notificationTypeBountyClaimMsg: 'Notifications/NotificationNames/CapsuleerBountyPayment',
 notificationTypeCloneActivationMsg: 'Notifications/NotificationNames/CloneActivation',
 notificationTypeCloneActivationMsg2: 'Notifications/NotificationNames/CloneActivation',
 notificationTypeCorpAppNewMsg: 'Notifications/NotificationNames/NewApplicationToJoinCorporation',
 notificationTypeCorpAppRejectMsg: 'Notifications/NotificationNames/YourCorporateApplicationRejected',
 notificationTypeCorpAppRejectCustomMsg: 'Notifications/NotificationNames/YourCorporateApplicationRejected',
 notificationTypeCorpAppAcceptMsg: 'Notifications/NotificationNames/YourCorporateApplicationAccepted',
 notificationTypeCorpAppInvitedMsg: 'Notifications/NotificationNames/NewInvitationToJoinCorp',
 notificationTypeCorpTaxChangeMsg: 'Notifications/NotificationNames/CorporationTaxChange',
 notificationTypeCorpNewsMsg: 'Notifications/NotificationNames/CorporationNews',
 notificationTypeCharLeftCorpMsg: 'Notifications/NotificationNames/PilotLeftCorporation',
 notificationTypeCorpNewCEOMsg: 'Notifications/NotificationNames/NewCorporationCEO',
 notificationTypeCorpDividendMsg: 'Notifications/NotificationNames/CorporateDividendPayout',
 notificationTypeCorpVoteMsg: 'Notifications/NotificationNames/CorporateVoteNotification',
 notificationTypeCorpVoteCEORevokedMsg: 'Notifications/NotificationNames/CEORolesRevokedDuringVote',
 notificationTypeCorpWarDeclaredMsg: 'Notifications/NotificationNames/CorporationWarDeclared',
 notificationTypeCorpWarFightingLegalMsg: 'Notifications/NotificationNames/CorporationWarFighting',
 notificationTypeCorpWarSurrenderMsg: 'Notifications/NotificationNames/CorporationWarSurrender',
 notificationTypeCorpWarRetractedMsg: 'Notifications/NotificationNames/CorporationWarRetracted',
 notificationTypeCorpWarInvalidatedMsg: 'Notifications/NotificationNames/CorporationWarInvalidated',
 notificationTypeContainerPasswordMsg: 'Notifications/NotificationNames/ContainerPassword',
 notificationTypeCustomsMsg: 'Notifications/NotificationNames/CustomsNotification',
 notificationTypeInsuranceFirstShipMsg: 'Notifications/NotificationNames/RookieShipReplacement',
 notificationTypeInsurancePayoutMsg: 'Notifications/NotificationNames/InsurancePayment',
 notificationTypeInsuranceInvalidatedMsg: 'Notifications/NotificationNames/InsuranceInvalidated',
 notificationTypeSovAllClaimFailMsg: 'Notifications/NotificationNames/AllianceSovereigntyClaimFailed',
 notificationTypeSovCorpClaimFailMsg: 'Notifications/NotificationNames/CorporateSovereigntyClaimFailed',
 notificationTypeSovAllBillLateMsg: 'Notifications/NotificationNames/AllianceSovereigntyBillDue',
 notificationTypeSovCorpBillLateMsg: 'Notifications/NotificationNames/CorporateAllianceBillDue',
 notificationTypeSovAllClaimLostMsg: 'Notifications/NotificationNames/AllianceSovereigntyClaimLost',
 notificationTypeSovCorpClaimLostMsg: 'Notifications/NotificationNames/CorporateSovereigntyClaimLost',
 notificationTypeSovAllClaimAquiredMsg: 'Notifications/NotificationNames/AllianceSovereigntyClaimAquired',
 notificationTypeSovCorpClaimAquiredMsg: 'Notifications/NotificationNames/CorporateSovereigntyClaimAquired',
 notificationTypeAllAnchoringMsg: 'Notifications/NotificationNames/StructureAnchoring',
 notificationTypeAllStructVulnerableMsg: 'Notifications/NotificationNames/SovereigntyStructuresVulnerable',
 notificationTypeAllStrucInvulnerableMsg: 'Notifications/NotificationNames/SovereigntyStructuresInvulnerable',
 notificationTypeSovDisruptorMsg: 'Notifications/NotificationNames/SovereigntyBlockadeUnitActive',
 notificationTypeCorpStructLostMsg: 'Notifications/NotificationNames/StructureLost',
 notificationTypeCorpOfficeExpirationMsg: 'Notifications/NotificationNames/OfficeLeaseExpiration',
 notificationTypeCloneRevokedMsg1: 'Notifications/NotificationNames/CloneContractRevoked1',
 notificationTypeCloneMovedMsg: 'Notifications/NotificationNames/CloneMoved',
 notificationTypeCloneRevokedMsg2: 'Notifications/NotificationNames/CloneContractRevoked2',
 notificationTypeInsuranceExpirationMsg: 'Notifications/NotificationNames/InsuranceExpired',
 notificationTypeInsuranceIssuedMsg: 'Notifications/NotificationNames/InsuranceIssued',
 notificationTypeJumpCloneDeletedMsg1: 'Notifications/NotificationNames/JumpCloneDeleted',
 notificationTypeJumpCloneDeletedMsg2: 'Notifications/NotificationNames/JumpCloneDistruction',
 notificationTypeFWCorpJoinMsg: 'Notifications/NotificationNames/CorporationHasJoinedFaction',
 notificationTypeFWCorpLeaveMsg: 'Notifications/NotificationNames/CorporationHasLeftFaction',
 notificationTypeFWCorpKickMsg: 'Notifications/NotificationNames/CorporationExpelledFromFaction',
 notificationTypeFWCharKickMsg: 'Notifications/NotificationNames/PilotExpelledFromFaction',
 notificationTypeFWCorpWarningMsg: 'Notifications/NotificationNames/CorporationFactionStandingWarning',
 notificationTypeFWCharWarningMsg: 'Notifications/NotificationNames/PilotFactionStandingWarning',
 notificationTypeFWCharRankLossMsg: 'Notifications/NotificationNames/PilotLosesFactionRank',
 notificationTypeFWCharRankGainMsg: 'Notifications/NotificationNames/PilotGainsFactionRank',
 notificationTypeAgentMoveMsg: 'Notifications/NotificationNames/AgentMovedNotice',
 notificationTypeTransactionReversalMsg: 'Notifications/NotificationNames/TransactionReversal',
 notificationTypeReimbursementMsg: 'Notifications/NotificationNames/Reimbursement',
 notificationTypeLocateCharMsg: 'Notifications/NotificationNames/PilotLocated',
 notificationTypeResearchMissionAvailableMsg: 'Notifications/NotificationNames/ResearchMissionAvailable',
 notificationTypeMissionOfferExpirationMsg: 'Notifications/NotificationNames/MissionOfferExpiration',
 notificationTypeMissionTimeoutMsg: 'Notifications/NotificationNames/MissionFailure',
 notificationTypeStoryLineMissionAvailableMsg: 'Notifications/NotificationNames/SpecialMissionAvailable',
 notificationTypeTutorialMsg: 'Notifications/NotificationNames/TutorialProgram',
 notificationTypeTowerAlertMsg: 'Notifications/NotificationNames/TowerUnderAttackAlert',
 notificationTypeTowerResourceAlertMsg: 'Notifications/NotificationNames/TowerResourceAlert',
 notificationTypeStationAggressionMsg1: 'Notifications/NotificationNames/StationUnderAttack',
 notificationTypeStationStateChangeMsg: 'Notifications/NotificationNames/StationChanged',
 notificationTypeStationConquerMsg: 'Notifications/NotificationNames/StationConquered',
 notificationTypeStationAggressionMsg2: 'Notifications/NotificationNames/StationAggression',
 notificationTypeFacWarCorpJoinRequestMsg: 'Notifications/NotificationNames/CorporationJoiningFaction',
 notificationTypeFacWarCorpLeaveRequestMsg: 'Notifications/NotificationNames/CorporationLeavingFaction',
 notificationTypeFacWarCorpJoinWithdrawMsg: 'Notifications/NotificationNames/CorporationJoinFactionWithdrawn',
 notificationTypeFacWarCorpLeaveWithdrawMsg: 'Notifications/NotificationNames/CorporationLeaveFactionWithdrawn',
 notificationTypeCorpLiquidationMsg: 'Notifications/NotificationNames/CorporateLiquidationSettlement',
 notificationTypeSovereigntyTCUDamageMsg: 'Notifications/NotificationNames/SovereigntyTCUDamage',
 notificationTypeSovereigntySBUDamageMsg: 'Notifications/NotificationNames/SovereigntySBUDamage',
 notificationTypeSovereigntyIHDamageMsg: 'Notifications/NotificationNames/SovereigntyIHUBDamage',
 notificationTypeContactAdd: 'Notifications/NotificationNames/AddedAsContact',
 notificationTypeContactEdit: 'Notifications/NotificationNames/ContactLevelModified',
 notificationTypeIncursionCompletedMsg: 'Notifications/NotificationNames/IncursionCompleted',
 notificationTypeCorpKicked: 'Notifications/NotificationNames/KickedFromCorporation',
 notificationTypeOrbitalAttacked: 'Notifications/NotificationNames/OrbitalStructureAttacked',
 notificationTypeOrbitalReinforced: 'Notifications/NotificationNames/OrbitalStructureReinforced',
 notificationTypeOwnershipTransferred: 'Notifications/NotificationNames/StructureOwnershipTransferred',
 notificationTypeFWAllianceWarningMsg: 'Notifications/NotificationNames/AllianceFactionStandingWarning',
 notificationTypeFWAllianceKickMsg: 'Notifications/NotificationNames/AllianceExpelledFromFaction',
 notificationTypeAllWarCorpJoinedAllianceMsg: 'Notifications/NotificationNames/CorporationJoinedAllianceAtWar',
 notificationTypeAllyJoinedWarDefenderMsg: 'Notifications/NotificationNames/DefenderAllyJoinsWar',
 notificationTypeAllyJoinedWarAggressorMsg: 'Notifications/NotificationNames/AggressorAllyJoinsWar',
 notificationTypeAllyJoinedWarAllyMsg: 'Notifications/NotificationNames/CorporationJoinsWarAsAlly',
 notificationTypeMercOfferedNegotiationMsg: 'Notifications/NotificationNames/WarAllyOfferReceived',
 notificationTypeWarSurrenderOfferMsg: 'Notifications/NotificationNames/SurrenderOfferReceived',
 notificationTypeWarSurrenderDeclinedMsg: 'Notifications/NotificationNames/SurrenderDeclined',
 notificationTypeFacWarLPPayoutKill: 'Notifications/NotificationNames/FactionKillEventLP',
 notificationTypeFacWarLPPayoutEvent: 'Notifications/NotificationNames/FactionStrategicEventLP',
 notificationTypeFacWarLPDisqualifiedEvent: 'Notifications/NotificationNames/StrategicEventLPDisqualification',
 notificationTypeFacWarLPDisqualifiedKill: 'Notifications/NotificationNames/KillEventLPDisqualification',
 notificationTypeAllyContractCancelled: 'Notifications/NotificationNames/WarAllyAgreementCancelled',
 notificationTypeWarAllyOfferDeclinedMsg: 'Notifications/NotificationNames/WarAllyOfferDeclined',
 notificationTypeBountyYourBountyClaimed: 'Notifications/NotificationNames/BountyOnYouClaimed',
 notificationTypeBountyPlacedChar: 'Notifications/NotificationNames/BountyPlacedOnYou',
 notificationTypeBountyPlacedCorp: 'Notifications/NotificationNames/BountyPlacedOnCorporation',
 notificationTypeBountyPlacedAlliance: 'Notifications/NotificationNames/BountyPlacedOnAlliance',
 notificationTypeKillRightAvailable: 'Notifications/NotificationNames/KillRightAvailable',
 notificationTypeKillRightAvailableOpen: 'Notifications/NotificationNames/KillRightAvailableToAll',
 notificationTypeKillRightEarned: 'Notifications/NotificationNames/KillRightEarned',
 notificationTypeKillRightUsed: 'Notifications/NotificationNames/KillRightUsed',
 notificationTypeKillRightUnavailable: 'Notifications/NotificationNames/KillRightUnavailable',
 notificationTypeKillRightUnavailableOpen: 'Notifications/NotificationNames/KillRightUnavailableToAll',
 notificationTypeDeclareWar: 'Notifications/NotificationNames/WarDeclaration',
 notificationTypeOfferedSurrender: 'Notifications/NotificationNames/SurrenderOffered',
 notificationTypeAcceptedSurrender: 'Notifications/NotificationNames/SurrenderAccepted',
 notificationTypeMadeWarMutual: 'Notifications/NotificationNames/WarMadeMutual',
 notificationTypeRetractsWar: 'Notifications/NotificationNames/WarRetracted',
 notificationTypeOfferedToAlly: 'Notifications/NotificationNames/YouOfferedWarAlly',
 notificationTypeAcceptedAlly: 'Notifications/NotificationNames/YouAcceptedWarAlly',
 notificationTypeCharAppAcceptMsg: 'Notifications/NotificationNames/MercenaryInvitationAccepted',
 notificationTypeCharAppRejectMsg: 'Notifications/NotificationNames/MercenaryInvitationRejected',
 notificationTypeCharAppWithdrawMsg: 'Notifications/NotificationNames/MercenaryApplicationWithdrawn',
 notificationTypeDustAppAcceptedMsg: 'Notifications/NotificationNames/MercenaryApplicationAccepted',
 notificationTypeDistrictAttacked: 'Notifications/NotificationNames/CorporationDistrictAttacked',
 notificationTypeBattlePunishFriendlyFire: 'Notifications/NotificationNames/FriendlyFireStandingsLoss',
 notificationTypeBountyESSTaken: 'Notifications/NotificationNames/ESSPoolTaken',
 notificationTypeBountyESSShared: 'Notifications/NotificationNames/ESSPoolShared',
 notificationTypeIndustryTeamAuctionWon: 'Notifications/NotificationNames/IndustryTeamAuctionWon',
 notificationTypeIndustryTeamAuctionLost: 'Notifications/NotificationNames/IndustryTeamAuctionLost',
 notificationTypeMailSummary: 'Notifications/NotificationNames/NewMailSummary',
 notificationTypeNewMailFrom: 'Notifications/NotificationNames/NewMail',
 notificationTypeUnusedSkillPoints: 'Notifications/NotificationNames/UnusedSkillPoints',
 notificationTypeContractAssigned: 'Notifications/NotificationNames/ContractAssigned',
 notificationTypeContractNeedsAttention: 'Notifications/NotificationNames/ContractNeedsAttention',
 notificationTypeKillReportVictim: 'Notifications/NotificationNames/KillReportYouDied',
 notificationTypeKillReportFinalBlow: 'Notifications/NotificationNames/KillReportFinalBlow',
 notificationTypeCorpFriendlyFireEnableTimerStarted: 'Notifications/NotificationNames/CorpFriendlyFireEnableTimerStarted',
 notificationTypeCorpFriendlyFireDisableTimerStarted: 'Notifications/NotificationNames/CorpFriendlyFireDisableTimerStarted',
 notificationTypeCorpFriendlyFireEnableTimerCompleted: 'Notifications/NotificationNames/CorpFriendlyFireEnableTimerCompleted',
 notificationTypeCorpFriendlyFireDisableTimerCompleted: 'Notifications/NotificationNames/CorpFriendlyFireDisableTimerCompleted',
 notificationTypeAchievementTaskFinished: 'Notifications/NotificationNames/OpportunityTaskCompleted',
 notificationTypeOpportunityFinished: 'Notifications/NotificationNames/OpportunityCompleted'}
groupUnread = 0
groupAgents = 1
groupBills = 2
groupCorp = 3
groupMisc = 4
groupOld = 5
groupSov = 6
groupStructures = 7
groupWar = 8
groupContacts = 9
groupBounties = 10
groupInsurance = 11
groupSkillTraining = 12
groupOpportunities = 13
groupTypes = {groupSkillTraining: [notificationTypeSkillEmptyQueue, notificationTypeSkillFinished, notificationTypeUnusedSkillPoints],
 groupAgents: [notificationTypeAgentMoveMsg,
               notificationTypeLocateCharMsg,
               notificationTypeResearchMissionAvailableMsg,
               notificationTypeMissionOfferExpirationMsg,
               notificationTypeMissionTimeoutMsg,
               notificationTypeStoryLineMissionAvailableMsg,
               notificationTypeTutorialMsg],
 groupBills: [notificationTypeAllMaintenanceBillMsg,
              notificationTypeCharBillMsg,
              notificationTypeCorpAllBillMsg,
              notificationTypeBillOutOfMoneyMsg,
              notificationTypeBillPaidCharMsg,
              notificationTypeBillPaidCorpAllMsg,
              notificationTypeCorpOfficeExpirationMsg],
 groupContacts: [notificationTypeContactAdd,
                 notificationTypeContactEdit,
                 notificationTypeContactSignedOn,
                 notificationTypeContactSignedOff],
 groupCorp: [notificationTypeCharTerminationMsg,
             notificationTypeCharMedalMsg,
             notificationTypeCorpAppNewMsg,
             notificationTypeCorpAppRejectMsg,
             notificationTypeCorpAppRejectCustomMsg,
             notificationTypeCorpAppAcceptMsg,
             notificationTypeCorpAppInvitedMsg,
             notificationTypeCorpTaxChangeMsg,
             notificationTypeCorpNewsMsg,
             notificationTypeCharLeftCorpMsg,
             notificationTypeCorpNewCEOMsg,
             notificationTypeCorpDividendMsg,
             notificationTypeCorpVoteMsg,
             notificationTypeCorpVoteCEORevokedMsg,
             notificationTypeCorpLiquidationMsg,
             notificationTypeCorpKicked,
             notificationTypeCharAppAcceptMsg,
             notificationTypeCharAppRejectMsg,
             notificationTypeCharAppWithdrawMsg,
             notificationTypeDustAppAcceptedMsg,
             notificationTypeCorpFriendlyFireEnableTimerStarted,
             notificationTypeCorpFriendlyFireDisableTimerStarted,
             notificationTypeCorpFriendlyFireEnableTimerCompleted,
             notificationTypeCorpFriendlyFireDisableTimerCompleted],
 groupInsurance: {notificationTypeInsuranceFirstShipMsg,
                  notificationTypeInsurancePayoutMsg,
                  notificationTypeInsuranceInvalidatedMsg,
                  notificationTypeInsuranceExpirationMsg,
                  notificationTypeInsuranceIssuedMsg},
 groupMisc: [notificationTypeCloneActivationMsg,
             notificationTypeCloneActivationMsg2,
             notificationTypeContainerPasswordMsg,
             notificationTypeCustomsMsg,
             notificationTypeCloneRevokedMsg1,
             notificationTypeCloneMovedMsg,
             notificationTypeCloneRevokedMsg2,
             notificationTypeJumpCloneDeletedMsg1,
             notificationTypeJumpCloneDeletedMsg2,
             notificationTypeTransactionReversalMsg,
             notificationTypeReimbursementMsg,
             notificationTypeIncursionCompletedMsg,
             notificationTypeKillRightAvailable,
             notificationTypeKillRightAvailableOpen,
             notificationTypeKillRightEarned,
             notificationTypeKillRightUsed,
             notificationTypeKillRightUnavailable,
             notificationTypeKillRightUnavailableOpen,
             notificationTypeBattlePunishFriendlyFire,
             notificationTypeBountyESSTaken,
             notificationTypeBountyESSShared,
             notificationTypeIndustryTeamAuctionWon,
             notificationTypeIndustryTeamAuctionLost,
             notificationTypeMailSummary,
             notificationTypeNewMailFrom,
             notificationTypeContractAssigned,
             notificationTypeContractNeedsAttention,
             notificationTypeAchievementTaskFinished],
 groupOld: [notificationTypeOldLscMessages],
 groupSov: [notificationTypeSovAllClaimFailMsg,
            notificationTypeSovCorpClaimFailMsg,
            notificationTypeSovAllBillLateMsg,
            notificationTypeSovCorpBillLateMsg,
            notificationTypeSovAllClaimLostMsg,
            notificationTypeSovCorpClaimLostMsg,
            notificationTypeSovAllClaimAquiredMsg,
            notificationTypeSovCorpClaimAquiredMsg,
            notificationTypeSovDisruptorMsg,
            notificationTypeAllStructVulnerableMsg,
            notificationTypeAllStrucInvulnerableMsg,
            notificationTypeSovereigntyTCUDamageMsg,
            notificationTypeSovereigntySBUDamageMsg,
            notificationTypeSovereigntyIHDamageMsg],
 groupStructures: [notificationTypeAllAnchoringMsg,
                   notificationTypeCorpStructLostMsg,
                   notificationTypeTowerAlertMsg,
                   notificationTypeTowerResourceAlertMsg,
                   notificationTypeStationAggressionMsg1,
                   notificationTypeStationStateChangeMsg,
                   notificationTypeStationConquerMsg,
                   notificationTypeStationAggressionMsg2,
                   notificationTypeOrbitalAttacked,
                   notificationTypeOrbitalReinforced,
                   notificationTypeOwnershipTransferred,
                   notificationTypeDistrictAttacked],
 groupWar: [notificationTypeAllWarDeclaredMsg,
            notificationTypeAllWarSurrenderMsg,
            notificationTypeAllWarRetractedMsg,
            notificationTypeAllWarInvalidatedMsg,
            notificationTypeCorpWarDeclaredMsg,
            notificationTypeCorpWarFightingLegalMsg,
            notificationTypeCorpWarSurrenderMsg,
            notificationTypeCorpWarRetractedMsg,
            notificationTypeCorpWarInvalidatedMsg,
            notificationTypeFWCorpJoinMsg,
            notificationTypeFWCorpLeaveMsg,
            notificationTypeFWCorpKickMsg,
            notificationTypeFWCharKickMsg,
            notificationTypeFWCorpWarningMsg,
            notificationTypeFWCharWarningMsg,
            notificationTypeFWCharRankLossMsg,
            notificationTypeFWCharRankGainMsg,
            notificationTypeFacWarCorpJoinRequestMsg,
            notificationTypeFacWarCorpLeaveRequestMsg,
            notificationTypeFacWarCorpJoinWithdrawMsg,
            notificationTypeFacWarCorpLeaveWithdrawMsg,
            notificationTypeFWAllianceWarningMsg,
            notificationTypeFWAllianceKickMsg,
            notificationTypeAllWarCorpJoinedAllianceMsg,
            notificationTypeAllyJoinedWarDefenderMsg,
            notificationTypeAllyJoinedWarAggressorMsg,
            notificationTypeAllyJoinedWarAllyMsg,
            notificationTypeMercOfferedNegotiationMsg,
            notificationTypeWarSurrenderOfferMsg,
            notificationTypeWarSurrenderDeclinedMsg,
            notificationTypeFacWarLPPayoutKill,
            notificationTypeFacWarLPPayoutEvent,
            notificationTypeFacWarLPDisqualifiedEvent,
            notificationTypeFacWarLPDisqualifiedKill,
            notificationTypeAllyContractCancelled,
            notificationTypeWarAllyOfferDeclinedMsg,
            notificationTypeDeclareWar,
            notificationTypeOfferedSurrender,
            notificationTypeAcceptedSurrender,
            notificationTypeMadeWarMutual,
            notificationTypeRetractsWar,
            notificationTypeOfferedToAlly,
            notificationTypeAcceptedAlly,
            notificationTypeKillReportVictim,
            notificationTypeKillReportFinalBlow],
 groupBounties: [notificationTypeBountyClaimMsg,
                 notificationTypeBountyYourBountyClaimed,
                 notificationTypeBountyPlacedChar,
                 notificationTypeBountyPlacedCorp,
                 notificationTypeBountyPlacedAlliance],
 groupOpportunities: [notificationTypeAchievementTaskFinished, notificationTypeOpportunityFinished]}
nonCommunicationTypes = [notificationTypeContactSignedOn,
 notificationTypeContactSignedOff,
 notificationTypeMailSummary,
 notificationTypeNewMailFrom,
 notificationTypeUnusedSkillPoints,
 notificationTypeContractAssigned,
 notificationTypeContractNeedsAttention,
 notificationTypeKillReportFinalBlow,
 notificationTypeKillReportVictim,
 notificationTypeAchievementTaskFinished,
 notificationTypeOpportunityFinished] + groupTypes[groupSkillTraining]
groupNamePaths = {groupAgents: 'Notifications/groupAgents',
 groupBills: 'Notifications/groupBills',
 groupContacts: 'Notifications/groupContacts',
 groupCorp: 'Notifications/groupCorporation',
 groupMisc: 'Notifications/groupMisc',
 groupOld: 'Notifications/groupOld',
 groupSov: 'Notifications/groupSovereignty',
 groupStructures: 'Notifications/groupStructures',
 groupWar: 'Notifications/groupWar',
 groupBounties: 'Notifications/groupBounties',
 groupInsurance: 'UI/Station/Insurance'}
groupNamePathsNewNotifications = {groupAgents: 'Notifications/groupAgents',
 groupBills: 'Notifications/groupBills',
 groupContacts: 'Notifications/groupContacts',
 groupCorp: 'Notifications/groupCorporation',
 groupMisc: 'Notifications/groupMisc',
 groupOld: 'Notifications/groupOld',
 groupSov: 'Notifications/groupSovereignty',
 groupStructures: 'Notifications/groupStructures',
 groupWar: 'Notifications/groupWar',
 groupBounties: 'Notifications/groupBounties',
 groupSkillTraining: 'Notifications/GroupNames/groupSkillTraining',
 groupInsurance: 'UI/Station/Insurance',
 groupOpportunities: 'Notifications/groupOpportunities'}
notificationGroupUnread = groupUnread
notificationGroupAgents = groupAgents
notificationGroupBills = groupBills
notificationGroupCorp = groupCorp
notificationGroupMisc = groupMisc
notificationGroupOld = groupOld
notificationGroupSov = groupSov
notificationGroupStructures = groupStructures
notificationGroupWar = groupWar
notificationGroupContacts = groupContacts
notificationGroupBounties = groupBounties
notificationDisplaySender = groupTypes[groupAgents] + groupTypes[groupCorp] + groupTypes[groupContacts] + [notificationTypeCorpOfficeExpirationMsg,
 notificationTypeSovereigntyTCUDamageMsg,
 notificationTypeSovereigntySBUDamageMsg,
 notificationTypeSovereigntyIHDamageMsg,
 notificationTypeCharTerminationMsg,
 notificationTypeCharMedalMsg,
 notificationTypeNewMailFrom]
notificationShowStanding = [notificationTypeContactSignedOn, notificationTypeContactSignedOff, notificationTypeNewMailFrom]

def GetTypeGroup(typeID):
    for groupID, typeIDs in groupTypes.iteritems():
        if typeID in typeIDs:
            return groupID


def IsTypeInCommunications(typeID):
    if typeID in nonCommunicationTypes:
        return False
    else:
        return True
