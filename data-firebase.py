import firebase_admin
from firebase_admin import credentials, storage
from picamera2 import Picamera2
from datetime import datetime

# Initialize the PiCamera
picam2 = Picamera2()


# Capture a photo
picam2.start_and_capture_files('foto.jpg')

# Initialize the Firebase Admin SDK with your service account credentials
cred = credentials.Certificate("/home/admin/rasp-test-8e035-firebase-adminsdk-ra7h9-f6fa22f310.json")  # Replace with the path to your service account JSON file
firebase_admin.initialize_app(cred, {
    'storageBucket': 'rasp-test-8e035.appspot.com'
})

# Define a unique filename for your uploaded photo
now = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
filename = "foto_" + now + ".jpg"

# Upload the photo to Firebase Storage
bucket = storage.bucket()
blob = bucket.blob(filename)
blob.upload_from_filename('foto.jpg')

