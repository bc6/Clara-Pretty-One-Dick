#Embedded file name: industry/activities\invention.py
import industry
import operator

class Invention(industry.Activity):
    REQUIRES_COPY = True

    def job_modifiers(self, job):
        """
        Invention produces probability modifiers, based on skills and the products being produced.
        """
        modifiers = []
        base = self.base_probability()
        modifiers.append(industry.ProbabilityModifier(base, reference=industry.Reference.BLUEPRINT))
        amount = 1.0 + sum([ job.skills.get(skill.typeID, 0) * self.skill_probability(skill.typeID) for skill in self.skills ])
        modifiers.append(industry.ProbabilityModifier(amount, reference=industry.Reference.SKILLS))
        return modifiers

    def base_probability(self):
        base = industry.mean([ product.probability or 1.0 for product in self.products ])
        return base

    def skill_probability(self, typeID):
        """
        Returns the probability adjustment each level of a skill provides.
        """
        return industry.INVENTION_SKILL_PROBABILITIES.get(typeID, industry.INVENTION_SKILL_PROBABILITY)

    def job_cost(self, job):
        if job.product:
            return job.prices.get(job.product.typeID, 0) * industry.COST_PERCENTAGE * float(job.runs)
        else:
            return 0

    def job_max_runs(self, job):
        return job.blueprint.runsRemaining

    def job_probability(self, job):
        """
        Job probability is just all of the ProbabilityModifiers multiplied together.
        """
        modifiers = [ modifier.amount for modifier in job.all_modifiers if isinstance(modifier, industry.ProbabilityModifier) ]
        return max(min(reduce(operator.mul, modifiers, 1), 1.0), 0.0)

    def job_output_products(self, job):
        """
        Invention has multiple possible outcomes which the player must select from.
        """
        output = []
        modifiers = job.output_modifiers
        materialEfficiency = int(sum([ modifier.amount * 100.0 for modifier in modifiers if isinstance(modifier, industry.MaterialModifier) ]))
        timeEfficiency = int(sum([ modifier.amount * 100.0 for modifier in modifiers if isinstance(modifier, industry.TimeModifier) ]))
        maxRuns = sum([ modifier.amount for modifier in modifiers if isinstance(modifier, industry.MaxRunsModifier) ])
        for product in self.products:
            output.append(industry.Blueprint(original=False, blueprintTypeID=product.typeID, runsRemaining=int(round(product.quantity + maxRuns)), materialEfficiency=industry.INVENTION_MATERIAL_EFFICIENCY + materialEfficiency, timeEfficiency=industry.INVENTION_TIME_EFFICIENCY + timeEfficiency, quantity=job.successfulRuns))

        return output

    def job_output_extras(self, job):
        """
        Invention consumes 1 run of the original blueprint.
        """
        blueprint = job.blueprint.copy()
        blueprint.runsRemaining = max(blueprint.runsRemaining - job.runs, 0)
        return [blueprint]
