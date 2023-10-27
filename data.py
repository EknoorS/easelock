import pyrebase 
from picamera2 import Picamera2
from datetime import datetime

picam2 = Picamera2()

config = {
  "apiKey": "AIzaSyAKEVwS8wwBRlGU8PUo9ntNmKX9POqWEEo",
  "authDomain": "rasp-test-8e035.firebaseapp.com",
  "databaseURL": "https://rasp-test-8e035-default-rtdb.europe-west1.firebasedatabase.app",
  "projectId": "rasp-test-8e035",
  "storageBucket": "rasp-test-8e035.appspot.com",
  "messagingSenderId": "103939666521",
  "appId": "1:103939666521:web:69a25cf854b9dbfcf67748",
  "measurementId": "G-WWDZW8THGB"
}
  

firebase = pyrebase.initialize_app(config)

picam2.start_and_capture_files('foto.jpg')

database = firebase.database()
storage = firebase.storage()
storage.child("foto: " + datetime.now().strftime("%d-%m-%Y, %H:%M:%S")).put("foto.jpg")

