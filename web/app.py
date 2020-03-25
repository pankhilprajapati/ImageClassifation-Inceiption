from flask import *
from flask_restful import *
from pymongo import *
import bcrypt
import requests
import subprocess
import json

app = Flask(__name__)

api = Api(app)


client = MongoClient("mongodb://db:27017")
db = client.ImageR
users = db['Users']


def UserExist(username):
    if users.find({"Username":username}).count() != 0:
        return True
    else:
        return False

class Register(Resource):
    def post(self):
        postedData = request.get_json()


        username = postedData['username']
        password = postedData['password']

        if UserExist(username):
            return jsonify({
                "status": 301,
                "message": "user already present"
            })
        
        hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

        users.insert({
            "Username": username,
            "Password": hashed_pw,
            "Token": 4
        })

        return jsonify({
            "status": 200,
            "message": 'Successfully saved'
        })

def verify_pw(username, password):
    if not UserExist(username):
        return False
    hashed_pw = users.find({"Username":username})[0]['Password']

    if bcrypt.hashpw(password.encode('utf8'), hashed_pw) == hashed_pw :
        return True
    else:
        return False

def genReturnDict(status, msg):
    return {
        "status": status,
        "message": msg
    }

def verifyCred(username, password):
    if not UserExist(username):
        return genReturnDict(301,"Invalid username"), True
    
    correct_pw = verify_pw(username, password)
    if not correct_pw:
        return genReturnDict(302, "Invalid Password"), True
    return None, False,
class Classify(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        url = postedData["url"]

        retJson , err = verifyCred(username,password)

        if err:
            return jsonify(retJson)
        

        tokens = users.find({"Username":username})[0]["Token"]
        if tokens<=0:
            return jsonify(genReturnDict(303, "Not Enough token"))

        r = requests.get(url=url)
        retJson = {}
        with open("temp.jpg","wb") as f:
            f.write(r.content)
            proc = subprocess.Popen('python classify_image.py --model_dir =. --image_file=./temp.jpg ',
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            ret = proc.communicate()[0]
            proc.wait()
            with open("text.txt") as g:
                retJson = json.load(g)
        users.update({
            "Username":username
        },{
            "$set":{
                "Token": tokens-1
            }
        })
        return retJson

class Refill(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["admin_pw"]
        amount = postedData["amount"]

        if not UserExist(username):
            return jsonify(genReturnDict(301, "User not exist"))

        correct_pw = 'abc123'
        if not password == correct_pw:
            return jsonify(genReturnDict(304, "Invalid admin password"))
        

        users.update({
            "Username": username
        },{
            "$set":{
                "Token": amount
            }
        })
        return jsonify(genReturnDict(200, "Refill Done"))




api.add_resource(Register, '/register')
api.add_resource(Classify, "/classify")
api.add_resource(Refill, "/refill")


if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True)