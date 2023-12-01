import firebase_admin
from firebase_admin import credentials, db
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from datetime import date, datetime
from time import sleep
import uuid
import bcrypt
from OpenDoor import *

# ----------
cred = credentials.Certificate("/home/admin/easelock/rasp-test-8e035-firebase-adminsdk-ra7h9-e116fc027b.json")  # Replace with the path to your service account JSON file
firebase_admin.initialize_app(cred, {
	"databaseURL": "https://rasp-test-8e035-default-rtdb.europe-west1.firebasedatabase.app",
    'storageBucket': 'rasp-test-8e035.appspot.com'
})
reader = SimpleMFRC522()
DAYS = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']

TAGID = 'TagID'
CURRENTID = 'CurrentTagID'
TAGS = 'Tags'
USERS = 'users'

ENCODER = 'utf-8'
# ----------
class Tag:
	def __init__(self, TagID, currentTagID):
		self.TagID = tagID
		self.CurrentTagID = currentTagID


def GetTagsDB():
	global USERS
	allTags = []
	ref = db.reference(f'/{USERS}')
	users = ref.get()
	for user in users:
		try:
			allTags.append({user: (users[user][TAGS])})
		except:
			pass
	return allTags


def GetDB():
	global USERS
	allTags = []
	ref = db.reference(f'/{USERS}')
	return ref.get()
	

# ----------
def GetTags():
	global USERS
	global TAGS
	ids = []
	ref = db.reference(f'/{USERS}')
	users = ref.get()
	for user in users:
		try:
			ids.append((users[user][TAGS]))
		except:
			pass
	return ids


def GetAllTagIDs(allTags):
	print(allTags)
	global TAGID
	allIDs = []
	for tag in allTags:
		allIDs.append(str(tag[TAGID]).strip())
	print(allIDs)
	return allIDs
	

def GetAllCurrentTagIDs(allTags):
	global CURRENTID
	allIDs = []
	for tag in allTags:
		allIDs.append(str(tag[CURRENTID]).strip())
	return allIDs
# ----------


# ----------
def GetAllUsers():
	global USERS
	ref = db.reference(f'/{USERS}')
	return ref.get()


def GetUserByID(ID, currentID):
	users = GetAllUsers()
	for user in users:
		try:
			if str(ID).strip() == str((users[user][TAGS][TAGID])).strip() and str(currentID).strip() == str((users[user][TAGS][CURRENTID])).strip():
				return str(user)
		except:
			pass
	return None
	
def GetUsername(ID):
	global USERS
	ref = db.reference(f'/{USERS}/{ID}/Username')
	return ref.get()
# ----------


# ----------
def SetCurrentID(user, newID):
	global USERS
	global TAGS
	global CURRENTID
	if user is not None:
		ref = db.reference(f'/{USERS}/{user}/{TAGS}/{CURRENTID}')
		ref.set(newID)
# ----------
	

def AddEntry(user):
	print("adding entry")
	now = datetime.now()
	key = now.strftime('%Y-%m-%d') + '_' + now.strftime('%H-%M-%S')
	ref = db.reference(f'/logs/{key}')
	ref.set(user)



def AddNewKey(ID, currentID):
	print("id not recognized, adding new key")
	ref = db.reference(f'/NewKeys')
	ref.set({str(uuid.uuid4()): {'ID': str(ID).strip(), 'DID': str(currentID).strip()}})
	sleep(3)
	ref.set({str(uuid.uuid4()): {'ID': 'dummy', 'DID': 'dummy'}})
	
	'''
	newKeys = ref.get()
	for key in newKeys:
		currentKey = newKeys[key]
		for idCheck in currentKey:
			if str(currentKey[idCheck]).strip() not in [str(ID).strip(), str(currentID).strip()]:
				ref.set({str(uuid.uuid4()): {'TagID': str(ID).strip(), 'CurrentTagID': str(currentID).strip()}})
	'''
	
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
	global USERS
	ref = db.reference(f'/{USERS}/{user}/Access')
	access = ref.get()
	if access['AlwaysAccess'] or CheckTime(access['TimeSlots']):
		print("access verleend")
		opendoor()


def CheckTag(entered):
	allTags = GetTags()
	check = False
	for tag in allTags:
		if TagComparison(entered.TagID, tag[TAGID]) and TagComparison(entered.CurrentTagID, tag[CURRENTID]):
			check = True
			break
	return check


def Tagcomparison(entered, primary):
	return bcrypt.checkpw(entered.strip().encode(ENCODER), primary.strip())



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

'''
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
            print(allTagIDs)
            if currentID.strip() in allCurrentTagIDs and str(id).strip() in allTagIDs:
            #if CheckTag(Tag(str(id).strip(), currentID.strip())):
                print("id recognised")
                newID = str(uuid.uuid4())
                reader.write(newID)
                SetCurrentID(user, newID)
                CheckTimeslot(GetUserByID(id, newID))
            else:
                print('addnewkey')
                AddNewKey(id, currentID)
            AddEntry(GetUsername(user) if user is not None else 'Unauthorized')
    except:
        pass
'''
