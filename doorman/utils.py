##################################################################################
### Module : utils.py
### Description : Utilities for doorman lib
### Requirements : PyMongo
###
###
###
### Written by : scalphunter@gmail.com 
### Licence : MIT
##################################################################################

import uuid

def addUUID(doc):
	doc["_id"]=str(uuid.uuid4())
	return doc