import os

from pathvalidate import is_valid_filename
from flask import Blueprint, request, safe_join
from flask_login import login_required, current_user

from tools.file_manip import get_save_file, update_file_info
from tools.app_manip import json_response
from tools.database import (
	db, File, Status
)

file_api = Blueprint('file_api', __name__)


@file_api.route('/uploads/', methods=['POST'])
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


@file_api.route('/uploads/', methods=['GET'])
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


@file_api.route('/uploads/<string:filename>', methods=['PUT'])
@login_required
def put_file(filename):
	'''
	Принимает имя файла в URI и json объект в теле запроса с новым именем, на которое нужно поменять

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


@file_api.route('/uploads/<string:filename>', methods=['DELETE'])
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


@file_api.route('/uploads/<string:filename>/', methods=['GET'])
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

		return json_response(data, 404)
