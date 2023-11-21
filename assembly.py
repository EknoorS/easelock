import firebase_admin
from firebase_admin import credentials, storage
from picamera2 import Picamera2
from datetime import datetime
from firebase_admin import db
import signal
import sys
import RPi.GPIO as GPIO
from multiprocessing import Process
from picamera2 import Picamera2, Preview
import time
from EaseLock_Main import *
from NumpadMain import *
 

#camera settings
picam2 = Picamera2()
camera_config = picam2.create_preview_configuration()
picam2.configure(camera_config)
picam2.start_preview(Preview.QTGL)
picam2.start()
time.sleep(2)




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
GPIO.setmode(GPIO.BOARD)
BUTTON_GPIO = 11  # You can use a different GPIO pin
LOCK_GPIO = 8

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
# als state True is dan moet de slot sluiten anders openen
def slot(state):
    print("slot functie gaat runnen met state: ", state)
    if not state:
        print("slot gaat open")
        GPIO.output(LOCK_GPIO, GPIO.HIGH)
        time.sleep(5)
        print("slot gaat toe")
        GPIO.output(LOCK_GPIO, GPIO.LOW)
    elif state:
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
        print("reading card")
        try:
            id, currentID = reader.read()
            if id is not None:
                print("id wordt gechecked")
                user = GetUserByID(id, currentID)
                print(f"user:{user}")
                tags = GetTags()
                allCurrentTagIDs = GetAllCurrentTagIDs(tags)
                allTagIDs = GetAllTagIDs(tags)
                if currentID.strip() in allCurrentTagIDs and str(id).strip() in allTagIDs:
                    print("id recognised")
                    newID = str(uuid.uuid4())
                    reader.write(newID)
                    SetCurrentID(user, newID)
                    CheckTimeslot(GetUserByID(id, newID))
                    
                else:
                    print("id not recognized, adding new key")
                    AddNewKey(id, currentID)
                    sleep(3)
                print("adding entry")
                AddEntry(GetUsername(user) if user is not None else 'Unauthorized')
        except:
            pass
        

def numpad_reader_monitor():
    try:
        factory = KeypadFactory()
        keypad = factory.create_keypad(keypad=KEYPAD, row_pins=ROW_PINS,
                                       col_pins=COL_PINS)  # makes assumptions about keypad layout and GPIO pin numbers
        keypad.registerKeyPressHandler(check_key)

        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        keypad.cleanup()



button_thread = Process(target=button_monitor)
cardreader_thread = Process(target=cardreader_monitor)
numpad_reader_thread = Process(target=numpad_reader_monitor)


try:
    readlock_monitor()
    
    button_thread.start()
    numpad_reader_thread.start()
    cardreader_thread.start()
    

except KeyboardInterrupt:
    GPIO.cleanup()
