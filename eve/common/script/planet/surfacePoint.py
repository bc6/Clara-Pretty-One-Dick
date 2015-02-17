#Embedded file name: eve/common/script/planet\surfacePoint.py
"""
Surface point
"""
import math
MATH_2PI = math.pi * 2

class SurfacePoint:
    """
    Represents a point on the surface of a sphere, both in cartesian and spherical coordiantes.
    A surface point can be created by specifying the cartesian coordinates:
        - sp = planet.SurfacePoint(x=1.0, y=2.0, z=3.0)
    ... or by specifying the spherical coordinates
        - sp = planet.SurfacePoint(radius=100.0, theta=math.pi, phi=math.pi/4)
    
    In spherical coordinates, theta should be in the range [0,PI]  
    - THETA [0, 2*PI] indicates the angle from the positive X-axis on the XZ plane 
    - PHI [0, PI] indicates the angle from the positive Y-axis
    """
    __guid__ = 'planet.SurfacePoint'

    def __init__(self, x = 0.0, y = 0.0, z = 0.0, radius = 1.0, theta = None, phi = None):
        if theta is not None and phi is not None:
            self.SetRadThPhi(radius, theta, phi)
        else:
            self.SetXYZ(x, y, z)

    def SetXYZ(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self._CalcRadThPhi()

    def Copy(self, surfacePoint):
        self.x = surfacePoint.x
        self.y = surfacePoint.y
        self.z = surfacePoint.z
        self.radius = surfacePoint.radius
        self.theta = surfacePoint.theta
        self.phi = surfacePoint.phi

    def SetRadThPhi(self, radius, theta, phi):
        self.radius = radius
        self.theta = theta
        self.phi = phi
        self._CalcXYZ()

    def _CalcRadThPhi(self):
        self.radius = math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)
        if self.radius == 0.0:
            self.theta = self.phi = 0.0
            return
        self.phi = math.acos(self.y / self.radius)
        self.theta = math.atan2(self.z, self.x)
        self._CheckTheta()

    def _CheckTheta(self):
        """This will normalize theta to a range of [0..2*Pi)"""
        while self.theta >= MATH_2PI:
            self.theta -= MATH_2PI

        while self.theta < 0.0:
            self.theta += MATH_2PI

    def _CalcXYZ(self):
        """
        x = r * sin(phi) * cos(theta)
        y = r * sin(phi) * cos(theta)
        z = r * cos(phi)
        """
        radSinPhi = self.radius * math.sin(self.phi)
        self.x = radSinPhi * math.cos(self.theta)
        self.z = radSinPhi * math.sin(self.theta)
        self.y = self.radius * math.cos(self.phi)

    def SetX(self, x):
        self.x = x
        self._CalcRadThPhi()

    def SetY(self, y):
        self.y = y
        self._CalcRadThPhi()

    def SetZ(self, z):
        self.z = z
        self._CalcRadThPhi()

    def SetRadius(self, radius):
        self.radius = radius
        self._CalcXYZ()

    def SetTheta(self, theta):
        self.theta = theta
        self._CheckTheta()
        self._CalcXYZ()

    def SetPhi(self, phi):
        self.phi = phi
        self._CalcXYZ()

    def GetAsXYZTuple(self):
        return (self.x, self.y, self.z)

    def GetAsRadThPhiTuple(self):
        return (self.radius, self.theta, self.phi)

    def GetAsXYZString(self):
        return '(%6.2f, %6.2f, %6.2f) = (x,y,z)' % self.GetAsXYZTuple()

    def GetAsRadThPhiString(self):
        return '(%6.2f, %6.2f, %6.2f) = (rad,theta,phi)' % self.GetAsRadThPhiTuple()

    def GetAngleBetween(self, other):
        dotProduct = (self.x * other.x + self.y * other.y + self.z * other.z) / self.radius / other.radius
        if dotProduct > 1.0:
            dotProduct = 1.0
        return math.acos(dotProduct)

    def GetDistanceToOther(self, other):
        return self.radius * self.GetAngleBetween(other)


__exports__ = {'planet.SurfacePoint': SurfacePoint}
