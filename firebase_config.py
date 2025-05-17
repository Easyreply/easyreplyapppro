import os
import json
import firebase_admin
from firebase_admin import credentials, db

# Load FIREBASE_JSON (stringified JSON) and FIREBASE_DB_URL from Railway env
firebase_json = os.environ.get("FIREBASE_JSON")
firebase_db_url = os.environ.get("FIREBASE_DB_URL")

if not firebase_json or not firebase_db_url:
    raise ValueError("Missing FIREBASE_JSON or FIREBASE_DB_URL environment variables")

# Convert stringified FIREBASE_JSON to dictionary
firebase_cred_dict = json.loads(firebase_json)

# Initialize Firebase app (only once)
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_cred_dict)
    firebase_admin.initialize_app(cred, {
        'databaseURL': firebase_db_url
    })
