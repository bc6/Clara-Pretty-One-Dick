#Embedded file name: carbon/common/lib/cherrypy/tutorial\bonus-sqlobject.py
"""
Bonus Tutorial: Using SQLObject

This is a silly little contacts manager application intended to
demonstrate how to use SQLObject from within a CherryPy2 project. It
also shows how to use inline Cheetah templates.

SQLObject is an Object/Relational Mapper that allows you to access
data stored in an RDBMS in a pythonic fashion. You create data objects
as Python classes and let SQLObject take care of all the nasty details.

This code depends on the latest development version (0.6+) of SQLObject.
You can get it from the SQLObject Subversion server. You can find all
necessary information at <http://www.sqlobject.org>. This code will NOT
work with the 0.5.x version advertised on their website!

This code also depends on a recent version of Cheetah. You can find
Cheetah at <http://www.cheetahtemplate.org>.

After starting this application for the first time, you will need to
access the /reset URI in order to create the database table and some
sample data. Accessing /reset again will drop and re-create the table,
so you may want to be careful. :-)

This application isn't supposed to be fool-proof, it's not even supposed
to be very GOOD. Play around with it some, browse the source code, smile.

:)

-- Hendrik Mans <hendrik@mans.de>
"""
import cherrypy
from Cheetah.Template import Template
from sqlobject import *
__connection__ = 'mysql://root:@localhost/test'

class Contact(SQLObject):
    lastName = StringCol(length=50, notNone=True)
    firstName = StringCol(length=50, notNone=True)
    phone = StringCol(length=30, notNone=True, default='')
    email = StringCol(length=30, notNone=True, default='')
    url = StringCol(length=100, notNone=True, default='')


class ContactManager:

    def index(self):
        contacts = Contact.select()
        template = Template('\n            <h2>All Contacts</h2>\n\n            #for $contact in $contacts\n                <a href="mailto:$contact.email">$contact.lastName, $contact.firstName</a>\n                [<a href="./edit?id=$contact.id">Edit</a>]\n                [<a href="./delete?id=$contact.id">Delete</a>]\n                <br/>\n            #end for\n\n            <p>[<a href="./edit">Add new contact</a>]</p>\n        ', [locals(), globals()])
        return template.respond()

    index.exposed = True

    def edit(self, id = 0):
        id = int(id)
        if id > 0:
            contact = Contact.get(id)
            title = 'Edit Contact'
        else:
            contact = None
            title = 'New Contact'
        template = Template('\n            <h2>$title</h2>\n\n            <form action="./store" method="POST">\n                <input type="hidden" name="id" value="$id" />\n                Last Name: <input name="lastName" value="$getVar(\'contact.lastName\', \'\')" /><br/>\n                First Name: <input name="firstName" value="$getVar(\'contact.firstName\', \'\')" /><br/>\n                Phone: <input name="phone" value="$getVar(\'contact.phone\', \'\')" /><br/>\n                Email: <input name="email" value="$getVar(\'contact.email\', \'\')" /><br/>\n                URL: <input name="url" value="$getVar(\'contact.url\', \'\')" /><br/>\n                <input type="submit" value="Store" />\n            </form>\n        ', [locals(), globals()])
        return template.respond()

    edit.exposed = True

    def delete(self, id):
        contact = Contact.get(int(id))
        contact.destroySelf()
        return 'Deleted. <a href="./">Return to Index</a>'

    delete.exposed = True

    def store(self, lastName, firstName, phone, email, url, id = None):
        if id and int(id) > 0:
            contact = Contact.get(int(id))
            contact.set(lastName=lastName, firstName=firstName, phone=phone, email=email, url=url)
        else:
            contact = Contact(lastName=lastName, firstName=firstName, phone=phone, email=email, url=url)
        return 'Stored. <a href="./">Return to Index</a>'

    store.exposed = True

    def reset(self):
        Contact.dropTable(True)
        Contact.createTable()
        Contact(firstName='Hendrik', lastName='Mans', email='hendrik@mans.de', phone='++49 89 12345678', url='http://www.mornography.de')
        return 'reset completed!'

    reset.exposed = True


print "If you're running this application for the first time, please go to http://localhost:8080/reset once in order to create the database!"
cherrypy.quickstart(ContactManager())
