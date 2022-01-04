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
import bson
from bson.binary import Binary
from oauth2client.service_account import ServiceAccountCredentials

import firebase_admin
from firebase_admin import credentials, messaging
from math import radians, cos, sin, asin, sqrt
from datetime import datetime

cred = credentials.Certificate("closingtime-e1fe0-firebase-adminsdk-1zdrb-228c74a754.json")
firebase_admin.initialize_app(cred)

app = Flask(__name__)

CONNECTION_STRING = "mongodb+srv://closingtime:closingtime@closingtime.1bd7w.mongodb.net/closingtime?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE"
database_name = "closingtime"
password = "closingtime"

client = pymongo.MongoClient(CONNECTION_STRING)
db = client.get_database('closingtime')


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
    print(input)
    donor_reg = getCollectionName('donor_registration')
    record = donor_reg.find_one({'email': input['email']})
    if record:
        pwd = base64.b64decode(record['password']).decode('utf-8')
        print(pwd)
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
    print(input)
    donor_reg = getCollectionName('donor_registration')
    recipient_reg = getCollectionName('recipient_registration')

    donor_record = donor_reg.find_one({'email': input['email']})
    recipient_record = recipient_reg.find_one({'email': input['email']})

    if donor_record is not None:
        data = dict(donor_record).copy()
        print(data)
        data.pop('_id')
        data.update({'user_id': str(donor_record['_id'])})
        updateFirebaseToken(data['user_id'], input['firebase_token'], constants.Utils.donor)
        print(data)
        return flask.jsonify(api_response.apiResponse(constants.Utils.user_exists, False, data))

    if recipient_record is not None:
        data = dict(recipient_record).copy()
        print(data)
        data.pop('_id')
        data.update({'user_id': str(recipient_record['_id'])})
        print(data)
        updateFirebaseToken(data['user_id'], input['firebase_token'], constants.Utils.recipient)

        return flask.jsonify(api_response.apiResponse(constants.Utils.user_exists, False, data))

    return flask.jsonify(api_response.apiResponse(constants.Utils.new_user, False, {}))


def updateFirebaseToken(id, fb_token, role):
    user_firebase_token = getCollectionName('user_firebase_token')
    print(fb_token)
    user_firebase_token.replace_one({"user_id": id}, {"firebase_token": fb_token, "user_id": id, "role": role})

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
    print('Successfully sent message:', response)


# *******************************************         donor           *****************************************************


@app.route('/food_donor/getUserProfile', methods=['POST'])
def get_user_profile():
    input = request.get_json()

    donor_reg = getCollectionName('donor_registration')
    print(ObjectId(input['user_id']))
    print(input['user_id'])

    isUserIdPresent = donor_reg.find_one({'_id': ObjectId(input['user_id'])})

    if isUserIdPresent is None:
        return flask.jsonify(api_response.apiResponse(constants.Utils.no_user_found, False, {}))

    print(isUserIdPresent)
    data = dict(isUserIdPresent).copy()
    # data.pop('password')
    data.pop('_id')
    data.update({'user_id': str(isUserIdPresent['_id'])})
    print(data)
    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, data))


@app.route('/food_donor/registration', methods=['POST'])
def donor_registration():
    input = request.get_json()

    # user_collection = pymongo.collection.Collection(db, 'donor_registration')
    donor_reg = getCollectionName('donor_registration')
    recipient_reg = getCollectionName('recipient_registration')

    flag = checkIfDataExists(recipient_reg, donor_reg, input)

    if flag is not None:
        return flag

    data = dict(input).copy()
    data.pop('firebase_token')
    obj = donor_reg.insert_one(data).inserted_id
    print(obj)
    print(input)
    # data = dict(input).copy()
    # data.pop('password')
    data.pop('_id')
    data.update({'user_id': str(obj)})
    save_firebase_token(str(obj), input["firebase_token"], input["role"])
    print(data)

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

    isUserIdPresent = donor_reg.find_one({'user_id': input['user_id']})

    if isUserIdPresent is not None:
        donor_reg.update_one({'user_id': input['user_id']}, {
            'name': input['name'],
            'business_name': input['business_name'],
            'contact_number': input['contact_number'],
            'country': input['country'],
            'area_name': input['area_name'],
            'street_name': input['postcode'],
            'postcode': input['postcode']
        })

    obj = donor_reg.insert_one(input).inserted_id

    data = dict(input).copy()
    data.pop('password')
    data.pop('_id')
    data.update({'user_id': str(obj)})
    print(data)
    return flask.jsonify(api_response.apiResponse(constants.Utils.inserted, False, data))


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

    print(ids)

    # food_donations_nearby_recipients_col = getCollectionName("food_donations_nearby_recipients")

    user_firebase_token_col = getCollectionName("user_firebase_token")
    recipients_firebase_tokens = user_firebase_token_col.find({"user_id": {"$in": ids}})

    tokens = list()

    for item in recipients_firebase_tokens:
        print(item)

        print(item['firebase_token'])
        tokens.append(item['firebase_token'])

    send_notifications_to_recipients(tokens, input['food_name'], input['quantity'])

    return flask.jsonify(api_response.apiResponse(constants.Utils.inserted, False, {}))


@app.route('/test', methods=['POST'])
def test():
    user_firebase_token = getCollectionName("user_firebase_token")

    objj = user_firebase_token.find({"role": constants.Utils.recipient})

    print(str(objj))

    l = list(objj)

    # print(l)

    for x in l:
        print(x['firebase_token'])

    return flask.jsonify(api_response.apiResponse(constants.Utils.inserted, False, {}))


@app.route('/food_donor/added_food_list', methods=['POST'])
def added_food_list():
    input = request.get_json()
    add_food_col = getCollectionName('add_food')

    if input['user_id'] == "":
        data = add_food_col.find({})

    else:
        data = add_food_col.find({'user_id': str(input['user_id'])})

    foodList = []
    array = list(data)
    if len(array):
        for x in array:
            obj = dict(x)
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
        add_food_col.update_one({'user_id': input['user_id']}, {
            'food_name': input['food_name'],
            'food_desc': input['food_desc'],
            'quantity': input['quantity'],
            'food_ingredients': input['food_ingredients'],
            'pick_up_date': input['pick_up_date'],
            'allergen': input['allergen'],
            'image': input['image']
        })

        return flask.jsonify(api_response.apiResponse(constants.Utils.updated, False, {}))

    return flask.jsonify(api_response.apiResponse(constants.Utils.failed, False, {}))


# *******************************************         recipient           *****************************************************


@app.route('/recipient/registration', methods=['POST'])
def recipient_registration():
    input = request.get_json()

    recipient_reg = getCollectionName('recipient_registration')
    donor_reg = getCollectionName('donor_registration')
    # recipient_reg = getCollectionName('volunteer_registration')

    flag = checkIfDataExists(recipient_reg, donor_reg, input)

    if flag is not None:
        return flag

    data = dict(input).copy()
    data.pop('firebase_token')
    obj = recipient_reg.insert_one(data).inserted_id
    print(obj)
    print(input)
    # data = dict(input).copy()
    # data.pop('password')
    data.pop('_id')
    data.update({'user_id': str(obj)})
    save_firebase_token(str(obj), input["firebase_token"], input["role"])
    print(data)
    return flask.jsonify(api_response.apiResponse(constants.Utils.inserted, False, data))


def checkIfDataExists(recipient_reg, donor_reg, input):
    isEmailPresentInRecipient = recipient_reg.find_one({'email': input['email']})
    isMobilePresentRecipient = recipient_reg.find_one({'contact_number': input['contact_number']})

    isEmailPresentInDonor = donor_reg.find_one({'email': input['email']})
    isMobilePresentDonor = donor_reg.find_one({'contact_number': input['contact_number']})

    if isEmailPresentInRecipient is not None:
        return flask.jsonify(api_response.apiResponse(constants.Utils.user_exists, False, {}))
    if isMobilePresentRecipient is not None:
        return flask.jsonify(api_response.apiResponse(constants.Utils.contact_number_exists, False, {}))

    if isEmailPresentInDonor is not None:
        return flask.jsonify(api_response.apiResponse(constants.Utils.user_exists, False, {}))
    if isMobilePresentDonor is not None:
        return flask.jsonify(api_response.apiResponse(constants.Utils.contact_number_exists, False, {}))

    return None


@app.route('/recipient/getUserProfile', methods=['POST'])
def get_recipient_user_profile():
    input = request.get_json()

    recipient_reg = getCollectionName('recipient_registration')
    print(ObjectId(input['user_id']))
    print(input['user_id'])

    isUserIdPresent = recipient_reg.find_one({'_id': ObjectId(input['user_id'])})

    if isUserIdPresent is None:
        return flask.jsonify(api_response.apiResponse(constants.Utils.no_user_found, False, {}))

    print(isUserIdPresent)
    data = dict(isUserIdPresent).copy()
    # data.pop('password')
    data.pop('_id')
    data.update({'user_id': str(isUserIdPresent['_id'])})
    print(data)
    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, data))


@app.route('/recipient/getAvailableFoodList', methods=['POST'])
def getAvailableFoodList():
    input = request.get_json()
    add_food_col = getCollectionName('add_food')

    # data = add_food_col.find({'isFoodAccepted': input['isFoodAccepted']})
    data = add_food_col.find()

    foodList = []
    array = list(data)
    if len(array):
        present_date = datetime.now().date()
        for x in array:
            obj = dict(x)
            pick_up_date = datetime.strptime(obj['pick_up_date'], "%Y-%m-%d").date()
            if pick_up_date <= present_date:
                obj.update({"status": constants.Utils.expired})
            obj.update({'id': str(obj['_id'])})
            del obj['_id']

            miles = dist(input['recipient_lat'], input['recipient_lng'], obj['pick_up_lat'], obj['pick_up_lng'])

            if miles < constants.Utils.miles:
                foodList.append(obj)
        array.clear()

    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, foodList))


@app.route('/recipient/accept_food', methods=['POST'])
def accept_food():
    input = request.get_json()

    # recipient_reg = getCollectionName('recipient_registration')
    accept_food = getCollectionName('accept_food')
    add_food = getCollectionName('add_food')
    user_firebase_token = getCollectionName('user_firebase_token')

    accept_food.insert_one(input)

    add_food.update_one({
        '_id': ObjectId(input['food_item_id'])
    }, {
        '$set': {
            'isFoodAccepted': True,
            'status': constants.Utils.waiting_for_volunteer
        }
    }, upsert=False)

    obj = user_firebase_token.find_one({"user_id": input["donor_user_id"]})

    send_notification_to_donor(obj['firebase_token'], input["business_name"])

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
    print('Successfully sent message:', response)

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
        print('List of tokens that caused failures: {0}'.format(failed_tokens))


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
    print(access_token_info)
    return access_token_info.access_token


if __name__ == '__main__':
    # present_date = datetime.now().date()
    # pick_up_date = datetime.strptime("2022-01-03", "%Y-%m-%d").date()
    # print(pick_up_date)
    # if pick_up_date <= present_date:
    #     print("working")
    # print(present_date)
    app.run(debug=True)
