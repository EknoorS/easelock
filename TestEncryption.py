# Imports
import bcrypt
import firebase_admin
from firebase_admin import credentials, db

# example password
ENCODER = 'utf-8'
TAGID = 'TagID'
CURRENTID = 'CurrentTagID'
cred = credentials.Certificate("C:/Users/matth/Downloads/rasp-test-8e035-firebase-adminsdk-ra7h9-e116fc027b.json")  # Replace with the path to your service account JSON file
firebase_admin.initialize_app(cred, {"databaseURL": "https://rasp-test-8e035-default-rtdb.europe-west1.firebasedatabase.app", 'storageBucket': 'rasp-test-8e035.appspot.com'})


class Tag:
    def __init__(self, tagID, currentTagID):
        self.TagID = tagID
        self.CurrentTagID = currentTagID


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


def testHash(testKey):
    keyBytes = testKey.encode(ENCODER)
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(keyBytes, salt)


def CheckTag(entered):
    allTags = GetTags()
    check = False
    for tag in allTags:
        if TagComparison(entered.TagID, testHash(tag[TAGID])) and TagComparison(entered.CurrentTagID, testHash(tag[CURRENTID])):
            check = True
            break
    return check


def TagComparison(entered, primary):
    return bcrypt.checkpw(entered.strip().encode(ENCODER), primary.strip())


test = Tag('Frisco in den disco', 'Jupilair')
print(CheckTag(test))
