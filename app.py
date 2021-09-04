# -*- coding: utf-8 -*-

import jinja2
from flask import Flask, url_for, Response

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
	additional_page = None

app = Flask(APPNAME)

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://{USERNAME}:{PASSWORD}@{HOST}/{DB_NAME}'
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True

app.register_blueprint(login_page)
app.register_blueprint(file_page)

if additional_page:
	app.register_blueprint(additional_page)
	
app.register_blueprint(file_api, url_prefix="/api")
app.register_blueprint(user_api, url_prefix="/api")

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login_page.sign_in'  # куда идет перенаправление для логина

templateLoader = jinja2.FileSystemLoader(searchpath="./static/styles")  # обработчик для собственных jinja шаблонов

templateEnv = jinja2.Environment(loader=templateLoader)
templateEnv.globals.update(url_for=url_for)  # добавляем функцию url_for в среду jinja


@app.route("/static/styles/<file>")
def css_render(file):
	template = templateEnv.get_template(file)
	headers = {
		"Content-Type": "text/css; charset=utf-8"
	}
	response = Response(template.render(), status=200, headers=headers)
	return response


if __name__ == "__main__":
	with app.app_context():
		db.create_all()

		fill_status_defaults()  # заполнение таблицы статусов
		add_admin(ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD)  # создание профиля админа

	app.run()
