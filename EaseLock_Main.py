import firebase_admin
from firebase_admin import credentials, db
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from datetime import date, datetime
from time import sleep
import uuid
from OpenDoor import *

# ----------
cred = credentials.Certificate("/home/admin/easelock/rasp-test-8e035-firebase-adminsdk-ra7h9-e116fc027b.json")  # Replace with the path to your service account JSON file
firebase_admin.initialize_app(cred, {
	"databaseURL": "https://rasp-test-8e035-default-rtdb.europe-west1.firebasedatabase.app",
    'storageBucket': 'rasp-test-8e035.appspot.com'
})
reader = SimpleMFRC522()
DAYS = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
# ----------


def GetTagsDB():
	allTags = []
	ref = db.reference('/users')
	users = ref.get()
	for user in users:
		try:
			allTags.append({user: (users[user]['Tags'])})
		except:
			pass
	return allTags


def GetDB():
	allTags = []
	ref = db.reference('/users')
	return ref.get()
	

# ----------
def GetTags():
	ids = []
	ref = db.reference('/users')
	users = ref.get()
	for user in users:
		try:
			ids.append((users[user]['Tags']))
		except:
			pass
	return ids


def GetAllTagIDs(allTags):
	allIDs = []
	for tag in allTags:
		allIDs.append(str(tag['TagID']).strip())
	return allIDs
	

def GetAllCurrentTagIDs(allTags):
	allIDs = []
	for tag in allTags:
		allIDs.append(str(tag['CurrentTagID']).strip())
	return allIDs
# ----------


# ----------
def GetAllUsers():
	ref = db.reference('/users')
	return ref.get()


def GetUserByID(ID, currentID):
	users = GetAllUsers()
	for user in users:
		try:
			if str(ID).strip() == str((users[user]['Tags']['TagID'])).strip() and str(currentID).strip() == str((users[user]['Tags']['CurrentTagID'])).strip():
				return str(user)
		except:
			pass
	return None
	
def GetUsername(ID):
	ref = db.reference(f'/users/{ID}/Username')
	return ref.get()
# ----------


# ----------
def SetCurrentID(user, newID):
	if user is not None:
		ref = db.reference(f'/users/{user}/Tags/CurrentTagID')
		ref.set(newID)
# ----------
	

def AddEntry(user):
	now = datetime.now()
	key = now.strftime('%Y-%m-%d') + '_' + now.strftime('%H-%M-%S')
	ref = db.reference(f'/logs/{key}')
	ref.set(user)
	
	
def AddNewKey(ID, currentID):
	#ref = db.reference(f'/NewKeys/{str(uuid.uuid4())}')
	ref = db.reference(f'/NewKeys')
	newKeys = ref.get()
	for key in newKeys:
		currentKey = newKeys[key]
		for idCheck in currentKey:
			if str(currentKey[idCheck]).strip() not in [str(ID).strip(), str(currentID).strip()]:
				ref.set({str(uuid.uuid4()): {'TagID': str(ID).strip(), 'CurrentTagID': str(currentID).strip()}})
	
	
def CheckTime(times):
	specTimes = times['Specific']
	weeklyTimes = times['Weekly']
	now = datetime.now()
	for timeslot in specTimes:
		time = specTimes[timeslot]
		dt, hr = time.split('_')
		hr1, hr2 = hr.split('-')
		if dt == str(date.today()) and int(hr1.strip()) <= int(now.strftime("%H%M")) <= int(hr2.strip()):
			return True
		#YYYY-MM-DD_HHMM-HHMM
	for timeslot in weeklyTimes:
		time = weeklyTimes[timeslot]
		dy, hr = time.split('_')
		hr1, hr2 = hr.split('-')
		if dy == DAYS[now.weekday()] and int(hr1.strip()) <= int(now.strftime("%H%M")) <= int(hr2.strip()):
			return True
		#DD_HHMM-HHMM
	return False
	
	
def CheckTimeslot(user):
	ref = db.reference(f'/users/{user}/Access')
	access = ref.get()
	if access['AlwaysAccess'] or CheckTime(access['TimeSlots']):
		print("access verleend")
		opendoor()



'''
while True:
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
	except KeyboardInterrupt:
		GPIO.cleanup()
'''
