import base64
import os
from logging import FileHandler, WARNING
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from bson import ObjectId
from flask import Flask, request
# from flask_mongoengine import MongoEngine  # Not currently used
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
from datetime import datetime, timedelta
from cfg.cfg import get_prod_db, get_dev_db
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit
import qrcode
import io
import base64
import uuid
import json
import smtplib
import hashlib
import secrets
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from firebase_admin import storage
import requests
from utils.donation_page import get_donor_registration_email_template
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

file_handler = FileHandler('error_logs.txt')
file_handler.setLevel(WARNING)

# Initialize Firebase Admin SDK with error handling
FIREBASE_ENABLED = False
try:
    # Check if Firebase app is already initialized
    if not firebase_admin._apps:
        # Try to get Firebase config from environment variables first
        firebase_config = os.environ.get('FIREBASE_CONFIG')
        if firebase_config:
            try:
                import json
                config_dict = json.loads(firebase_config)
                cred = credentials.Certificate(config_dict)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': 'closingtime-e1fe0.appspot.com'
                })
                FIREBASE_ENABLED = True
                print("✅ Firebase Admin SDK initialized successfully with environment config")
            except Exception as e:
                print(f"⚠️  Failed to initialize with environment config: {e}")
        
        # If environment config failed or not available, try local files
        if not FIREBASE_ENABLED:
            # Try the NEWEST service account key first (e732fc6e97) - production path
            try:
                cred = credentials.Certificate("/etc/secrets/closingtime-e1fe0-firebase-adminsdk-1zdrb-e732fc6e97.json")
                firebase_admin.initialize_app(cred, {
                    'storageBucket': 'closingtime-e1fe0.appspot.com'
                })
                FIREBASE_ENABLED = True
                print("✅ Firebase Admin SDK initialized successfully with NEWEST key (e732fc6e97)")
            except Exception as e0:
                print(f"⚠️  Failed to initialize with NEWEST key: {e0}")
                # Try the newer service account key as fallback - production path
                try:
                    cred = credentials.Certificate("/etc/secrets/closingtime-e1fe0-firebase-adminsdk-1zdrb-daa665d59c.json")
                    firebase_admin.initialize_app(cred, {
                        'storageBucket': 'closingtime-e1fe0.appspot.com'
                    })
                    FIREBASE_ENABLED = True
                    print("✅ Firebase Admin SDK initialized successfully with newer key")
                except Exception as e1:
                    print(f"⚠️  Failed to initialize with newer key: {e1}")
                    # Try the older service account key as final fallback - production path
                    try:
                        cred = credentials.Certificate("/etc/secrets/closingtime-e1fe0-firebase-adminsdk-1zdrb-228c74a754.json")
                        firebase_admin.initialize_app(cred, {
                            'storageBucket': 'closingtime-e1fe0.appspot.com'
                        })
                        FIREBASE_ENABLED = True
                        print("✅ Firebase Admin SDK initialized successfully with oldest key")
                    except Exception as e2:
                        print(f"⚠️  Failed to initialize with oldest key: {e2}")
                        print("❌ Firebase initialization failed - photo uploads will be disabled")
                        FIREBASE_ENABLED = False
                
    else:
        FIREBASE_ENABLED = True
        print("✅ Firebase Admin SDK already initialized")
except Exception as e:
    FIREBASE_ENABLED = False
    print(f"❌ Firebase initialization failed: {e}")
    print("💡 Photo uploads will be disabled. Please check Firebase service account key.")
    # Continue without Firebase if initialization fails

app = Flask(__name__)
app.logger.addHandler(file_handler)

# CONNECTION_STRING = "mongodb+srv://closingtime:closingtime@closingtime.1bd7w.mongodb.net/closingtime?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE"

#to debug comment prod db
# CONNECTION_STRING, db = get_dev_db()
CONNECTION_STRING, db = get_prod_db()

import ssl
import certifi

# MongoDB client with explicit SSL configuration
client = pymongo.MongoClient(
    CONNECTION_STRING,
    tls=True,
    tlsAllowInvalidCertificates=True,  # Allow invalid certificates
    serverSelectionTimeoutMS=30000,  # 30 second timeout
    connectTimeoutMS=30000,  # 30 second timeout
    socketTimeoutMS=30000,  # 30 second socket timeout
    retryWrites=True,
    retryReads=True,
    w='majority'
)
db = client.get_database(db)

# Health check function for MongoDB
def mongodb_health_check():
    """Perform MongoDB health check by pinging the database"""
    try:
        # Ping the database to check connection
        client.admin.command('ping')
        print(f"✅ MongoDB Health Check - {datetime.now()}: Connection successful")
        return True
    except Exception as e:
        print(f"❌ MongoDB Health Check - {datetime.now()}: Connection failed - {e}")
        return False

def comprehensive_health_check():
    """Perform comprehensive health check of all services (runs every 20 minutes)"""
    try:
        print(f"🔍 Comprehensive Health Check - {datetime.now()}: Starting...")
        
        # Ping MongoDB
        client.admin.command('ping')
        server_info = client.server_info()
        db_stats = db.command("dbStats")
        
        # Safely check scheduler status
        scheduler_running = False
        jobs_count = 0
        try:
            if 'scheduler' in globals():
                scheduler_running = scheduler.running
                jobs_count = len(scheduler.get_jobs())
        except Exception as scheduler_err:
            print(f"Scheduler check error: {scheduler_err}")
        
        health_status = {
            "mongodb": {
                "connected": True,
                "server_version": server_info.get('version', 'unknown'),
                "database_name": db.name,
                "collections": db_stats.get('collections', 0),
                "data_size": db_stats.get('dataSize', 0)
            },
            "firebase": {
                "enabled": FIREBASE_ENABLED
            },
            "scheduler": {
                "running": scheduler_running,
                "jobs_count": jobs_count
            }
        }
        
        print(f"✅ Comprehensive Health Check - {datetime.now()}: All systems operational")
        print(f"   MongoDB: {health_status['mongodb']['connected']}")
        print(f"   Firebase: {health_status['firebase']['enabled']}")
        print(f"   Scheduler: {health_status['scheduler']['running']} ({health_status['scheduler']['jobs_count']} jobs)")
        return True
        
    except Exception as e:
        print(f"❌ Comprehensive Health Check - {datetime.now()}: Check failed - {e}")
        return False

# Initialize scheduler for health checks
print("🔧 Initializing Background Scheduler...")
scheduler = BackgroundScheduler()

try:
    # MongoDB health check every 3 hours
    print("📅 Adding MongoDB health check job (every 3 hours)...")
    scheduler.add_job(
        func=mongodb_health_check,
        trigger=IntervalTrigger(hours=3),
        id='mongodb_health_check',
        name='MongoDB Health Check every 3 hours',
        replace_existing=True
    )

    # Comprehensive health check every 3 hours
    print("📅 Adding Comprehensive health check job (every 3 hours)...")
    scheduler.add_job(
        func=comprehensive_health_check,
        trigger=IntervalTrigger(hours=3),
        id='comprehensive_health_check',
        name='Comprehensive Health Check every 3 hours',
        replace_existing=True
    )

    # Start the scheduler
    print("🚀 Starting Background Scheduler...")
    scheduler.start()
    print(f"✅ Scheduler started successfully! Jobs count: {len(scheduler.get_jobs())}")
    
    # Run initial health check immediately
    print("🔍 Running initial health checks...")
    mongodb_health_check()
    comprehensive_health_check()
    
except Exception as scheduler_error:
    print(f"❌ Scheduler initialization failed: {scheduler_error}")
    print("⚠️  Health checks will not run automatically")

# Shutdown scheduler when app exits
atexit.register(lambda: scheduler.shutdown() if scheduler.running else None)

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


@app.route('/assets/<filename>')
def serve_assets(filename):
    """Serve static files from the assets directory"""
    return flask.send_from_directory('assets', filename)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint that returns MongoDB connection status"""
    try:
        # Perform MongoDB health check
        client.admin.command('ping')
        
        # Get additional MongoDB stats
        server_info = client.server_info()
        db_stats = db.command("dbStats")
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "mongodb": {
                "connected": True,
                "server_version": server_info.get('version', 'unknown'),
                "database_name": db.name,
                "collections": db_stats.get('collections', 0),
                "data_size": db_stats.get('dataSize', 0)
            },
            "firebase": {
                "enabled": FIREBASE_ENABLED
            },
            "scheduler": {
                "running": scheduler.running,
                "jobs_count": len(scheduler.get_jobs())
            }
        }
        
        return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, health_data))
        
    except Exception as e:
        error_data = {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "mongodb": {
                "connected": False
            },
            "firebase": {
                "enabled": FIREBASE_ENABLED
            },
            "scheduler": {
                "running": scheduler.running if 'scheduler' in locals() else False
            }
        }
        
        return flask.jsonify(api_response.apiResponse(constants.Utils.failed, False, error_data)), 503


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


@app.route('/admin/register', methods=['POST'])
def admin_register():
    """
    Register a new admin user
    Expected payload: {"name": "Admin Name", "username": "admin", "password": "password"}
    Note: In production, you might want to protect this endpoint or disable after initial setup
    """
    try:
        input_data = request.get_json()
        
        if not input_data:
            return flask.jsonify(api_response.apiResponse("Invalid request format", True, {}))
        
        # Validate required fields
        required_fields = ['name', 'username', 'password']
        for field in required_fields:
            if field not in input_data:
                return flask.jsonify(api_response.apiResponse(f"Missing required field: {field}", True, {}))
        
        admin_reg = getCollectionName('admin_registration')
        
        # Check if admin already exists
        existing_admin = admin_reg.find_one({'username': input_data['username']})
        if existing_admin:
            return flask.jsonify(api_response.apiResponse("Admin with this username already exists", True, {}))
        
        # Encode password (same pattern as donors)
        pwd = input_data['password'].encode("utf-8")
        encoded_password = base64.b64encode(pwd)
        
        # Prepare admin data
        admin_data = {
            'name': input_data['name'],
            'username': input_data['username'],
            'password': encoded_password,
            'role': 'Admin',
            'created_at': datetime.now(pytz.UTC).isoformat(),
            'status': 'active'
        }
        
        # Insert admin
        obj = admin_reg.insert_one(admin_data).inserted_id
        
        # Prepare response (without password)
        response_data = {
            'user_id': str(obj),
            'name': input_data['name'],
            'username': input_data['username'],
            'role': 'Admin'
        }
        
        return flask.jsonify(api_response.apiResponse("Admin registered successfully", False, response_data))
    
    except Exception as e:
        print(f"Admin registration error: {str(e)}")
        return flask.jsonify(api_response.apiResponse(f"Registration failed: {str(e)}", True, {}))


@app.route('/admin/login', methods=['POST'])
def admin_login():
    """
    Admin login endpoint - validates against database
    Expected payload: {"username": "admin", "password": "password"}
    """
    try:
        input_data = request.get_json()
        
        if not input_data:
            return flask.jsonify(api_response.apiResponse("Invalid request format", True, {}))
        
        username = input_data.get('username', '')
        password = input_data.get('password', '')
        
        if not username or not password:
            return flask.jsonify(api_response.apiResponse("Username and password are required", True, {}))
        
        # Get admin from database
        admin_reg = getCollectionName('admin_registration')
        record = admin_reg.find_one({'username': username})
        
        if not record:
            return flask.jsonify(api_response.apiResponse(constants.Utils.invalid_cred, True, {}))
        
        # Decode and verify password (same pattern as donors)
        pwd = base64.b64decode(record['password']).decode('utf-8')
        
        if pwd != password:
            return flask.jsonify(api_response.apiResponse(constants.Utils.invalid_cred, True, {}))
        
        # Generate session token
        session_token = secrets.token_hex(32)
        
        # Store session token in database
        admin_sessions = getCollectionName('admin_sessions')
        session_data = {
            'admin_id': str(record['_id']),
            'username': username,
            'session_token': session_token,
            'created_at': datetime.now(pytz.UTC).isoformat(),
            'expires_at': (datetime.now(pytz.UTC) + timedelta(hours=24)).isoformat()
        }
        admin_sessions.insert_one(session_data)
        
        # Prepare response data
        admin_data = {
            'user_id': str(record['_id']),
            'name': record['name'],
            'username': record['username'],
            'role': 'Admin',
            'session_token': session_token,
            'login_time': datetime.now(pytz.UTC).isoformat()
        }
        
        return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, admin_data))
    
    except Exception as e:
        print(f"Admin login error: {str(e)}")
        return flask.jsonify(api_response.apiResponse("Login failed", True, {}))


def require_admin_token(f):
    """
    Decorator to require admin authentication for protected endpoints
    Validates token against database and checks expiration
    Expects 'Authorization' header with format: 'Bearer <token>'
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            auth_header = request.headers.get('Authorization', '')
            
            if not auth_header.startswith('Bearer '):
                return flask.jsonify(api_response.apiResponse("Missing or invalid authorization header", True, {}))
            
            token = auth_header.replace('Bearer ', '')
            
            if not token:
                return flask.jsonify(api_response.apiResponse("Invalid admin token", True, {}))
            
            # Validate token against database
            admin_sessions = getCollectionName('admin_sessions')
            session = admin_sessions.find_one({'session_token': token})
            
            if not session:
                return flask.jsonify(api_response.apiResponse("Invalid or expired admin token", True, {}))
            
            # Check if token is expired
            expires_at = datetime.fromisoformat(session['expires_at'])
            if datetime.now(pytz.UTC) > expires_at:
                # Delete expired session
                admin_sessions.delete_one({'session_token': token})
                return flask.jsonify(api_response.apiResponse("Session expired. Please login again", True, {}))
            
            # Token is valid, attach admin_id to request for use in endpoint
            request.admin_id = session['admin_id']
            
            return f(*args, **kwargs)
        
        except Exception as e:
            print(f"Admin auth error: {str(e)}")
            return flask.jsonify(api_response.apiResponse("Authentication failed", True, {}))
    
    return decorated_function


@app.route('/admin/logout', methods=['POST'])
@require_admin_token
def admin_logout():
    """
    Admin logout endpoint - removes session from database
    Requires valid admin token in Authorization header
    """
    try:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '')
        
        # Delete session from database
        admin_sessions = getCollectionName('admin_sessions')
        result = admin_sessions.delete_one({'session_token': token})
        
        if result.deleted_count > 0:
            return flask.jsonify(api_response.apiResponse("Logged out successfully", False, {}))
        else:
            return flask.jsonify(api_response.apiResponse("Session not found", True, {}))
    
    except Exception as e:
        print(f"Admin logout error: {str(e)}")
        return flask.jsonify(api_response.apiResponse("Logout failed", True, {}))


@app.route('/admin/test', methods=['GET'])
@require_admin_token
def admin_test():
    """
    Test endpoint to verify admin authentication is working
    Requires admin token in Authorization header
    """
    return flask.jsonify(api_response.apiResponse("Admin access granted", False, {
        'message': 'This is a protected admin endpoint',
        'timestamp': datetime.now(pytz.UTC).isoformat()
    }))


@app.route('/admin/health', methods=['GET'])
def admin_health():
    """
    Admin health check endpoint - no authentication required
    """
    return flask.jsonify(api_response.apiResponse("Admin API is running", False, {
        'status': 'healthy',
        'timestamp': datetime.now(pytz.UTC).isoformat()
    }))


@app.route('/admin/scheduler_status', methods=['GET'])
@require_admin_token
def scheduler_status():
    """
    Get detailed scheduler status and job information
    Requires admin authentication token
    """
    try:
        jobs = scheduler.get_jobs()
        job_details = []
        
        for job in jobs:
            job_details.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger),
                'func_name': job.func.__name__ if hasattr(job.func, '__name__') else str(job.func)
            })
        
        scheduler_info = {
            'running': scheduler.running,
            'shutdown': scheduler.shutdown,
            'total_jobs': len(jobs),
            'jobs': job_details
        }
        
        return flask.jsonify(api_response.apiResponse("Scheduler status retrieved", False, scheduler_info))
    
    except Exception as e:
        print(f"Scheduler status error: {str(e)}")
        return flask.jsonify(api_response.apiResponse(f"Scheduler status error: {str(e)}", True, {}))


@app.route('/admin/test_health_checks', methods=['POST'])
@require_admin_token
def test_health_checks():
    """
    Manually trigger health checks for testing
    Requires admin authentication token
    """
    try:
        print("🧪 Manual health check test triggered by admin...")
        
        # Run MongoDB health check
        mongodb_result = mongodb_health_check()
        
        # Run comprehensive health check
        comprehensive_result = comprehensive_health_check()
        
        test_results = {
            'mongodb_health_check': mongodb_result,
            'comprehensive_health_check': comprehensive_result,
            'scheduler_running': scheduler.running if 'scheduler' in globals() else False,
            'scheduler_jobs': len(scheduler.get_jobs()) if 'scheduler' in globals() else 0,
            'test_time': datetime.now(pytz.UTC).isoformat()
        }
        
        return flask.jsonify(api_response.apiResponse("Health checks completed", False, test_results))
    
    except Exception as e:
        print(f"Manual health check test error: {str(e)}")
        return flask.jsonify(api_response.apiResponse(f"Health check test failed: {str(e)}", True, {}))


@app.route('/isUserExists', methods=['POST'])
def isUserExists():
    input = request.get_json()

    # print(input)
    donor_reg = getCollectionName('donor_registration')
    recipient_reg = getCollectionName('recipient_registration')
    volunteer_reg = getCollectionName('volunteer_registration')

    donor_record = donor_reg.find_one({'email': input['email']})

    if donor_record is not None:
        data = dict(donor_record).copy()
        # print(data)
        data.pop('_id')
        data.update({'user_id': str(donor_record['_id'])})
        updateFirebaseToken(data['user_id'], input['firebase_token'], constants.Utils.donor)
        # print(data)
        return flask.jsonify(api_response.apiResponse(constants.Utils.user_exists, False, data))

    recipient_record = recipient_reg.find_one({'email': input['email']})
    if recipient_record is not None:
        data = dict(recipient_record).copy()
        # print(data)
        data.pop('_id')
        data.update({'user_id': str(recipient_record['_id'])})
        # print(data)
        updateFirebaseToken(data['user_id'], input['firebase_token'], constants.Utils.recipient)

        return flask.jsonify(api_response.apiResponse(constants.Utils.user_exists, False, data))

    volunteer_record = volunteer_reg.find_one({'email': input['email']})
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
    response = messaging.send_each_for_multicast(message)
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
    volunteer_registration_col = getCollectionName('volunteer_registration')

    food_id = add_food_col.insert_one(input)

    volunteers_obj = volunteer_registration_col.find({})

    volunteers_obj_list = list(volunteers_obj)

    volunteer_ids = list()

    # Find nearby volunteers based on their serving distance
    print(f"🔍 Total volunteers in database: {len(volunteers_obj_list)}")
    print(f"📍 Food pickup location: ({input['pick_up_lat']}, {input['pick_up_lng']})")
    print(f"🏢 Food pickup address: {input.get('pick_up_address', input.get('address', 'No address'))}")
    
    for item in volunteers_obj_list:
        miles = dist(float(input['pick_up_lat']), float(input['pick_up_lng']), float(item['lat']), float(item['lng']))
        volunteer_address = item.get('address', 'No address')
        print(f"👤 Volunteer {item.get('name', 'Unknown')}: Distance={miles:.2f} miles, Serving distance={item.get('serving_distance', 'N/A')} miles")
        print(f"   📍 Volunteer location: ({item.get('lat', 'N/A')}, {item.get('lng', 'N/A')}) - Address: {volunteer_address}")
        # Check if the food donation is within volunteer's serving distance
        if miles <= float(item['serving_distance']):
            volunteer_ids.append(str(ObjectId(item['_id'])))
            print(f"✅ Volunteer {item.get('name', 'Unknown')} is within range!")

    print(f"📢 Found {len(volunteer_ids)} volunteers within range")

    # Get volunteer firebase tokens and send notifications
    user_firebase_token_col = getCollectionName("user_firebase_token")
    volunteers_firebase_tokens = user_firebase_token_col.find({"user_id": {"$in": volunteer_ids}})

    tokens = list()

    for item in volunteers_firebase_tokens:
        tokens.append(item['firebase_token'])
    
    print(f"🔔 Found {len(tokens)} firebase tokens for notifications")

    # Send push notifications to nearby volunteers
    send_notifications_to_volunteers(tokens, input['food_name'])
    
    # Send email notifications to nearby volunteers
    print(f"📧 Sending email notifications to {len(volunteer_ids)} volunteers")
    send_volunteer_email_notifications(volunteer_ids, input)

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
    return datetime.now(pytz.timezone('US/Eastern')).date()


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
        if obj['firebase_token']:
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
    
    # Send email notifications to nearby volunteers
    send_volunteer_email_notifications(ids, add_food_obj)

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

    # Get all available food for volunteers (available, waiting_for_volunteer, or pickup_scheduled)
    waiting_for_volunteer_foods = add_food_col.find({
        "status": {"$in": [constants.Utils.available, constants.Utils.waiting_for_volunteer, constants.Utils.pickeup_schedule]}
    })

    present_date = get_today_date()

    waiting_for_volunteer_food_list = list(waiting_for_volunteer_foods)

    foodList = []

    if len(waiting_for_volunteer_food_list):
        for obj in waiting_for_volunteer_food_list:
            pick_up_date = datetime.strptime(obj['pick_up_date'], "%Y-%m-%d").date()
            if pick_up_date >= present_date:
                obj.update({'id': str(obj['_id'])})
                del obj['_id']
                # Calculate distance from volunteer to food pickup location
                miles = dist(input['volunteer_lat'], input['volunteer_lng'], obj['pick_up_lat'], obj['pick_up_lng'])
                if miles <= float(input['serving_distance']):
                    obj.update({"distance": '%.2f' % (miles)})
                    foodList.append(obj)

    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, foodList))


@app.route('/volunteer/getFoodItemDetails', methods=['POST'])
def getFoodItemDetails():
    input = request.get_json()
    donor_registration_col = getCollectionName('donor_registration')
    business_registration_col = getCollectionName(constants.Utils.qr_business_collection)

    donor_user_id = input['donor_user_id']
    
    # Try to find donor - could be in donor_registration (ObjectId) or qr_business_registration (UUID)
    donor_obj = None
    
    # First, try as MongoDB ObjectId (for app-registered donors)
    try:
        if ObjectId.is_valid(donor_user_id):
            donor_obj = donor_registration_col.find_one({"_id": ObjectId(donor_user_id)})
            print(f"✅ Found donor in donor_registration collection")
    except Exception as e:
        print(f"⚠️ Not a valid ObjectId: {e}")
    
    # If not found, try as business_id (UUID for QR-registered donors)
    if donor_obj is None:
        donor_obj = business_registration_col.find_one({"business_id": donor_user_id})
        if donor_obj:
            print(f"✅ Found donor in QR business_registration collection")
    
    final_obj = dict()
    if donor_obj is not None:
        # Return donor details for volunteer to pickup food
        final_obj.update({
            "donor_name": donor_obj.get('name', donor_obj.get('business_name', 'Unknown')), 
            "donor_business_name": donor_obj.get('business_name', ''),
            "donor_contact_number": donor_obj.get('contact_number', donor_obj.get('phone', '')),
            "donor_address": donor_obj.get('address', donor_obj.get('street_name', '')),
            "donor_lat": donor_obj.get('lat', 0),
            "donor_lng": donor_obj.get('lng', 0)
        })
        
        # Calculate distance from volunteer to donor if volunteer location is provided
        if 'volunteer_lat' in input and 'volunteer_lng' in input:
            distance_in_miles = dist(float(input['volunteer_lat']), float(input['volunteer_lng']), 
                                   float(donor_obj.get('lat', 0)), float(donor_obj.get('lng', 0)))
            final_obj.update({"distance": '%.2f' % (distance_in_miles)})
    else:
        print(f"❌ Donor not found with ID: {donor_user_id}")

    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, final_obj))


@app.route('/volunteer/collect_food', methods=['POST'])
def collect_food():
    input = request.get_json()
    collect_food_col = getCollectionName('collect_food')
    add_food_col = getCollectionName('add_food')

    add_food_obj = add_food_col.find_one({"_id": ObjectId(input["food_item_id"])})

    if add_food_obj is not None:

        # Volunteer can collect food that is available or waiting for volunteer
        if add_food_obj['status'] in [constants.Utils.available, constants.Utils.waiting_for_volunteer]:

            id = collect_food_col.insert_one(input).inserted_id
            obj = add_food_col.update_one({'_id': ObjectId(input['food_item_id'])}, {
                '$set': {'status': constants.Utils.pickeup_schedule}}, upsert=False)
            
            # Send email notification to donor that volunteer has accepted the pickup
            donor_email, donor_name = get_donor_email(add_food_obj["user_id"], add_food_obj)
            if donor_email:
                volunteer_registration_col = getCollectionName('volunteer_registration')
                volunteer_obj = volunteer_registration_col.find_one({"_id": ObjectId(input.get('volunteer_user_id'))})
                volunteer_name = volunteer_obj.get('name', 'A volunteer') if volunteer_obj else 'A volunteer'
                
                subject = f"Volunteer Accepted Your Food Donation - {add_food_obj.get('food_name', 'Food')}"
                html_content = f"""
                <html>
                <body>
                    <h2>✅ Volunteer Accepted Your Donation</h2>
                    <p>Hello {donor_name},</p>
                    <p>Great news! A volunteer has accepted your food donation and will pick it up soon.</p>
                    
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0;">
                        <h3>Donation Details:</h3>
                        <ul>
                            <li><strong>Food:</strong> {add_food_obj.get('food_name', 'N/A')}</li>
                            <li><strong>Volunteer:</strong> {volunteer_name}</li>
                            <li><strong>Pickup Date:</strong> {add_food_obj.get('pick_up_date', 'N/A')}</li>
                            <li><strong>Pickup Time:</strong> {add_food_obj.get('pick_up_time', 'N/A')}</li>
                            <li><strong>Location:</strong> {add_food_obj.get('pick_up_address', add_food_obj.get('address', 'N/A'))}</li>
                        </ul>
                    </div>
                    
                    <p>The volunteer will arrive at the scheduled time to collect the food. Please have it ready for pickup.</p>
                    <p>Thank you for your contribution to reducing food waste!</p>
                    <p>Best regards,<br>Closing Time Team</p>
                </body>
                </html>
                """
                send_donor_email_notification(donor_email, donor_name, subject, html_content)
        else:
            return flask.jsonify(api_response.apiResponse(constants.Utils.already_assigned, False, {}))

    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, {}))


@app.route('/volunteer/mark_picked_up', methods=['POST'])
def volunteer_mark_picked_up():
    """Endpoint for volunteer to mark food as collected/picked up from donor"""
    input = request.get_json()
    add_food_col = getCollectionName('add_food')

    add_food_obj = add_food_col.find_one({"_id": ObjectId(input["food_item_id"])})

    if add_food_obj is not None:
        # Validate that food is in "Pick up scheduled" status
        if add_food_obj['status'] not in [constants.Utils.pickeup_schedule, constants.Utils.waiting_for_volunteer]:
            return flask.jsonify(api_response.apiResponse("Food must be in 'Pick up scheduled' status before marking as collected", True, {
                'message': 'Food must be in "Pick up scheduled" status before marking as collected'
            }))
        
        # Update status to collected
        add_food_col.update_one({
            '_id': ObjectId(input['food_item_id'])
        }, {
            '$set': {
                'status': constants.Utils.collected,
                'picked_up_at': datetime.now().isoformat()
            }
        }, upsert=False)
        
        # Send email notification to donor that food has been collected
        donor_email, donor_name = get_donor_email(add_food_obj["user_id"], add_food_obj)
        if donor_email:
            subject = f"Food Collected - {add_food_obj.get('food_name', 'Your Donation')}"
            html_content = f"""
            <html>
            <body>
                <h2>📦 Food Collected!</h2>
                <p>Hello {donor_name},</p>
                <p>The volunteer has successfully collected your food donation. It is now on its way to the recipient.</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <h3>Collection Details:</h3>
                    <ul>
                        <li><strong>Food:</strong> {add_food_obj.get('food_name', 'N/A')}</li>
                        <li><strong>Collected At:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                        <li><strong>Status:</strong> Collected - On the way to recipient</li>
                    </ul>
                </div>
                
                <p>Thank you for your donation! The food will be delivered to a shelter soon.</p>
                <p>Best regards,<br>Closing Time Team</p>
            </body>
            </html>
            """
            send_donor_email_notification(donor_email, donor_name, subject, html_content)
        
        return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, {
            'message': 'Food marked as collected successfully'
        }))
    else:
        return flask.jsonify(api_response.apiResponse(constants.Utils.no_user_found, False, {
            'message': 'Food item not found'
        }))


@app.route('/volunteer/mark_delivered', methods=['POST'])
def volunteer_mark_delivered():
    """Endpoint for volunteer to mark food as delivered to shelter"""
    input = request.get_json()
    add_food_col = getCollectionName('add_food')

    add_food_obj = add_food_col.find_one({"_id": ObjectId(input["food_item_id"])})

    if add_food_obj is not None:
        # Validate that food is in "Collected food" status
        if add_food_obj['status'] not in [constants.Utils.collected, constants.Utils.pickeup_schedule]:
            return flask.jsonify(api_response.apiResponse("Food must be in 'Collected food' status before marking as delivered", True, {
                'message': 'Food must be in "Collected food" status before marking as delivered'
            }))
        
        # Update status to delivered
        add_food_col.update_one({
            '_id': ObjectId(input['food_item_id'])
        }, {
            '$set': {
                'status': constants.Utils.delivered,
                'delivered_at': datetime.now().isoformat()
            }
        }, upsert=False)
        
        # Send email notification to donor that food has been delivered
        donor_email, donor_name = get_donor_email(add_food_obj["user_id"], add_food_obj)
        if donor_email:
            subject = f"Food Delivered! - {add_food_obj.get('food_name', 'Your Donation')}"
            html_content = f"""
            <html>
            <body>
                <h2>🎉 Food Successfully Delivered!</h2>
                <p>Hello {donor_name},</p>
                <p>Your food donation has been successfully delivered to a shelter. Thank you for your contribution to reducing food waste!</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <h3>Delivery Details:</h3>
                    <ul>
                        <li><strong>Food:</strong> {add_food_obj.get('food_name', 'N/A')}</li>
                        <li><strong>Delivered At:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                        <li><strong>Status:</strong> Delivered to shelter</li>
                    </ul>
                </div>
                
                <p>Your donation has made a positive impact in your community. We appreciate your generosity!</p>
                <p>Best regards,<br>Closing Time Team</p>
            </body>
            </html>
            """
            send_donor_email_notification(donor_email, donor_name, subject, html_content)
        
        return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, {
            'message': 'Food marked as delivered successfully'
        }))
    else:
        return flask.jsonify(api_response.apiResponse(constants.Utils.no_user_found, False, {
            'message': 'Food item not found'
        }))


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
            # Show foods that are still active (not yet delivered)
            if pick_up_date >= present_date:
                obj.update({'id': str(obj['_id'])})
                del obj['_id']
                # Calculate distance from volunteer to food pickup location
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
    if not FIREBASE_ENABLED:
        print(f"📱 Notification skipped (Firebase disabled): {food_name} - {quantity}")
        return
        
    if not ids or len(ids) == 0:
        print(f"📱 No tokens provided for notification: {food_name} - {quantity}")
        return
        
    try:
        notification = messaging.Notification(title=food_name, body=quantity)

        # See documentation on defining a message payload.
        message = messaging.MulticastMessage(
            notification=notification,
            tokens=ids,
        )
        response = messaging.send_each_for_multicast(message)
        print(f"📱 Successfully sent {response.success_count} notifications, {response.failure_count} failed")
        
        # if response.failure_count > 0:
        #     responses = response.responses
        #     failed_tokens = []
        #     for idx, resp in enumerate(responses):
        #         if not resp.success:
        #             # The order of responses corresponds to the order of the registration tokens.
        #             failed_tokens.append(ids[idx])
        #             print(f"📱 Failed to send to token {idx}: {resp.exception}")
                    
    except Exception as e:
        print(f"Firebase notification error: {e}")
        # Continue execution even if notifications fail


def send_notifications_to_volunteers(ids, food_name):
    if not FIREBASE_ENABLED:
        print(f"📱 Volunteer notification skipped (Firebase disabled): {food_name}")
        return
        
    if not ids or len(ids) == 0:
        print(f"📱 No tokens provided for volunteer notification: {food_name}")
        return
        
    try:
        notification = messaging.Notification(title=food_name,
                                              body="New food item has been added in your locality, pick up food now?")

        # See documentation on defining a message payload.
        message = messaging.MulticastMessage(
            notification=notification,
            tokens=ids,
        )
        response = messaging.send_each_for_multicast(message)
        print(f"📱 Successfully sent {response.success_count} volunteer notifications, {response.failure_count} failed")
        
        # if response.failure_count > 0:
        #     responses = response.responses
        #     failed_tokens = []
        #     for idx, resp in enumerate(responses):
        #         if not resp.success:
        #             # The order of responses corresponds to the order of the registration tokens.
        #             failed_tokens.append(ids[idx])
        #             print(f"📱 Failed to send volunteer notification to token {idx}: {resp.exception}")
                    
    except Exception as e:
        print(f"Firebase notification error: {e}")
        # Continue execution even if notifications fail


def send_notification_to_donor(token, recipient_name):
    if not FIREBASE_ENABLED:
        print(f"📱 Donor notification skipped (Firebase disabled): Food accepted by {recipient_name}")
        return
        
    if not token:
        print(f"📱 No token provided for donor notification: Food accepted by {recipient_name}")
        return
        
    try:
        notification = messaging.Notification(title="Food Accepted by " + str(recipient_name), body="")

        # See documentation on defining a message payload.
        message = messaging.Message(
            notification=notification,
            token=token,
        )
        response = messaging.send(message)
        print(f"📱 Successfully sent donor notification: {response}")
    except Exception as e:
        print(f"Firebase notification error: {e}")
        # Continue execution even if notifications fail


def get_donor_email(user_id, food_donation_obj=None):
    """Get donor email from user_id. Checks donor_registration, qr_business_registration, and food donation object."""
    try:
        donor_registration_col = getCollectionName('donor_registration')
        business_registration_col = getCollectionName(constants.Utils.qr_business_collection)
        
        # First, check if business_email is directly in the food donation (for QR donations)
        if food_donation_obj and food_donation_obj.get('business_email'):
            donor_email = food_donation_obj.get('business_email')
            donor_name = food_donation_obj.get('business_name', 'Business')
            print(f"✅ Found donor email in food donation: {donor_email}")
            return donor_email, donor_name
        
        # Try to find donor - could be in donor_registration (ObjectId) or qr_business_registration (UUID)
        donor_obj = None
        
        # First, try as MongoDB ObjectId (for app-registered donors)
        try:
            if ObjectId.is_valid(user_id):
                donor_obj = donor_registration_col.find_one({"_id": ObjectId(user_id)})
                if donor_obj:
                    print(f"✅ Found donor in donor_registration collection")
        except Exception as e:
            print(f"⚠️ Not a valid ObjectId: {e}")
        
        # If not found, try as business_id (UUID for QR-registered donors)
        if donor_obj is None:
            donor_obj = business_registration_col.find_one({"business_id": user_id})
            if donor_obj:
                print(f"✅ Found donor in QR business_registration collection")
        
        if donor_obj is not None:
            donor_email = donor_obj.get('email') or donor_obj.get('business_email')
            donor_name = donor_obj.get('name') or donor_obj.get('business_name', 'Business')
            if donor_email:
                print(f"✅ Found donor email: {donor_email}")
                return donor_email, donor_name
        
        print(f"⚠️ Could not find donor email for user_id: {user_id}")
        return None, None
        
    except Exception as e:
        print(f"❌ Error getting donor email: {e}")
        return None, None


def send_donor_email_notification(donor_email, donor_name, subject, html_content):
    """Send email notification to donor"""
    try:
        if not donor_email:
            print(f"⚠️ No email provided for donor notification")
            return False
        
        # Send email using Brevo API
        success = send_email_via_brevo_api(
            to_email=donor_email,
            to_name=donor_name or 'Business',
            subject=subject,
            html_content=html_content
        )
        
        if success:
            print(f"✅ Donor email sent to: {donor_name} ({donor_email})")
            return True
        else:
            print(f"❌ Failed to send donor email to: {donor_name} ({donor_email})")
            return False
            
    except Exception as e:
        print(f"❌ Error sending email to donor {donor_name}: {e}")
        return False


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


def geocode_address(address):
    """
    Geocode an address string to get latitude and longitude
    Returns tuple (lat, lng) or (None, None) if geocoding fails
    """
    try:
        geolocator = Nominatim(user_agent="closingtime_app")
        location = geolocator.geocode(address, timeout=10)
        
        if location:
            print(f"✅ Geocoded '{address}' to ({location.latitude}, {location.longitude})")
            return location.latitude, location.longitude
        else:
            print(f"⚠️ Could not geocode address: {address}")
            return None, None
            
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"❌ Geocoding error for '{address}': {e}")
        return None, None
    except Exception as e:
        print(f"❌ Unexpected geocoding error: {e}")
        return None, None


def _get_access_token():
    """Retrieve a valid access token that can be used to authorize requests.

  :return: Access token.
  """
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        '/etc/secrets/closingtime-e1fe0-firebase-adminsdk-1zdrb-e732fc6e97.json',
        'https://www.googleapis.com/auth/firebase.messaging')
    access_token_info = credentials.get_access_token()
    return access_token_info.access_token


def generate_qr_token(business_id, token_type="donation"):
    """Generate a permanent business identifier token for QR codes"""
    # Create a random token
    token = secrets.token_urlsafe(32)
    
    # Store token in database (permanent business identifier - no expiry)
    qr_tokens_collection = getCollectionName('qr_tokens')
    token_data = {
        'token': token,
        'business_id': business_id,
        'token_type': token_type,  # 'donation' or 'collection'
        'created_at': datetime.now().isoformat(),
        'permanent': True,  # Mark as permanent business identifier
        'used_at': None
    }
    
    qr_tokens_collection.insert_one(token_data)
    return token


def validate_qr_token(token):
    """Validate and get data for a QR token (permanent business identifier)"""
    qr_tokens_collection = getCollectionName('qr_tokens')
    
    # Find the token (permanent business identifier - no expiry check)
    token_data = qr_tokens_collection.find_one({
        'token': token
    })
    
    if not token_data:
        return None
    
    # Update last used time for analytics
    qr_tokens_collection.update_one(
        {'token': token},
        {'$set': {'last_used_at': datetime.now().isoformat()}}
    )
    
    # Get business data
    business_collection = getCollectionName(constants.Utils.qr_business_collection)
    business_data = business_collection.find_one({'business_id': token_data['business_id']})
    
    return {
        'token_data': token_data,
        'business_data': business_data
    }


def send_qr_code_email(business_email, admin_email, business_name, qr_image_data, business_id):
    """Send QR code to business and admin emails"""
    try:
        # Email configuration - use environment variables first, fallback to constants
        smtp_username = os.environ.get('SMTP_USERNAME', constants.Utils.smtp_username)
        smtp_password = os.environ.get('SMTP_PASSWORD', constants.Utils.smtp_password)
        smtp_server = os.environ.get('SMTP_SERVER', constants.Utils.smtp_server)
        smtp_port = int(os.environ.get('SMTP_PORT', constants.Utils.smtp_port))
        
        # Check if SMTP credentials are available
        if not smtp_username or not smtp_password:
            print(f"⚠️  SMTP credentials not configured. Skipping email for {business_name}")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = business_email
        msg['Subject'] = f"QR Code for {business_name} - Closing Time Food Donation"
        
        # Email body
        body = get_donor_registration_email_template(business_name, business_id)
        
        msg.attach(MIMEText(body, 'html'))
        
        # Attach QR code image
        qr_attachment = MIMEImage(qr_image_data)
        qr_attachment.add_header('Content-Disposition', 'attachment', filename=f'qr_code_{business_name}.png')
        msg.attach(qr_attachment)
        
        # Send to business
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
            print(f"✅ QR code sent to business: {business_name}")
        except Exception as email_error:
            print(f"❌ Failed to send QR code to business: {email_error}")
            return False
        
        # Send notification to admin
        try:
            admin_msg = MIMEMultipart()
            admin_msg['From'] = smtp_username
            admin_msg['To'] = admin_email
            admin_msg['Subject'] = f"New Business Registered: {business_name}"
            
            admin_body = f"""
            <html>
            <body>
                <h2>New Business Registration</h2>
                <p>A new business has been registered for the QR code food donation program:</p>
                <ul>
                    <li><strong>Business Name:</strong> {business_name}</li>
                    <li><strong>Email:</strong> {business_email}</li>
                    <li><strong>Business ID:</strong> {business_id}</li>
                    <li><strong>Registration Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                </ul>
                <p>QR code has been sent to the business email.</p>
            </body>
            </html>
            """
            
            admin_msg.attach(MIMEText(admin_body, 'html'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(admin_msg)
            server.quit()
            print(f"✅ Admin notification sent for: {business_name}")
            
        except Exception as admin_error:
            print(f"❌ Failed to send admin notification: {admin_error}")
            # Don't return False here as business email was sent successfully
        
        return True
        
    except Exception as e:
        print(f"❌ Error in email sending process: {e}")
        print(f"💡 SMTP credentials may not be configured properly")
        return False
        # Don't raise exception - continue with business registration even if email fails


def send_email_via_brevo_api(to_email, to_name, subject, html_content, sender_name="Closing Time", sender_email="sclosingtime@gmail.com", attachment_data=None, attachment_name=None):
    """Send email via Brevo Python SDK with optional attachment"""
    try:
        from brevo_python import TransactionalEmailsApi, SendSmtpEmail, SendSmtpEmailSender, SendSmtpEmailTo, SendSmtpEmailAttachment
        
        # Get Brevo API key from environment
        brevo_api_key = os.environ.get('BREVO_API_KEY')
        
        print(f"🔧 Brevo SDK Configuration:")
        print(f"   API Key: {'*' * len(brevo_api_key) if brevo_api_key else 'None'}")
        print(f"   API Key Length: {len(brevo_api_key) if brevo_api_key else 0}")
        print(f"   Environment Variable Set: {'Yes' if os.environ.get('BREVO_API_KEY') else 'No'}")
        
        if not brevo_api_key:
            print(f"❌ Brevo API key not configured")
            return False
        
        # Initialize the API client
        api_instance = TransactionalEmailsApi()
        api_instance.api_client.configuration.api_key['api-key'] = brevo_api_key
        
        # Create email
        sender = SendSmtpEmailSender(name=sender_name, email=sender_email)
        to = [SendSmtpEmailTo(email=to_email, name=to_name)]
        
        # Create email object
        email = SendSmtpEmail(
            sender=sender,
            to=to,
            subject=subject,
            html_content=html_content
        )
        
        # Add attachment if provided
        if attachment_data and attachment_name:
            import base64
            attachment_content = base64.b64encode(attachment_data).decode('utf-8')
            attachment = SendSmtpEmailAttachment(
                content=attachment_content,
                name=attachment_name
            )
            email.attachment = [attachment]
            print(f"📎 Adding attachment: {attachment_name}")
        
        print(f"📧 Sending email via Brevo SDK to {to_email}")
        
        # Send email
        api_response = api_instance.send_transac_email(email)
        print(f"✅ Brevo SDK email sent successfully to {to_email}")
        print(f"   Message ID: {api_response.message_id}")
        return True
            
    except Exception as e:
        print(f"❌ Brevo SDK Error: {str(e)}")
        return False


def send_qr_code_email_via_brevo_api(business_email, admin_email, business_name, business_id, qr_image_data=None):
    """Send QR code to business and admin emails via Brevo API"""
    try:
        # Get email template
        email_body = get_donor_registration_email_template(business_name, business_id)
        
        # Send to business with QR code attachment
        business_email_sent = send_email_via_brevo_api(
            to_email=business_email,
            to_name=business_name,
            subject=f"Registration successful {business_name} - ClosingTime",
            html_content=email_body,
            attachment_data=qr_image_data,
            attachment_name=f"qr_code_{business_name.replace(' ', '_')}.png"
        )
        
        if not business_email_sent:
            print(f"❌ Failed to send QR code to business: {business_name}")
            return False
        
        # Send notification to admin
        admin_body = f"""
        <html>
        <body>
            <h2>New Business Registration</h2>
            <p>A new business has been registered for the QR code food donation program:</p>
            <ul>
                <li><strong>Business Name:</strong> {business_name}</li>
                <li><strong>Email:</strong> {business_email}</li>
                <li><strong>Business ID:</strong> {business_id}</li>
                <li><strong>Registration Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
            </ul>
            <p>QR code has been sent to the business email.</p>
        </body>
        </html>
        """
        
        admin_email_sent = send_email_via_brevo_api(
            to_email=admin_email,
            to_name="Admin",
            subject=f"New Business Registered: {business_name}",
            html_content=admin_body
        )
        
        if not admin_email_sent:
            print(f"❌ Failed to send admin notification for: {business_name}")
            # Don't return False here as business email was sent successfully
        
        print(f"✅ QR code emails sent successfully for business: {business_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error in Brevo API email process: {e}")
        return False


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
    collect_food_list = getCollectionName('collect_food')
    donor_reg_list = getCollectionName('donor_registration').find({}, {'_id': False})
    recipient_reg_list = getCollectionName('recipient_registration').find({}, {'_id': False})
    volunteer_reg = getCollectionName('volunteer_registration')
    volunteer_reg_list = volunteer_reg.find({}, {'_id': False})

    # print(list(donor_reg_list))

    volunteers_list = collect_food_list.aggregate([
        {
            '$group':
                {
                    '_id': '$volunteer_user_id',
                    'orders_collected': {'$sum': 1}
                }
        }
    ])

    final_data = []

    for i in volunteers_list:
        volunteer_profile = volunteer_reg.find_one({'_id': ObjectId(i['_id'])}, {'_id': False})
        print(volunteer_profile['name'], volunteer_profile['email'])

        data = {
            "volunteer_id": i['_id'],
            "name": str(volunteer_profile['name']),
            "email": str(volunteer_profile['email']),
            "orders_collected": i['orders_collected']
        }
        final_data.append(data)

    data = {
        'donor': list(donor_reg_list),
        'recipient': list(recipient_reg_list),
        'volunteer': list(volunteer_reg_list),
        "volunteers_profile_list": final_data
    }

    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, data))


@app.route('/admin/get_all_donors', methods=['GET'])
@require_admin_token
def get_all_donors():
    """
    Get all donors (QR businesses) with their registration details
    Returns list of all QR business donors without _id fields
    Requires admin authentication token
    """
    try:
        # Get QR businesses (these are the donors)
        qr_business_reg = getCollectionName(constants.Utils.qr_business_collection)
        donor_list = list(qr_business_reg.find({}, {'_id': False}))
        
        # Add user_id field for each donor (using business_id)
        for donor in donor_list:
            # Use business_id as user_id for QR businesses
            donor['user_id'] = donor.get('business_id', '')
            # Add role field to match regular donors
            donor['role'] = 'Donor'
        
        data = {
            'total_count': len(donor_list),
            'donors': donor_list
        }
        
        return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, data))
    
    except Exception as e:
        print(f"Error fetching all donors: {str(e)}")
        return flask.jsonify(api_response.apiResponse("Failed to fetch donors", True, {}))


@app.route('/admin/get_donor/<business_id>', methods=['GET'])
@require_admin_token
def get_donor(business_id):
    """
    Get single donor (QR business) by business_id
    Requires admin authentication token
    """
    try:
        qr_business_reg = getCollectionName(constants.Utils.qr_business_collection)
        donor = qr_business_reg.find_one({'business_id': business_id}, {'_id': False})
        
        if not donor:
            return flask.jsonify(api_response.apiResponse("Donor not found", True, {}))
        
        # Add user_id and role fields
        donor['user_id'] = donor.get('business_id', '')
        donor['role'] = 'Donor'
        
        return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, donor))
    
    except Exception as e:
        print(f"Error fetching donor: {str(e)}")
        return flask.jsonify(api_response.apiResponse("Failed to fetch donor", True, {}))


@app.route('/admin/update_donor', methods=['PUT'])
@require_admin_token
def update_donor():
    """
    Update donor (QR business) information
    Requires admin authentication token
    """
    try:
        input_data = request.get_json()
        
        if not input_data or 'business_id' not in input_data:
            return flask.jsonify(api_response.apiResponse("business_id is required", True, {}))
        
        business_id = input_data['business_id']
        qr_business_reg = getCollectionName(constants.Utils.qr_business_collection)
        
        # Check if donor exists
        existing_donor = qr_business_reg.find_one({'business_id': business_id})
        if not existing_donor:
            return flask.jsonify(api_response.apiResponse("Donor not found", True, {}))
        
        # Prepare update data (exclude business_id and _id)
        update_data = {}
        allowed_fields = ['business_name', 'email', 'contact_number', 'address', 'lat', 'lng', 'place_id', 'status']
        
        for field in allowed_fields:
            if field in input_data:
                update_data[field] = input_data[field]
        
        # Add updated timestamp
        update_data['updated_at'] = datetime.now(pytz.UTC).isoformat()
        
        # Update the donor
        result = qr_business_reg.update_one(
            {'business_id': business_id},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            # Get updated donor
            updated_donor = qr_business_reg.find_one({'business_id': business_id}, {'_id': False})
            updated_donor['user_id'] = updated_donor.get('business_id', '')
            updated_donor['role'] = 'Donor'
            
            return flask.jsonify(api_response.apiResponse("Donor updated successfully", False, updated_donor))
        else:
            return flask.jsonify(api_response.apiResponse("No changes made", True, {}))
    
    except Exception as e:
        print(f"Error updating donor: {str(e)}")
        return flask.jsonify(api_response.apiResponse("Failed to update donor", True, {}))


@app.route('/admin/delete_donor', methods=['DELETE'])
@require_admin_token
def delete_donor():
    """
    Delete donor (QR business)
    Requires admin authentication token
    """
    try:
        input_data = request.get_json()
        
        if not input_data or 'business_id' not in input_data:
            return flask.jsonify(api_response.apiResponse("business_id is required", True, {}))
        
        business_id = input_data['business_id']
        qr_business_reg = getCollectionName(constants.Utils.qr_business_collection)
        
        # Check if donor exists
        existing_donor = qr_business_reg.find_one({'business_id': business_id})
        if not existing_donor:
            return flask.jsonify(api_response.apiResponse("Donor not found", True, {}))
        
        # Delete the donor
        result = qr_business_reg.delete_one({'business_id': business_id})
        
        if result.deleted_count > 0:
            return flask.jsonify(api_response.apiResponse("Donor deleted successfully", False, {
                'business_id': business_id,
                'deleted_at': datetime.now(pytz.UTC).isoformat()
            }))
        else:
            return flask.jsonify(api_response.apiResponse("Failed to delete donor", True, {}))
    
    except Exception as e:
        print(f"Error deleting donor: {str(e)}")
        return flask.jsonify(api_response.apiResponse("Failed to delete donor", True, {}))


@app.route('/admin/toggle_donor_status', methods=['POST'])
@require_admin_token
def toggle_donor_status():
    """
    Toggle donor (QR business) status between active/inactive
    Requires admin authentication token
    """
    try:
        input_data = request.get_json()
        
        if not input_data or 'business_id' not in input_data:
            return flask.jsonify(api_response.apiResponse("business_id is required", True, {}))
        
        business_id = input_data['business_id']
        new_status = input_data.get('status', 'inactive')  # Default to inactive
        
        if new_status not in ['active', 'inactive']:
            return flask.jsonify(api_response.apiResponse("Status must be 'active' or 'inactive'", True, {}))
        
        qr_business_reg = getCollectionName(constants.Utils.qr_business_collection)
        
        # Check if donor exists
        existing_donor = qr_business_reg.find_one({'business_id': business_id})
        if not existing_donor:
            return flask.jsonify(api_response.apiResponse("Donor not found", True, {}))
        
        # Update status
        result = qr_business_reg.update_one(
            {'business_id': business_id},
            {'$set': {
                'status': new_status,
                'updated_at': datetime.now(pytz.UTC).isoformat()
            }}
        )
        
        if result.modified_count > 0:
            # Get updated donor
            updated_donor = qr_business_reg.find_one({'business_id': business_id}, {'_id': False})
            updated_donor['user_id'] = updated_donor.get('business_id', '')
            updated_donor['role'] = 'Donor'
            
            return flask.jsonify(api_response.apiResponse(f"Donor status updated to {new_status}", False, updated_donor))
        else:
            return flask.jsonify(api_response.apiResponse("Failed to update donor status", True, {}))
    
    except Exception as e:
        print(f"Error updating donor status: {str(e)}")
        return flask.jsonify(api_response.apiResponse("Failed to update donor status", True, {}))


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


@app.route('/admin/get_volunteer_trips', methods=['GET'])
def get_volunteer_trips():
    # input = request.get_json()
    collect_food_list = getCollectionName('collect_food')
    donor_reg_list = getCollectionName('donor_registration').find({}, {'_id': False})
    recipient_reg_list = getCollectionName('recipient_registration').find({}, {'_id': False})
    volunteer_reg_list = getCollectionName('volunteer_registration')

    volunteers_list = collect_food_list.aggregate([
        {
            '$group':
                {
                    '_id': '$volunteer_user_id',
                    'orders_collected': {'$sum': 1}
                }
        }
    ])

    final_data = []

    for i in volunteers_list:
        volunteer_profile = volunteer_reg_list.find_one({'_id': ObjectId(i['_id'])}, {'_id': False})
        print(volunteer_profile['name'], volunteer_profile['email'])

        data = {
            "volunteer_id": i['_id'],
            "name": str(volunteer_profile['name']),
            "email": str(volunteer_profile['email']),
            "orders_collected": i['orders_collected']
        }
        final_data.append(data)

    return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, final_data))


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


@app.route('/admin/register_business', methods=['POST'])
def register_business():
    """Register a business and generate QR code for food donation"""
    input_data = request.get_json()
    
    try:
        # Validate required fields
        required_fields = ['business_name', 'email', 'contact_number', 'address', 'lat', 'lng', 'admin_email']
        for field in required_fields:
            if field not in input_data:
                return flask.jsonify(api_response.apiResponse(f"Missing required field: {field}", False, {})), 400
        
        # Generate unique business ID
        business_id = str(uuid.uuid4())
        
        # Create business data
        business_data = {
            'business_id': business_id,
            'business_name': input_data['business_name'],
            'email': input_data['email'],
            'contact_number': input_data['contact_number'],
            'address': input_data['address'],
            'lat': input_data['lat'],
            'lng': input_data['lng'],
            'place_id': input_data.get('place_id', ''),
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        # Save to database
        business_collection = getCollectionName(constants.Utils.qr_business_collection)
        result = business_collection.insert_one(business_data)
        
        # Generate secure QR token
        qr_token = generate_qr_token(business_id, "donation")
        
        # Create clean URL with secure token
        qr_code_data = f"{constants.Utils.server_url}/qr_scan?token={qr_token}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_code_data)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for email attachment
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        qr_image_data = img_buffer.getvalue()
        
        # Send QR code via Brevo API (graceful failure)
        email_sent = send_qr_code_email_via_brevo_api(
            business_email=input_data['email'],
            admin_email=input_data['admin_email'],
            business_name=input_data['business_name'],
            business_id=business_id,
            qr_image_data=qr_image_data
        )
        
        if email_sent:
            message = "Business registered successfully and QR code sent to admin email"
        else:
            message = "Business registered successfully. QR code generation failed - please check email configuration"
        
        response_data = {
            'business_id': business_id,
            'business_name': input_data['business_name'],
            'email': input_data['email'],
            'qr_token': qr_token,
            'qr_url': qr_code_data,
            'email_sent': email_sent
        }
        
        return flask.jsonify(api_response.apiResponse(message, True, response_data))
        
    except Exception as e:
        print(f"Error registering business: {e}")
        return flask.jsonify(api_response.apiResponse(f"Error registering business: {str(e)}", False, {})), 500


@app.route('/qr_donate_food', methods=['POST'])
def qr_donate_food():
    """Handle food donation from QR code scan"""
    try:
        # Get form data
        food_name = request.form.get('food_name')
        food_desc = request.form.get('food_desc', '')
        pickup_date = request.form.get('pickup_date')
        pickup_time = request.form.get('pickup_time')
        pick_up_lat = request.form.get('pick_up_lat')
        pick_up_lng = request.form.get('pick_up_lng')
        pick_up_address = request.form.get('pick_up_address')
        business_id = request.form.get('business_id')
        business_email = request.form.get('business_email')
        photo_data = request.form.get('photo')
        token = request.form.get('token')
        
        # Validate required fields
        required_fields = ['food_name', 'pickup_date', 'pickup_time', 'pick_up_lat', 'pick_up_lng', 'pick_up_address', 'business_id', 'business_email', 'photo', 'token']
        for field in required_fields:
            if not request.form.get(field):
                return flask.jsonify(api_response.apiResponse(f"Missing required field: {field}", False, {})), 400
        
        # Upload photo to Firebase Storage
        photo_url = upload_photo_to_firebase(photo_data, business_id, food_name)
        
        if not photo_url:
            return flask.jsonify(api_response.apiResponse("Failed to upload photo", False, {})), 500
        
        # Get business info
        business_collection = getCollectionName(constants.Utils.qr_business_collection)
        business_info = business_collection.find_one({'business_id': business_id})
        
        if not business_info:
            return flask.jsonify(api_response.apiResponse("Business not found", False, {})), 404
        
        # Validate and correct coordinates if needed
        # Check if coordinates match the address by geocoding
        corrected_lat, corrected_lng = geocode_address(pick_up_address)
        
        if corrected_lat and corrected_lng:
            # Calculate distance between provided coordinates and geocoded coordinates
            distance_diff = dist(float(pick_up_lat), float(pick_up_lng), corrected_lat, corrected_lng)
            
            if distance_diff > 50:  # If more than 50 miles difference, use geocoded coordinates
                print(f"⚠️ Coordinate mismatch detected! Frontend sent ({pick_up_lat}, {pick_up_lng}) but address geocodes to ({corrected_lat}, {corrected_lng}). Distance: {distance_diff:.2f} miles")
                print(f"✅ Using geocoded coordinates instead")
                pick_up_lat = corrected_lat
                pick_up_lng = corrected_lng
            else:
                print(f"✅ Coordinates match address (difference: {distance_diff:.2f} miles)")
        else:
            print(f"⚠️ Could not geocode address, using provided coordinates")
        
        # Create food donation data
        food_donation = {
            'food_name': food_name,
            'food_desc': food_desc,
            'quantity': '1 serving',  # Default quantity
            'food_ingredients': '',  # No allergen field
            'allergen': '',  # No allergen field
            'pick_up_date': pickup_date,
            'pick_up_time': pickup_time,
            'pick_up_lat': float(pick_up_lat),
            'pick_up_lng': float(pick_up_lng),
            'pick_up_address': pick_up_address,
            'address': pick_up_address,
            'image': photo_url,
            'user_id': business_id,  # Use business_id as user_id
            'business_name': business_info['business_name'],
            'business_email': business_email,
            'isFoodAccepted': False,
            'status': constants.Utils.available,
            'created_at': datetime.now().isoformat(),
            'donation_type': 'qr_scan',
            'token': token
        }
        
        # Save to database
        add_food_col = getCollectionName('add_food')
        food_id = add_food_col.insert_one(food_donation).inserted_id
        
        # Find nearby volunteers and send notifications
        volunteer_registration_col = getCollectionName('volunteer_registration')
        volunteers_obj = volunteer_registration_col.find({})
        volunteers_obj_list = list(volunteers_obj)
        
        print(f"🔍 QR Donation - Total volunteers in database: {len(volunteers_obj_list)}")
        print(f"📍 QR Donation - Food pickup location: ({pick_up_lat}, {pick_up_lng})")
        print(f"🏢 QR Donation - Food pickup address: {pick_up_address}")
        
        nearby_volunteer_ids = []
        for item in volunteers_obj_list:
            miles = dist(float(pick_up_lat), float(pick_up_lng), float(item['lat']), float(item['lng']))
            volunteer_address = item.get('address', 'No address')
            print(f"👤 QR - Volunteer {item.get('name', 'Unknown')}: Distance={miles:.2f} miles, Serving distance={item.get('serving_distance', 'N/A')} miles")
            print(f"   📍 Volunteer location: ({item.get('lat', 'N/A')}, {item.get('lng', 'N/A')}) - Address: {volunteer_address}")
            # Check if the food donation is within volunteer's serving distance
            if miles <= float(item['serving_distance']):
                nearby_volunteer_ids.append(str(ObjectId(item['_id'])))
                print(f"✅ QR - Volunteer {item.get('name', 'Unknown')} is within range!")
        
        print(f"📢 QR Donation - Found {len(nearby_volunteer_ids)} volunteers within range")
        
        # Get volunteer tokens and send notifications
        if nearby_volunteer_ids:
            user_firebase_token_col = getCollectionName("user_firebase_token")
            volunteers_firebase_tokens = user_firebase_token_col.find({"user_id": {"$in": nearby_volunteer_ids}})
            
            tokens = [item['firebase_token'] for item in volunteers_firebase_tokens]
            print(f"🔔 QR - Found {len(tokens)} firebase tokens for notifications")
            send_notifications_to_volunteers(tokens, food_name)
            
            # Send email notifications to nearby volunteers
            print(f"📧 QR - Sending email notifications to {len(nearby_volunteer_ids)} volunteers")
            send_volunteer_email_notifications(nearby_volunteer_ids, food_donation)
        else:
            print(f"⚠️ QR Donation - No volunteers found within serving distance!")
        
        response_data = {
            'food_id': str(food_id),
            'food_name': food_name,
            'business_name': business_info['business_name'],
            'pickup_location': pick_up_address,
            'pickup_date': pickup_date,
            'pickup_time': pickup_time,
            'photo_url': photo_url,
            'nearby_volunteers': len(nearby_volunteer_ids),
            'message': 'Food donation posted successfully! Nearby volunteers have been notified.'
        }
        
        return flask.jsonify(api_response.apiResponse(constants.Utils.success, False, response_data))
        
    except Exception as e:
        print(f"Error in QR food donation: {e}")
        return flask.jsonify(api_response.apiResponse(f"Error posting donation: {str(e)}", False, {})), 500


def upload_photo_to_firebase(photo_data, business_id, food_name):
    """Upload photo to Firebase Storage"""
    try:
        # Initialize Firebase Storage bucket
        bucket = storage.bucket()
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"food_donations/{business_id}/{food_name}_{timestamp}.jpg"
        
        # Remove data URL prefix if present
        if photo_data.startswith('data:image'):
            photo_data = photo_data.split(',')[1]
        
        # Decode base64 data
        photo_bytes = base64.b64decode(photo_data)
        
        # Create blob and upload
        blob = bucket.blob(filename)
        blob.upload_from_string(photo_bytes, content_type='image/jpeg')
        
        # Make blob publicly accessible
        blob.make_public()
        
        return blob.public_url
        
    except Exception as e:
        print(f"Error uploading photo to Firebase: {e}")
        return None


def send_volunteer_email_notifications(volunteer_ids, food_data):
    """Send email notifications to nearby volunteers about food pickup opportunity"""
    try:
        if not volunteer_ids or len(volunteer_ids) == 0:
            print("⚠️  No volunteers found for email notification")
            return
        
        # Get volunteer details
        volunteer_registration_col = getCollectionName('volunteer_registration')
        volunteers = volunteer_registration_col.find({'_id': {'$in': [ObjectId(vid) for vid in volunteer_ids]}})
        
        for volunteer in volunteers:
            try:
                volunteer_email = volunteer.get('email')
                volunteer_name = volunteer.get('name', 'Volunteer')
                
                if not volunteer_email:
                    print(f"⚠️  No email found for volunteer: {volunteer_name}")
                    continue
                
                # Email content
                subject = f"Food Pickup Opportunity - {food_data['food_name']}"
                html_content = f"""
                <html>
                <body>
                    <h2>🍽️ Food Pickup Opportunity</h2>
                    <p>Hello {volunteer_name},</p>
                    <p>A nearby food donation is ready for pickup!</p>
                    
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0;">
                        <h3>Pickup Details:</h3>
                        <ul>
                            <li><strong>Food:</strong> {food_data['food_name']}</li>
                            <li><strong>Business:</strong> {food_data['business_name']}</li>
                            <li><strong>Pickup Date:</strong> {food_data['pick_up_date']}</li>
                            <li><strong>Pickup Time:</strong> {food_data['pick_up_time']}</li>
                            <li><strong>Location:</strong> {food_data['pick_up_address']}</li>
                        </ul>
                    </div>
                    
                    <p><strong>Instructions:</strong></p>
                    <ol>
                        <li>Go to the pickup location at the scheduled time</li>
                        <li>Contact the business staff to collect the food</li>
                        <li>Deliver the food to the accepting recipient</li>
                        <li>Mark the delivery as complete in the app</li>
                    </ol>
                    
                    <p>Thank you for helping reduce food waste in our community!</p>
                    <p>Best regards,<br>Closing Time Team</p>
                </body>
                </html>
                """
                
                # Send email using Brevo API
                success = send_email_via_brevo_api(
                    to_email=volunteer_email,
                    to_name=volunteer_name,
                    subject=subject,
                    html_content=html_content
                )
                
                if success:
                    print(f"✅ Volunteer email sent to: {volunteer_name} ({volunteer_email})")
                else:
                    print(f"❌ Failed to send volunteer email to: {volunteer_name} ({volunteer_email})")
                    
            except Exception as e:
                print(f"❌ Error sending email to volunteer {volunteer.get('name', 'Unknown')}: {e}")
                continue
                
    except Exception as e:
        print(f"❌ Error in send_volunteer_email_notifications: {e}")


def send_donation_qr_code(business_email, business_name, donation_data, food_name):
    """Send QR code for specific food donation to business using Brevo API"""
    try:
        # Generate QR code for this donation with URL
        qr_code_data = f"{constants.Utils.server_url}/volunteer/collect_food_qr?data={json.dumps(donation_data).replace(' ', '%20')}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_code_data)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        qr_image_data = img_buffer.getvalue()
        
        # Email content
        subject = f"New Food Donation QR Code - {food_name}"
        
        # Email body
        body = f"""
        <html>
        <body>
            <h2>New Food Donation Posted!</h2>
            <p>Dear {business_name},</p>
            <p>A new food donation has been posted from your location:</p>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <h3>Donation Details:</h3>
                <ul>
                    <li><strong>Food:</strong> {food_name}</li>
                    <li><strong>Pickup Date:</strong> {donation_data['pickup_date']}</li>
                    <li><strong>Pickup Time:</strong> {donation_data['pickup_time']}</li>
                    <li><strong>Location:</strong> {donation_data['pickup_location']}</li>
                </ul>
            </div>
            
            <p>Please find the QR code attached. You can print this and display it for volunteers to scan when they come to collect the food.</p>
            
            <p>Thank you for helping reduce food waste!</p>
            <p>Best regards,<br>Closing Time Team</p>
        </body>
        </html>
        """
        
        # Send email using Brevo API with QR code attachment
        success = send_email_via_brevo_api(
            to_email=business_email,
            to_name=business_name,
            subject=subject,
            html_content=body,
            attachment_data=qr_image_data,
            attachment_name=f'donation_qr_{food_name}.png'
        )
        
        if success:
            print(f"✅ Donation QR code sent to {business_name}")
            return True
        else:
            print(f"❌ Failed to send donation QR code to {business_name}")
            return False
        
    except Exception as e:
        print(f"❌ Error in donation email process: {e}")
        return False


@app.route('/test_email', methods=['GET'])
def test_email():
    """Test email configuration with detailed debugging"""
    try:
        # Get SMTP settings
        smtp_username = os.environ.get('SMTP_USERNAME', constants.Utils.smtp_username)
        smtp_password = os.environ.get('SMTP_PASSWORD', constants.Utils.smtp_password)
        smtp_server = os.environ.get('SMTP_SERVER', constants.Utils.smtp_server)
        smtp_port = int(os.environ.get('SMTP_PORT', constants.Utils.smtp_port))
        
        print(f"🔧 Testing SMTP Configuration:")
        print(f"   Server: {smtp_server}")
        print(f"   Port: {smtp_port}")
        print(f"   Username: {smtp_username}")
        print(f"   Password: {'*' * len(smtp_password) if smtp_password else 'None'}")
        
        # Test connection with timeout
        print(f"📡 Attempting to connect to {smtp_server}:{smtp_port}")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        print(f"✅ Connected to SMTP server")
        
        print(f"🔐 Starting TLS...")
        server.starttls()
        print(f"✅ TLS started successfully")
        
        print(f"🔑 Attempting login...")
        server.login(smtp_username, smtp_password)
        print(f"✅ Login successful")
        
        server.quit()
        print(f"✅ Connection closed successfully")
        
        return flask.jsonify({
            "success": True,
            "message": "Email configuration is working!",
            "debug_info": {
                "smtp_server": smtp_server,
                "smtp_port": smtp_port,
                "smtp_username": smtp_username,
                "connection_test": "passed",
                "tls_test": "passed",
                "auth_test": "passed"
            }
        })
        
    except smtplib.SMTPConnectError as e:
        error_msg = f"Failed to connect to SMTP server: {str(e)}"
        print(f"❌ SMTP Connect Error: {error_msg}")
        return flask.jsonify({
            "success": False,
            "error_type": "SMTPConnectError",
            "message": error_msg,
            "debug_info": {
                "smtp_server": os.environ.get('SMTP_SERVER', constants.Utils.smtp_server),
                "smtp_port": os.environ.get('SMTP_PORT', constants.Utils.smtp_port),
                "smtp_username": os.environ.get('SMTP_USERNAME', constants.Utils.smtp_username),
                "possible_causes": ["Port blocked by cloud provider", "Wrong server/port", "Network connectivity issue"]
            }
        }), 500
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"SMTP authentication failed: {str(e)}"
        print(f"❌ SMTP Auth Error: {error_msg}")
        return flask.jsonify({
            "success": False,
            "error_type": "SMTPAuthenticationError",
            "message": error_msg,
            "debug_info": {
                "smtp_server": os.environ.get('SMTP_SERVER', constants.Utils.smtp_server),
                "smtp_port": os.environ.get('SMTP_PORT', constants.Utils.smtp_port),
                "smtp_username": os.environ.get('SMTP_USERNAME', constants.Utils.smtp_username),
                "possible_causes": ["Wrong username/password", "App password not enabled", "2FA not enabled"]
            }
        }), 500
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ Unexpected Error: {error_msg}")
        return flask.jsonify({
            "success": False,
            "error_type": "UnexpectedError",
            "message": error_msg,
            "debug_info": {
                "smtp_server": os.environ.get('SMTP_SERVER', constants.Utils.smtp_server),
                "smtp_port": os.environ.get('SMTP_PORT', constants.Utils.smtp_port),
                "smtp_username": os.environ.get('SMTP_USERNAME', constants.Utils.smtp_username),
                "error_details": str(e)
            }
        }), 500

@app.route('/test_smtp_configs', methods=['GET'])
def test_smtp_configs():
    """Test different SMTP configurations"""
    configs = [
        {"name": "Gmail Port 587", "server": "smtp.gmail.com", "port": 587},
        {"name": "Gmail Port 465", "server": "smtp.gmail.com", "port": 465},
        {"name": "SendGrid", "server": "smtp.sendgrid.net", "port": 587},
        {"name": "Brevo", "server": "smtp-relay.brevo.com", "port": 587},
        {"name": "Brevo Alt", "server": "smtp.brevo.com", "port": 587},
        {"name": "Outlook", "server": "smtp-mail.outlook.com", "port": 587},
    ]
    
    results = []
    
    for config in configs:
        try:
            print(f"🧪 Testing {config['name']}: {config['server']}:{config['port']}")
            server = smtplib.SMTP(config['server'], config['port'], timeout=5)
            server.quit()
            results.append({
                "config": config['name'],
                "server": config['server'],
                "port": config['port'],
                "status": "✅ Connection successful"
            })
            print(f"✅ {config['name']} - Connection successful")
        except Exception as e:
            results.append({
                "config": config['name'],
                "server": config['server'],
                "port": config['port'],
                "status": f"❌ Failed: {str(e)}"
            })
            print(f"❌ {config['name']} - Failed: {str(e)}")
    
    return flask.jsonify({
        "message": "SMTP Configuration Test Results",
        "results": results,
        "recommendation": "Try the configurations that show 'Connection successful'"
    })

@app.route('/test_brevo_api', methods=['POST'])
def test_brevo_api():
    """Test Brevo Python SDK email sending"""
    try:
        input_data = request.get_json()
        test_email = input_data.get('email', 'sclosingtime@gmail.com')
        
        # Use the SDK function
        email_sent = send_email_via_brevo_api(
            to_email=test_email,
            to_name="Test User",
            subject="Closing Time - Email Test",
            html_content="""
            <html>
            <body>
                <h2>Email Test Successful!</h2>
                <p>This is a test email from your Closing Time application using Brevo Python SDK.</p>
                <p>If you received this, your Brevo configuration is working correctly.</p>
                <p>Best regards,<br>Closing Time Team</p>
            </body>
            </html>
            """
        )
        
        if email_sent:
            return flask.jsonify({
                "success": True,
                "message": f"Test email sent successfully to {test_email}"
            })
        else:
            return flask.jsonify({
                "success": False,
                "message": "Failed to send test email"
            }), 500
            
    except Exception as e:
        error_msg = f"Failed to send email via Brevo SDK: {str(e)}"
        print(f"❌ Brevo SDK Error: {error_msg}")
        return flask.jsonify({
            "success": False,
            "message": error_msg
        }), 500

@app.route('/send_test_email', methods=['POST'])
def send_test_email():
    """Send a test email"""
    try:
        input_data = request.get_json()
        test_email = input_data.get('email', 'sclosingtime@gmail.com')
        
        # Get SMTP settings
        smtp_username = os.environ.get('SMTP_USERNAME', constants.Utils.smtp_username)
        smtp_password = os.environ.get('SMTP_PASSWORD', constants.Utils.smtp_password)
        smtp_server = os.environ.get('SMTP_SERVER', constants.Utils.smtp_server)
        smtp_port = int(os.environ.get('SMTP_PORT', constants.Utils.smtp_port))
        
        # Create test message
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = test_email
        msg['Subject'] = "Closing Time - Email Test"
        
        body = """
        <html>
        <body>
            <h2>Email Test Successful!</h2>
            <p>This is a test email from your Closing Time application.</p>
            <p>If you received this, your email configuration is working correctly.</p>
            <p>Best regards,<br>Closing Time Team</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        return flask.jsonify({
            "success": True,
            "message": f"Test email sent successfully to {test_email}"
        })
        
    except Exception as e:
        return flask.jsonify({
            "success": False,
            "message": f"Failed to send test email: {str(e)}"
        }), 500

@app.route('/qr_scan', methods=['GET'])
def qr_scan_page():
    """Serve the QR scanning web page with token validation"""
    token = request.args.get('token')
    
    if not token:
        return """
        <html>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <div style="background: white; padding: 40px; border-radius: 20px; max-width: 500px; margin: 0 auto;">
                <h1 style="color: #ff6b6b;">❌ Invalid QR Code</h1>
                <p>This QR code is missing required information.</p>
                <p>Please scan a valid QR code from a registered business.</p>
            </div>
        </body>
        </html>
        """, 400
    
    # Validate token and get business data
    try:
        validation_result = validate_qr_token(token)
        
        if not validation_result or not validation_result.get('business_data'):
            return """
            <html>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                <div style="background: white; padding: 40px; border-radius: 20px; max-width: 500px; margin: 0 auto;">
                    <h1 style="color: #ff6b6b;">❌ Invalid QR Code</h1>
                    <p>This QR code is not recognized or the business is not registered.</p>
                    <p>Please scan a valid QR code from a registered business.</p>
                </div>
            </body>
            </html>
            """, 400
        
        business_data = validation_result['business_data']
        
        # Get Google API key from environment variable
        google_api_key = os.environ.get('GOOGLE_API_KEY', '')
        
        # Get donor address from business data
        donor_address = business_data.get('address', '')
        
        # Return the actual food donation form
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Donate Food - {business_data['business_name']}</title>
    <script src="https://maps.googleapis.com/maps/api/js?key={google_api_key}&libraries=places"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            background: #000000; 
            min-height: 100vh; 
            padding: 20px; 
        }}
        .container {{ 
            max-width: 500px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 20px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1); 
            overflow: hidden; 
        }}
        .logo-container {{ 
            background: #ffb366; 
            padding: 5px; 
            text-align: center; 
            border-bottom: 3px solid #ff9500; 
            height: 100px; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
        }}
        .logo {{ 
            font-size: 32px; 
            font-weight: 700; 
            color: white; 
            text-shadow: 0 2px 4px rgba(0,0,0,0.2); 
        }}
        .header {{ 
            background: #ffb366; 
            color: black; 
            padding: 25px 20px; 
            text-align: center; 
        }}
        .header h1 {{ 
            font-size: 24px; 
            margin-bottom: 8px; 
            font-weight: 600; 
            color: black; 
        }}
        .header p {{ 
            opacity: 0.8; 
            font-size: 14px; 
            font-weight: 400; 
            color: black; 
        }}
        .form-container {{ 
            padding: 30px 20px; 
        }}
        .business-info {{ 
            background: #fff4e6; 
            border: 2px solid #ffb366; 
            border-radius: 12px; 
            padding: 18px; 
            margin-bottom: 25px; 
        }}
        .business-info h3 {{ 
            color: #cc6600; 
            margin-bottom: 12px; 
            font-size: 16px; 
            font-weight: 600; 
        }}
        .business-info p {{ 
            color: #cc6600; 
            font-size: 14px; 
            margin-bottom: 6px; 
            font-weight: 500; 
        }}
        .form-group {{ 
            margin-bottom: 22px; 
        }}
        .form-group label {{ 
            display: block; 
            margin-bottom: 10px; 
            font-weight: 600; 
            color: #333; 
            font-size: 15px; 
        }}
        .form-group input, .form-group textarea {{ 
            width: 100%; 
            padding: 14px 16px; 
            border: 2px solid #e1e8ed; 
            border-radius: 12px; 
            font-size: 16px; 
            font-family: inherit; 
            font-weight: 400; 
            transition: all 0.3s ease; 
            background: #fafafa; 
            display: block; 
        }}
        .form-group input:focus, .form-group textarea:focus {{ 
            outline: none; 
            border-color: #ffb366; 
            background: white; 
            box-shadow: 0 0 0 3px rgba(255, 179, 102, 0.1); 
        }}
        gmp-place-autocomplete {{ 
            width: 100%; 
            border: 2px solid #e1e8ed; 
            border-radius: 12px; 
            background: #fafafa; 
            display: block; 
            transition: all 0.3s ease; 
        }}
        gmp-place-autocomplete:focus-within {{ 
            outline: none; 
            border-color: #ffb366; 
            background: white; 
            box-shadow: 0 0 0 3px rgba(255, 179, 102, 0.1); 
        }}
        gmp-place-autocomplete input, 
        gmp-place-autocomplete input[type="text"],
        gmp-place-autocomplete .input,
        gmp-place-autocomplete * {{ 
            border: none !important; 
            outline: none !important; 
            background: transparent !important; 
            width: 100% !important; 
            padding: 14px 16px !important; 
            margin: 0 !important; 
            font-size: 16px !important; 
            font-family: inherit !important; 
            color: black !important; 
        }}
        gmp-place-autocomplete input::placeholder,
        gmp-place-autocomplete input[type="text"]::placeholder,
        gmp-place-autocomplete .input::placeholder {{ 
            color: #999 !important; 
        }}
        gmp-place-autocomplete input::-webkit-input-placeholder,
        gmp-place-autocomplete input[type="text"]::-webkit-input-placeholder {{ 
            color: #999 !important; 
        }}
        gmp-place-autocomplete input::-moz-placeholder,
        gmp-place-autocomplete input[type="text"]::-moz-placeholder {{ 
            color: #999 !important; 
        }}
        gmp-place-autocomplete input:-ms-input-placeholder,
        gmp-place-autocomplete input[type="text"]:-ms-input-placeholder {{ 
            color: #999 !important; 
        }}
        
        /* More aggressive targeting */
        gmp-place-autocomplete,
        gmp-place-autocomplete *,
        gmp-place-autocomplete input,
        gmp-place-autocomplete input[type="text"],
        gmp-place-autocomplete .input,
        gmp-place-autocomplete .input-container,
        gmp-place-autocomplete .input-container input {{
            color: black !important;
        }}
        
        /* Force black text on all autocomplete elements */
        gmp-place-autocomplete input,
        gmp-place-autocomplete input[type="text"],
        gmp-place-autocomplete .input,
        gmp-place-autocomplete .input-container input,
        gmp-place-autocomplete .pac-container,
        gmp-place-autocomplete .pac-item,
        gmp-place-autocomplete .pac-item-query,
        gmp-place-autocomplete * {{
            color: black !important;
            background-color: white !important;
        }}
        
        /* Ensure dropdown items are visible */
        gmp-place-autocomplete .pac-container .pac-item {{
            color: black !important;
            background-color: white !important;
            border-bottom: 1px solid #eee;
        }}
        
        gmp-place-autocomplete .pac-container .pac-item:hover {{
            background-color: #f5f5f5 !important;
            color: black !important;
        }}
        
        /* Override any Google Maps styling */
        .pac-container,
        .pac-container *,
        .pac-item,
        .pac-item * {{
            color: black !important;
            background-color: white !important;
        }}
        
        /* Force text color on focus and input */
        gmp-place-autocomplete input:focus,
        gmp-place-autocomplete input:active,
        gmp-place-autocomplete input:visited {{
            color: black !important;
            background-color: white !important;
        }}
        
        /* Regular input styling for address */
        #pickup-address {{
            color: black !important;
            background-color: white !important;
        }}
        
        /* Google Places dropdown styling */
        .pac-container {{
            background-color: white !important;
            border: 1px solid #ccc !important;
        }}
        
        .pac-item {{
            color: black !important;
            background-color: white !important;
        }}
        
        .pac-item:hover {{
            background-color: #f5f5f5 !important;
        }}
        .form-group textarea {{ 
            resize: vertical; 
            min-height: 90px; 
        }}
        .camera-container {{ 
            margin-bottom: 25px; 
        }}
        #camera-preview {{ 
            width: 100%; 
            height: 250px; 
            background: #f8f9fa; 
            border: 2px dashed #dee2e6; 
            border-radius: 12px; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            color: #6c757d; 
            font-size: 14px; 
            font-weight: 500; 
            overflow: hidden; 
        }}
        #camera-preview img {{ 
            width: 100%; 
            height: 100%; 
            object-fit: cover; 
        }}
        .camera-controls {{ 
            display: flex; 
            gap: 12px; 
            margin-top: 12px; 
        }}
        .btn {{ 
            flex: 1; 
            padding: 14px 20px; 
            border: none; 
            border-radius: 12px; 
            font-size: 16px; 
            font-weight: 600; 
            cursor: pointer; 
            transition: all 0.3s ease; 
            font-family: inherit; 
        }}
        .btn-primary {{ 
            background: #ffb366; 
            color: white; 
        }}
        .btn-primary:hover {{ 
            background: #ff9500; 
            transform: translateY(-2px); 
            box-shadow: 0 6px 20px rgba(255, 149, 0, 0.3); 
        }}
        .btn-secondary {{ 
            background: #6c757d; 
            color: white; 
        }}
        .btn-secondary:hover {{ 
            background: #5a6268; 
            transform: translateY(-1px); 
        }}
        .btn-success {{ 
            background: #ffb366; 
            color: white; 
            width: 100%; 
            margin-top: 25px; 
            padding: 16px 24px; 
            font-size: 17px; 
        }}
        .btn-success:hover {{ 
            background: #ff9500; 
            transform: translateY(-2px); 
            box-shadow: 0 6px 20px rgba(255, 149, 0, 0.3); 
        }}
        .btn-success:disabled {{ 
            background: #ccc; 
            cursor: not-allowed; 
            transform: none; 
            box-shadow: none; 
        }}
        #file-input {{ 
            display: none; 
        }}
        .error {{ 
            background: #f8d7da; 
            color: #721c24; 
            padding: 12px 16px; 
            border-radius: 10px; 
            margin-bottom: 18px; 
            display: none; 
            font-weight: 500; 
        }}
        .error.show {{ 
            display: block; 
        }}
        .success {{ 
            background: #d4edda; 
            color: #155724; 
            padding: 12px 16px; 
            border-radius: 10px; 
            margin-bottom: 18px; 
            display: none; 
            font-weight: 500; 
        }}
        .success.show {{ 
            display: block; 
        }}
        .loading {{ 
            display: none; 
            text-align: center; 
            padding: 25px; 
        }}
        .loading.show {{ 
            display: block; 
        }}
        .spinner {{ 
            border: 4px solid #f3f3f3; 
            border-top: 4px solid #ffb366; 
            border-radius: 50%; 
            width: 45px; 
            height: 45px; 
            animation: spin 1s linear infinite; 
            margin: 0 auto 18px; 
        }}
        @keyframes spin {{ 
            0% {{ transform: rotate(0deg); }} 
            100% {{ transform: rotate(360deg); }} 
        }}
        .required {{ 
            color: #dc3545; 
            font-weight: 700; 
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo-container">
            <img src="/assets/logo_white.png" alt="Closing Time Logo" style="height: 220px; width: auto;" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';" />
            <div class="logo" style="display: none;">Closing Time</div>
        </div>
        
        <div class="header">
            <h1>Food Donation</h1>
            <p>from</p>
            <div class="business-info" style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px; margin-top: 15px;">
                <h3 style="margin: 0 0 8px 0; color: black; font-size: 18px;">{business_data['business_name']}</h3>
            </div>
        </div>

        <div class="form-container">
            <div id="error-message" class="error"></div>
            <div id="success-message" class="success"></div>


            <form id="donation-form">
                <div class="camera-container">
                    <label>📷 Food Photo <span class="required">*</span></label>
                    
                    <!-- Video container for live camera -->
                    <div id="video-container" style="display: none; width: 100%; height: 250px; background: #000; border-radius: 12px; overflow: hidden;">
                        <video id="camera-video" autoplay muted playsinline style="width: 100%; height: 100%; object-fit: cover;"></video>
                    </div>
                    
                    <!-- Preview container for captured image -->
                    <div id="camera-preview">
                        <div>Click "Take Photo" to add photo</div>
                    </div>
                    
                    <div class="camera-controls">
                        <button type="button" id="camera-btn" class="btn btn-primary" onclick="startCamera()">📷 Take Photo</button>
                    </div>
                    <input type="file" id="file-input" accept="image/*" onchange="handleFileSelect(event)">
                </div>

                <div class="form-group">
                    <label for="food-name">Food Name <span class="required">*</span></label>
                    <input type="text" id="food-name" name="food_name" placeholder="e.g., Pizza, Sandwiches, Salad" required>
                </div>

                <div class="form-group">
                    <label for="pickup-date">Pickup Date <span class="required">*</span></label>
                    <input type="date" id="pickup-date" name="pickup_date" required>
                </div>

                <div class="form-group">
                    <label for="pickup-time">Pickup Time <span class="required">*</span></label>
                    <input type="time" id="pickup-time" name="pickup_time" required>
                </div>

                <div class="form-group">
                    <label for="pickup-address">Pickup Address <span class="required">*</span></label>
                    <input type="text" id="pickup-address" placeholder="Start typing your address..." required style="color: black !important; background-color: white !important;">
                    <small style="color: #cc6600; font-size: 13px; margin-top: 5px; display: block;">Start typing to see address suggestions</small>
                </div>

                <div class="form-group">
                    <label for="food-notes">Additional Notes (Optional)</label>
                    <textarea id="food-notes" name="food_notes" placeholder="Any special notes, ingredients, or instructions..."></textarea>
                </div>

                <button type="submit" class="btn btn-success" id="submit-btn">
                    Submit Donation
                </button>
            </form>

            <div id="loading" class="loading">
                <div class="spinner"></div>
                <p>Submitting your donation...</p>
            </div>
        </div>
    </div>

    <script>
        let currentStream = null;
        let capturedPhoto = null;
        const businessData = {{
            business_id: '{business_data['business_id']}',
            email: '{business_data['email']}',
            name: '{business_data['business_name']}',
            lat: {business_data['lat']},
            lng: {business_data['lng']},
            address: '{business_data['address']}'
        }};

        // Initialize form
        document.addEventListener('DOMContentLoaded', function() {{
            // Set date range: tomorrow to one week from today
            const today = new Date();
            const tomorrow = new Date(today);
            tomorrow.setDate(tomorrow.getDate() + 1);
            
            const oneWeekLater = new Date(today);
            oneWeekLater.setDate(oneWeekLater.getDate() + 7);
            
            const dateInput = document.getElementById('pickup-date');
            dateInput.min = tomorrow.toISOString().split('T')[0];
            dateInput.max = oneWeekLater.toISOString().split('T')[0];
            
            // Initialize Google Places Autocomplete
            initializePlacesAutocomplete();
        }});
        
        function initializePlacesAutocomplete() {{
            const input = document.getElementById('pickup-address');
            if (input && window.google && window.google.maps) {{
                // Pre-populate with donor address if available
                const donorAddress = '{donor_address if donor_address else ""}';
                if (donorAddress && donorAddress !== 'None') {{
                    input.value = donorAddress;
                }}
                
                // Initialize Google Places Autocomplete
                const autocomplete = new google.maps.places.Autocomplete(input, {{
                    componentRestrictions: {{ country: 'us' }},
                    types: ['address']
                }});
                
                // Listen for place selection
                autocomplete.addListener('place_changed', function() {{
                    const place = autocomplete.getPlace();
                    if (place.formatted_address) {{
                        console.log('Address selected:', place.formatted_address);
                        input.style.color = 'black';
                        input.style.setProperty('color', 'black', 'important');
                    }}
                }});
                
                // Ensure text color is always black
                input.addEventListener('input', function() {{
                    input.style.color = 'black';
                    input.style.setProperty('color', 'black', 'important');
                }});
                
                input.addEventListener('focus', function() {{
                    input.style.color = 'black';
                    input.style.setProperty('color', 'black', 'important');
                }});
                
            }} else {{
                console.log('Google Maps API not loaded');
            }}
        }}

        function startCamera() {{
            // Clear previous captured photo when starting camera
            capturedPhoto = null;
            
            // Stop any existing camera stream
            if (currentStream) {{
                currentStream.getTracks().forEach(track => track.stop());
                currentStream = null;
            }}
            
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {{
                navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: 'environment' }} }})
                    .then(function(stream) {{
                        currentStream = stream;
                        
                        const video = document.getElementById('camera-video');
                        video.srcObject = stream;
                        
                        // Show video container, hide preview
                        document.getElementById('video-container').style.display = 'block';
                        document.getElementById('camera-preview').style.display = 'none';
                        
                        // Change button to Capture
                        const btn = document.getElementById('camera-btn');
                        btn.textContent = '📸 Capture';
                        btn.onclick = captureFromVideo;
                    }})
                    .catch(function(error) {{
                        console.error('Error accessing camera:', error);
                        showError('Unable to access camera. Please try again.');
                    }});
            }} else {{
                showError('Camera not supported on this device.');
            }}
        }}

        function captureFromVideo() {{
            const video = document.getElementById('camera-video');
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0);
            
            capturedPhoto = canvas.toDataURL('image/jpeg', 0.8);
            
            // Stop camera immediately
            if (currentStream) {{
                currentStream.getTracks().forEach(track => track.stop());
                currentStream = null;
            }}
            
            // Hide video container
            document.getElementById('video-container').style.display = 'none';
            
            // Show preview container with captured image
            const preview = document.getElementById('camera-preview');
            preview.innerHTML = '<img src="' + capturedPhoto + '" alt="Captured Photo" style="width: 100%; height: 100%; object-fit: cover; border-radius: 8px;">';
            preview.style.display = 'flex';
            
            // Change button to Re-capture
            const btn = document.getElementById('camera-btn');
            btn.textContent = '🔄 Re-capture';
            btn.onclick = startCamera;
            
            showSuccess('Photo captured successfully!');
        }}

        function handleFileSelect(event) {{
            const file = event.target.files[0];
            if (file) {{
                const reader = new FileReader();
                reader.onload = function(e) {{
                    capturedPhoto = e.target.result;
                    const preview = document.getElementById('camera-preview');
                    preview.innerHTML = '<img src="' + capturedPhoto + '" alt="Selected Photo">';
                    document.getElementById('clear-btn').style.display = 'inline-block';
                    showSuccess('Photo selected successfully!');
                }};
                reader.readAsDataURL(file);
            }}
        }}


        function showError(message) {{
            const errorDiv = document.getElementById('error-message');
            errorDiv.textContent = message;
            errorDiv.classList.add('show');
            setTimeout(() => {{ errorDiv.classList.remove('show'); }}, 5000);
        }}

        function showSuccess(message) {{
            const successDiv = document.getElementById('success-message');
            successDiv.textContent = message;
            successDiv.classList.add('show');
            setTimeout(() => {{ successDiv.classList.remove('show'); }}, 3000);
        }}

        document.getElementById('donation-form').addEventListener('submit', async function(e) {{
            e.preventDefault();
            
            if (!capturedPhoto) {{
                showError('Please take or select a photo of the food');
                return;
            }}

            document.getElementById('loading').classList.add('show');
            document.getElementById('donation-form').style.display = 'none';
            document.getElementById('submit-btn').disabled = true;

            try {{
                const formData = new FormData();
                formData.append('food_name', document.getElementById('food-name').value);
                formData.append('food_desc', document.getElementById('food-notes').value);
                formData.append('pickup_date', document.getElementById('pickup-date').value);
                formData.append('pickup_time', document.getElementById('pickup-time').value);
                formData.append('pick_up_address', document.getElementById('pickup-address').value);
                formData.append('pick_up_lat', businessData.lat);
                formData.append('pick_up_lng', businessData.lng);
                formData.append('business_id', businessData.business_id);
                formData.append('business_email', businessData.email);
                formData.append('photo', capturedPhoto);
                formData.append('token', '{token}');

                const response = await fetch('/qr_donate_food', {{
                    method: 'POST',
                    body: formData
                }});

                const result = await response.json();

                if (result.error === false) {{
                    document.getElementById('loading').classList.remove('show');
                    document.getElementById('donation-form').style.display = 'none';
                    
                    const container = document.querySelector('.form-container');
                    container.innerHTML = `
                        <div style="text-align: center; padding: 40px 20px;">
                            <div style="font-size: 64px; margin-bottom: 20px;">🎉</div>
                            <h2 style="color: #28a745; margin-bottom: 15px;">Success!</h2>
                            <p style="color: #666; margin-bottom: 20px;">Your food donation has been posted successfully!</p>
                            <div style="background: #e3f2fd; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                                <p style="color: #1976d2; margin-bottom: 10px;"><strong>What's Next?</strong></p>
                                <p style="color: #424242; font-size: 14px;">Volunteers will pickup your donation on the scheduled date and time.</p>
                            </div>
                            <button onclick="location.reload()" class="btn btn-primary" style="width: 100%;">
                                ➕ Donate More Food
                            </button>
                        </div>
                    `;
                }} else {{
                    showError('Error: ' + result.message);
                    document.getElementById('loading').classList.remove('show');
                    document.getElementById('donation-form').style.display = 'block';
                    document.getElementById('submit-btn').disabled = false;
                }}
            }} catch (error) {{
                console.error('Error:', error);
                showError('Network error. Please check your connection and try again.');
                document.getElementById('loading').classList.remove('show');
                document.getElementById('donation-form').style.display = 'block';
                document.getElementById('submit-btn').disabled = false;
            }}
        }});
    </script>
    </body>
    </html>
        """
        
    except Exception as e:
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <div style="background: white; padding: 40px; border-radius: 20px; max-width: 500px; margin: 0 auto;">
                <h1 style="color: #ff6b6b;">❌ Error</h1>
                <p>An error occurred while validating the QR code.</p>
                <p style="font-size: 12px; color: #666;">{str(e)}</p>
            </div>
        </body>
        </html>
        """, 500


@app.route('/volunteer/collect_food_qr', methods=['GET'])
def volunteer_collect_food_page():
    """Handle QR code scan for volunteer food collection"""
    try:
        # Get donation data from URL parameters
        donation_data = request.args.get('data')
        if not donation_data:
            return "❌ Invalid QR code - no data found", 400
        
        # Decode the JSON data
        import urllib.parse
        decoded_data = urllib.parse.unquote(donation_data)
        donation_info = json.loads(decoded_data)
        
        # Create a simple HTML page for volunteers
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Food Collection - Closing Time</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: #4CAF50; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; }}
                .info {{ background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 10px 0; }}
                .label {{ font-weight: bold; color: #333; }}
                .value {{ color: #666; margin-bottom: 8px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🍽️ Food Collection</h1>
                    <p>Volunteer Pickup Information</p>
                </div>
                
                <div class="info">
                    <h3>📋 Collection Details</h3>
                    <div class="label">Food Item:</div>
                    <div class="value">{donation_info.get('food_name', 'N/A')}</div>
                    
                    <div class="label">Business:</div>
                    <div class="value">{donation_info.get('business_name', 'N/A')}</div>
                    
                    <div class="label">Pickup Location:</div>
                    <div class="value">{donation_info.get('pickup_location', 'N/A')}</div>
                    
                    <div class="label">Pickup Date:</div>
                    <div class="value">{donation_info.get('pickup_date', 'N/A')}</div>
                    
                    <div class="label">Pickup Time:</div>
                    <div class="value">{donation_info.get('pickup_time', 'N/A')}</div>
                </div>
                
                <div class="info">
                    <h3>✅ Collection Confirmed</h3>
                    <p>Thank you for volunteering! You have successfully scanned the QR code for food collection.</p>
                    <p><strong>Next Steps:</strong></p>
                    <ul>
                        <li>Go to the pickup location at the specified time</li>
                        <li>Collect the food from the business</li>
                        <li>Deliver to the assigned recipient</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
        
    except Exception as e:
        return f"❌ Error processing QR code: {str(e)}", 400


if __name__ == '__main__':
    app.run(debug=True)
    # Listen on all interfaces (0.0.0.0) so phone can connect to laptop's IP
    # app.run(host='0.0.0.0', port=5005)  # Use port 5003 to avoid AirPlay conflict
