#Embedded file name: carbon/common/script/net\httpSettings.py
import blue
TEMPLATES_DIR = [ blue.paths.ResolvePath(p) for p in ('wwwroot:/assets/views', 'wwwroot:/assets/views/old') ]
exports = {'httpSettings.TEMPLATES_DIR': TEMPLATES_DIR}
