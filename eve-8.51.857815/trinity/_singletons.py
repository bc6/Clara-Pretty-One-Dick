#Embedded file name: trinity\_singletons.py
"""
This is where we initialize singletons that are accessible at module root level.
e.g. trinity.SingletonName
"""
import blue
from . import _trinity
platform = _trinity._ImportDll()
adapters = _trinity._blue.classes.CreateInstance('trinity.Tr2VideoAdapters')
device = _trinity._blue.classes.CreateInstance('trinity.TriDevice')
app = _trinity._blue.classes.CreateInstance('triui.App')
shaderManager = _trinity.GetShaderManager()
from . import renderjobs
renderJobs = renderjobs.RenderJobs()
from . import GraphManager
graphs = GraphManager.GraphManager()
