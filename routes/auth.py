import re
import secrets
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from app import db, oauth, mail
from models import User

auth = Blueprint('auth', __name__)


def _send_verification_email(user):
    try:
        site_url = current_app.config.get('SITE_URL', 'https://www.omninexsus.com')
        verify_url = f"{site_url}/auth/verify/{user.verification_token}"
        msg = Message(
            subject='OmniNexus - E-posta Dogrulamasi',
            recipients=[user.email],
            html=f"""<html><body style="font-family:Arial;background:#0f172a;padding:20px;">
<div style="max-width:500px;margin:0 auto;background:#1e293b;border-radius:12px;padding:32px;">
<h1 style="color:#818cf8;">OmniNexus</h1>
<h2 style="color:#e2e8f0;">Hosgeldiniz, {user.username}!</h2>
<p style="color:#94a3b8;">Hesabinizi aktiflestirek icin asagidaki butona tiklayin.</p>
<a href="{verify_url}" style="display:inline-block;margin:20px 0;padding:14px 28px;
   background:linear-gradient(135deg,#6366f1,#a855f7);color:white;
   text-decoration:none;border-radius:8px;font-weight:bold;">E-postami Dogrula</a>
<p style="color:#64748b;font-size:12px;margin-top:24px;">Bu link 48 saat gecerlidir.</p>
</div></body></html>"""
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"[Mail] Send failed: {e}")
        return False


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            msg = 'Gecersiz e-posta veya sifre.'
            return jsonify({'success': False, 'error': msg}), 401 if request.is_json else (flash(msg,'error'), render_template('auth/login.html'))[1]
        if not user.is_active:
            msg = 'Hesabiniz dogrulanmamis. Lutfen e-postanizi kontrol edin.'
            return jsonify({'success': False, 'error': msg}), 403 if request.is_json else (flash(msg,'warning'), render_template('auth/login.html'))[1]
        login_user(user, remember=bool(data.get('remember', False)))
        if request.is_json:
            return jsonify({'success': True, 'username': user.username})
        return redirect(url_for('main.index'))
    return render_template('auth/login.html')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        if not username or not email or not password:
            msg = 'Tum alanlar zorunludur.'
            return jsonify({'success': False, 'error': msg}), 400 if request.is_json else (flash(msg,'error'), render_template('auth/register.html'))[1]
        if User.query.filter_by(email=email).first():
            msg = 'Bu e-posta zaten kayitli.'
            return jsonify({'success': False, 'error': msg}), 400 if request.is_json else (flash(msg,'error'), render_template('auth/register.html'))[1]
        if User.query.filter_by(username=username).first():
            msg = 'Bu kullanici adi zaten alinmis.'
            return jsonify({'success': False, 'error': msg}), 400 if request.is_json else (flash(msg,'error'), render_template('auth/register.html'))[1]
        user = User(username=username, email=email, is_active=False, email_verified=False)
        user.set_password(password)
        user.generate_verification_token()
        db.session.add(user)
        db.session.commit()
        mail_ok = bool(current_app.config.get('MAIL_USERNAME'))
        if mail_ok:
            _send_verification_email(user)
            msg = 'Kayit basarili! E-postanizi kontrol edin ve hesabinizi dogrulayin.'
            if request.is_json:
                return jsonify({'success': True, 'username': user.username, 'message': msg, 'needs_verification': True})
            flash(msg, 'success')
            return render_template('auth/register.html')
        user.is_active = True
        user.email_verified = True
        db.session.commit()
        login_user(user)
        if request.is_json:
            return jsonify({'success': True, 'username': user.username})
        return redirect(url_for('main.index'))
    return render_template('auth/register.html')


@auth.route('/verify/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if not user:
        flash('Dogrulama linki gecersiz.', 'error')
        return redirect(url_for('main.index'))
    user.is_active = True
    user.email_verified = True
    user.verification_token = None
    db.session.commit()
    login_user(user)
    flash(f'Hosgeldiniz {user.username}! Hesabiniz dogrulandi.', 'success')
    return redirect(url_for('main.index'))


@auth.route('/resend-verification', methods=['POST'])
def resend_verification():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip().lower()
    user = User.query.filter_by(email=email).first()
    if user and not user.email_verified:
        user.generate_verification_token()
        db.session.commit()
        _send_verification_email(user)
    return jsonify({'success': True, 'message': 'Dogrulama e-postasi gonderildi.'})


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@auth.route('/profile', methods=['GET', 'PUT'])
@login_required
def profile():
    if request.method == 'PUT':
        data = request.get_json(silent=True) or {}
        current_user.bio = data.get('bio', current_user.bio)[:300]
        current_user.avatar = data.get('avatar', current_user.avatar)[:500]
        db.session.commit()
        return jsonify({'success': True})
    return render_template('auth/profile.html', user=current_user)


@auth.route('/google')
def google_login():
    if not current_app.config.get('GOOGLE_CLIENT_ID'):
        flash('Google girisi yapilandirilmamis.', 'error')
        return redirect(url_for('main.index'))
    return oauth.google.authorize_redirect(url_for('auth.google_callback', _external=True))


@auth.route('/google/callback')
def google_callback():
    if not current_app.config.get('GOOGLE_CLIENT_ID'):
        return redirect(url_for('main.index'))
    try:
        token = oauth.google.authorize_access_token()
        userinfo = token.get('userinfo') or oauth.google.userinfo()
    except Exception as e:
        flash(f'Google girisi basarisiz: {e}', 'error')
        return redirect(url_for('main.index'))
    google_id = str(userinfo.get('sub', ''))
    email = (userinfo.get('email') or '').strip().lower()
    name = userinfo.get('name') or email.split('@')[0]
    avatar = userinfo.get('picture') or ''
    if not google_id or not email:
        flash('Google hesap bilgileri alinamadi.', 'error')
        return redirect(url_for('main.index'))
    user = User.query.filter_by(google_id=google_id).first() or User.query.filter_by(email=email).first()
    if user:
        if not user.google_id: user.google_id = google_id
        if avatar and not user.avatar: user.avatar = avatar
        if not user.is_active: user.is_active = True; user.email_verified = True
        db.session.commit()
    else:
        slug = re.sub(r'[^a-zA-Z0-9_]', '', name.replace(' ', '_'))[:32] or 'user'
        username, i = slug, 1
        while User.query.filter_by(username=username).first():
            username = f"{slug}{i}"; i += 1
        user = User(username=username, email=email, google_id=google_id, avatar=avatar, is_active=True, email_verified=True)
        db.session.add(user); db.session.commit()
    login_user(user, remember=True)
    return redirect(url_for('main.index'))
