import requests
import time
import os
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import json
from flask import Flask, request, jsonify
from flask_restful import Resource, Api
import base64
from flask_swagger_ui import get_swaggerui_blueprint
from functools import wraps
from flask_pymongo import PyMongo
from flask_httpauth import HTTPBasicAuth
import hashlib
from threading import Thread

auth = HTTPBasicAuth()
app = Flask(__name__)
api = Api(app)


app = Flask(__name__)
api = Api(app)
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
mongo = PyMongo(app)

SWAGGER_URL = ''
API_URL = '/static/swagger.yaml'
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL
)

app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)


@auth.verify_password
def verify_password(username, password):
    try:
        users = mongo.db.users
        user = users.find_one({'username': username})
        password = (hashlib.md5(password.encode())).hexdigest()
        if user['password'] == password:
            return username
    except:
        return None


langs = {
    "python": 71,
    "javascript": 63,
    "java": 62,
    "cc": 54
}


def getResults(instring, outstring, data, lang, b):
    # instring = (base64.b64decode(
    #     data['input'][key].encode('ascii'))).decode('ascii')
    # outstring = (base64.b64decode(
    #     data['output'][key].encode('ascii'))).decode('ascii')
    # pool = ThreadPoolExecutor()
    # for key in data.keys():
    #     sub = (base64.b64decode(
    #         data[key].encode('ascii'))).decode('ascii')
    #     x = pool.submit(lambda p: getSubmissionResults(*p), [
    #         lang, instring, outstring, sub, b, key])
    # x.result()
    threads = []
    for key in data.keys():
        sub = (base64.b64decode(
            data[key].encode('ascii'))).decode('ascii')
        # x = pool.submit(lambda p: getSubmissionResults(*p), [
        #     lang, instring, outstring, sub, b, key])
        t = Thread(target=getSubmissionResults, args=(
            lang, instring, outstring, sub, b, key, ))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()


def getSubmissionResults(lang, inputstring, outputstring, dat, b, x):
    url = "https://judge0.p.rapidapi.com/submissions"
    headers = {
        'x-rapidapi-host': "judge0.p.rapidapi.com",
        'x-rapidapi-key': "ba7248e172msh8b0540a4038e441p165e9fjsn9e78d907167c"
    }
    # url = "https://api.judge0.com/submissions/"
    data = {
        "source_code": dat,
        "language_id": langs[lang],
        "stdin": inputstring,
        "expected_output": outputstring
    }

    r = requests.post(url, data=data, headers=headers).json()["token"]
    b[r] = x
    # print(dat, r)
    # print(r)


class languages(Resource):
    @auth.login_required
    def get(self):
        return {"languages": list(langs.keys())}, 200


class grade(Resource):
    @auth.login_required
    def post(self):
        # start_time = time.time()
        data = request.get_json()
        a, b = {}, {}
        lang = data['lang']
        for key in data['submissions'].keys():
            a[key] = 0
        # pool1 = ThreadPoolExecutor()
        threads = []
        for key in data['input'].keys():
            #     y = pool1.submit(lambda p: getResults(*p), [key, data, lang, b])
            # y.result()

            instring = (base64.b64decode(
                data['input'][key].encode('ascii'))).decode('ascii')

            outstring = (base64.b64decode(
                data['output'][key].encode('ascii'))).decode('ascii')
            # threads = []

            # for key in data["submissions"].keys():
            #     sub = (base64.b64decode(
            #         data["submissions"][key].encode('ascii'))).decode('ascii')
            #     # x = pool.submit(lambda p: getSubmissionResults(*p), [
            #     #     lang, instring, outstring, sub, b, key])
            #     t = Thread(target=getSubmissionResults, args=(
            #         lang, instring, outstring, sub, b, key, ))
            #     threads.append(t)
            #     t.start()
            # for t in threads:
            #     t.join()

            t = Thread(target=getResults, args=(
                instring, outstring, data['submissions'], lang, b, ))
            threads.append(t)
            t.start()
            for t in threads:
                t.join()
            # pool = ThreadPoolExecutor()
            # threads = []
            # for key in data['submissions'].keys():
            #     sub = (base64.b64decode(
            #         data['submissions'][key].encode('ascii'))).decode('ascii')
            #     # x = pool.submit(lambda p: getSubmissionResults(*p), [
            #     #     lang, instring, outstring, sub, b, key])
            #     t = Thread(target=getSubmissionResults, args=(
            #         lang, instring, outstring, sub, b, key, ))
            #     threads.append(t)
            #     t.start()
            # for t in threads:
            #     t.join()
            # x.result()

        # url = "https://api.judge0.com/submissions/batch/?tokens="
        url = "https://judge0.p.rapidapi.com/submissions/"
        headers = {
            'x-rapidapi-host': "judge0.p.rapidapi.com",
            'x-rapidapi-key': "ba7248e172msh8b0540a4038e441p165e9fjsn9e78d907167c"
        }
        n = len(b)
        done = []
        while (True):
            if n == 0:
                break
            for key in b.keys():
                if (key not in done):
                    r1 = requests.get(url+key, headers=headers).json()
                    if (r1['status']['id'] not in [1, 2]):
                        # token = r1['token']
                        if (r1['status']['id'] == 3):
                            a[b[key]] += 1
                        n -= 1
                        done.append(key)
                        # del(b[token])
        # print(key)
        # r1 = requests.get(url+",".join(list(b.keys()))).json()
        # for x in r1["submissions"]:
        #     if (x["status"]["id"] not in [1, 2]):
        #         token = x["token"]
        #         if (x["status"]["id"] == 3):
        #             a[b[token]] += 1
        #         del(b[token])
        # print(time.time()-start_time)
        return a, 200


api.add_resource(grade, '/grade')
api.add_resource(languages, '/languages')
if __name__ == '__main__':
    app.run(debug=True)
