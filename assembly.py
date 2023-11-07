import firebase_admin
from firebase_admin import credentials, storage
from picamera2 import Picamera2
from datetime import datetime
from firebase_admin import db
import signal
import sys
import RPi.GPIO as GPIO
import threading
from picamera2 import Picamera2, Preview
import time


#camera settings
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


# functies uit te voeren wanneer deurbel is gedrukt
def deurbel_pressed_callback():
    print("deurbel gedrukt!")
    picam2.capture_file("foto.jpg")
    # Define a unique filename for your uploaded photo
    now = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    filename = "foto_" + now + ".jpg"

    # Upload the photo to Firebase Storage
    bucket = storage.bucket()
    blob = bucket.blob(filename)
    blob.upload_from_filename('foto.jpg')

    # Laat de database weten dat er net aangebeld werd
    db.reference('/readtest').set("Er werd het laatst aangebeld op" + datetime.now().strftime("%d-%m-%Y, %H:%M:%S"))

# Set the GPIO mode and pin number
GPIO.setmode(GPIO.BCM)
BUTTON_GPIO = 17  # You can use a different GPIO pin

# Setup the button pin as an input with a pull-up resistor
GPIO.setup(BUTTON_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Initialize a variable to keep track of the button state
previous_state = GPIO.input(BUTTON_GPIO)

# Function to monitor the button state
def button_monitor():
    global previous_state
    while True:
        current_state = GPIO.input(BUTTON_GPIO)

        if current_state != previous_state:
            if current_state == GPIO.LOW:
                deurbel_pressed_callback()


        time.sleep(0.1)  # Optional debounce delay

def on_data_change(event):
    db.reference('/readtest').set(f"succesvol change ({event.data}) gelezen op: " + datetime.now().strftime("%d-%m-%Y, %H:%M:%S"))
    deurbel_pressed_callback()

def readtest_monitor():
    db.reference('/Locked').listen(on_data_change)

# Create a thread for button monitoring
button_thread = threading.Thread(target=button_monitor)
button_thread.daemon = True  # Allow the thread to exit when the main program ends

readtest_thread = threading.Thread(target=readtest_monitor)
readtest_thread.daemon = True  # Allow the thread to exit when the main program ends


try:
    # Start the button monitoring thread
    button_thread.start()
    readtest_thread.start()
    # Your main program logic here
    while True:
        # Do something else in your program
        print(1)
        time.sleep(2)

except KeyboardInterrupt:
    GPIO.cleanup()
