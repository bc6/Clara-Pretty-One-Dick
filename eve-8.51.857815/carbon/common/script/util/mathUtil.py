#Embedded file name: carbon/common/script/util\mathUtil.py
"""
Writte by: Unknown in most cases (Probably Many)
Assembled by: Paul Gilmore
Assembled on: July 2008

All of the various math functions scattered throughout the code, which could be useful on a global scale are moved to here.
This especially includes functions which were defined in several places with identical implementations.
"""
import math
import geo2
DEG_2_RAD = math.pi / 180.0
RAD_2_DEG = 180.0 / math.pi
MATH_PI_2 = math.pi / 2
MATH_PI_4 = math.pi / 4
MATH_PI_8 = math.pi / 8
MATH_2_PI = math.pi * 2

def LtoI(v):
    if v < 2147483648L:
        return int(v)
    return ~int(~v & 4294967295L)


def LerpList(color1, color2, lerpValue):
    invLerpValue = 1.0 - lerpValue
    return [invLerpValue * color1[0] + lerpValue * color2[0],
     invLerpValue * color1[1] + lerpValue * color2[1],
     invLerpValue * color1[2] + lerpValue * color2[2],
     invLerpValue * color1[3] + lerpValue * color2[3]]


def LerpVector(v1, v2, s):
    v = v1.CopyTo()
    v.Lerp(v2, s)
    return v


def Lerp(start, end, s):
    """
    Returns a number between start and end that is s percent between the two. s
    has to be between 0.0 and 1.0
    """
    return start + min(max(s, 0.0), 1.0) * (end - start)


def LerpTupleThree(tuple1, tuple2, scaling):
    return (Lerp(tuple1[0], tuple2[0], scaling), Lerp(tuple1[1], tuple2[1], scaling), Lerp(tuple1[2], tuple2[2], scaling))


def LerpTupleFour(tuple1, tuple2, scaling):
    return (Lerp(tuple1[0], tuple2[0], scaling),
     Lerp(tuple1[1], tuple2[1], scaling),
     Lerp(tuple1[2], tuple2[2], scaling),
     Lerp(tuple1[3], tuple2[3], scaling))


def LerpByTime(startVal, endVal, startTime, endTime, curTime):
    """ linear interpolation between two values over time"""
    lerpRatio = float(curTime - startTime) / float(endTime - startTime)
    return Lerp(startVal, endVal, lerpRatio)


def DegToRad(degs):
    return degs * DEG_2_RAD


def RadToDeg(degs):
    return degs * RAD_2_DEG


def RayToPlaneIntersection(P, d, Q, n):
    """
    Computes the intersection of the ray defined by point P and direction d with the plane
    defined by the point Q and the normal n.
    
    If the P lies on the plane defined by n and Q, there are infinite number of 
    intersection points, so the function returns P.
    
    d' = - Q.Dot(n)
    t = -(n.Dot(P) + d' )/n.Dot(d)
    S = P + t*d
    """
    denom = geo2.Vec3Dot(n, d)
    if abs(denom) < 1e-05:
        return P
    else:
        distance = -geo2.Vec3Dot(Q, n)
        t = -(geo2.Vec3Dot(n, P) + distance) / denom
        S = geo2.Add(geo2.Scale(d, t), P)
        return S


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('mathUtil', locals())
