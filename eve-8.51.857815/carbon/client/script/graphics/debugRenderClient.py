#Embedded file name: carbon/client/script/graphics\debugRenderClient.py
"""
Interface to Trinity debug renderer with persistence.
"""
import service
import trinity
import blue
import yaml
import safeThread
import sys
import log
DEBUG_FILENAME = 'debugLog.yaml'
FULL_DEBUG_PATH = blue.paths.ResolvePath(u'res:/') + DEBUG_FILENAME
DEBUG_RES_PATH = 'res:/' + DEBUG_FILENAME

class DebugRay:
    """
    A ray defining the source and destination.  Can 'pulse' to allow strings of rays that show direction over time.
    """
    __guid__ = 'debugShapes.DebugRay'

    def __init__(self, src = (0.0, 0.0, 0.0), dst = (0.0, 0.0, 0.0), srcColor = 4294967295L, dstColor = 4294967295L, time = 500, pulse = False):
        self.src = src
        self.srcColor = srcColor
        self.dst = dst
        self.dstColor = dstColor
        self.time = time
        self.currentTime = 0
        self.pulse = pulse

    def Render(self):
        if self.pulse is True:
            newColor = int(255.0 - 255.0 * (float(self.currentTime) / float(self.time))) % 16
            srcColor = self.srcColor & 4278190080L | self.srcColor & newColor << 20 | self.srcColor & newColor << 12 | self.srcColor & newColor << 6
            dstColor = self.dstColor & 4278190080L | self.srcColor & newColor << 20 | self.srcColor & newColor << 12 | self.srcColor & newColor << 6
        else:
            srcColor = self.srcColor
            dstColor = self.dstColor
        trinity.GetDebugRenderer().DrawLine(self.src, srcColor, self.dst, dstColor)
        self.currentTime += 1


class DebugCapsule:
    """
    A capsule with source, destination and radius.
    """
    __guid__ = 'debugShapes.DebugCapsule'

    def __init__(self, src = (0.0, 0.0, 0.0), dst = (0.0, 0.0, 0.0), radius = 0.0, color = 4294967295L, time = 500):
        self.src = src
        self.dst = dst
        self.radius = radius
        self.color = color
        self.time = time
        self.currentTime = 0

    def Render(self):
        newAlpha = int(255.0 - 255.0 * (float(self.currentTime) / float(self.time)))
        color = self.color & 16777215 | newAlpha << 24
        trinity.GetDebugRenderer().DrawCapsule(self.src, self.dst, self.radius, 6, color)
        self.currentTime += 1


class DebugSphere:
    """
    A capsule with source position and radius.
    """
    __guid__ = 'debugShapes.DebugSphere'

    def __init__(self, src = (0.0, 0.0, 0.0), radius = 0.0, color = 4294967295L, time = 500):
        self.src = src
        self.radius = radius
        self.color = color
        self.time = time
        self.currentTime = 0

    def Render(self):
        newAlpha = int(255.0 - 255.0 * (float(self.currentTime) / float(self.time)))
        color = self.color & 16777215 | newAlpha << 24
        trinity.GetDebugRenderer().DrawSphere(self.src, self.radius, 6, color)
        self.currentTime += 1


class DebugCylinder:
    """
    A cylinder with source, destination and radius.
    """
    __guid__ = 'debugShapes.DebugCylinder'

    def __init__(self, src = (0.0, 0.0, 0.0), dst = (0.0, 0.0, 0.0), radius = 0.0, color = 4294967295L, time = 500):
        self.src = src
        self.dst = dst
        self.radius = radius
        self.color = color
        self.time = time
        self.currentTime = 0

    def Render(self):
        newAlpha = int(255.0 - 255.0 * (float(self.currentTime) / float(self.time)))
        color = self.color & 16777215 | newAlpha << 24
        trinity.GetDebugRenderer().DrawCylinder(self.src, self.dst, self.radius, 6, color)
        self.currentTime += 1


class DebugCone:
    """
    A cone with source, destination and radius.
    """
    __guid__ = 'debugShapes.DebugCone'

    def __init__(self, src = (0.0, 0.0, 0.0), dst = (0.0, 0.0, 0.0), radius = 0.0, color = 4294967295L, time = 500):
        self.src = src
        self.dst = dst
        self.radius = radius
        self.color = color
        self.time = time
        self.currentTime = 0

    def Render(self):
        newAlpha = int(255.0 - 255.0 * (float(self.currentTime) / float(self.time)))
        color = self.color & 16777215 | newAlpha << 24
        trinity.GetDebugRenderer().DrawCone(self.src, self.dst, self.radius, 6, color)
        self.currentTime += 1


class DebugBox:
    """
    A box defined by the lower-left and upper-right bounds.
    """
    __guid__ = 'debugShapes.DebugBox'

    def __init__(self, min = (0.0, 0.0, 0.0), max = (0.0, 0.0, 0.0), color = 4294967295L, time = 500):
        self.min = min
        self.max = max
        self.color = color
        self.time = time
        self.currentTime = 0

    def Render(self):
        newAlpha = int(255.0 - 255.0 * (float(self.currentTime) / float(self.time)))
        color = self.color & 16777215 | newAlpha << 24
        trinity.GetDebugRenderer().DrawBox(self.min, self.max, color)
        self.currentTime += 1


class DebugText:
    """
    A message placed in 3D space.
    """
    __guid__ = 'debugShapes.DebugText'

    def __init__(self, src = (0.0, 0.0, 0.0), msg = '', color = 4294967295L, time = 500, fade = True):
        self.src = src
        self.color = color
        self.msg = msg
        self.time = time
        self.currentTime = 0
        self.fade = fade

    def Render(self):
        if self.fade is True:
            newAlpha = int(255.0 - 255.0 * (self.currentTime / float(self.time)))
            color = self.color & 16777215 | newAlpha << 24
            trinity.GetDebugRenderer().Print3D(self.src, color, self.msg)
        else:
            trinity.GetDebugRenderer().Print3D(self.src, self.color, self.msg)
        self.currentTime += 1


class DebugRenderClient(service.Service, safeThread.SafeThread):
    """
    Manages 3D rendered debug shapes over time.
    """
    __guid__ = 'svc.debugRenderClient'

    def __init__(self, *args):
        service.Service.__init__(self, *args)
        self.shapes = []
        self.debugRender = False
        self.renderJob = None
        safeThread.SafeThread.init(self, 'debugRenderClient')

    def Run(self, *args):
        service.Service.Run(self, *args)
        self.LaunchSafeThreadLoop_BlueTime(const.ONE_TICK)

    def SetDebugRendering(self, enabled):
        """
        Sets up debug rendering in the main viewport
        """
        self.debugRender = enabled
        if enabled and self.renderJob is None:
            self.renderJob = trinity.CreateRenderJob()
            dr = self.renderJob.RenderDebug()
            dr.name = 'DebugRendererInPlace'
            trinity.SetDebugRenderer(dr)
            self.renderJob.ScheduleRecurring()
        elif not enabled and self.renderJob is not None:
            self.renderJob.UnscheduleRecurring()
            self.renderJob = None

    def GetDebugRendering(self):
        """
        Return whether we are rendering or not.
        """
        return self.debugRender

    def ClearAllShapes(self):
        """
        Nuke the list of shapes.
        """
        self.shapes = []

    def SafeThreadLoop(self, now):
        """
        Render all shapes and kill off any that are no longer active.
        """
        shapesToKill = []
        if self.debugRender:
            try:
                for shape in self.shapes:
                    shape.Render()
                    if shape.currentTime > shape.time:
                        shapesToKill.append(shape)

            except:
                log.LogException('Error rendering shape in debugRenderClient.SafeThreadLoop')
                self.shapes = []

        else:
            self.ClearAllShapes()
        for shape in shapesToKill:
            self.shapes.remove(shape)

    def RenderRay(self, src, dst, srcColor = 4294967295L, dstColor = 4294967295L, time = 500, pulse = False):
        """
        Utility function to render a ray in 3D space.
        """
        self.shapes.append(DebugRay(src, dst, srcColor, dstColor, time, pulse))

    def RenderText(self, pos, msg, color = 4294967295L, time = 500, fade = True):
        """
        Utility function to render text in 3D space.
        """
        self.shapes.append(DebugText(pos, msg, color, time, fade))

    def RenderCapsule(self, src, dst, radius, color, time = 500):
        """
        Utility function to render a capsule in 3D space.
        """
        self.shapes.append(DebugCapsule(src, dst, radius, color, time))

    def RenderCylinder(self, src, dst, radius, color, time = 500):
        """
        Utility function to render a cylinder in 3D space.
        """
        self.shapes.append(DebugCylinder(src, dst, radius, color, time))

    def RenderCone(self, src, dst, radius, color, time = 500):
        """
        Utility function to render a cone in 3D space.
        """
        self.shapes.append(DebugCone(src, dst, radius, color, time))

    def RenderBox(self, min, max, color, time = 500):
        """
        Utility function to render a box in 3D space.
        """
        self.shapes.append(DebugBox(min, max, color, time))

    def RenderSphere(self, src, radius, color = 4294967295L, time = 500):
        """
        Utility function to render a sphere in 3D space.
        """
        self.shapes.append(DebugSphere(src, radius, color, time))

    def ExportDebugData(self, path = FULL_DEBUG_PATH):
        """
        Write out the active shapes to a file.
        """
        outFile = open(path, 'w')
        yaml.dump(self.shapes, outFile)
        outFile.close()

    def LoadDebugData(self, path = DEBUG_RES_PATH):
        """
        Load written out debug data and put it in the list.
        """
        import debugShapes
        sys.modules[debugShapes.__name__] = debugShapes
        resourceFile = blue.ResFile()
        resFile = resourceFile.open(path)
        self.shapes = yaml.load(resFile)
        resourceFile.close()
        del sys.modules[debugShapes.__name__]
