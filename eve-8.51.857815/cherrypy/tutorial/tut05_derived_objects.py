#Embedded file name: cherrypy/tutorial\tut05_derived_objects.py
"""
Tutorial - Object inheritance

You are free to derive your request handler classes from any base
class you wish. In most real-world applications, you will probably
want to create a central base class used for all your pages, which takes
care of things like printing a common page header and footer.
"""
import cherrypy

class Page:
    title = 'Untitled Page'

    def header(self):
        return '\n            <html>\n            <head>\n                <title>%s</title>\n            <head>\n            <body>\n            <h2>%s</h2>\n        ' % (self.title, self.title)

    def footer(self):
        return '\n            </body>\n            </html>\n        '


class HomePage(Page):
    title = 'Tutorial 5'

    def __init__(self):
        self.another = AnotherPage()

    def index(self):
        return self.header() + '\n            <p>\n            Isn\'t this exciting? There\'s\n            <a href="./another/">another page</a>, too!\n            </p>\n        ' + self.footer()

    index.exposed = True


class AnotherPage(Page):
    title = 'Another Page'

    def index(self):
        return self.header() + '\n            <p>\n            And this is the amazing second page!\n            </p>\n        ' + self.footer()

    index.exposed = True


import os.path
tutconf = os.path.join(os.path.dirname(__file__), 'tutorial.conf')
if __name__ == '__main__':
    cherrypy.quickstart(HomePage(), config=tutconf)
else:
    cherrypy.tree.mount(HomePage(), config=tutconf)
