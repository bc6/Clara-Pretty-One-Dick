#Embedded file name: eve/common/script/util\standingUtil.py
"""
Contains functions for the standings system that are useful to both the client and server.
"""
CRIMINAL_FACTIONS = (500010, 500011, 500012, 500019, 500020)

def GetStandingBonus(fromStanding, fromFactionID, skills):
    """
        Retrieves the standing bonus factor for a given entity's skills,
        based on the from-entity's standing & faction affiliation.
        NOTE: Entities without a faction affiliation will default to being non-criminal.
    
        ARGUMENTS:
            fromStanding:       The standing of the from-entity towards the subject entity.
            fromFactionID:      The faction ID of the from-entity, or None if not affiliated.
            skills:             A dict of the subject entity's skill levels, in the format:
                                    { skill Type ID: skill Level, ... }
    
        RETURNS:
            A tuple. The first value indicates which skill is providing the bonus, or None if there is no bonus.
            The second value is a floating point number indicating the standing modifier.
    """
    bonus = 0.0
    bonusType = None
    if fromStanding < 0.0:
        bonus = skills.get(const.typeDiplomacy, 0.0) * 0.4
        bonusType = const.typeDiplomacy
    elif fromStanding > 0.0:
        if fromFactionID is not None and fromFactionID in (500010, 500011, 500012, 500019, 500020):
            bonus = skills.get(const.typeCriminalConnections, 0.0) * 0.4
            bonusType = const.typeCriminalConnections
        else:
            bonus = skills.get(const.typeConnections, 0.0) * 0.4
            bonusType = const.typeConnections
    return (bonusType, bonus)


exports = {'standingUtil.GetStandingBonus': GetStandingBonus}
