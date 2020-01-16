from flask import Flask , request, Response
from flask_jwt import JWT,jwt_required,current_identity
from flask_restful import Resource, Api

from werkzeug.security import safe_str_cmp
from hashlib import sha256
import datetime

from pymongo import MongoClient
from bson.objectid import ObjectId

from doorman.auth import Auth
from doorman.datastore import MongoDataStore

app = Flask(__name__)
app.debug = True
 
### Authentication & Authorization module (Mongodb host is )
auth = Auth(app,MongoDataStore(host='localhost',port=27017,db='fip'),tablename='users',jwt_expiration_delta=3600)


# @app.route('/secret')
# @auth.admin_required
# def secret():
#     return "accessed protcted resource\n %s " % current_identity


# @app.route('/')
# @auth.admin_required
# def public():
#     return "Hello world"

# @app.route('/protected')
# @auth.supervisor_required
# def protected():
#     return '%s' % current_identity

# @app.route('/ownertest',methods=["POST"])
# @auth.owner_required
# def personal(): 
#     return '%s' % current_identity

if __name__ == '__main__':
    app.run(host='localhost',port=5001)