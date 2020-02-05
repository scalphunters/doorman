##################################################################################
### Module : auth.py
### Description : Authentication & Authorization module for Flask-JWT
### Requirements : Flask, Flask_JWT, Flask_Restful, PyMongo
###
###
###
### Written by : scalphunter@gmail.com ,  2020/01/15
### Licence : MIT
##################################################################################

from flask import Flask , request, Response
from flask_jwt import JWT,jwt_required,current_identity
from flask_cors import CORS

# from flask_restful import Resource, Api

from werkzeug.security import safe_str_cmp
from hashlib import sha256
import datetime
from functools import wraps
from enum import IntEnum
import json
import uuid


from .datastore import DataStore
from . import utils

class UserLevel(IntEnum):
    ADMIN=0
    SUPERVISOR=1
    SCORER=2
    ANNOTATOR=3
    GUEST=4


class User(object):
    def __init__(self,doc):

        self.id  = str(doc["_id"]) # FOR JWT internal
        self._id = doc["_id"]
        self.username = doc["username"]
        self.password = doc["password"]
        self.user_level = doc["user_level"]
        self.user_group = doc["user_group"]
 
    def toDict(self):
        out={
            "_id" : self._id,
            "username" : self.username,
            "password" : self.password,
            "user_level" : self.user_level,
            "user_group" : self.user_group
        }
        return out

    def __str__(self):
        out={
            "_id" : str(self._id),
            "username" : self.username,
            #"password" : self.password,
            "user_level" : self.user_level,
            "user_group" : self.user_group
        }
        return json.dumps(out)


class Auth(object):
    def __init__(self,app,datastore,**kwargs):
        
        self.tablename='users'
        if "tablename" in kwargs:
            self.tablename=kwargs['tablename']
        self.jwt_expiration_delta=3600
        if "jwt_expiration_delta" in kwargs:
            self.jwt_expiration_delta=kwargs["jwt_expiration_delta"]
        self.appKey=None
        if "app_key" in kwargs:
            self.appKey=kwargs['app_key']
        self.dbInstance=datastore
        self.app=app 
        CORS(self.app)
        ### initialize admin
        self.checkAdminExists()
        ### JWT initialize
        self.app.config['SECRET_KEY'] = 'wosqwiepuqwrepvb3p9v297923972379239'
        self.app.config['JWT_EXPIRATION_DELTA'] = datetime.timedelta(seconds=self.jwt_expiration_delta)
        self.jwt = JWT(self.app, self.authenticate, self.identity)
        ### Register auth APIs to flask app
        self.registerAuthUri() 

    def checkAdminExists(self):

        self.adminExists=self.dbInstance.find_one(self.tablename,{"username":"admin"}) is not None
        self.dbInstance.set_field_unique(self.tablename,"username",unique=True)
        
        cred=   {"username": "admin",
                 "password" : "hello123",
                 "user_level" : int(UserLevel.ADMIN),
                 "user_group" : "admin"}  

        ### Create admin user at the first run
        if not self.adminExists:
            print("admin user doesn't exist, trying to make one ... ")
            adminCredential={
                             "username": cred["username"],
                             "password" : self.hashPassword(cred[u"password"]),
                             "user_level" : cred["user_level"],
                             "user_group" : cred["user_group"]} 
            adminCredential=utils.addUUID(adminCredential)
            res=self.dbInstance.insert_one(self.tablename,adminCredential)
            if res.inserted_id:
                print(cred)
            else:
                print("Admin creation has failed, please try again")
        else:
            print("admin exists, starting server ...\n",cred)

    def registerAuthUri(self):

        @self.app.route('/auth/checkAppKey/<k>',methods=["GET"])
        def _checkAppKey(k):
            flag= str(self.appKey)==str(k)
            res=Response(json.dumps({"result":flag,"app_key":self.appKey}),status=200)
            res.headers['Content-Type']='application/json'
            return res
        @self.app.route('/auth/whoAmI',methods=["GET"])
        @jwt_required()
        def _whoAmI():
            res=Response(str(current_identity), 200)
            res.headers['Content-Type']='application/json'
            return res

        @self.app.route('/auth/registerUser',methods=["POST"])
        @self.admin_required
        def _registerUser():
            req=request.get_json()
            status_code , res=self.registerUser(req)
            res=Response(res,status=status_code)
            res.headers['Content-Type']='application/json'
            return res

        @self.app.route('/auth/resetPassword',methods=["POST"])
        @self.admin_required
        def _resetPassword():
            req=request.get_json()
            status_code , res =self.resetPassword(req)
            res=Response(res,status=status_code)
            res.headers['Content-Type']='application/json'
            return res

        @self.app.route('/auth/changePassword',methods=["POST"])
        @jwt_required()
        def _changePassword():
            req=request.get_json()
            status_code, res =self.changePassword(req)
            res=Response(res,status=status_code)
            res.headers['Content-Type']='application/json'
            return res

        @self.app.route('/auth/changeUserLevel',methods=["POST"])
        @self.admin_required
        def _changeUserLevel():
            req=request.get_json()
            status_code, res =self.changeUserLevel(req)
            res=Response(res,status=status_code)
            res.headers['Content-Type']='application/json'
            return res

        @self.app.route('/auth/removeUser',methods=["POST"])
        @self.admin_required
        def _removeUser():
            req=request.get_json()
            status_code, res =self.removeUser(req)
            res=Response(res,status=status_code)
            res.headers['Content-Type']='application/json'
            return res

    ### utility function
    def hashPassword(self,s):
        return sha256(s.encode('utf-8')).hexdigest()
    

    ### JWT functions

    def authenticate(self,username, password): #### This is internal authentication function
        print(username,password)
        user = None
        obj=self.dbInstance.find_one(self.tablename,{"username":username})
        if obj is not None:
            user=User(obj)
        else:
            return None
        if user and safe_str_cmp(user.password, self.hashPassword(password)):
            return user

    def identity(self,payload):   ### This returns current_identity
        user_id = payload['identity'] 
        res=self.dbInstance.find_one(self.tablename,{"_id": user_id })
        if res is not None:
            return User(res)
        else:
            return None

    ### User creation and management API endpoints
    
    def credentialSanityCheck(self,doc):   ### this needs to be elaborated more
        if "username" in doc and "password" in doc and "user_level" in doc and "user_group" in doc:
            return True
        else:
            return False

    def registerUser(self,doc):  ## register a user by admin 
        if self.credentialSanityCheck(doc):
            doc["password"]=self.hashPassword(doc["password"])
            doc=utils.addUUID(doc)
            try:
                iid=self.dbInstance.insert_one(self.tablename,doc)
                return 200, "Success"
            except Exception as e :
                return 403, "Exception in registerUser : %s" % str(e) 
            finally:
                pass  
        else:
            return 403,"Input data is something wrong. please try again"

    def removeUser(self,doc): ## remove a user by admin
        if "username" in doc:
            username=doc['username']
            try:
                cnt=self.dbInstance.remove_one(self.tablename,{"username":username})
                if cnt >=1 :
                    return 200, "Sucessfully removed user : %s" % username
                else:
                    return 500, "There is no such user"
            except Exception as e:
                return 401, "Exception in removeUser : %s" % str(e)
            finally:
                pass

    def changePassword(self,doc,**kwargs):  ## self change password
        if "old_password" in doc and "new_password" in doc:
            old_pwd=doc["old_password"]
            new_pwd=doc["new_password"]
            cred=current_identity
            
            if cred.password != self.hashPassword(old_pwd):
                return 401, "Old password is not correct"
            try:
                cred.password=self.hashPassword(new_pwd)
                cnt=self.dbInstance.replace_one(self.tablename,{"_id":cred._id}, cred.toDict())
                return 200, "Success : %s" % str(cred)

            except Exception as e :
                return 403, "Exception in changePassword : %s" % str(e)
            finally : 
                pass
                
        else:
            return 403, "Old password and new password should be sent together"

    def resetPassword(self, doc, **kwargs): ## force reset of password by admin
        if "username" in doc and "password" in doc:
            username=doc["username"]
            password=doc["password"]

            try:                
                hashed = self.hashPassword(password)
                m={"$set" : {"password" : hashed}}
                cnt=self.dbInstance.update_one(self.tablename,{"username":username},m)
                return 200, "Success : %s" % cnt

            except Exception as e :
                return 403,"Exception in resetPassword : %s" % str(e) 
            finally : 
                pass
                
        else:
            return 403,"user name and password field should be filled"

    def changeUserLevel(self,doc, **kwargs): ## change user level by admin
        if "username" in doc and "user_level" in doc:
            username=doc["username"]
            user_level=doc["user_level"]

            try:                
                m={"$set" : {"user_level" : user_level}}
                cnt=self.dbInstance.update_one(self.tablename,{"username":username},m)
                return 200, "Success : %s" % cnt

            except Exception as e :
                return 403,"Exception in changeUserLevel : %s" % str(e) 
            finally : 
                pass
                
        else:
            return 403,"user name and user_level field should be filled"


    #### db access for auth


    def getOwnerOfDocumentById(self,collectionName,id):
        res=self.dbInstance.find_one(self.tablename,{_id : id})
        if "owner" in res:
            return res["owner"]
        else:
            return None

    def getGroupOfDocumentById(self,collectionName,id):
        res=self.dbInstance.find_one(self.tablename,{_id : id})
        if "group" in res:
            return res["group"]
        else:
            return None


    ########################### DECORATORS ###############################
    #### Authorization decorators by user level


    def admin_required(self,func):
        @jwt_required(func)
        @wraps(func)  # this is important when macro is expanded , this makes wrapper not redundant to prevent the error from defining same function twice
        def wrapper(*args,**kwargs):
            if current_identity.user_level==int(UserLevel.ADMIN):
                return func(*args,**kwargs)
            else:
                return Response("Admin required",status=401)
        return wrapper

    def supervisor_required(self,func):
        @jwt_required(func)
        @wraps(func)  # this is important when macro is expanded , this makes wrapper not redundant to prevent the error from defining same function twice
        def wrapper(*args,**kwargs):
            if current_identity.user_level<=int(UserLevel.SUPERVISOR):
                return func(*args,**kwargs)
            else:
                return Response("Supervisor level required",status=401)
        return wrapper

    def scorer_required(self,func):
        @jwt_required(func)
        @wraps(func)  # this is important when macro is expanded , this makes wrapper not redundant to prevent the error from defining same function twice
        def wrapper(*args,**kwargs):
            if current_identity.user_level<=int(UserLevel.SCORER):
                return func(*args,**kwargs)
            else:
                return Response("Scorer level required",status=401)
        return wrapper

    def annotator_required(self,func):
        @jwt_required(func)
        @wraps(func)  # this is important when macro is expanded , this makes wrapper not redundant to prevent the error from defining same function twice
        def wrapper(*args,**kwargs):
            if current_identity.user_level<=int(UserLevel.ANNOTATOR):
                return func(*args,**kwargs)
            else:
                return Response("Annotator level required",status=401)
        return wrapper

    def guest_required(self,func):
        @jwt_required(func)
        @wraps(func)  # this is important when macro is expanded , this makes wrapper not redundant to prevent the error from defining same function twice
        def wrapper(*args,**kwargs):
            if current_identity.user_level<=int(UserLevel.GUEST):
                return func(*args,**kwargs)
            else:
                return Response("Guest level required",status=401)
        return wrapper

    #### Authorization by user id and group

    def owner_required(self,func):
        @jwt_required(func)
        @wraps(func)  # this is important when macro is expanded , this makes wrapper not redundant to prevent the error from defining same function twice
        def wrapper(*args,**kwargs):
            if current_identity["_id"] is not None:
                userid=current_identity["_id"]
                print(request.get_json())
                return func(*args,**kwargs)
            else:
                return Response("Only the owner of the resource can access",status=401)
        return wrapper

    def group_required(self,func):
        @jwt_required(func)
        @wraps(func)  # this is important when macro is expanded , this makes wrapper not redundant to prevent the error from defining same function twice
        def wrapper(*args,**kwargs):
            if current_identity["_id"] is not None:
                userid=current_identity["_id"]
                print(request.get_json())
                return func(*args,**kwargs)
            else:
                return Response("Only the permitted groups can access the resource",status=401)
        return wrapper

