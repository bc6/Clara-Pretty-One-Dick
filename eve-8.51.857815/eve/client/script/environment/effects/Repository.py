#Embedded file name: eve/client/script/environment/effects\Repository.py
"""
This file serves as a repository for effect class definitions.

The dict is set up in this way:
Keys are the effect.guids that we receive from the server. Yes they
are actually strings.
Values are a tuple with the following attributes:
 -  Class type associated with the effect guid.
 -  Scaling, Rotational and translational enums.
    These control how we place the graphics on the affected balls.
 -  Merging enums
    These control how effect with the same guids stack.
 -  Graphic file path.
 -  Time Scaling
    Determines whether the vfx duration should be scaled to match
    the duration of the game logic effect.
 -  Duration
    Effect duration in ms.
"""
from eve.client.script.environment.effects.effectConsts import *
from eve.client.script.environment.effects.accelerationGate import AccelerationGate
from eve.client.script.environment.effects.anchoring import AnchorDrop, AnchorLift
from eve.client.script.environment.effects.cloaking import CloakNoAnim, Cloaking, CloakRegardless, Cloak, Uncloak
from eve.client.script.environment.effects.EMPWave import EMPWave
from eve.client.script.environment.effects.GenericEffect import ShipEffect, ShipRenderEffect, StretchEffect, GenericEffect
from eve.client.script.environment.effects.Jump import JumpDriveIn, JumpDriveInBO, JumpDriveOut, JumpDriveOutBO, JumpIn, JumpOut, JumpOutWormhole
from eve.client.script.environment.effects.Jump import GateActivity, WormholeActivity
from eve.client.script.environment.effects.JumpPortal import JumpPortal, JumpPortalBO
from eve.client.script.environment.effects.MicroJumpDrive import MicroJumpDriveJump, MicroJumpDriveEngage
from eve.client.script.environment.effects.orbitalStrike import OrbitalStrike
from eve.client.script.environment.effects.siegeMode import SiegeMode
from eve.client.script.environment.effects.soundEffect import SoundEffect
from eve.client.script.environment.effects.structures import StructureOnlined, StructureOnline, StructureOffline
from eve.client.script.environment.effects.turrets import StandardWeapon, CloudMining, MissileLaunch
from eve.client.script.environment.effects.Warp import Warping
from eve.client.script.environment.effects.WarpDisruptFieldGenerating import WarpDisruptFieldGenerating
from eve.client.script.environment.effects.WarpFlash import WarpFlashOut, WarpFlashIn
definitions = {'effects.Afterburner': (SoundEffect,
                         FX_TF_NONE,
                         FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                         None,
                         1,
                         10000),
 'effects.AnchorDrop': (AnchorDrop,
                        FX_TF_NONE,
                        FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                        None,
                        1,
                        10000),
 'effects.AnchorLift': (AnchorLift,
                        FX_TF_NONE,
                        FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                        None,
                        1,
                        10000),
 'effects.ArmorHardening': (ShipRenderEffect,
                            FX_TF_NONE,
                            FX_MERGE_SHIP | FX_MERGE_GUID,
                            'res:/dx9/Model/Effect/ArmorHardening.red',
                            1,
                            10000),
 'effects.ArmorRepair': (ShipRenderEffect,
                         FX_TF_NONE,
                         FX_MERGE_SHIP | FX_MERGE_GUID,
                         'res:/dx9/Model/Effect/ArmorRepair.red',
                         1,
                         10000),
 'effects.Barrage': (StandardWeapon,
                     FX_TF_NONE,
                     FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                     None,
                     1,
                     10000),
 'effects.CargoScan': (StretchEffect,
                       FX_TF_NONE,
                       FX_MERGE_SHIP | FX_MERGE_GUID,
                       'res:/Model/Effect3/CargoScan.red',
                       1,
                       10000),
 'effects.Cloak': (Cloak,
                   FX_TF_POSITION_BALL | FX_TF_ROTATION_BALL,
                   FX_MERGE_SHIP | FX_MERGE_GUID,
                   'res:/fisfx/cloaking/cloaking.red',
                   0,
                   6000),
 'effects.CloakingCovertOps': (Cloak,
                               FX_TF_POSITION_BALL | FX_TF_ROTATION_BALL,
                               FX_MERGE_SHIP | FX_MERGE_GUID,
                               'res:/fisfx/cloaking/cloaking_pentagon.red',
                               0,
                               6000),
 'effects.CloakingPrototype': (Cloak,
                               FX_TF_POSITION_BALL | FX_TF_ROTATION_BALL,
                               FX_MERGE_SHIP | FX_MERGE_GUID,
                               'res:/fisfx/cloaking/cloaking_triangle.red',
                               0,
                               6000),
 'effects.CloakNoAmim': (CloakNoAnim,
                         FX_TF_POSITION_BALL | FX_TF_ROTATION_BALL,
                         FX_MERGE_SHIP | FX_MERGE_GUID,
                         'res:/fisfx/cloaking/gate_cloaking.red',
                         0,
                         6000),
 'effects.CloakRegardless': (CloakRegardless,
                             FX_TF_POSITION_BALL | FX_TF_ROTATION_BALL,
                             FX_MERGE_SHIP | FX_MERGE_GUID,
                             'res:/fisfx/cloaking/cloaking.red',
                             1,
                             6000),
 'effects.Cloaking': (Cloaking,
                      FX_TF_POSITION_BALL | FX_TF_ROTATION_BALL,
                      FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                      None,
                      0,
                      10000),
 'effects.CloudMining': (CloudMining,
                         FX_TF_NONE,
                         FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                         None,
                         1,
                         10000),
 'effects.ECMBurst': (ShipEffect,
                      FX_TF_POSITION_BALL,
                      FX_MERGE_SHIP | FX_MERGE_GUID,
                      'res:/Model/Effect3/EcmBurst.red',
                      1,
                      10000),
 'effects.EMPWave': (EMPWave,
                     FX_TF_NONE,
                     FX_MERGE_SHIP | FX_MERGE_MODULE,
                     None,
                     1,
                     10000),
 'effects.ElectronicAttributeModifyActivate': (ShipEffect,
                                               FX_TF_SCALE_RADIUS | FX_TF_POSITION_BALL,
                                               FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                                               'res:/Model/Effect3/ECM.red',
                                               1,
                                               10000),
 'effects.ElectronicAttributeModifyTarget': (StretchEffect,
                                             FX_TF_NONE,
                                             FX_MERGE_SHIP | FX_MERGE_TARGET | FX_MERGE_GUID,
                                             'res:/Model/Effect3/SensorBoost.red',
                                             1,
                                             10000),
 'effects.EnergyDestabilization': (StretchEffect,
                                   FX_TF_NONE,
                                   FX_MERGE_SHIP | FX_MERGE_TARGET | FX_MERGE_GUID,
                                   'res:/Model/Effect3/EnergyDestabilization.red',
                                   1,
                                   10000),
 'effects.EnergyTransfer': (StretchEffect,
                            FX_TF_NONE,
                            FX_MERGE_SHIP | FX_MERGE_TARGET | FX_MERGE_GUID,
                            'res:/Model/Effect3/EnergyTransfer.red',
                            1,
                            10000),
 'effects.BeamCollecting': (StretchEffect,
                            FX_TF_NONE,
                            FX_MERGE_SHIP | FX_MERGE_TARGET | FX_MERGE_GUID,
                            'res:/fisfx/generic/tractor_beam/beam_collect.red',
                            1,
                            10000),
 'effects.EnergyVampire': (StretchEffect,
                           FX_TF_NONE,
                           FX_MERGE_SHIP | FX_MERGE_TARGET | FX_MERGE_GUID,
                           'res:/Model/Effect3/EnergyVampire.red',
                           1,
                           10000),
 'effects.GateActivity': (GateActivity,
                          FX_TF_NONE,
                          FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                          None,
                          1,
                          10000),
 'effects.HybridFired': (StandardWeapon,
                         FX_TF_NONE,
                         FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                         None,
                         1,
                         10000),
 'effects.Jettison': (ShipEffect,
                      FX_TF_POSITION_BALL,
                      FX_MERGE_SHIP | FX_MERGE_GUID,
                      'res:/Model/Effect3/Jettison.red',
                      1,
                      10000),
 'effects.JumpDriveIn': (JumpDriveIn,
                         FX_TF_SCALE_SYMMETRIC | FX_TF_POSITION_BALL | FX_TF_ROTATION_BALL,
                         FX_MERGE_SHIP | FX_MERGE_GUID,
                         'res:/FisFX/Jump/Cyno_Jump/cyno_jump_in.red',
                         1,
                         10000),
 'effects.JumpDriveInBO': (JumpDriveInBO,
                           FX_TF_SCALE_SYMMETRIC | FX_TF_POSITION_BALL | FX_TF_ROTATION_BALL,
                           FX_MERGE_SHIP | FX_MERGE_GUID,
                           'res:/Model/Effect3/JumpDriveBO_in.red',
                           1,
                           10000),
 'effects.JumpDriveOut': (JumpDriveOut,
                          FX_TF_SCALE_SYMMETRIC | FX_TF_POSITION_BALL,
                          FX_MERGE_SHIP | FX_MERGE_GUID,
                          'res:/fisfx/jump/cyno_jump/cyno_jump_out.red',
                          1,
                          10000),
 'effects.JumpDriveOutBO': (JumpDriveOutBO,
                            FX_TF_SCALE_SYMMETRIC | FX_TF_POSITION_BALL,
                            FX_MERGE_SHIP | FX_MERGE_GUID,
                            'res:/fisfx/jump/cyno_jump/cyno_jump_out_bo.red',
                            1,
                            10000),
 'effects.JumpIn': (JumpIn,
                    FX_TF_SCALE_SYMMETRIC | FX_TF_POSITION_BALL | FX_TF_ROTATION_BALL,
                    FX_MERGE_SHIP | FX_MERGE_GUID,
                    'res:/Model/Effect3/warpEntry.red',
                    1,
                    10000),
 'effects.JumpOut': (JumpOut,
                     FX_TF_SCALE_SYMMETRIC | FX_TF_POSITION_BALL | FX_TF_ROTATION_BALL,
                     FX_MERGE_SHIP | FX_MERGE_GUID,
                     'res:/Model/Effect3/Jump_out.red',
                     1,
                     10000),
 'effects.JumpOutWormhole': (JumpOutWormhole,
                             FX_TF_SCALE_SYMMETRIC | FX_TF_POSITION_BALL | FX_TF_ROTATION_BALL,
                             FX_MERGE_SHIP | FX_MERGE_GUID,
                             'res:/Model/Effect3/WormJump.red',
                             1,
                             10000),
 'effects.JumpPortal': (JumpPortal,
                        FX_TF_POSITION_BALL | FX_TF_ROTATION_BALL,
                        FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                        'res:/Model/Effect3/JumpPortal.red',
                        1,
                        10000),
 'effects.JumpPortalBO': (JumpPortalBO,
                          FX_TF_POSITION_BALL | FX_TF_ROTATION_BALL,
                          FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                          'res:/Model/Effect3/JumpPortal_BO.red',
                          1,
                          10000),
 'effects.Laser': (StandardWeapon,
                   FX_TF_NONE,
                   FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                   None,
                   1,
                   10000),
 'effects.MicroWarpDrive': (SoundEffect,
                            FX_TF_NONE,
                            FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                            None,
                            1,
                            10000),
 'effects.Mining': (StandardWeapon,
                    FX_TF_NONE,
                    FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                    None,
                    1,
                    10000),
 'effects.MissileDeployment': (MissileLaunch,
                               FX_TF_NONE,
                               FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                               None,
                               1,
                               12000),
 'effects.ModifyShieldResonance': (ShipRenderEffect,
                                   FX_TF_NONE,
                                   FX_MERGE_SHIP | FX_MERGE_GUID,
                                   'res:/dx9/Model/Effect/ShieldHardening.red',
                                   1,
                                   10000),
 'effects.ModifyTargetSpeed': (ShipEffect,
                               FX_TF_SCALE_SYMMETRIC | FX_TF_POSITION_TARGET,
                               FX_MERGE_TARGET | FX_MERGE_GUID,
                               'res:/Model/Effect3/StasisWeb.red',
                               1,
                               10000),
 'effects.ProjectileFired': (StandardWeapon,
                             FX_TF_NONE,
                             FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                             None,
                             1,
                             10000),
 'effects.ProjectileFiredForEntities': (StandardWeapon,
                                        FX_TF_NONE,
                                        FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                                        None,
                                        1,
                                        10000),
 'effects.RemoteArmourRepair': (StretchEffect,
                                FX_TF_NONE,
                                FX_MERGE_SHIP | FX_MERGE_TARGET | FX_MERGE_GUID,
                                'res:/Model/Effect3/RemoteArmorRepair.red',
                                1,
                                10000),
 'effects.RemoteECM': (StretchEffect,
                       FX_TF_NONE,
                       FX_MERGE_SHIP | FX_MERGE_TARGET | FX_MERGE_GUID,
                       'res:/Model/Effect3/RemoteECM.red',
                       1,
                       10000),
 'effects.Salvaging': (StandardWeapon,
                       FX_TF_NONE,
                       FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                       None,
                       1,
                       10000),
 'effects.ScanStrengthBonusActivate': (ShipEffect,
                                       FX_TF_SCALE_RADIUS | FX_TF_POSITION_BALL,
                                       FX_MERGE_SHIP | FX_MERGE_GUID,
                                       'res:/Model/Effect3/ECCM.red',
                                       1,
                                       10000),
 'effects.ScanStrengthBonusTarget': (ShipEffect,
                                     FX_TF_SCALE_SYMMETRIC | FX_TF_POSITION_BALL,
                                     FX_MERGE_SHIP | FX_MERGE_GUID,
                                     'res:/Model/Effect3/ECCM.red',
                                     1,
                                     10000),
 'effects.ShieldBoosting': (ShipRenderEffect,
                            FX_TF_NONE,
                            FX_MERGE_SHIP | FX_MERGE_GUID,
                            'res:/dx9/Model/Effect/ShieldBoosting.red',
                            0,
                            10000),
 'effects.ShieldTransfer': (StretchEffect,
                            FX_TF_NONE,
                            FX_MERGE_SHIP | FX_MERGE_TARGET | FX_MERGE_GUID,
                            'res:/Model/Effect3/ShieldTransfer.red',
                            1,
                            10000),
 'effects.ShipScan': (StretchEffect,
                      FX_TF_NONE,
                      FX_MERGE_SHIP | FX_MERGE_GUID,
                      'res:/Model/Effect3/ShipScan.red',
                      1,
                      10000),
 'effects.SiegeMode': (SiegeMode,
                       FX_TF_NONE,
                       FX_MERGE_SHIP,
                       None,
                       1,
                       10000),
 'effects.SpeedBoost': (GenericEffect,
                        FX_TF_NONE,
                        FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                        None,
                        1,
                        10000),
 'effects.StructureOffline': (StructureOffline,
                              FX_TF_NONE,
                              FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                              None,
                              1,
                              10000),
 'effects.StructureOnline': (StructureOnline,
                             FX_TF_NONE,
                             FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                             None,
                             1,
                             10000),
 'effects.StructureOnlined': (StructureOnlined,
                              FX_TF_NONE,
                              FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                              None,
                              1,
                              10000),
 'effects.StructureRepair': (ShipRenderEffect,
                             FX_TF_NONE,
                             FX_MERGE_SHIP | FX_MERGE_GUID,
                             'res:/dx9/Model/Effect/HullRepair.red',
                             1,
                             10000),
 'effects.SuperWeaponAmarr': (StretchEffect,
                              FX_TF_NONE,
                              FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                              'res:/Model/Effect3/Superweapon/A_DoomsDay.red',
                              False,
                              10000),
 'effects.SuperWeaponCaldari': (StretchEffect,
                                FX_TF_NONE,
                                FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                                'res:/Model/Effect3/Superweapon/C_DoomsDay.red',
                                False,
                                10000),
 'effects.SuperWeaponGallente': (StretchEffect,
                                 FX_TF_NONE,
                                 FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                                 'res:/Model/Effect3/Superweapon/G_DoomsDay.red',
                                 False,
                                 10000),
 'effects.SuperWeaponMinmatar': (StretchEffect,
                                 FX_TF_NONE,
                                 FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                                 'res:/Model/Effect3/Superweapon/M_DoomsDay.red',
                                 False,
                                 10000),
 'effects.SurveyScan': (ShipEffect,
                        FX_TF_SCALE_SYMMETRIC | FX_TF_POSITION_BALL,
                        FX_MERGE_SHIP | FX_MERGE_TARGET | FX_MERGE_GUID,
                        'res:/Model/Effect3/SurveyScan.red',
                        1,
                        10000),
 'effects.TargetPaint': (StretchEffect,
                         FX_TF_NONE,
                         FX_MERGE_SHIP | FX_MERGE_TARGET | FX_MERGE_GUID,
                         'res:/Model/Effect3/TargetPaint.red',
                         1,
                         10000),
 'effects.TargetScan': (StretchEffect,
                        FX_TF_NONE,
                        FX_MERGE_SHIP | FX_MERGE_TARGET | FX_MERGE_GUID,
                        'res:/Model/Effect3/SurveyScan2.red',
                        1,
                        10000),
 'effects.TorpedoDeployment': (GenericEffect,
                               FX_TF_NONE,
                               FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                               None,
                               1,
                               10000),
 'effects.TractorBeam': (StandardWeapon,
                         FX_TF_NONE,
                         FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                         None,
                         1,
                         10000),
 'effects.TriageMode': (ShipRenderEffect,
                        FX_TF_NONE,
                        FX_MERGE_SHIP | FX_MERGE_GUID,
                        'res:/dx9/Model/Effect/TriageMode.red',
                        0,
                        10000),
 'effects.TurretWeaponRangeTrackingSpeedMultiplyActivate': (ShipEffect,
                                                            FX_TF_SCALE_RADIUS | FX_TF_POSITION_BALL,
                                                            FX_MERGE_SHIP | FX_MERGE_GUID,
                                                            'res:/Model/Effect3/TrackingBoost.red',
                                                            1,
                                                            10000),
 'effects.TurretWeaponRangeTrackingSpeedMultiplyTarget': (StretchEffect,
                                                          FX_TF_NONE,
                                                          FX_MERGE_SHIP | FX_MERGE_GUID,
                                                          'res:/Model/Effect3/TrackingBoostTarget.red',
                                                          1,
                                                          10000),
 'effects.Uncloak': (Uncloak,
                     FX_TF_POSITION_BALL | FX_TF_ROTATION_BALL,
                     FX_MERGE_SHIP | FX_MERGE_GUID,
                     'res:/fisfx/cloaking/cloaking.red',
                     0,
                     6000),
 'effects.WarpDisruptFieldGenerating': (WarpDisruptFieldGenerating,
                                        FX_TF_POSITION_BALL,
                                        FX_MERGE_MODULE,
                                        'res:/fisfx/generic/warp_disruption/warp_disruption_field_generator.red',
                                        0,
                                        10000),
 'effects.WarpGateEffect': (AccelerationGate,
                            FX_TF_NONE,
                            FX_MERGE_SHIP | FX_MERGE_GUID,
                            None,
                            0,
                            10000),
 'effects.WarpScramble': (StretchEffect,
                          FX_TF_NONE,
                          FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                          'res:/Model/Effect3/WarpScrambler.red',
                          1,
                          10000),
 'effects.Warping': (Warping,
                     FX_TF_NONE,
                     FX_MERGE_SHIP | FX_MERGE_GUID,
                     'res:/Model/Effect3/warpTunnel2.red',
                     False,
                     1200000),
 'effects.WormholeActivity': (WormholeActivity,
                              FX_TF_NONE,
                              FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                              None,
                              1,
                              10000),
 'effects.TargetBreaker': (ShipEffect,
                           FX_TF_SCALE_RADIUS | FX_TF_POSITION_BALL,
                           FX_MERGE_SHIP | FX_MERGE_GUID,
                           'res:/dx9/model/Effect/TargetBreakerPulse.red',
                           0,
                           10000),
 'effects.OrbitalStrike': (OrbitalStrike,
                           FX_TF_NONE,
                           FX_MERGE_SHIP | FX_MERGE_MODULE | FX_MERGE_GUID,
                           None,
                           1,
                           10000),
 'effects.MicroJumpDriveEngage': (MicroJumpDriveEngage,
                                  FX_TF_SCALE_RADIUS | FX_TF_POSITION_MODEL | FX_TF_ROTATION_BALL,
                                  FX_MERGE_SHIP | FX_MERGE_GUID,
                                  'res:/dx9/model/effect/mjd_effect.red',
                                  1,
                                  10000),
 'effects.MicroJumpDriveJump': (MicroJumpDriveJump,
                                FX_TF_NONE,
                                FX_MERGE_SHIP | FX_MERGE_GUID,
                                None,
                                1,
                                10000),
 'effects.WarpOut': (WarpFlashOut,
                     FX_TF_NONE,
                     FX_MERGE_SHIP | FX_MERGE_GUID,
                     None,
                     1,
                     10000),
 'effects.WarpIn': (WarpFlashIn,
                    FX_TF_NONE,
                    FX_MERGE_SHIP | FX_MERGE_GUID,
                    None,
                    1,
                    10000),
 'effects.SleeperScannerStretch': (StretchEffect,
                                   FX_TF_NONE,
                                   FX_MERGE_SHIP | FX_MERGE_TARGET | FX_MERGE_GUID,
                                   'res:/Model/Effect3/sleeper_scanner_01.red',
                                   1,
                                   10000),
 'effects.SleeperScannerShip': (ShipRenderEffect,
                                FX_TF_NONE,
                                FX_MERGE_SHIP | FX_MERGE_GUID,
                                'res:/Model/Effect3/sleeper_scanner_overlay_01.red',
                                1,
                                10000)}

def GetGuids():
    return definitions.keys()


def GetClassification(guid):
    return definitions.get(guid, None)