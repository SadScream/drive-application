from flask import (
	Blueprint, request, render_template,
	url_for, redirect, flash
)
from flask_login import login_required, current_user, logout_user

from tools.database import (
	db, Status, User
)

login_page = Blueprint('login_page', __name__, template_folder="templates", static_folder="static", static_url_path='/login')


@login_page.route('/sign-up/', methods=['POST', 'GET'])
def sign_up():
	if current_user.is_authenticated:
		return redirect(url_for('file_page.upload_page'))

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
					return redirect(url_for('.sign_up'))
				if user_obj.email == email:
					flash("This email is already taken", 'error')
					return redirect(url_for('.sign_up'))

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

			flash("Registered successfully. Please, login", 'success')
			return redirect(url_for('.sign_in'))

		flash("Invalid username/email/password", 'error')
		return redirect(url_for('.sign_up'))

	font = url_for('static', filename='font/rawline-500-cirylic.woff2')
	return render_template('registration.html', font=font)


@login_page.route('/sign-in/', methods=['GET'])
def sign_in():
	if current_user.is_authenticated:
		return redirect(url_for('file_page.upload_page'))

	font = url_for('static', filename='font/rawline-500-cirylic.woff2')
	base64 = url_for('static', filename='packages/base64.js')

	return render_template('login.html', font=font, base64=base64)


@login_page.route('/logout/')
@login_required
def logout():
	logout_user()
	flash("You have been logged out.")

	return redirect(url_for('.sign_in'))