from flask import make_response
from json import dumps


def json_response(data: dict, code: int = 200):
	response = make_response(dumps(data, ensure_ascii=False), code)
	response.headers["Content-Type"] = "application/json"

	return response


# @app.after_request
# def add_header(r):
# 	r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
# 	r.headers["Pragma"] = "no-cache"
# 	r.headers["Expires"] = "0"
# 	r.headers['Cache-Control'] = 'public, max-age=0'

# 	return r
