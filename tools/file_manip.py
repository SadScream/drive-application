import os
import mimetypes
from flask import safe_join

from .database import File, db
from .image_manip import resize_image


SMALL_IMAGE_SIZE = (310, 320)


def mimetype(s):
	return mimetypes.guess_type(s)[0] or "application/octet-stream"


def get_save_file(file, file_size, user_folder, filename, current_user):
	# сохранить файл на диске и создать экземпляр объекта "файл"

	pth = os.path.join(user_folder, filename)
	file_owner_id = current_user.user_id
	file_type = mimetype(pth)
	file_url = safe_join("/uploads/", filename) + "?download=1"

	file.save(pth)
	current_user.used_space = int(current_user.used_space) + file_size

	file_obj = File(filename, file_size, file_owner_id, file_type, file_url)

	if "image" in file_type:
		user_small_folder = current_user.default_small_folder
		file_small_folder = os.path.join(user_small_folder, filename)

		file_width, file_height = resize_image(
			pth, file_small_folder, SMALL_IMAGE_SIZE)

		file_obj.set_small_url(
			safe_join("/uploads/", filename) + "?small=1&download=1")
		file_obj.set_width(file_width)
		file_obj.set_height(file_height)

	return file_obj


def update_file_info(file, file_size, user_folder, filename, current_user):
	file_obj = db.session.query(File).filter(
		File.filename == filename, File.owner_id == current_user.get_id()).first()

	# отнимаем предыдущий размер файла от
	# использованного пространства и прибавляем новый
	new_space = int(current_user.used_space) - int(file_obj.size)
	current_user.used_space = new_space + file_size

	pth = os.path.join(user_folder, filename)
	file.save(pth)

	file_obj.size = file_size
	file_obj._type = mimetype(pth)
	file_obj.url = safe_join("/uploads/", filename) + "?download=1"

	if "image" in file_obj._type:
		user_small_folder = current_user.default_small_folder
		file_small_url = os.path.join(user_small_folder, filename)

		file_width, file_height = resize_image(
			pth, file_small_url, SMALL_IMAGE_SIZE)

		file_obj.set_small_url(safe_join("/uploads/", filename) + "?small=1&download=1")
		file_obj.set_width(file_width)
		file_obj.set_height(file_height)
