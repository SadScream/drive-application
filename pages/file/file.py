import os

from flask import Blueprint, render_template, url_for, request, send_file, abort
from flask_login import login_required, current_user

file_page = Blueprint('file_page', __name__, template_folder="templates", static_folder="static", static_url_path='/')


@file_page.route("/", methods=['GET'])
@login_required
def upload_page():
	return render_template("upload.html")


@file_page.route('/uploads/', methods=['GET'])
@login_required
def list_uploads_page():
	font = url_for('static', filename='font/rawline-500-cirylic.woff2')
	file_icon = url_for('.static', filename='img/file_icon.png')

	return render_template(
		"uploads.html",
		font=font,
		file_icon=file_icon)


@file_page.route('/uploads/<string:filename>', methods=['GET'])
@login_required
def uploaded_file(filename):
	'''
	Принимает имя файла и отправляет в ответ файл

	-> filename:str
	-> :param: small - нужен ли уменьшенный экземпляр
	-> :param: download - отправлять ли как attachment
	'''

	path_to_file = os.path.join(current_user.get_default_folder(), filename)
	to_download = False

	if request.args.get("small") == "1":
		path_to_file = os.path.join(
			current_user.get_default_small_folder(), filename
		)
	if request.args.get("download") == "1":
		to_download = True

	if os.path.exists(path_to_file):
		return send_file(path_to_file, as_attachment=to_download, cache_timeout=0)
			
	# response = json_response({
	# 	"ok": False,
	# 	"message": "File doesn't exist"
	# }, 404)
	
	return abort(404)