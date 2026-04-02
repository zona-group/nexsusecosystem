from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash, current_app
from flask_login import login_required, current_user
from flask_mail import Message
from app import db, mail
from models import User, Comment, PushSubscription

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Bu sayfaya erisiminiz yok.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return login_required(decorated)


@admin_bp.route('/')
@admin_required
def dashboard():
    total_users    = User.query.count()
    active_users   = User.query.filter_by(is_active=True).count()
    pending_users  = User.query.filter_by(is_active=False).count()
    admin_users    = User.query.filter_by(role='admin').count()
    total_comments = Comment.query.filter_by(is_deleted=False).count()
    push_subs      = PushSubscription.query.count()
    recent_users   = User.query.order_by(User.created_at.desc()).limit(10).all()
    return render_template('admin/dashboard.html',
        total_users=total_users, active_users=active_users,
        pending_users=pending_users, admin_users=admin_users,
        total_comments=total_comments, push_subs=push_subs,
        recent_users=recent_users)


@admin_bp.route('/users')
@admin_required
def users():
    page  = request.args.get('page', 1, type=int)
    q     = request.args.get('q', '').strip()
    query = User.query
    if q:
        query = query.filter(User.username.ilike(f'%{q}%') | User.email.ilike(f'%{q}%'))
    users_page = query.order_by(User.created_at.desc()).paginate(page=page, per_page=25)
    return render_template('admin/users.html', users_page=users_page, q=q)


@admin_bp.route('/users/<int:user_id>/role', methods=['POST'])
@admin_required
def set_role(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'success': False, 'error': 'Kendi rolunuzu degistiremezsiniz.'}), 400
    role = (request.get_json(silent=True) or {}).get('role', 'user')
    if role not in ('user', 'admin'):
        return jsonify({'success': False, 'error': 'Gecersiz rol.'}), 400
    user.role = role
    db.session.commit()
    return jsonify({'success': True, 'username': user.username, 'role': user.role})


@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@admin_required
def toggle_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'success': False, 'error': 'Kendi hesabinizi pasiflestiremezsiniz.'}), 400
    user.is_active = not user.is_active
    db.session.commit()
    status = 'aktif' if user.is_active else 'pasif'
    return jsonify({'success': True, 'username': user.username, 'is_active': user.is_active,
                    'message': f'{user.username} {status} yapildi.'})


@admin_bp.route('/users/<int:user_id>/activate', methods=['POST'])
@admin_required
def activate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = True
    user.email_verified = True
    user.verification_token = None
    db.session.commit()
    return jsonify({'success': True, 'message': f'{user.username} aktif edildi.'})


@admin_bp.route('/notify', methods=['POST'])
@admin_required
def send_notification():
    data  = request.get_json(silent=True) or {}
    title = data.get('title', 'OmniNexus').strip()
    body  = data.get('body', '').strip()
    url   = data.get('url', '/')
    if not body:
        return jsonify({'success': False, 'error': 'Bildirim metni gerekli.'}), 400
    subs = PushSubscription.query.all()
    sent, failed = 0, 0
    try:
        from pywebpush import webpush, WebPushException
        import json
        vapid_private = current_app.config['VAPID_PRIVATE_KEY']
        vapid_claims  = current_app.config['VAPID_CLAIMS']
        for sub in subs:
            try:
                webpush(
                    subscription_info={'endpoint': sub.endpoint, 'keys': {'p256dh': sub.p256dh, 'auth': sub.auth}},
                    data=json.dumps({'title': title, 'body': body, 'url': url}),
                    vapid_private_key=vapid_private, vapid_claims=vapid_claims
                )
                sent += 1
            except WebPushException as e:
                if '410' in str(e) or '404' in str(e):
                    db.session.delete(sub)
                failed += 1
        db.session.commit()
    except ImportError:
        return jsonify({'success': False, 'error': 'pywebpush modulu yuklu degil.'}), 500
    return jsonify({'success': True, 'sent': sent, 'failed': failed,
                    'message': f'{sent} aboneye bildirim gonderildi.'})


@admin_bp.route('/mail-test', methods=['POST'])
@admin_required
def mail_test():
    try:
        msg = Message(subject='OmniNexus - Mail Test', recipients=[current_user.email],
                      body='OmniNexus mail sistemi calisiyor!')
        mail.send(msg)
        return jsonify({'success': True, 'message': f'Test maili {current_user.email} adresine gonderildi.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
