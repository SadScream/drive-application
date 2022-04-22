from flask import Blueprint, request
from flask_login import login_required, current_user, logout_user

from tools.json_manip import json_response
from tools.login_manip import login_and_create_folder
from database.database import (
	db, Status, User
)

user_api = Blueprint('user_api', __name__)


@user_api.route('/login/', methods=['GET'])
def login():
	'''
	BasicAuth метод авторизации

	-> HEADERS:
		Authorization: Basic <username:password>  *BASE64*
	:return: {
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


@user_api.route('/logout/')
@login_required
def logout():
	'''
	Выход из учетной записи

	:return: {
		"ok": bool
	}
	'''

	logout_user()
	return json_response({"ok": True})


@user_api.route('/users/<int:user_id>', methods=['GET'])
@login_required
def get_user_info(user_id):
	'''
	Возвращает информацию о пользователе с данным id

	-> user_id:int
	:return: {
		"ok": bool,
		"id": int,
		"username": str,
		"used_space": float,
		"space": int,
		"is_current": bool
	}
	'''
	user_obj = db.session.query(User).filter(User.user_id == user_id).first()
	data = {"ok": True}

	if user_obj:
		status_obj = db.session.query(Status).filter(Status.status_id == user_obj.status_id).first()
		
		data["id"] = user_obj.user_id
		data["username"] = user_obj.username
		data["used_space"] = float(user_obj.used_space)
		data["space"] = int(status_obj.available_size)
		data["is_current"] = current_user.user_id == user_obj.user_id

		return json_response(data)

	data["ok"] = False
	data["message"] = "User doesn't exist"

	return json_response(data, 404)


@user_api.route('/users/', methods=['GET'])
@login_required
def get_users():
	'''
	Возвращает список пользователей. Если текущий пользователь имеет статус админа
	то возвращается список всех пользователей, а иначе список из одного элемента -
	информации о текущем пользователе

	:return: {
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
