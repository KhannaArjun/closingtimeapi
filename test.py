import os
import firebase_admin
from firebase_admin import credentials, messaging

# --- optional: strip env vars that can break FCM ---
# for k in [
#     "HTTP_PROXY","HTTPS_PROXY","http_proxy","https_proxy",
#     "GOOGLE_API_USE_MTLS_ENDPOINT","GOOGLE_API_USE_CLIENT_CERTIFICATE"
# ]:
#     os.environ.pop(k, None)
# os.environ["GOOGLE_API_USE_MTLS_ENDPOINT"] = "never"

# --- init once with your service account ---
if not firebase_admin._apps:
    cred = credentials.Certificate("closingtime-e1fe0-firebase-adminsdk-1zdrb-daa665d59c.json")
    app = firebase_admin.initialize_app(cred)

print("🔥 Using project:", firebase_admin.get_app().options.get("projectId"))

# --- put your FCM device token here ---
DEVICE_TOKEN = "e-P8OMBATUlojwblTH_7H8:APA91bE26P6W4ivy82NF14QE1bwW0S7ioXiQ8NCPgHCt5c1F-WxEv9Rqs1CxR2KcmTMuVmKgue8vzDFr6fqxMoA9DTocrVNcmEzmvPjg-4lfUWw-eRgNpPM"

# --- build message ---
msg = messaging.Message(
    token=DEVICE_TOKEN,
    notification=messaging.Notification(
        title="Ping from Python",
        body="Single-send test ✅"
    ),
)

try:
    # dry-run (validates token/project/creds)
    messaging.send(msg, dry_run=True)
    print("✅ Dry-run OK")

    # real send
    rid = messaging.send(msg)
    print("✅ Sent successfully, message_id:", rid)
except Exception as e:
    print("❌ Send failed:", e)
