import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import uuid

#Classes
class Key:
	def __init__(self, tagID, currentID, user):
		self.TagID = tagID
		self.CurrentID = currentID
		self.User = user
	def UpdateID(self, newID):
		self.CurrentID = newID
		
		
#Declarations
reader = SimpleMFRC522()
retry = 'Y'
Tags = []
alreadyExists = False

#Processing
while retry == 'Y':
	try:
		print('Please place your tag.')
		id, currentID = reader.read()
		print(f'Tag ID: {str(id)}')
		print(f'Current ID: {str(currentID)}')
		newID = uuid.uuid4()
		for tag in Tags:
			alreadyExists = True if tag.TagID == id else False
			if alreadyExists:
				break
		if not alreadyExists:
			reader.write(str(newID))
			print(f'New ID: {str(newID)}')
			newUser = input('User: ')
			newTag = Key(id, newID, newUser)
			retry = input('Retry? (Y/N): ').upper()
			Tags.append(newTag)			
		else:
			reader.write(str(newID))
			for tag in Tags:
				if tag.TagID == id:
					tag.UpdateID(newID)
					print(f'New ID: {str(newID)} for {tag.User}')
			retry = input('Retry? (Y/N): ').upper()
			alreadyExists = False
	finally:
		GPIO.cleanup()

