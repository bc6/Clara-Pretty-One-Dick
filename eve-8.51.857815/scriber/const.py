#Embedded file name: scriber\const.py
"""
Constants used by the scriber package
"""
import re
LOGGER_NAME = 'scriber'
EMAIL_TAG_GRABBER = re.compile('<(/?[\\w._%+-]+@[\\w.-]+\\.[\\S]{2,4} ?/?)>')
EMAIL_TAG_REPLACE_HTML = '&lt;\\1&gt;'
EMAIL_TAG_REPLACE_BRACKET = '[\\1]'
URL_MATCHER = re.compile('^(?:(?:(?P<schema>(?:[a-z][a-z0-9+\\-.]*):)?//(?P<host>[^/?#\\s]*))?)?(?P<path>/?[^?#\\s]*)(?:\\?(?P<querystr>[^#\\s]*))?(?:#(?P<fragment>\\S*))?')
HOST_MATCHER = re.compile('^(?:(?P<user>[^@:\\s]*)(?::(?P<pass>[^@\\s]*))?@)?(?P<host>[^:\\s]+)(?::(?P<port>[\\d]+))?$')
EXTRA_AMP_MATCHER = re.compile('(?i)&amp;#([0-9a-z]{2,8});')
EXTRA_AMP_REPLACER = '&#\\1;'
PETITION_LINK_NOTE_PATTERN = '\\b(?=\\w)(?i)(pet(?:ition)?|tic(?:ket)?)([: ]{1,2})(\\d+)\\b(?!\\w)'
PETITION_LINK_NOTE_REPLACE = '<a href="/gm/petitionClient.py?action=ViewPetition&petitionID=\\3">\\1\\2\\3</a>'
