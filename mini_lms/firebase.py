import firebase_admin
from firebase_admin import credentials
import os
import json
info = json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON"))

# Load Firebase service account credentials
cred = credentials.Certificate(info)

# Initialize Firebase Admin SDK
firebase_admin.initialize_app(cred)