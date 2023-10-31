#Classes
class Key:
	def __init__(self, iD, currentTagID, userID):
		self.ID = iD
		self.CurrentTagID = currentTagID
		self.UserID = userId		


class User:
	def __init__(self, iD, email, username, password):
		self.ID = iD
		self.Email = email
		self.Username = username
		self._password = password


class AllowedEntries:
	 def __init__(self, iD, keyID, allowedStart, allowedEnd):
		 self.ID = iD
		 self.KeyID = keyID
		 self.AllowedStart = allowedStart
		 self.AllowedEnd = allowedEnd


class Entries:
	def __init__(self, iD, entryTime, keyID):
		self.ID = iD
		self.EntryTime = entryTime
		self.KeyID = keyID
