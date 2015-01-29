#Embedded file name: industry/activities\research_time.py
import industry

class ResearchTime(industry.Activity):
    REQUIRES_ORIGINAL = True

    def blueprint_level(self, blueprint):
        return blueprint.timeEfficiency / industry.STEP_TIME_EFFICIENCY

    def blueprint_levels(self):
        return [ self.time * industry.RESEARCH_TIMES[i] for i in range(industry.MAX_TIME_EFFICIENCY / industry.STEP_TIME_EFFICIENCY) ]

    def job_time(self, job):
        levels = self.blueprint_levels()
        current = self.blueprint_level(job.blueprint)
        return sum([ levels[min(current + i, len(levels) - 1)] for i in range(job.runs) ])

    def job_max_runs(self, job):
        return (industry.MAX_TIME_EFFICIENCY - job.blueprint.timeEfficiency) / industry.STEP_TIME_EFFICIENCY

    def job_cost(self, job):
        return job.prices.get(job.blueprint.blueprintTypeID, 0) * industry.COST_PERCENTAGE * self.job_time(job) / float(self.time)

    def job_output_products(self, job):
        """
        Returns the same blueprint but with a modified timeEfficiency.
        """
        blueprint = job.blueprint.copy()
        blueprint.timeEfficiency = min(blueprint.timeEfficiency + industry.STEP_TIME_EFFICIENCY * job.runs, industry.MAX_TIME_EFFICIENCY)
        return [blueprint]

    def job_validate(self, job):
        """
        Make sure we are not over-researching this blueprint.
        """
        max_level = len(self.blueprint_levels())
        current = self.blueprint_level(job.blueprint)
        if current < 0 or current >= max_level:
            job.add_error(industry.Error.RESEARCH_LIMIT, current, max_level)
