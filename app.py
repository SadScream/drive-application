# -*- coding: utf-8 -*-

import os

from flask import Flask

from tools.login_manip import login_manager
from tools.database import db, fill_status_defaults, add_admin
from db_config import (
	USERNAME, PASSWORD, HOST, DB_NAME, 
	SECRET_KEY, APPNAME, ADMIN_USERNAME, ADMIN_EMAIL, 
	ADMIN_PASSWORD
)

from api.file_methods import file_api
from api.user_methods import user_api

from pages.login.login import login_page
from pages.file.file import file_page

try:
	from pages.additional.additional import additional_page
except ModuleNotFoundError:
	pass

app = Flask(APPNAME)

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://{USERNAME}:{PASSWORD}@{HOST}/{DB_NAME}'
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True

app.register_blueprint(login_page)
app.register_blueprint(file_page)
app.register_blueprint(additional_page)
app.register_blueprint(file_api, url_prefix="/api")
app.register_blueprint(user_api, url_prefix="/api")

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login_page.sign_in'  # куда идет перенаправление для логина

# STATIC_FOLDER = os.path.join(app.root_path, "static")

if __name__ == "__main__":
	with app.app_context():
		db.create_all()

		fill_status_defaults()  # заполнение таблицы статусов
		add_admin(ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD)  # создание профиля админа

	app.run()
