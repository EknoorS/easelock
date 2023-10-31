import EaseLock_Classes
from firebase import firebase

firebase = firebase.Firebase

def GetAllKeys():
	tags = GetTagsDB()
	ids = []
	for tag in tags:
		ids.append(tag.CurrentTagID)
	return ids
	

def CheckID(tagID):
	allKeys = GetAllKeys()
	for key in allKeys:
		if key.CurrentTagID == tagID:
			return True
	return False
	
	
def NewUser():
	pass
	


def CheckEntry():
	
