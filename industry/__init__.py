#Embedded file name: industry\__init__.py
"""
    Authors:   Cameron Royal
    Created:   January 2014
    Project:   EVE

    The industry package extracts the static data and computational logic
    from the existing science and industry feature of EVE. It can be used
    in a standard python interperter (no ExeFile) and has no CCP specicifc
    package dependencies.
"""
import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
from .const import *
from .util import Base, SlotBase, repr, mean, Property
from .modifiers import MaterialModifier, TimeModifier, CostModifier, ProbabilityModifier, MaxRunsModifier, SlotModifier
from .material import Material
from .skill import Skill
from .activity import Activity
from .blueprint import Blueprint, BlueprintStorage
from .job import JobData, Job, Location, ValidationError
from .facility import Facility
from .team import Team
from .activities.invention import Invention
from .activities.manufacturing import Manufacturing
from .activities.research_time import ResearchTime
from .activities.research_material import ResearchMaterial
from .activities.copying import Copying
MAPPING = [('activities.[a-z_]+.skills$', Skill),
 ('activities.[a-z_]+.materials$', Material),
 ('activities.[a-z_]+.products$', Material),
 ('activities.invention$', Invention),
 ('activities.manufacturing$', Manufacturing),
 ('activities.research_time$', ResearchTime),
 ('activities.research_material$', ResearchMaterial),
 ('activities.copying$', Copying),
 ('$', Blueprint)]
INDEXES = ['activities.([a-z]+).products.typeID.(?P<productTypeID>[0-9]+)$']
ACTIVITY_CLASSES = {INVENTION: Invention,
 MANUFACTURING: Manufacturing,
 RESEARCH_TIME: ResearchTime,
 RESEARCH_MATERIAL: ResearchMaterial,
 COPYING: Copying}
ACTIVITY_IDS = {v:k for k, v in ACTIVITY_CLASSES.iteritems()}
