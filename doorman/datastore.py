##################################################################################
### Module : datastore.py
### Description : Database abstraction & implementations
### Requirements : PyMongo
###
###
###
### Written by : scalphunter@gmail.com 
### Licence : MIT
##################################################################################


from pymongo import MongoClient
from bson.objectid import ObjectId
import uuid

#####
class DataStore(object):  
    def __init__(self,**kwargs):

        self.kwargs=kwargs
        self.host=None
        self.port=None 
        self.db=None
        self.connection=None
        if "host" in kwargs:
            self.host=kwargs["host"]
        if "port" in kwargs:
            self.port=kwargs["port"]
        if "db" in kwargs:
            self.db=kwargs["db"]

        self.initialize()

    def initialize(self):
        self.connection=self.connect()

    def getHost(self):
        return self.host 
    def getPort(self):
        return self.port 

    #### To be implemented 
    #### Connection
    def connect(self,**kwargs):
        pass
    def disconnect(self,**kwargs):
        pass

    #### DB & Table
    def set_field_unique(self,table,field_name,**kwargs):
        pass
    #### CRUD interfaces ### 
    def find(self,table,query,doc,**kwargs):
        pass 
    def insert(self,table,doc,**kwargs):
        pass
    def update(self,table,query,doc,**kwargs):
        pass
    def replace(self,table,query,doc,**kwargs):
        pass
    def remove(self,table,query,**kwargs):
        pass
    def find_one(self,table,query,**kwargs):
        pass 
    def insert_one(self,table,doc,**kwargs):
        pass
    def update_one(self,table,query,doc,**kwargs):
        pass
    def replace_one(self,table,query,doc,**kwargs):
        pass
    def remove_one(self,table,query,**kwargs):
        pass


class MongoDataStore(DataStore):
    def __init__(self,**parameters):
        super().__init__(**parameters)
        
    #### Connection
    def connect(self,**kwargs):
        self._conn=MongoClient(self.host,self.port)
        return self._conn[self.db]

    def disconnect(self,**kwargs):
        pass

    #### DB & Table
    def set_field_unique(self,coll,field_name,**kwargs):
        return self.connection[coll].create_index(field_name,unique=True)

    #### CRUD interfaces ### - implementation
    def find(self,coll,query,**kwargs):
        return self.connection[coll].find(query,**kwargs)
    def insert(self,coll,docs,**kwargs):
        return self.connection[coll].insert_many(doc,**kwargs)
    def update(self,coll,query,modification,**kwargs):
        return self.connection[coll].update_many(query,modification,**kwargs)
    def replace(self,coll,query,doc,**kwargs):
        return self.connection[coll].replace_many(query,doc,**kwargs)
    def remove(self,coll,query,**kwargs):
        return self.connection[coll].delete_many(query,**kwargs)
    def find_one(self,coll,query,**kwargs):
        return self.connection[coll].find_one(query,**kwargs)
    def insert_one(self,coll,doc,**kwargs):
        return self.connection[coll].insert_one(doc,**kwargs)
    def update_one(self,coll,query,modification,**kwargs):
        return self.connection[coll].update_one(query,modification,**kwargs)
    def replace_one(self,coll,query,doc,**kwargs):
        return self.connection[coll].replace_one(query,doc,**kwargs)
    def remove_one(self,coll,query,**kwargs):
        return self.connection[coll].delete_one(query,**kwargs).deleted_count