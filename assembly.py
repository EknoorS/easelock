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
# import the necessary packages
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
from imutils.video import VideoStream
import numpy as np
import argparse
import imutils
import time
import cv2
import socket
import os

# Set the GPIO mode and pin number
GPIO.setmode(GPIO.BOARD)
BUTTON_GPIO = 11  # You can use a different GPIO pin
LOCK_GPIO = 8
BOX_GPIO = 8

# Setup the button pin as an input with a pull-up resistor
GPIO.setup(BUTTON_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(LOCK_GPIO, GPIO.OUT)

# Initialize a variable to keep track of the button state
previous_state = GPIO.input(BUTTON_GPIO)
mask_detected = False

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
    print('GEEN MASKER AAN') if not mask_detected else print("mondmasker detectie oke in slot functie")

    if not state and mask_detected:
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
    if state:
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
        db.reference('/readtest').set(
            f"succesvol change ({event.data}) gelezen op: " + datetime.now().strftime("%d-%m-%Y, %H:%M:%S"))
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
                # oude code
                tags = GetTags()
                allCurrentTagIDs = GetAllCurrentTagIDs(tags)
                allTagIDs = GetAllTagIDs(tags)
                if currentID.strip() in allCurrentTagIDs and str(id).strip() in allTagIDs:
                    # oude code
                    # if CheckTag(Tag(str(id).strip(), currentID.strip())):
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
readlock_monitor_thread = Process(target=readlock_monitor)

def detect_and_predict_mask(frame, faceNet, maskNet):
	# grab the dimensions of the frame and then construct a blob
	# from it
	(h, w) = frame.shape[:2]
	blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300),
		(104.0, 177.0, 123.0))

	# pass the blob through the network and obtain the face detections
	faceNet.setInput(blob)
	detections = faceNet.forward()

	# initialize our list of faces, their corresponding locations,
	# and the list of predictions from our face mask network
	faces = []
	locs = []
	preds = []

	# loop over the detections
	for i in range(0, detections.shape[2]):
		# extract the confidence (i.e., probability) associated with
		# the detection
		confidence = detections[0, 0, i, 2]

		# filter out weak detections by ensuring the confidence is
		# greater than the minimum confidence
		if confidence > args["confidence"]:
			# compute the (x, y)-coordinates of the bounding box for
			# the object
			box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
			(startX, startY, endX, endY) = box.astype("int")

			# ensure the bounding boxes fall within the dimensions of
			# the frame
			(startX, startY) = (max(0, startX), max(0, startY))
			(endX, endY) = (min(w - 1, endX), min(h - 1, endY))

			# extract the face ROI, convert it from BGR to RGB channel
			# ordering, resize it to 224x224, and preprocess it
			face = frame[startY:endY, startX:endX]
			face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
			face = cv2.resize(face, (224, 224))
			face = img_to_array(face)
			face = preprocess_input(face)

			# add the face and bounding boxes to their respective
			# lists
			faces.append(face)
			locs.append((startX, startY, endX, endY))

	# only make a predictions if at least one face was detected
	if len(faces) > 0:
		# for faster inference we'll make batch predictions on *all*
		# faces at the same time rather than one-by-one predictions
		# in the above `for` loop
		faces = np.array(faces, dtype="float32")
		preds = maskNet.predict(faces, batch_size=32)

	# return a 2-tuple of the face locations and their corresponding
	# locations
	return (locs, preds)

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-f", "--face", type=str,
	default="face_detector",
	help="path to face detector model directory")
ap.add_argument("-m", "--model", type=str,
	default="mask_detector.model",
	help="path to trained face mask detector model")
ap.add_argument("-c", "--confidence", type=float, default=0.5,
	help="minimum probability to filter weak detections")
args = vars(ap.parse_args())

# load our serialized face detector model from disk
print("[INFO] loading face detector model...")
prototxtPath = os.path.sep.join([args["face"], "deploy.prototxt"])
weightsPath = os.path.sep.join([args["face"],
	"res10_300x300_ssd_iter_140000.caffemodel"])
faceNet = cv2.dnn.readNet(prototxtPath, weightsPath)



# load the face mask detector model from disk
print("[INFO] loading face mask detector model...")
maskNet = load_model(args["model"])

# initialize the video stream and allow the camera sensor to warm up
print("[INFO] starting video stream...")
vs = VideoStream(usePiCamera=True).start()
time.sleep(2.0)




try:
    unlock_box_thread.start()
    capture_picture_button_thread.start()
    readlock_monitor_thread.start()
    button_thread.start()
    numpad_reader_thread.start()
    cardreader_thread.start()
    # loop over the frames from the video stream
    while True:
        # grab the frame from the threaded video stream and resize it
        # to have a maximum width of 400 pixels
        frame = vs.read()
        frame = imutils.resize(frame, width=400)

        # detect faces in the frame and determine if they are wearing a
        # face mask or not
        (locs, preds) = detect_and_predict_mask(frame, faceNet, maskNet)

        # loop over the detected face locations and their corresponding
        # locations
        for (box, pred) in zip(locs, preds):
            # unpack the bounding box and predictions
            (startX, startY, endX, endY) = box
            (mask, withoutMask) = pred

            # determine the class label and color we'll use to draw
            # the bounding box and text
            if mask > withoutMask:
                label = 'Mask'
                mask_detected = True
            else:
                'No Mask'

            color = (0, 255, 0) if label == "Mask" else (0, 0, 255)

            # include the probability in the label
            label = "{}: {:.2f}%".format(label, max(mask, withoutMask) * 100)

            # display the label and boundi ng box rectangle on the output
            # frame
            cv2.putText(frame, label, (startX, startY - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)
            cv2.rectangle(frame, (startX, startY), (endX, endY), color, 2)

        # show the output frame
        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF

        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break



except KeyboardInterrupt:
    GPIO.cleanup()


