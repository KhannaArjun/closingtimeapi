from mongoengine import Document, StringField

class AddFood(Document):


    user_id = StringField(required=True)
    food_name = StringField(required=True)
    food_desc = StringField(required=True)
    quantity = StringField(required=True)
    pick_up_date = StringField(required=True)