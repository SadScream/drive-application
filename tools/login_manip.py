import os
from flask_login import LoginManager, login_user
from sqlalchemy import exc

from .database import db, User

login_manager = LoginManager()

UPLOAD_FOLDER = "uploads"
SMALL_IMAGE_FOLDER = "uploads_small"


@login_manager.user_loader
def load_user(user_id):
	try:
		return db.session.query(User).get(user_id)
	except exc.OperationalError:
		return db.session.query(User).get(user_id)


def login_and_create_folder(user_obj, remember):
	'''
	:param user_obj: пользователь
	:type user_obj: `tools.database.User`
	:remember: сохранить ли сессию после закрытия браузера
	:type remember: `bool`
	'''

	login_user(user_obj, remember=remember)

	user_id = user_obj.user_id
	user_default_folder = os.path.join(UPLOAD_FOLDER, str(user_id))

	if not os.path.exists(user_default_folder):
		# если для юзера еще не создана папка загрузок то создаем ее

		user_default_small_folder = os.path.join(SMALL_IMAGE_FOLDER, str(user_id))

		os.mkdir(user_default_folder)
		os.mkdir(user_default_small_folder)

		user_obj.default_folder = user_default_folder
		user_obj.default_small_folder = user_default_small_folder

		db.session.commit()
