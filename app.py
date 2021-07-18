# -*- coding: utf-8 -*-

import os

from pathvalidate import is_valid_filename
from flask import (
	request, render_template, url_for,
	redirect, safe_join, send_file, flash
)
from flask_login import login_required, current_user, logout_user

from tools.app_manip import app, json_response
from tools.login_manip import login_manager, login_and_create_folder
from tools.database import (
	db, File, Status, User,
	fill_status_defaults, add_admin
)
from tools.file_manip import get_save_file, update_file_info
from db_config import ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD


login_manager.login_view = 'sign_in'  # куда идет перенаправление для логина


#####################################################
#################     API START    ##################
#####################################################

@app.route('/login/', methods=['GET'])
def login():
	'''
	BasicAuth метод авторизации

	-> HEADERS:
		Authorization: Basic <username:password>  *BASE64*
	:return: JSON {
		"ok": bool,
		"message": str
	}
	'''

	data = {
		"ok": True
	}

	if current_user.is_authenticated:
		data["message"] = "You're already logged in"
		return json_response(data)

	remember = True if request.args.get("remember") == "1" else False

	if request.authorization:
		username = request.authorization.username
		password = request.authorization.password
		user_obj = db.session.query(User).filter(User.username == username).first()

		if user_obj and user_obj.check_password(password):
			login_and_create_folder(user_obj, remember)
			return json_response(data)

		data["ok"] = False
		data["message"] = "Invalid username/password"
		return json_response(data, 403)

	data["ok"] = False
	data["message"] = "BasicAuth needs"
	return json_response(data, 401)


@app.route('/logout/')
@login_required
def logout():
	'''
	Выход из учетной записи

	:return: JSON {
		"ok": bool
	}
	'''

	logout_user()
	return json_response({"ok": True})


@app.route('/upload/', methods=['POST'])
@login_required
def post_file():
	'''
	Загрузка файла на сервер

	-> BODY: FILE
	:return: JSON {
		"ok": bool,
		"message": str
	}
	'''

	data = {"ok": True}

	if (("Content-Length" in request.headers) and (
		int(request.headers["Content-Length"]) >= (128 * 1024 * 1024))):

		data["ok"] = False
		data["message"] = "File is too large"

		return json_response(data, 413)

	if "file" in request.files:
		file = request.files['file']
	else:
		data["ok"] = False
		data["message"] = "File should be sent"

		return json_response(data, 400)

	if file:
		file.seek(0, os.SEEK_END)
		file_size = file.tell() / 1024  # kilobytes
		file.seek(0)

		allowed_space = db.session.query(Status).filter(
			Status.status_id == current_user.status_id).first().available_size

		if int(current_user.used_space) + file_size >= allowed_space:
			data["ok"] = False
			data["message"] = "Not enough free space"

			return json_response(data, 507)

		file_construct = os.path.splitext(file.filename)  # получаем имя файла и расширение

		# обрезаем название до 64 символов с учетом расширения
		filename = file_construct[0][:64 - len(file_construct[1])] + file_construct[1]
		user_folder = current_user.default_folder  # папка загрузок зашедшего пользователя

		if os.path.exists(os.path.join(user_folder, filename)):
			file_obj = update_file_info(file, file_size, user_folder, filename, current_user)
		else:
			file_obj = get_save_file(file, file_size, user_folder, filename, current_user)
			db.session.add(file_obj)

		db.session.commit()
		return json_response(data)

	data["ok"] = False
	data["message"] = "Error"

	return json_response(data, 400)


@app.route('/uploads/<string:filename>', methods=['GET'])
@login_required
def uploaded_file(filename):
	'''
	Принимает имя файла и отправляет в ответ файл, либо
	JSON с полем "ok": False, если файла не существует

	-> filename:str
	-> :param: small - нужен ли уменьшенный экземпляр
	-> :param: download - отправлять ли как attachment

	:return: JSON {
		"ok": bool,
		"message": str
	}
	or
		FILEOBJ
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
			
	response = json_response({
		"ok": False,
		"message": "File doesn't exist"
	}, 404)
	
	return response


@app.route('/uploads/<string:filename>', methods=['PUT'])
@login_required
def put_file(filename):
	'''
	Принимает имя файла и json объект с новым именем, на которое нужно поменять

	-> filename: str
	-> JSON {
		"name": str
	}
	:return: JSON {
		"ok": bool,
		"message": str
	}
	'''
	
	data = {
		"ok": True
	}

	if "name" not in request.json or not isinstance(request.json["name"], str):  # неверные данные в json
		data["ok"] = False
		data["message"] = "Json is incorrect"

		return json_response(data, 400)

	if is_valid_filename(request.json["name"]):  # если имя файла в порядке
		original_file_path = os.path.join(current_user.get_default_folder(), filename)

		if (os.path.exists(original_file_path)):  # если изменяемый файл существует
			new_file_path = safe_join(current_user.get_default_folder(), request.json["name"])
			original_file_construct = os.path.splitext(filename)  # получаем имя и расширение
			new_file_construct = os.path.splitext(request.json["name"])

			if ((not os.path.exists(new_file_path)) and (
				original_file_construct[1] == new_file_construct[1])):  # если новый файл уже не существует
				
				file_obj = db.session.query(File).filter(
					File.owner_id == current_user.get_id(), File.filename == filename).first()

				os.rename(original_file_path, new_file_path)

				file_obj.filename = request.json["name"]
				file_obj.url = safe_join("/uploads/", request.json["name"]) + "?download=1"
				original_small_file_path = os.path.join(current_user.get_default_small_folder(), filename)

				if os.path.exists(original_small_file_path):
					new_small_file_path = safe_join(
						current_user.get_default_small_folder(),
						request.json["name"])

					os.rename(original_small_file_path, new_small_file_path)
					file_obj.small_url = safe_join(
						"/uploads/", request.json["name"]) + "?small=1&download=1"

				db.session.commit()

				return json_response(data)

	data["ok"] = False
	data["message"] = "File error"

	return json_response(data, 400)


@app.route('/uploads/<string:filename>', methods=['DELETE'])
@login_required
def delete_file(filename):
	'''
	Принимает имя файла и удаляет файл с этим именем для данного пользователя

	-> filename: str
	:return: JSON {
		"ok": bool,
		"message": str
	}
	'''

	data = {
		"ok": True
	}

	pth = os.path.join(current_user.get_default_folder(), filename)

	if not os.path.exists(pth):
		data["ok"] = False
		data["message"] = "File doesn't exist"

		return json_response(data, 404)

	os.remove(pth)
	small_pth = os.path.join(current_user.get_default_small_folder(), filename)

	if os.path.exists(small_pth):
		os.remove(small_pth)
	
	file_obj = db.session.query(File).filter(
		File.owner_id == current_user.get_id(), File.filename == filename).first()
	current_user.used_space = int(current_user.used_space) - file_obj.size

	db.session.delete(file_obj)
	db.session.commit()

	return json_response(data)


@app.route('/files/', methods=['GET'])
@login_required
def get_files():
	'''
	Возвращает список файлов текущего пользователя
	:return: JSON {
		"ok": bool,
		"uploads": [
			{
				"id": int,
				"name": str,
				"type": str,
				"url": str,
					*если есть*
				"small_url": str,
				"width": int,
				"height": int
			},
			...]
	'''

	q_result = db.session.query(File).filter(File.owner_id == current_user.user_id)
	data = {"ok": True, "uploads": []}

	for item in q_result:
		file_path = safe_join(current_user.get_default_folder(), item.filename)
		file_json = {}

		if os.path.isfile(file_path) and os.path.exists(file_path):
			file_json = {
				'id': item.file_id,
				'name': item.filename,
				'type': item._type,
				'url': item.url
			}
			if "image" in item._type:
				file_json['small_url'] = item.small_url
				file_json['width'] = item.width
				file_json['height'] = item.height
			data["uploads"].append(file_json)

	return json_response(data)


@app.route('/files/<string:filename>/', methods=['GET'])
@login_required
def get_file(filename):
	'''
	Принимает имя файла и возвращает информацию о нем

	-> filename:str
	:return: JSON {
		"ok": bool,
		"id": int,
		"name": str,
		"type": str,
		"url": str,
		"owner_id": int,
		"small_url": str,  *если есть*
		"width": int,  *если есть*
		"height": int  *если есть*
	}
	'''

	file_obj = db.session.query(File).filter(
		File.owner_id == current_user.user_id, File.filename == filename).first()
	file_path = os.path.join(current_user.get_default_folder(), filename)

	if "small" in request.args and request.args.get("small") == "1":
		file_path = os.path.join(current_user.get_default_small_folder(), filename)

	data = {"ok": True}

	if (os.path.exists(file_path) and os.path.isfile(file_path)):
		data = {
			'id': file_obj.file_id,
			'name': file_obj.filename,
			'type': file_obj._type,
			'url': file_obj.url,
			'owner_id': file_obj.owner_id
		}

		if "image" in file_obj._type:
			data['small_url'] = file_obj.small_url
			data['width'] = file_obj.width
			data['height'] = file_obj.height

		return json_response(data)
	else:
		data["ok"] = False
		data["message"] = "File doesn't exist"
		response = json_response(data, 404)

		return redirect(url_for("list_uploads_page"), Response=response)


@app.route('/users/<int:user_id>', methods=['GET'])
@login_required
def get_user_info(user_id):
	'''
	Возвращает информацию о пользователе с данным id

	-> user_id:int
	:return: JSON {
		"ok": bool,
		"id": int,
		"username": str,
		"used_space": float,
		"space": int,
		"is_current": bool
	}
	'''
	# print(user_id)
	user_obj = db.session.query(User).filter(User.user_id == user_id).first()
	data = {
		"ok": True
	}

	if user_obj:
		status_obj = db.session.query(Status).filter(
			Status.status_id == user_obj.status_id).first()
		
		data["id"] = user_obj.user_id
		data["username"] = user_obj.username
		data["used_space"] = float(user_obj.used_space)
		data["space"] = int(status_obj.available_size)
		data["is_current"] = current_user.user_id == user_obj.user_id

		return json_response(data)

	data["ok"] = False
	data["message"] = "User doesn't exist"

	return json_response(data, 404)


@app.route('/users/', methods=['GET'])
@login_required
def get_users():
	'''
	Возвращает список пользователей. Если текущий пользователь имеет статус админа
	то возвращается список всех пользователей, а иначе список из одного элемента -
	информации о текущем пользователе

	:return: JSON {
		"ok": bool,
		"users": [
			{
				"ok": bool,
				"id": int,
				"username": str,
				"used_space": float,
				"space": int,
				"is_current": bool
			},
			...,]
	}
	'''

	admin_status = db.session.query(Status).filter(Status.name == "admin").first().status_id
	data = {"ok": True, "users": []}

	if current_user.status_id == admin_status:  # если текущий пользователь - админ
		users = db.session.query(User).all()

		for u in users:
			available_size = db.session.query(Status).filter(
				Status.status_id == u.status_id).first().available_size
			user = {
				"user_id": u.user_id,
				"username": u.username,
				"used_space": float(u.used_space),
				"space": int(available_size),
				"is_current": current_user.user_id == u.user_id
			}
			data["users"].append(user)
	else:
		available_size = db.session.query(Status).filter(
			Status.status_id == current_user.status_id).first().available_size

		user = {
			"user_id": current_user.user_id,
			"username": current_user.username,
			"used_space": float(current_user.used_space),
			"space": int(available_size),
			"is_current": True
		}

		data["users"].append(user)

	return json_response(data)


#####################################################
#################     API END     ###################
#####################################################


@app.route('/sign-up/', methods=['POST', 'GET'])
def sign_up():
	if current_user.is_authenticated:
		return redirect(url_for('main_page'))

	if request.method == 'POST':
		username = request.form.get('username')
		email = request.form.get('email')
		password = request.form.get('password')

		user_list = db.session.query(User).filter(
			(User.username == username) | (User.email == email)).all()

		if user_list:
			for user_obj in user_list:
				if user_obj.username == username:
					flash("This nickname is already taken", 'error')
					return redirect(url_for('sign_up'))
				if user_obj.email == email:
					flash("This email is already taken", 'error')
					return redirect(url_for('sign_up'))

		if len(username) and len(password) and len(email):
			status_id = db.session.query(Status).filter(Status.name == "user").first().status_id

			user = User(
				username=username,
				email=email,
				status_id=status_id,
				used_space=0)

			user.set_password(password)

			db.session.add(user)
			db.session.commit()

			return redirect(url_for('sign_in'))

		flash("Invalid username/email/password", 'error')
		return redirect(url_for('sign_up'))

	font = url_for('static', filename='font/rawline-500-cirylic.woff2')
	return render_template('registration.html', font=font)


@app.route('/sign-in/', methods=['GET'])
def sign_in():
	if current_user.is_authenticated:
		return redirect(url_for('main_page'))

	font = url_for('static', filename='font/rawline-500-cirylic.woff2')
	base64 = url_for('static', filename='packages/base64.js')

	return render_template('login.html', font=font, base64=base64)


@app.route("/", methods=['GET'])
@login_required
def main_page():
	font = url_for('static', filename='font/rawline-500-cirylic.woff2')

	return render_template("upload.html", font=font)


@app.route('/uploads/', methods=['GET'])
@login_required
def list_uploads_page():
	font = url_for('static', filename='font/rawline-500-cirylic.woff2')
	file_icon = url_for('static', filename='img/file_icon.png')

	return render_template(
		"uploads.html",
		font=font,
		file_icon=file_icon)


@app.route('/exit/')
@login_required
def exit():
	logout_user()
	flash("You have been logged out.")

	return redirect(url_for('sign_in'))


db.create_all()
fill_status_defaults()  # заполнение таблицы статусов
add_admin(ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD)  # создание профиля админа

if __name__ == "__main__":
	import additional_pages
	
	app.run()
