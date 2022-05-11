import base64

from bson import ObjectId
from flask import Flask, request
from flask_mongoengine import MongoEngine
from flask_pymongo import pymongo
import flask
from food_donor_model import food_donor_registration_model
from food_donor_model import add_food_model
from utils import api_response
from utils import constants
from pymongo.cursor import Cursor
import base64
from oauth2client.service_account import ServiceAccountCredentials

import firebase_admin
from firebase_admin import credentials, messaging
from math import radians, cos, sin, asin, sqrt
from datetime import datetime
from cfg.cfg import get_prod_db, get_dev_db

cred = credentials.Certificate("closingtime-e1fe0-firebase-adminsdk-1zdrb-228c74a754.json")
firebase_admin.initialize_app(cred)

app = Flask(__name__)

# CONNECTION_STRING = "mongodb+srv://closingtime:closingtime@closingtime.1bd7w.mongodb.net/closingtime?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE"

# CONNECTION_STRING, db = get_dev_db()
CONNECTION_STRING, db = get_prod_db()

client = pymongo.MongoClient(CONNECTION_STRING)
db = client.get_database(db)


# user_collection = pymongo.collection.Collection(db, 'user_collection')
#
# # app.config['MONGODB_HOST'] = DB_URI
#
# app.config['MONGODB_HOST'] = DB_URI
#
# mongoEngine = MongoEngine()
#
# mongoEngine.init_app(app)


def getCollectionName(col_name):
    return pymongo.collection.Collection(db, col_name)


# stream = getCollectionName("add_food").watch()
#
# while stream.alive:
#     try:
#         doc = stream.next()
#         print(doc)
#     except StopIteration:
#         print("exception")


@app.route('/', methods=['GET'])
def index():
    return "Closing Time!"


@app.route('/login', methods=['POST'])
def login():
    input = request.get_json()
    # print(input)
    donor_reg = getCollectionName('donor_registration')
    record = donor_reg.find_one({'email': input['email']})
    if record:
        pwd = base64.b64decode(record['password']).decode('utf-8')
        # print(pwd)
        if pwd == input['password']:
            data = dict(record).copy()
            data.pop('_id')
            data.pop('password')
            data.update({'user_id': str(record['_id'])})

            return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, data))
        else:
            return flask.jsonify(api_response.apiResponse(constants.Utils.invalid_cred, False, {}))

    else:
        return flask.jsonify(api_response.apiResponse(constants.Utils.invalid_cred, False, {}))


@app.route('/isUserExists', methods=['POST'])
def isUserExists():
    input = request.get_json()

    # print(input)
    donor_reg = getCollectionName('donor_registration')
    recipient_reg = getCollectionName('recipient_registration')
    volunteer_reg = getCollectionName('volunteer_registration')

    donor_record = donor_reg.find_one({'email': input['email']})
    recipient_record = recipient_reg.find_one({'email': input['email']})
    volunteer_record = volunteer_reg.find_one({'email': input['email']})

    if donor_record is not None:
        data = dict(donor_record).copy()
        # print(data)
        data.pop('_id')
        data.update({'user_id': str(donor_record['_id'])})
        updateFirebaseToken(data['user_id'], input['firebase_token'], constants.Utils.donor)
        # print(data)
        return flask.jsonify(api_response.apiResponse(constants.Utils.user_exists, False, data))

    if recipient_record is not None:
        data = dict(recipient_record).copy()
        # print(data)
        data.pop('_id')
        data.update({'user_id': str(recipient_record['_id'])})
        # print(data)
        updateFirebaseToken(data['user_id'], input['firebase_token'], constants.Utils.recipient)

        return flask.jsonify(api_response.apiResponse(constants.Utils.user_exists, False, data))

    if volunteer_record is not None:
        data = dict(volunteer_record).copy()
        # print(data)
        data.pop('_id')
        data.update({'user_id': str(volunteer_record['_id'])})
        # print(data)
        updateFirebaseToken(data['user_id'], input['firebase_token'], constants.Utils.volunteer)

        return flask.jsonify(api_response.apiResponse(constants.Utils.user_exists, False, data))

    return flask.jsonify(api_response.apiResponse(constants.Utils.new_user, False, {}))


def updateFirebaseToken(id, fb_token, role):
    user_firebase_token = getCollectionName('user_firebase_token')
    # print(fb_token)
    data = user_firebase_token.find_one({"user_id": id})

    if data is not None:
        user_firebase_token.replace_one({"user_id": id}, {"firebase_token": fb_token, "user_id": id, "role": role})
    else:
        user_firebase_token.insert_one({"firebase_token": fb_token, "user_id": id, "role": role})

    return ""


def sendPush(title, msg, registration_token, dataObject=None):
    # See documentation on defining a message payload.
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=msg
        ),
        data=dataObject,
        tokens=registration_token,
    )

    # Send a message to the device corresponding to the provided
    # registration token.
    response = messaging.send_multicast(message)
    # Response is a message ID string.
    # print('Successfully sent message:', response)


# *******************************************         donor           *****************************************************


@app.route('/food_donor/getUserProfile', methods=['POST'])
def get_user_profile():
    input = request.get_json()

    donor_reg = getCollectionName('donor_registration')

    # print(ObjectId(input['user_id']))
    # print(input['user_id'])

    isUserIdPresent = donor_reg.find_one({'_id': ObjectId(input['user_id'])})

    if isUserIdPresent is None:
        return flask.jsonify(api_response.apiResponse(constants.Utils.no_user_found, False, {}))

    # print(isUserIdPresent)
    data = dict(isUserIdPresent).copy()
    # data.pop('password')
    data.pop('_id')
    data.update({'user_id': str(isUserIdPresent['_id'])})
    # print(data)
    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, data))


@app.route('/food_donor/registration', methods=['POST'])
def donor_registration():
    input = request.get_json()

    donor_reg = getCollectionName('donor_registration')
    recipient_reg = getCollectionName('recipient_registration')
    volunteer_reg = getCollectionName('volunteer_registration')

    flag = checkIfDataExists(recipient_reg, donor_reg, volunteer_reg, input)

    if flag is not None:
        return flag

    data = dict(input).copy()
    data.pop('firebase_token')
    obj = donor_reg.insert_one(data).inserted_id

    # data = dict(input).copy()
    # data.pop('password')
    data.pop('_id')
    data.update({'user_id': str(obj)})
    save_firebase_token(str(obj), input["firebase_token"], input["role"])

    # pwd = input['password'].encode("utf-8")
    # encoded = base64.b64encode(pwd)
    # print(encoded)
    # input['password'] = encoded

    return flask.jsonify(api_response.apiResponse(constants.Utils.inserted, False, data))


def save_firebase_token(id, token, role):
    user_firebase_token = getCollectionName("user_firebase_token")

    data = user_firebase_token.find_one({"user_id": id})

    if data is not None:
        return user_firebase_token.replace_one({'user_id': id}, {'user_id': id, "firebase_token": token, "role": role})
    else:
        return user_firebase_token.insert_one({'user_id': id, "firebase_token": token, "role": role})


@app.route('/food_donor/update_profile', methods=['POST'])
def update_profile():
    input = request.get_json()

    # user_collection = pymongo.collection.Collection(db, 'donor_registration')
    donor_reg = getCollectionName('donor_registration')

    isUserIdPresent = donor_reg.find_one({'_id': ObjectId(input['user_id'])})

    if isUserIdPresent is not None:
        obj = donor_reg.update_one({'_id': ObjectId(input['user_id'])}, {
            '$set': {'name': input['name'],
                     'business_name': input['business_name'],
                     'contact_number': input['contact_number'],
                     'address': input['address'],
                     'lat': input['lat'],
                     'lng': input['lng'],
                     'place_id': input['place_id']
                     }}, upsert=False)

        # accept_food_col = getCollectionName('accept_food')
        #
        # accept_food_objects = accept_food_col.find({"donor_user_id": input['user_id']})
        #
        # if accept_food_objects is not None:
        #     accept_food_objects_list = list(accept_food_objects)
        #
        #
        # add_food_col = getCollectionName('add_food')

        data = dict(input).copy()
        return flask.jsonify(api_response.apiResponse(constants.Utils.updated, False, data))
    else:
        return flask.jsonify(api_response.apiResponse(constants.Utils.no_user_found, False, {}))


@app.route('/food_donor/add_food', methods=['POST'])
def add_food():
    input = request.get_json()
    add_food_col = getCollectionName('add_food')
    recipient_registration_col = getCollectionName('recipient_registration')

    food_id = add_food_col.insert_one(input)

    recipients_obj = recipient_registration_col.find({})

    recipients_obj_list = list(recipients_obj)

    ids = list()
    # food_donations_nearby_recipients_obj_list = list()

    for item in recipients_obj_list:
        miles = dist(float(input['pick_up_lat']), float(input['pick_up_lng']), float(item['lat']), float(item['lng']))
        # print(miles)
        if miles < constants.Utils.miles:
            # print(item)
            ids.append(str(ObjectId(item['_id'])))
            # food_donations_nearby_recipients_obj = {
            #     "recipient_id" : str(ObjectId(item['_id'])),
            #     "food_id": [food_id]
            # }
            #
            # food_donations_nearby_recipients_obj_list.append(food_donations_nearby_recipients_obj)

    # print(ids)

    # food_donations_nearby_recipients_col = getCollectionName("food_donations_nearby_recipients")

    user_firebase_token_col = getCollectionName("user_firebase_token")
    recipients_firebase_tokens = user_firebase_token_col.find({"user_id": {"$in": ids}})

    tokens = list()

    for item in recipients_firebase_tokens:
        # print(item)
        #
        # print(item['firebase_token'])
        tokens.append(item['firebase_token'])

    send_notifications_to_recipients(tokens, input['food_name'], input['quantity'])

    return flask.jsonify(api_response.apiResponse(constants.Utils.inserted, False, {}))


@app.route('/test', methods=['POST'])
def test():
    user_firebase_token = getCollectionName("user_firebase_token")

    objj = user_firebase_token.find({"role": constants.Utils.recipient})

    # print(str(objj))

    l = list(objj)

    # print(l)

    # for x in l:
    #     # print(x['firebase_token'])

    return flask.jsonify(api_response.apiResponse(constants.Utils.inserted, False, {}))


@app.route('/food_donor/added_food_list', methods=['POST'])
def added_food_list():
    input = request.get_json()
    add_food_col = getCollectionName('add_food')

    if input['user_id'] == "":
        data = add_food_col.find({})

    else:
        data = add_food_col.find({'user_id': str(input['user_id'])})

    present_date = get_today_date()

    foodList = []
    array = list(data)
    if len(array):
        for obj in array:
            # obj = dict(x)
            pick_up_date = datetime.strptime(obj['pick_up_date'], "%Y-%m-%d").date()
            # and obj['status'] != constants.Utils.delivered
            if pick_up_date >= present_date:
                # obj.update({"status": constants.Utils.expired})
                obj.update({'id': str(obj['_id'])})
                del obj['_id']
                foodList.append(obj)
        array.clear()

    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, foodList))


@app.route('/food_donor/remove_food_item', methods=['POST'])
def remove_food_item():
    input = request.get_json()
    add_food_col = getCollectionName('add_food')
    data = add_food_col.find_one({'user_id': str(input['user_id']), '_id': ObjectId(input['id'])})

    add_food_col.delete_one(data)

    return flask.jsonify(api_response.apiResponse(constants.Utils.deleted, False, {}))


@app.route('/food_donor/modify_food_item', methods=['POST'])
def modify_food_item():
    input = request.get_json()
    add_food_col = getCollectionName('add_food')
    data = add_food_col.find_one({'user_id': str(input['user_id']), '_id': ObjectId(input['id'])})

    if data is not None:
        val = add_food_col.update_one({'_id': ObjectId(input['id'])}, {
            '$set': {'food_name': input['food_name'],
                     'food_desc': input['food_desc'],
                     'quantity': input['quantity'],
                     'food_ingredients': input['food_ingredients'],
                     'pick_up_date': input['pick_up_date'],
                     'pick_up_time': input['pick_up_time'],
                     'allergen': input['allergen'],
                     'image': input['image']}
        }, upsert=False)

        # print(dict(val))

        data = add_food_col.find_one({'user_id': str(input['user_id']), '_id': ObjectId(input['id'])})

        obj = dict(data)
        obj.update({"id": input['id']})
        del obj['_id']

        obj_list = list()
        obj_list.append(obj)
        return flask.jsonify(api_response.apiResponse(constants.Utils.updated, False, obj_list))

    return flask.jsonify(api_response.apiResponse(constants.Utils.failed, False, []))


@app.route('/food_donor/getAllFoodsByDonor', methods=['POST'])
def getAllFoodsByDonor():
    input = request.get_json()
    add_food_col = getCollectionName('add_food')

    data = add_food_col.find({'user_id': str(input['user_id'])})

    present_date = get_today_date()

    foodList = []
    array = list(data)
    if len(array):
        for obj in array:
            # obj = dict(x)
            pick_up_date = datetime.strptime(obj['pick_up_date'], "%Y-%m-%d").date()
            # or obj['status'] == constants.Utils.delivered
            if pick_up_date < present_date:
                obj.update({'id': str(obj['_id'])})
                del obj['_id']
                foodList.append(obj)
        array.clear()

    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, foodList))


# *******************************************         recipient           **************************************


@app.route('/recipient/registration', methods=['POST'])
def recipient_registration():
    input = request.get_json()

    recipient_reg = getCollectionName('recipient_registration')
    donor_reg = getCollectionName('donor_registration')
    volunteer_reg = getCollectionName('volunteer_registration')

    flag = checkIfDataExists(recipient_reg, donor_reg, volunteer_reg, input)

    if flag is not None:
        return flag

    data = dict(input).copy()
    data.pop('firebase_token')
    obj = recipient_reg.insert_one(data).inserted_id

    # data = dict(input).copy()
    # data.pop('password')
    data.pop('_id')
    data.update({'user_id': str(obj)})
    save_firebase_token(str(obj), input["firebase_token"], input["role"])
    return flask.jsonify(api_response.apiResponse(constants.Utils.inserted, False, data))


@app.route('/recipient/update_profile', methods=['POST'])
def update_recipient_profile():
    input = request.get_json()

    recipient_reg = getCollectionName('recipient_registration')

    isUserIdPresent = recipient_reg.find_one({'_id': ObjectId(input['user_id'])})

    if isUserIdPresent is not None:
        obj = recipient_reg.update_one({'_id': ObjectId(input['user_id'])}, {
            '$set': {'name': input['name'],
                     'business_name': input['business_name'],
                     'contact_number': input['contact_number'],
                     'address': input['address'],
                     'lat': input['lat'],
                     'lng': input['lng'],
                     'place_id': input['place_id']
                     }}, upsert=False)

        data = dict(input).copy()
        return flask.jsonify(api_response.apiResponse(constants.Utils.updated, False, data))
    else:
        return flask.jsonify(api_response.apiResponse(constants.Utils.no_user_found, False, {}))


def checkIfDataExists(recipient_reg, donor_reg, volunteer_reg, input):
    isEmailPresentInRecipient = recipient_reg.find_one({'email': input['email']})
    # isMobilePresentRecipient = recipient_reg.find_one({'contact_number': input['contact_number']})

    isEmailPresentInDonor = donor_reg.find_one({'email': input['email']})
    # isMobilePresentDonor = donor_reg.find_one({'contact_number': input['contact_number']})

    isEmailPresentInVolunteer = volunteer_reg.find_one({'email': input['email']})

    if isEmailPresentInRecipient is not None:
        return flask.jsonify(api_response.apiResponse(constants.Utils.user_exists, False, {}))
    # if isMobilePresentRecipient is not None:
    #     return flask.jsonify(api_response.apiResponse(constants.Utils.contact_number_exists, False, {}))

    if isEmailPresentInDonor is not None:
        return flask.jsonify(api_response.apiResponse(constants.Utils.user_exists, False, {}))
    # if isMobilePresentDonor is not None:
    #     return flask.jsonify(api_response.apiResponse(constants.Utils.contact_number_exists, False, {}))

    if isEmailPresentInVolunteer is not None:
        return flask.jsonify(api_response.apiResponse(constants.Utils.user_exists, False, {}))

    return None


@app.route('/recipient/getUserProfile', methods=['POST'])
def get_recipient_user_profile():
    input = request.get_json()

    recipient_reg = getCollectionName('recipient_registration')


    isUserIdPresent = recipient_reg.find_one({'_id': ObjectId(input['user_id'])})

    if isUserIdPresent is None:
        return flask.jsonify(api_response.apiResponse(constants.Utils.no_user_found, False, {}))

    data = dict(isUserIdPresent).copy()
    # data.pop('password')
    data.pop('_id')
    data.update({'user_id': str(isUserIdPresent['_id'])})
    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, data))


@app.route('/recipient/getAvailableFoodList', methods=['POST'])
def getAvailableFoodList():
    input = request.get_json()
    add_food_col = getCollectionName('add_food')
    accept_food_col = getCollectionName('accept_food')

    available_foods = add_food_col.find({'isFoodAccepted': input['isFoodAccepted']})
    accepted_food = accept_food_col.find({"recipient_user_id": input['user_id']}, {"food_item_id": 2, '_id': False})

    present_date = get_today_date()

    accepted_food_id_list = []
    available_food_list = list(available_foods)
    accepted_food_list = list(accepted_food)
    # print(accepted_food_list)

    foodList = []

    if len(available_food_list):
        for obj in available_food_list:
            # obj = dict(x)
            pick_up_date = datetime.strptime(obj['pick_up_date'], "%Y-%m-%d").date()
            if pick_up_date >= present_date:
                # obj.update({"status": constants.Utils.expired})
                obj.update({'id': str(obj['_id'])})
                del obj['_id']

                miles = dist(input['recipient_lat'], input['recipient_lng'], obj['pick_up_lat'], obj['pick_up_lng'])

                if miles < constants.Utils.miles:
                    obj.update({"distance": '%.2f' % (miles)})
                    foodList.append(obj)

    if len(accepted_food_list):
        for item in accepted_food_list:
            accepted_food_id_list.append(ObjectId(item['food_item_id']))

        accepted_food_obj = add_food_col.find({"_id": {"$in": accepted_food_id_list}})
        accepted_food_obj_list = list(accepted_food_obj)
        for i in accepted_food_obj_list:
            pick_up_date = datetime.strptime(i['pick_up_date'], "%Y-%m-%d").date()
            if pick_up_date >= present_date:
                i.update({'id': str(i['_id'])})
                del i['_id']
                miles = dist(input['recipient_lat'], input['recipient_lng'], i['pick_up_lat'], i['pick_up_lng'])
                i.update({"distance": '%.2f' % (miles)})
                foodList.append(i)

        # print(foodList)
    # else:
    #     if len(available_food_list):
    #         for obj in available_food_list:
    #             # obj = dict(x)
    #             pick_up_date = datetime.strptime(obj['pick_up_date'], "%Y-%m-%d").date()
    #             if pick_up_date >= present_date:
    #                 # obj.update({"status": constants.Utils.expired})
    #                 obj.update({'id': str(obj['_id'])})
    #                 del obj['_id']
    #
    #                 miles = dist(input['recipient_lat'], input['recipient_lng'], obj['pick_up_lat'], obj['pick_up_lng'])
    #
    #                 if miles < constants.Utils.miles:
    #                     foodList.append(obj)

    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, foodList))


def get_today_date():
    return datetime.now().date()


@app.route('/recipient/accept_food', methods=['POST'])
def accept_food():
    input = request.get_json()

    # recipient_reg = getCollectionName('recipient_registration')
    accept_food = getCollectionName('accept_food')
    add_food = getCollectionName('add_food')
    user_firebase_token_col = getCollectionName('user_firebase_token')
    volunteer_registration_col = getCollectionName('volunteer_registration')

    accept_food.insert_one(input)

    add_food.update_one({
        '_id': ObjectId(input['food_item_id'])
    }, {
        '$set': {
            'isFoodAccepted': True,
            'status': constants.Utils.waiting_for_volunteer
        }
    }, upsert=False)

    add_food_obj = add_food.find_one({'_id': ObjectId(input['food_item_id'])})

    obj = user_firebase_token_col.find_one({"user_id": input["donor_user_id"]})

    if obj is not None:
        if not obj['firebase_token']:
            send_notification_to_donor(obj['firebase_token'], input["business_name"])

    volunteer_obj = volunteer_registration_col.find({})

    volunteer_obj_list = list(volunteer_obj)

    ids = list()
    # food_donations_nearby_recipients_obj_list = list()

    for item in volunteer_obj_list:
        miles = dist(float(add_food_obj['pick_up_lat']), float(add_food_obj['pick_up_lng']), float(item['lat']),
                     float(item['lng']))
        # print(miles)
        if miles <= float(item['serving_distance']):
            # print(item)
            ids.append(str(ObjectId(item['_id'])))


    recipients_firebase_tokens = user_firebase_token_col.find({"user_id": {"$in": ids}})

    tokens = list()

    for item in recipients_firebase_tokens:
        tokens.append(item['firebase_token'])

    send_notifications_to_volunteers(tokens, add_food_obj['food_name'])

    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, {}))


@app.route('/recipient/food_delivered', methods=['POST'])
def food_delivered():
    input = request.get_json()

    # recipient_reg = getCollectionName('recipient_registration')
    # delivered_food = getCollectionName('delivered_food')
    add_food = getCollectionName('add_food')
    # collect_food = getCollectionName('collect_food')
    # user_firebase_token_col = getCollectionName('user_firebase_token')
    # volunteer_registration_col = getCollectionName('volunteer_registration')

    # collect_food_obj = collect_food.find_one({"food_item_id": input["food_item_id"]})
    #
    # data = dict(input)
    # data.update({"volunteer_id"})

    # delivered_food.insert_one(input)

    add_food.update_one({
        '_id': ObjectId(input['food_item_id'])
    }, {
        '$set': {
            'isFoodAccepted': True,
            'status': constants.Utils.delivered
        }
    }, upsert=False)

    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, {}))


@app.route('/send_notif', methods=['POST'])
def send_notif():
    input = request.get_json()
    # See documentation on defining a message payload.
    notification = messaging.Notification(title="Title", body="Body")

    # See documentation on defining a message payload.
    message = messaging.Message(
        notification=notification, token=input["token"])

    response = messaging.send(message)
    # Response is a message ID string.

    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, {}))


@app.route('/recipient/getAllFoodsByRecipient', methods=['POST'])
def getAllFoodsByRecipient():
    input = request.get_json()
    add_food_col = getCollectionName('add_food')
    accept_food_col = getCollectionName('accept_food')

    accept_food_obj = accept_food_col.find({'recipient_user_id': str(input['user_id'])})

    present_date = get_today_date()

    food_ids = []
    array = list(accept_food_obj)
    if len(array):
        for obj in array:
            food_ids.append(ObjectId(obj['food_item_id']))
        array.clear()

    data = add_food_col.find({'_id': {"$in": food_ids}})

    food_list = list(data)
    final_food_list = []
    if len(food_list):
        for obj in food_list:
            pick_up_date = datetime.strptime(obj['pick_up_date'], "%Y-%m-%d").date()
            # or obj['status'] == constants.Utils.delivered
            if pick_up_date < present_date:
                obj.update({'id': str(obj['_id'])})
                del obj['_id']
                final_food_list.append(obj)
        array.clear()

    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, final_food_list))


# ***************************************** volunteer *****************************************

@app.route('/volunteer/registration', methods=['POST'])
def volunteer_registration():
    input = request.get_json()

    volunteer_reg = getCollectionName('volunteer_registration')
    donor_reg = getCollectionName('donor_registration')
    recipient_reg = getCollectionName('recipient_registration')

    flag = checkIfDataExists(recipient_reg, volunteer_reg, donor_reg, input)

    if flag is not None:
        return flag

    data = dict(input).copy()
    data.pop('firebase_token')
    obj = volunteer_reg.insert_one(data).inserted_id
    data.pop('_id')
    data.update({'user_id': str(obj)})
    save_firebase_token(str(obj), input["firebase_token"], input["role"])

    return flask.jsonify(api_response.apiResponse(constants.Utils.inserted, False, data))


@app.route('/volunteer/update_profile', methods=['POST'])
def volunteer_update_profile():
    input = request.get_json()

    donor_reg = getCollectionName('volunteer_registration')

    isUserIdPresent = donor_reg.find_one({'_id': ObjectId(input['user_id'])})

    if isUserIdPresent is not None:
        obj = donor_reg.update_one({'_id': ObjectId(input['user_id'])}, {
            '$set': {'name': input['name'],
                     'serving_distance': input['serving_distance'],
                     'contact_number': input['contact_number'],
                     'address': input['address'],
                     'lat': input['lat'],
                     'lng': input['lng'],
                     'place_id': input['place_id']
                     }}, upsert=False)

        data = dict(input).copy()
        return flask.jsonify(api_response.apiResponse(constants.Utils.updated, False, data))
    else:
        return flask.jsonify(api_response.apiResponse(constants.Utils.no_user_found, False, {}))


@app.route('/volunteer/getAvailableFoodList', methods=['POST'])
def getAvailableFoodListForVolunteer():
    input = request.get_json()
    add_food_col = getCollectionName('add_food')

    waiting_for_volunteer_foods = add_food_col.find(
        {'isFoodAccepted': {"$in": [input['isFoodAccepted']]},
         "status": {"$in": [constants.Utils.waiting_for_volunteer, constants.Utils.pickeup_schedule]}})

    present_date = get_today_date()

    waiting_for_volunteer_food_list = list(waiting_for_volunteer_foods)


    foodList = []

    if len(waiting_for_volunteer_food_list):
        accepted_food_col = getCollectionName("accept_food")
        # recipient_registration_col = getCollectionName("recipient_registration")

        for obj in waiting_for_volunteer_food_list:
            # obj = dict(x)
            pick_up_date = datetime.strptime(obj['pick_up_date'], "%Y-%m-%d").date()
            if pick_up_date >= present_date:
                # obj.update({"status": constants.Utils.expired})
                obj.update({'id': str(obj['_id'])})
                del obj['_id']
                accepted_food_obj = accepted_food_col.find_one({"food_item_id": obj['id']})
                obj.update({"recipient_user_id": accepted_food_obj["recipient_user_id"]})
                miles = dist(input['volunteer_lat'], input['volunteer_lng'], obj['pick_up_lat'], obj['pick_up_lng'])
                if miles <= float(input['serving_distance']):
                    obj.update({"distance": '%.2f' % (miles)})
                    foodList.append(obj)

    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, foodList))


@app.route('/volunteer/getFoodItemDetails', methods=['POST'])
def getFoodItemDetails():
    input = request.get_json()
    recipient_registration_col = getCollectionName('recipient_registration')
    donor_registration_col = getCollectionName('donor_registration')

    recipient_obj = recipient_registration_col.find_one({"_id": ObjectId(input['recipient_user_id'])})
    donor_obj = donor_registration_col.find_one({"_id": ObjectId(input['donor_user_id'])})

    final_obj = dict()
    if recipient_obj is not None:
        final_obj.update(
            {"recipient_name": recipient_obj['name'], "recipient_business_name": recipient_obj['business_name'],
             "recipient_contact_number": recipient_obj['contact_number'], "code": recipient_obj['code'],
             "recipient_address": recipient_obj['address'],
             "recipient_lat": recipient_obj['lat'], "recipient_lng": recipient_obj['lng']})

        if donor_obj is not None:
            distance_in_miles = dist(float(recipient_obj['lat']), float(recipient_obj['lng']), float(donor_obj['lat']),
                                     float(donor_obj['lng']))
            final_obj.update(
                {"donor_name": donor_obj['name'], "donor_business_name": donor_obj['business_name'],
                 "donor_contact_number": donor_obj['contact_number'],
                 "donor_address": donor_obj['address'],
                 "donor_lat": donor_obj['lat'], "donor_lng": donor_obj['lng'], "distance": '%.2f' % (distance_in_miles)
                 }
            )

    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, final_obj))


@app.route('/volunteer/collect_food', methods=['POST'])
def collect_food():
    input = request.get_json()
    collect_food_col = getCollectionName('collect_food')
    add_food_col = getCollectionName('add_food')

    add_food_obj = add_food_col.find_one({"_id": ObjectId(input["food_item_id"])})

    if add_food_obj is not None:

        if add_food_obj['status'] == constants.Utils.waiting_for_volunteer:

            id = collect_food_col.insert_one(input).inserted_id
            obj = add_food_col.update_one({'_id': ObjectId(input['food_item_id'])}, {
                '$set': {'status': constants.Utils.pickeup_schedule}}, upsert=False)
        else:
            return flask.jsonify(api_response.apiResponse(constants.Utils.already_assigned, False, {}))

    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, {}))


@app.route('/volunteer/getAllFoodsByVolunteer', methods=['POST'])
def getAllFoodsByVolunteer():
    input = request.get_json()
    add_food_col = getCollectionName('add_food')
    collect_food_col = getCollectionName('collect_food')

    collect_food_col_obj = collect_food_col.find({'volunteer_user_id': str(input['user_id'])})

    present_date = get_today_date()

    food_ids = []
    array = list(collect_food_col_obj)
    if len(array):
        for obj in array:
            food_ids.append(ObjectId(obj['food_item_id']))
        # array.clear()

    data = add_food_col.find({'_id': {"$in": food_ids}})

    food_list = list(data)
    final_food_list = []
    if len(food_list):
        for obj in food_list:
            pick_up_date = datetime.strptime(obj['pick_up_date'], "%Y-%m-%d").date()
            # or obj['status'] == constants.Utils.delivered
            if pick_up_date < present_date:
                obj.update({'id': str(obj['_id'])})
                del obj['_id']
                collect_food_col_objct = collect_food_col.find_one(
                    {"volunteer_user_id": str(input['user_id']), "food_item_id": str(obj['id'])})
                obj.update({"recipient_user_id": collect_food_col_objct['recipient_user_id']})
                miles = dist(input['volunteer_lat'], input['volunteer_lng'], obj['pick_up_lat'], obj['pick_up_lng'])
                obj.update({"distance": '%.2f' % (miles)})
                final_food_list.append(obj)

    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, final_food_list))


@app.route('/logout', methods=['POST'])
def logout():
    input = request.get_json()

    user_firebase_token_col = getCollectionName('user_firebase_token')
    user_firebase_token_col.delete_one({"user_id": input['user_id']})

    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, {}))


def send_notifications_to_recipients(ids, food_name, quantity):
    # registration_tokens = [
    #     'YOUR_REGISTRATION_TOKEN_1',
    #     # ...
    #     'YOUR_REGISTRATION_TOKEN_N',
    # ]

    notification = messaging.Notification(title=food_name, body=quantity)

    # See documentation on defining a message payload.
    message = messaging.MulticastMessage(
        notification=notification,
        tokens=ids,
    )
    response = messaging.send_multicast(message)
    if response.failure_count > 0:
        responses = response.responses
        failed_tokens = []
        for idx, resp in enumerate(responses):
            if not resp.success:
                # The order of responses corresponds to the order of the registration tokens.
                failed_tokens.append(ids[idx])


def send_notifications_to_volunteers(ids, food_name):
    notification = messaging.Notification(title=food_name,
                                          body="New food item has been added in your locality, pick up food now?")

    # See documentation on defining a message payload.
    message = messaging.MulticastMessage(
        notification=notification,
        tokens=ids,
    )
    response = messaging.send_multicast(message)
    if response.failure_count > 0:
        responses = response.responses
        failed_tokens = []
        for idx, resp in enumerate(responses):
            if not resp.success:
                # The order of responses corresponds to the order of the registration tokens.
                failed_tokens.append(ids[idx])


def send_notification_to_donor(token, recipient_name):
    notification = messaging.Notification(title="Food Accepted by " + str(recipient_name), body="")

    # See documentation on defining a message payload.
    message = messaging.Message(
        notification=notification,
        token=token,
    )
    response = messaging.send(message)


def dist(lat1, long1, lat2, long2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lat1, long1, lat2, long2 = map(radians, [lat1, long1, lat2, long2])
    # haversine formula
    dlon = long2 - long1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    # Radius of earth in kilometers is 6371, use 3956 for miles
    miles = 3956 * c
    return miles


def _get_access_token():
    """Retrieve a valid access token that can be used to authorize requests.

  :return: Access token.
  """
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        '/Users/srikamalteja/Desktop/closingtime_backend/closingtimeapi/closingtime-e1fe0-firebase-adminsdk-1zdrb-228c74a754.json',
        'https://www.googleapis.com/auth/firebase.messaging')
    access_token_info = credentials.get_access_token()
    return access_token_info.access_token


# Admin API's
@app.route('/login_admin', methods=['POST'])
def login_admin():
    input = request.get_json()
    # print(input)
    admin_cred = getCollectionName('admin_reg')
    record = admin_cred.find_one({'uname': input['uname']})
    if record:
        pwd = base64.b64decode(record['pwd']).decode('utf-8')
        if pwd == input['pwd']:
            data = dict(record).copy()
            data.pop('_id')
            data.pop('pwd')
            data.update({'user_id': str(record['_id'])})

            return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, data))
        else:
            return flask.jsonify(api_response.apiResponse(constants.Utils.invalid_cred, False, {}))
    else:
        return flask.jsonify(api_response.apiResponse(constants.Utils.invalid_cred, False, {}))


@app.route('/admin/get_all_users_list', methods=['GET'])
def get_all_users_list():
    # input = request.get_json()
    donor_reg_list = getCollectionName('donor_registration').find({}, {'_id': False})
    recipient_reg_list = getCollectionName('recipient_registration').find({}, {'_id': False})
    volunteer_reg_list = getCollectionName('volunteer_registration').find({}, {'_id': False})

    # print(list(donor_reg_list))

    data = {
        'donor': list(donor_reg_list),
        'recipient': list(recipient_reg_list),
        'volunteer': list(volunteer_reg_list)
    }

    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, data))


@app.route('/admin/get_all_users_count', methods=['GET'])
def get_all_users_count():
    # input = request.get_json()
    donor_reg_count = getCollectionName('donor_registration').find().count()
    recipient_reg_count = getCollectionName('recipient_registration').find().count()
    volunteer_reg_count = getCollectionName('volunteer_registration').find().count()

    data = {
        'donor_count': str(donor_reg_count),
        'recipient_count': str(recipient_reg_count),
        'volunteer_count': str(volunteer_reg_count)
    }

    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, data))


@app.route('/admin/registration', methods=['POST'])
def admin_registration():
    input = request.get_json()

    admin_reg = getCollectionName('admin_reg')

    pwd = input['pwd'].encode("utf-8")
    encoded = base64.b64encode(pwd)
    # print(encoded)
    input['pwd'] = encoded

    data = dict(input)
    obj = admin_reg.insert_one(data).inserted_id

    return flask.jsonify(api_response.apiResponse(constants.Utils.inserted, False, {}))


if __name__ == '__main__':
    # app.run(debug=True)
    app.run()
