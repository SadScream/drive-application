from flask import Flask, make_response
import json
import os

from db_config import USERNAME, PASSWORD, HOST, SECRET_KEY, APPNAME

app = Flask(APPNAME)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{0}:{1}@{2}/{3}'.format(
	USERNAME, PASSWORD, HOST, "saddy$drive")
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True


STATIC_FOLDER = os.path.join(app.root_path, "static")


def json_response(data: dict, code: int = 200):
	response = make_response(json.dumps(data, ensure_ascii=False), code)
	response.headers["Content-Type"] = "application/json"

	return response


# @app.after_request
# def add_header(r):
# 	r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
# 	r.headers["Pragma"] = "no-cache"
# 	r.headers["Expires"] = "0"
# 	r.headers['Cache-Control'] = 'public, max-age=0'

# 	return r
