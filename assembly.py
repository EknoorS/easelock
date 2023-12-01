import firebase_admin
from firebase_admin import credentials, storage
from datetime import datetime
from firebase_admin import db
import signal
import sys
import RPi.GPIO as GPIO
from multiprocessing import Process, Value
from picamera2 import Picamera2, Preview
import time
from EaseLock_Main import *
from NumpadMain import *
import bcrypt
 





# Set the GPIO mode and pin number
GPIO.setmode(GPIO.BOARD)
BUTTON_GPIO = 11  # You can use a different GPIO pin
LOCK_GPIO = 8
BOX_GPIO = 8

# Setup the button pin as an input with a pull-up resistor
GPIO.setup(BUTTON_GPIO, GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(LOCK_GPIO, GPIO.OUT)

# Initialize a variable to keep track of the button state
previous_state = GPIO.input(BUTTON_GPIO)

# functies uit te voeren wanneer deurbel is gedrukt
def deurbel_pressed_callback():
    print("deurbel gedrukt!")
    foto_trekken_en_uploaden()
    # Laat de database weten dat er net aangebeld werd
    db.reference('/readtest').set("Er werd het laatst aangebeld op" + datetime.now().strftime("%d-%m-%Y, %H:%M:%S"))

# Deurbel drukknop monitor
def button_monitor():
    global previous_state
    while True:
        GPIO.setmode(GPIO.BOARD)
        current_state = GPIO.input(BUTTON_GPIO)
        print(current_state)
        if current_state != previous_state:
            if current_state == GPIO.LOW:
                deurbel_pressed_callback()
        previous_state = current_state 
        time.sleep(0.1)  # Optional debounce delay

# slot openen (max 5 seconden) of slot sluiten
# als state True is dan moet de slot sluiten anders openen
def slot(state):
    state = bool(state)
    print("slot functie gaat runnen met state: ", state)
    if not state:
        print("slot gaat open")
        GPIO.output(LOCK_GPIO, GPIO.HIGH)
        time.sleep(5)
        print("slot gaat toe")
        GPIO.output(LOCK_GPIO, GPIO.LOW)
        db.reference('/Locked').set(True)
        time.sleep(1)
    elif state:
        print(f"slot gaat toe: {state} (elif satement) ")
        GPIO.output(LOCK_GPIO, GPIO.LOW)

def slot_box(state):
    state = bool(state)
    print("slot functie gaat runnen met state: ", state)
    if  state:
        print("box gaat open")
        GPIO.output(BOX_GPIO, GPIO.HIGH)
        time.sleep(5)
        print("box gaat toe")
        GPIO.output(BOX_GPIO, GPIO.LOW)
        db.reference('/BoxUnlock').set(False)
        time.sleep(1)
    elif not state:
        print(f"box gaat toe: {state} (elif satement) ")
        GPIO.output(BOX_GPIO, GPIO.LOW)

# Functie die opgeroepen word als de deur ontgrendeld moet worden
def on_data_change_lock(event):
    # laat weten dat we de change in slot status hebben geregistreerd
    if not event.data:
        db.reference('/readtest').set(f"succesvol change ({event.data}) gelezen op: " + datetime.now().strftime("%d-%m-%Y, %H:%M:%S"))
        #open slot
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
                #oude code
                tags = GetTags()
                allCurrentTagIDs = GetAllCurrentTagIDs(tags)
                allTagIDs = GetAllTagIDs(tags)
                if currentID.strip() in allCurrentTagIDs and str(id).strip() in allTagIDs:
                #oude code
                #if CheckTag(Tag(str(id).strip(), currentID.strip())):
                    print("id recognised")
                    newID = str(uuid.uuid4())
                    reader.write(newID)
                    SetCurrentID(user, newID)
                    CheckTimeslot(GetUserByID(id, newID))
                else:
                    print('addnewkey')
                    foto_trekken_en_uploaden()
                    AddNewKey(id, currentID)
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
            sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        keypad.cleanup()

def capture_picture_button_monitor():
    db.reference('/capture').listen(on_data_change_capture_picture)
    
def on_data_change_capture_picture(event):
    if event.data:
        foto_trekken_en_uploaden()
        ref = db.reference('/capture')
        ref.set(False)
    
def unlock_box_monitor():
    db.reference('/BoxUnlock').listen(on_data_change_box_unlock)
    
def on_data_change_box_unlock(event):
    if event.data:
        slot_box(event.data)
    
        
        
def foto_trekken_en_uploaden():
    picam2 = Picamera2()
    picam2.start_and_capture_files('foto.jpg', preview_mode="Preview.NULL")
    print("foto getrokken")
    # Define a unique filename for your uploaded photo
    now = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    filename = "foto_" + now + ".jpg"
    picam2.close()
    # Upload the photo to Firebase Storage
    bucket = storage.bucket()
    blob = bucket.blob(filename)
    blob.upload_from_filename('foto.jpg')
    now = datetime.now()
    key = now.strftime('%Y-%m-%d') + '_' + now.strftime('%H-%M-%S')
    ref = db.reference(f'/Photos/{key}')
    ref.set(filename)
    
capture_picture_button_thread = Process(target=capture_picture_button_monitor)
unlock_box_thread = Process(target=unlock_box_monitor)
button_thread = Process(target=button_monitor)
cardreader_thread = Process(target=cardreader_monitor)
numpad_reader_thread = Process(target=numpad_reader_monitor)
readlock_monitor_thread = Process(target = readlock_monitor)

try:
    unlock_box_thread.start()
    capture_picture_button_thread.start()
    readlock_monitor_thread.start()
    button_thread.start()
    numpad_reader_thread.start()
    cardreader_thread.start()
    

except KeyboardInterrupt:
    GPIO.cleanup()
    
    
