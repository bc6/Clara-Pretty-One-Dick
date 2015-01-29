#Embedded file name: industry\modifiers.py
import industry

class Modifier(industry.Base):
    """
    A modifier can be applied to a blueprint, job or facility and provides a bonus to the
    efficiency of the job being installed. In EVE these will come from system wide bonuses,
    specific installation bonuses, characters skills or attributes specifiec to the blueprint.
    
    The output property indicates this modifier should affect the resultant product.
    """

    def __init__(self, amount, reference = None, activity = None, output = False, blueprints = None, categoryID = None, groupID = None):
        self.amount = amount
        self.reference = reference
        self.activity = activity
        self.output = output
        self.blueprints = set(blueprints or [])
        self.categoryID = categoryID
        self.groupID = groupID


class MaterialModifier(Modifier):
    """
    Adjusts the material requirements for a job.
    """
    pass


class TimeModifier(Modifier):
    """
    Adjusts the time for a job.
    """
    pass


class CostModifier(Modifier):
    """
    Adjusts the overall cost for a job.
    """
    pass


class ProbabilityModifier(Modifier):
    """
    Affects the probability of a job.
    """
    pass


class MaxRunsModifier(Modifier):
    """
    Affects the number of runs of a blueprint / job.
    """
    pass


class SlotModifier(Modifier):
    """
    Affects the number of concurrent jobs allowed per character.
    """
    pass
