from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()


class Status(db.Model):
	__tablename__ = 'status'
	status_id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100))
	available_size = db.Column(db.Integer)  # kilobytes

	def __init__(self, name, available_size):
		self.name = name
		self.available_size = available_size

	def __repr__(self):
		return "<{0}: {1}>".format(self.status_id, self.name)


class User(db.Model, UserMixin):
	__tablename__ = 'user'
	user_id = db.Column(db.Integer, primary_key=True, autoincrement='ignore_fk')
	username = db.Column(db.String(36), nullable=False, unique=True)
	email = db.Column(db.String(100), nullable=False, unique=True)
	password_hash = db.Column(db.String(256), nullable=False)
	status_id = db.Column(db.Integer, db.ForeignKey("status.status_id"))
	used_space = db.Column(db.Numeric(10, 2))  # kilobytes
	default_folder = db.Column(db.String(72), unique=True)
	default_small_folder = db.Column(db.String(80), unique=True)

	def __repr__(self):
		return "<{0}: {1}>".format(self.user_id, self.username)

	def get_default_folder(self):
		return self.default_folder

	def get_default_small_folder(self):
		return self.default_small_folder

	def set_default_folder(self, folder):
		self.default_folder = folder

	def set_default_small_folder(self, folder):
		self.default_small_folder = folder

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

	def get_id(self):
		return self.user_id


class File(db.Model):
	__tablename__ = 'file'
	file_id = db.Column(db.Integer, primary_key=True, autoincrement='ignore_fk')
	filename = db.Column(db.String(65), nullable=False)
	size = db.Column(db.Numeric(10, 2))  # kilobytes
	# owner_id = db.Column(db.Integer, db.ForeignKey("user.user_id"))
	owner_id = db.Column(
		db.Integer,
		db.ForeignKey("user.user_id",
		ondelete='CASCADE'),
	)
	_type = db.Column("type", db.String(128), nullable=False)
	url = db.Column(db.String(128), nullable=False)
	small_url = db.Column(db.String(136))
	width = db.Column(db.Integer)
	height = db.Column(db.Integer)

	def __init__(self, filename, size,
				owner_id, _type, url,
				small_url=None, width=None, height=None):
		self.filename = filename
		self.size = size
		self.owner_id = owner_id
		self._type = _type
		self.url = url
		self.small_url = small_url
		self.width = width
		self.height = height

	def __repr__(self):
		return "<{0}: {1}>".format(self.file_id, self.filename)

	def set_small_url(self, url):
		self.small_url = url

	def set_width(self, width):
		self.width = width

	def set_height(self, height):
		self.height = height


def fill_status_defaults():
	default_status_list = [
		Status("banned", 0),
		Status("user", 64 * 1024),
		Status("admin", 128 * 1024)]
	status_list = Status.query.all()

	if (len(status_list) != len(default_status_list)):
		for s in status_list:
			db.session.delete(s)
	else:
		return

	for s in default_status_list:
		db.session.add(s)

	db.session.commit()


def add_admin(username, email, password):
	search_admin = db.session.query(User).filter(User.username == username).first()

	if search_admin:
		return

	admin = User(
		username=username,
		email=email,
		status_id=db.session.query(Status).filter(Status.name == "admin").first().status_id,
		used_space=0)
	admin.set_password(password)
	db.session.add(admin)
	db.session.commit()
