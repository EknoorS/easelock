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
import EaseLock_Main as em
import NumpadMain as nm



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
LOCK_GPIO = 14 

# Setup the button pin as an input with a pull-up resistor
GPIO.setup(BUTTON_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LOCK_GPIO, GPIO.OUT)

# Initialize a variable to keep track of the button state
previous_state = GPIO.input(BUTTON_GPIO)

# Deurbel drukknop monitor
def button_monitor():
    global previous_state
    while True:
        current_state = GPIO.input(BUTTON_GPIO)

        if current_state != previous_state:
            if current_state == GPIO.LOW:
                deurbel_pressed_callback()


        time.sleep(0.1)  # Optional debounce delay

# slot openen (max 5 seconden) of slot sluiten
def slot(state):
    print("slot functie gaat runnen met state: ", state)
    if state:
        print("slot gaat open")
        GPIO.output(LOCK_GPIO, GPIO.HIGH)
        time.sleep(5)
        print("slot gaat toe")
        GPIO.output(LOCK_GPIO, GPIO.LOW)
    elif not state:
        print(f"slot gaat toe: {state} (elif satement) ")
        GPIO.output(LOCK_GPIO, GPIO.LOW)

# Functie die opgeroepen word als de deur ontgrendeld moet worden
def on_data_change_lock(event):
    # laat weten dat we de change in slot status hebben geregistreerd
    db.reference('/readtest').set(f"succesvol change ({event.data}) gelezen op: " + datetime.now().strftime("%d-%m-%Y, %H:%M:%S"))
    # open slot
    slot(event.data)

# THREAD FUNCTION die kijkt of de deur al dan niet geunlocked moet worden
def readlock_monitor():
    db.reference('/Locked').listen(on_data_change_lock)

def cardreader_monitor():
    while True:
        try:
            id, currentID = em.reader.read()
            if id is not None:
                user = em.GetUserByID(id, currentID)
                tags = em.GetTags()
                allCurrentTagIDs = em.GetAllCurrentTagIDs(tags)
                allTagIDs = em.GetAllTagIDs(tags)
                if currentID.strip() in allCurrentTagIDs and str(id).strip() in allTagIDs:
                    newID = str(em.uuid.uuid4())
                    em.reader.write(newID)
                    em.CheckTimeslot(em.GetUserByID(id, currentID))
                    em.SetCurrentID(user, newID)
                else:
                    em.AddNewKey(id, currentID)
                em.AddEntry(em.GetUsername(user) if user is not None else 'Unauthorized')
                em.sleep(3)
        except:
            pass

def numpad_reader_monitor():
    try:
        factory = nm.KeypadFactory()
        keypad = factory.create_keypad(keypad=nm.KEYPAD, row_pins=nm.ROW_PINS,
                                       col_pins=nm.COL_PINS)  # makes assumptions about keypad layout and GPIO pin numbers
        keypad.registerKeyPressHandler(nm.check_key)

        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        keypad.cleanup()


# Create a thread for button monitoring
button_thread = threading.Thread(target=button_monitor)
button_thread.daemon = True  # Allow the thread to exit when the main program ends

readlock_thread = threading.Thread(target=readlock_monitor)
readlock_thread.daemon = True  # Allow the thread to exit when the main program ends

cardreader_thread = threading.Thread(target=cardreader_monitor)
cardreader_thread.daemon = True

numpad_reader_thread = threading.Thread(target=numpad_reader_monitor)
readlock_thread.daemon = True

try:
    # Start the button monitoring thread
    button_thread.start()
    # Start de lock change thread
    readlock_thread.start()
    # Your main program logic here
    while True:
        # Do something else in your program
        pass

except KeyboardInterrupt:
    GPIO.cleanup()
