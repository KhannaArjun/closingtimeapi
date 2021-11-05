from mongoengine import Document, StringField

class Donor__Registration(Document):


    name = StringField(required=True)
    business_name = StringField(required=True)
    email = StringField(required=True, unique=True)
    password = StringField(required=True)
    contact_number = StringField(required=True, unique=True)
    street_name = StringField(required=True)
    postcode = StringField(required=True)