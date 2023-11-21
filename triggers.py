import firebase_admin
from firebase_admin import credentials, storage
from picamera2 import Picamera2
from datetime import datetime
from firebase_admin import db


# Initialize the Firebase Admin SDK with your service account credentials
<<<<<<< HEAD
cred = credentials.Certificate("/home/admin/rasp-test-8e035-firebase-adminsdk-ra7h9-f6fa22f310.json")  # Replace with the path to your service account JSON file
=======
cred = credentials.Certificate("/home/admin/easelock/rasp-test-8e035-firebase-adminsdk-ra7h9-f6fa22f310.json")  # Replace with the path to your service account JSON file
>>>>>>> 3390538c0d97e1cfb5b2e378c0500c2a89a296ee
firebase_admin.initialize_app(cred, {
	"databaseURL": "https://rasp-test-8e035-default-rtdb.europe-west1.firebasedatabase.app",
    'storageBucket': 'rasp-test-8e035.appspot.com'
})


ref = db.reference('/Locked')
def on_data_change(event):
	db.reference('/readtest').set(f"succesvol change ({event.data}) gelezen op: " + datetime.now().strftime("%d-%m-%Y, %H:%M:%S"))

ref.listen(on_data_change)

while(True):
	print(1)
