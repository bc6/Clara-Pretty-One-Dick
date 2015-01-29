#Embedded file name: everesourceprefetch\__init__.py
import blue
import remotefilecache
import logging
import yaml
log = logging.getLogger('everesourceprefetch')
filesets = {}
ALL_FILES = lambda x: True
FILESET_DEFINITIONS = [('staticdata', ['res:/staticdata'], ALL_FILES),
 ('animation', ['res:/animation'], ALL_FILES),
 ('interior_amarr', ['res:/graphics/interior/amarr'], ALL_FILES),
 ('interior_caldari', ['res:/graphics/interior/caldari'], ALL_FILES),
 ('interior_gallente', ['res:/graphics/interior/gallente'], ALL_FILES),
 ('interior_minmatar', ['res:/graphics/interior/minmatar'], ALL_FILES),
 ('ui_cc', ['res:/ui/texture/charactercreation', 'res:/video/charactercreation'], ALL_FILES),
 ('ui_basics', ['res:/ui/cursor', 'res:/ui/fonts'], ALL_FILES),
 ('ui_classes', ['res:/ui/texture/classes'], ALL_FILES),
 ('bloodline_select_amarr', ['res:/Graphics/Character/Unique/CharacterSelect/AmarrFemaleClothing',
   'res:/Graphics/Character/Unique/CharacterSelect/AmarrMaleClothing',
   'res:/Graphics/Character/Unique/CharacterSelect/KhanidFemaleClothing',
   'res:/Graphics/Character/Unique/CharacterSelect/KhanidMaleClothing',
   'res:/Graphics/Character/Unique/CharacterSelect/NikunniFemaleClothing',
   'res:/Graphics/Character/Unique/CharacterSelect/NikunniMaleClothing'], ALL_FILES),
 ('bloodline_select_caldari', ['res:/Graphics/Character/Unique/CharacterSelect/AchuraFemaleClothing',
   'res:/Graphics/Character/Unique/CharacterSelect/AchuraMaleClothing',
   'res:/Graphics/Character/Unique/CharacterSelect/CivireFemaleClothing',
   'res:/Graphics/Character/Unique/CharacterSelect/CivireMaleClothing',
   'res:/Graphics/Character/Unique/CharacterSelect/DeteisFemaleClothing',
   'res:/Graphics/Character/Unique/CharacterSelect/DeteisMaleClothing'], ALL_FILES),
 ('bloodline_select_gallente', ['res:/Graphics/Character/Unique/CharacterSelect/GallenteFemaleClothing',
   'res:/Graphics/Character/Unique/CharacterSelect/GallenteMaleClothing',
   'res:/Graphics/Character/Unique/CharacterSelect/IntakiFemaleClothing',
   'res:/Graphics/Character/Unique/CharacterSelect/IntakiMaleClothing',
   'res:/Graphics/Character/Unique/CharacterSelect/JinmeiFemaleClothing',
   'res:/Graphics/Character/Unique/CharacterSelect/JinMeiMaleClothing'], ALL_FILES),
 ('bloodline_select_minmatar', ['res:/Graphics/Character/Unique/CharacterSelect/BrutorFemaleClothing',
   'res:/Graphics/Character/Unique/CharacterSelect/BrutorMaleClothing',
   'res:/Graphics/Character/Unique/CharacterSelect/SebiestorFemaleClothing',
   'res:/Graphics/Character/Unique/CharacterSelect/SebiestorMaleClothing',
   'res:/Graphics/Character/Unique/CharacterSelect/VherokiorFemaleClothing',
   'res:/Graphics/Character/Unique/CharacterSelect/VherokiorMaleClothing'], ALL_FILES),
 ('low_detail_ships', ['res:/dx9/model/ship'], lambda x: '_lowdetail.' in x),
 ('medium_detail_ships', ['res:/dx9/model/ship'], lambda x: '_mediumdetail.' in x),
 ('black_files', ['res:/'], lambda x: x.endswith('.black'))]
FILE_DEPENDENCIES = {}

def PrepareFilesets():
    for key, folders, condition in FILESET_DEFINITIONS:
        _AddFolderListAsKey(folders, key, condition=condition)

    dependencies_file = 'app:/resfiledependencies.yaml'
    if blue.paths.exists(dependencies_file):
        dep = blue.paths.GetFileContentsWithYield(dependencies_file)
        dep_dict = yaml.load(dep.Read(), Loader=yaml.CSafeLoader)
        FILE_DEPENDENCIES.update(dep_dict)


def AddFileset(key, fileset):
    if key in filesets:
        raise IndexError("'%s' is already defined" % key)
    fileset_as_list = list(fileset)
    for each in fileset_as_list:
        dependencies = FILE_DEPENDENCIES.get(each, [])
        for dep in dependencies:
            fileset.add(dep)

    filesets[key] = list(fileset)


def KeyExists(key):
    return key in filesets


def Schedule(key):
    try:
        remotefilecache.schedule(key, filesets[key])
    except KeyError:
        log.warning('Schedule: unknown key %s' % key)


def ScheduleFront(key):
    try:
        remotefilecache.schedule(key, filesets[key])
        remotefilecache.pull_to_front(key)
    except KeyError:
        log.warning('ScheduleFront: unknown key %s' % key)


def PullToFront(key):
    remotefilecache.pull_to_front(key)


def PushToBack(key):
    remotefilecache.push_to_back(key)


def _AddFolderListAsKey(folderList, key, condition = None):
    if condition == None:
        condition = lambda x: True
    file_set = set()
    for folder in folderList:
        remotefilecache.gather_files_conditionally_to_prefetch(folder, condition, file_set, FILE_DEPENDENCIES)

    filesets[key] = list(file_set)
