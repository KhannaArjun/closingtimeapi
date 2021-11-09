from flask import Flask, request
from flask_mongoengine import MongoEngine
from flask_pymongo import pymongo
import flask
from food_donor_model import food_donor_registration_model
from food_donor_model import add_food_model
from utils import api_response
from utils import constants
from pymongo.cursor import Cursor

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

@app.route('/', methods= ['GET'])
def index():
    return "hello"

@app.route('/login', methods= ['POST'])
def login():
    input = request.get_json()
    print(input)
    donor_reg = getCollectionName('donor___registration')
    record = donor_reg.find_one({'email': input['email']})
    if record:
       if record['password'] == input['password']:
           data = dict(record).copy()
           data.pop('_id')
           data.update({'user_id': str(record['_id'])})

           return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, data))
       else:
           return flask.jsonify(api_response.apiResponse(constants.Utils.invalid_cred, False, {}))

    else:
        return flask.jsonify(api_response.apiResponse(constants.Utils.invalid_cred, False, {}))


# *******************************************         donor           *****************************************************


@app.route('/food_donor/registration', methods=['POST'])
def donor_registration():
    input = request.get_json()

    # user_collection = pymongo.collection.Collection(db, 'donor___registration')
    donor_reg = getCollectionName('donor___registration')

    isEmailPresent = donor_reg.find_one({'email': input['email']})
    print(isEmailPresent)

    if isEmailPresent is not None:

        return flask.jsonify(api_response.apiResponse(constants.Utils.user_exists, False, {}))

    obj = donor_reg.insert_one(input).inserted_id
    data = {
        "user_id": str(obj)
    }
    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, data))


@app.route('/food_donor/add_food', methods=['POST'])
def add_food():
    input = request.get_json()

    obj = add_food_model.AddFood(**input).save()

    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, {}))



@app.route('/food_donor/added_food_list', methods=['POST'])
def added_food_list():
    input = request.get_json()
    data = db.add_food.find({'user_id': str(input['user_id'])})

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


if __name__ == '__main__':
    app.run(debug=True)
