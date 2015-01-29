#Embedded file name: sensorsuite\common.py
SITE_DIFFICULTY_EASY = 1
SITE_DIFFICULTY_MEDIUM = 2
SITE_DIFFICULTY_HARD = 3

def MapDungeonDifficulty(dungeonDifficulty):
    if dungeonDifficulty is None:
        return SITE_DIFFICULTY_EASY
    elif dungeonDifficulty < 4:
        return SITE_DIFFICULTY_EASY
    elif dungeonDifficulty < 7:
        return SITE_DIFFICULTY_MEDIUM
    else:
        return SITE_DIFFICULTY_HARD
