from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
import re

auth = Blueprint('auth', __name__)

def valid_email(email):
    return re.match(r'^[^@]+@[^@]+\.[^@]+$', email)

@auth.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username','').strip()
        email    = data.get('email','').strip().lower()
        password = data.get('password','')

        error = None
        if not username or len(username) < 3:
            error = 'Username must be at least 3 characters.'
        elif not valid_email(email):
            error = 'Invalid email address.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        elif User.query.filter_by(username=username).first():
            error = 'Username already taken.'
        elif User.query.filter_by(email=email).first():
            error = 'Email already registered.'

        if error:
            if request.is_json:
                return jsonify({'success': False, 'error': error}), 400
            flash(error, 'danger')
            return render_template('auth.html', mode='register')

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        if request.is_json:
            return jsonify({'success': True, 'username': user.username})
        return redirect(url_for('main.index'))

    return render_template('auth.html', mode='register')


@auth.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        data     = request.get_json() if request.is_json else request.form
        email    = data.get('email','').strip().lower()
        password = data.get('password','')
        remember = data.get('remember', False)

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            error = 'Invalid email or password.'
            if request.is_json:
                return jsonify({'success': False, 'error': error}), 401
            flash(error, 'danger')
            return render_template('auth.html', mode='login')

        login_user(user, remember=bool(remember))
        if request.is_json:
            return jsonify({'success': True, 'username': user.username, 'role': user.role})
        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.index'))

    return render_template('auth.html', mode='login')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@auth.route('/me')
def me():
    if current_user.is_authenticated:
        return jsonify({
            'logged_in': True,
            'id':        current_user.id,
            'username':  current_user.username,
            'email':     current_user.email,
            'role':      current_user.role,
            'avatar':    current_user.avatar,
        })
    return jsonify({'logged_in': False})
