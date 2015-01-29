#Embedded file name: carbonui/util\mouseTargetObject.py
__author__ = 'fridrik'
import uthread
import blue
import geo2
import weakref
SAMPLESIZE = 10

class MouseTargetObject(object):
    _owner = None
    _mouseTrace = None

    def __init__(self, owner, *args):
        self._owner = weakref.ref(owner)
        self._mouseTrace = []
        uicore.uilib.AddMouseTargetObject(self)

    def GetOwner(self):
        if self._owner:
            owner = self._owner()
            if owner and not owner.destroyed:
                return owner
            self._owner = None

    def IsMouseHeadingTowards(self):
        owner = self.GetOwner()
        if owner.destroyed:
            return False
        mx, my = uicore.ScaleDpi(uicore.uilib.x), uicore.ScaleDpi(uicore.uilib.y)
        if len(self._mouseTrace) > SAMPLESIZE:
            self._mouseTrace.pop(0)
        self._mouseTrace.append((mx, my))
        tl, tt, tw, th = (owner.displayX,
         owner.displayY,
         owner.displayWidth,
         owner.displayHeight)
        if tl <= mx <= tl + tw and tt <= my <= tt + th:
            return False
        oldX, oldY = self._mouseTrace[0]
        if (oldX, oldY) == (mx, my):
            return False
        mouseVector = geo2.Vec2Subtract((oldX, oldY), (mx, my))
        dirX, dirY = geo2.Vec2Scale(mouseVector, 1000)
        hit = intersect((tl, tt), (tl + tw, tt + th), (mx, my), (mx - dirX, my - dirY))
        if not hit:
            hit = intersect((tl + tw, tt), (tl, tt + th), (mx, my), (mx - dirX, my - dirY))
        if hit:
            return True
        return False


def ccw(A, B, C):
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])


def intersect(A, B, C, D):
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)
