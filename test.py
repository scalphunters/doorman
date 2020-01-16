##################################################################################
### Module : test.py
### Description : Test module for api endpoints
### Requirements : PyMongo
###
###
###
### Written by : scalphunter@gmail.com 
### Licence : MIT
##################################################################################




import requests
import json
from functools import wraps

def testing(f):
    @wraps(f)
    def wrap(*args,**kwargs):

        status_code, content = f(*args,**kwargs)
        print("\n--------- Testing : %s ----------" % f.__name__)
        print("- Parameters \n- args : %s \n- kwargs : %s \n" % (args,kwargs))
        print("- RESULTS :\n")
        if status_code==200:
            print("SUCCESS - %s \n" % content)
            return status_code, content
        else:
            print("ERROR -  %s \n" % content)
            return status_code, content

    return wrap 

#### login as administrator

url='http://localhost:5001'

@testing
def login_test(user,pwd,**kwargs):
    access_token=""
    if "access_token" in kwargs:
        access_token=kwargs["access_token"]
    payload={"username":user,"password":pwd}
    headers={'Content-Type':'application/json' ,'Authorization':'JWT '+ access_token}
    res=requests.post(url + '/auth',data=json.dumps(payload), headers=headers)
    return res.status_code, res.content

@testing
def registerUser_test(username,password,user_level,user_group,**kwargs):
    access_token=""
    if "access_token" in kwargs:
        access_token=kwargs["access_token"]
    payload={"username" : username,"password":password, "user_level":user_level,"user_group":user_group}
    headers={'Content-Type':'application/json' ,'Authorization':'JWT '+ access_token}
    res=requests.post(url+'/auth/registerUser', data=json.dumps(payload),headers=headers)
    return res.status_code, res.content

@testing
def changePassword_test(old_pwd,new_pwd,**kwargs):
    access_token=""
    if "access_token" in kwargs:
        access_token=kwargs["access_token"]
    payload={"old_password":old_pwd,"new_password":new_pwd}
    headers={'Content-Type':'application/json' ,'Authorization':'JWT '+ access_token}
    res=requests.post(url+'/auth/changePassword', data=json.dumps(payload),headers=headers)
    return res.status_code, res.content

@testing
def resetPassword_test(username,new_pwd,**kwargs):
    access_token=""
    if "access_token" in kwargs:
        access_token=kwargs["access_token"]
    payload={"username":username,"password":new_pwd}
    headers={'Content-Type':'application/json' ,'Authorization':'JWT '+ access_token}
    res=requests.post(url+'/auth/resetPassword', data=json.dumps(payload),headers=headers)
    return res.status_code, res.content

@testing
def changeUserLevel_test(username,new_level,**kwargs):
    access_token=""
    if "access_token" in kwargs:
        access_token=kwargs["access_token"]
    payload={"username":username,"user_level": new_level}
    headers={'Content-Type':'application/json' ,'Authorization':'JWT '+ access_token}
    res=requests.post(url+'/auth/changeUserLevel', data=json.dumps(payload),headers=headers)
    return res.status_code, res.content

@testing
def removeUser_test(username,**kwargs):
    access_token=""
    if "access_token" in kwargs:
        access_token=kwargs["access_token"]
    payload={"username":username}
    headers={'Content-Type':'application/json' ,'Authorization':'JWT '+ access_token}
    res=requests.post(url+'/auth/removeUser', data=json.dumps(payload),headers=headers)
    return res.status_code, res.content


if __name__ == '__main__':

    n_succeeded=0
    n_failed=0

    print("\n-------------- TEST begins with %s --------------------\n" % url)

    admin_cred=["admin","hello123"]
    user_creation1=["sv2","hello123",1,"niral"]
    user_creation2=["sv3","hello123",1,"niral"]
    user_creation3=["sc1","hello123",2,"niral"]
    user_creation4=["an1","hello123",3,"niral"]

    reset_password1=["sv3","hello123"]
    admin_token=""
    #### LOGIN test
    sc ,res = login_test(*admin_cred)
    if sc==200:
        admin_token=json.loads(res)["access_token"]

    #### Register User test
    sc, res = registerUser_test(*user_creation1, access_token=admin_token)

    ### Change password test
    sc, res = changePassword_test(admin_cred[1],"hello123",access_token=admin_token)

    #### Register User test
    sc, res = registerUser_test(*user_creation2, access_token=admin_token)
    sc, res = registerUser_test(*user_creation3, access_token=admin_token)
    sc, res = registerUser_test(*user_creation4, access_token=admin_token)

    ### Reset password test 
    sc, res = resetPassword_test(*reset_password1, access_token=admin_token)

    ### login as supervisor (sv2)

    sc, res = login_test(*user_creation1[:2])
    try:
        resobj=json.loads(res)
        assert("access_token" in resobj)
        supervisor_token=resobj["access_token"]
        n_succeeded+=1
    except:
        n_failed+=1

    ### change User level
    newlevel=["sv3",4]
    sc, res = changeUserLevel_test(*newlevel, access_token=supervisor_token)
    try:
        assert(sc!=200)
        n_succeeded+=1
    except:
        n_failed+=1

    sc, res = changeUserLevel_test(*newlevel, access_token=admin_token)
    try :
        assert(sc==200)
        n_succeeded+=1
    except:
        n_failed+=1

    sc, res = removeUser_test("sc1", access_token=supervisor_token)
    try:
        assert(sc!=200)
        n_succeeded+=1
    except:
        n_failed+=1

    sc, res = removeUser_test("sc1", access_token=admin_token)
    try :
        assert(sc==200)
        n_succeeded+=1
    except:
        n_failed+=1

    sc, res = removeUser_test("sc1", access_token=admin_token)
    try :
        assert(sc!=200)
        n_succeeded+=1
    except:
        n_failed+=1


    print("%d succeeded, %d failed out of %d tests" % ( n_succeeded,n_failed,n_succeeded+n_failed))
