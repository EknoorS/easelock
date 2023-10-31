import firebase_admin
from firebase_admin import credentials, storage
from picamera2 import Picamera2
from datetime import datetime
from firebase_admin import db
import signal
import sys
import RPi.GPIO as GPIO

from picamera2 import Picamera2, Preview
import time

picam2 = Picamera2()
camera_config = picam2.create_preview_configuration()
picam2.configure(camera_config)
picam2.start_preview(Preview.QTGL)
picam2.start()
time.sleep(2)



# Initialize the Firebase Admin SDK with your service account credentials
cred = credentials.Certificate("/home/admin/easelock/rasp-test-8e035-firebase-adminsdk-ra7h9-f6fa22f310.json")  # Replace with the path to your service account JSON file
firebase_admin.initialize_app(cred, {
	"databaseURL": "https://rasp-test-8e035-default-rtdb.europe-west1.firebasedatabase.app",
    'storageBucket': 'rasp-test-8e035.appspot.com'
})


BUTTON_GPIO = 16

def deurbel_pressed_callback(channel):
    print("deurbel gedrukt!")
    picam2.capture_file("test.jpg")
    # Define a unique filename for your uploaded photo
    now = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    filename = "foto_" + now + ".jpg"

    # Upload the photo to Firebase Storage
    bucket = storage.bucket()
    blob = bucket.blob(filename)
    blob.upload_from_filename('foto.jpg')

if __name__ == '__main__':
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(BUTTON_GPIO, GPIO.FALLING,
                          callback=deurbel_pressed_callback, bouncetime=100)
