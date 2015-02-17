#Embedded file name: carbon/common/lib/cherrypy/tutorial\tut07_sessions.py
"""
Tutorial - Sessions

Storing session data in CherryPy applications is very easy: cherrypy
provides a dictionary called "session" that represents the session
data for the current user. If you use RAM based sessions, you can store
any kind of object into that dictionary; otherwise, you are limited to
objects that can be pickled.
"""
import cherrypy

class HitCounter:
    _cp_config = {'tools.sessions.on': True}

    def index(self):
        count = cherrypy.session.get('count', 0) + 1
        cherrypy.session['count'] = count
        return "\n            During your current session, you've viewed this\n            page %s times! Your life is a patio of fun!\n        " % count

    index.exposed = True


import os.path
tutconf = os.path.join(os.path.dirname(__file__), 'tutorial.conf')
if __name__ == '__main__':
    cherrypy.quickstart(HitCounter(), config=tutconf)
else:
    cherrypy.tree.mount(HitCounter(), config=tutconf)
