import json
from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user
from app import db
from models import PushSubscription

push_bp = Blueprint('push', __name__)


@push_bp.route('/vapid-public-key')
def vapid_public_key():
    return jsonify({'publicKey': current_app.config.get('VAPID_PUBLIC_KEY', '')})


@push_bp.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.get_json(silent=True)
    if not data or 'endpoint' not in data:
        return jsonify({'success': False, 'error': 'Gecersiz abonelik verisi.'}), 400
    endpoint = data.get('endpoint')
    keys     = data.get('keys', {})
    p256dh   = keys.get('p256dh', '')
    auth     = keys.get('auth', '')
    if not endpoint or not p256dh or not auth:
        return jsonify({'success': False, 'error': 'Eksik abonelik alanlari.'}), 400
    existing = PushSubscription.query.filter_by(endpoint=endpoint).first()
    if existing:
        existing.p256dh  = p256dh
        existing.auth    = auth
        existing.user_id = current_user.id if current_user.is_authenticated else None
    else:
        db.session.add(PushSubscription(
            endpoint=endpoint, p256dh=p256dh, auth=auth,
            user_id=current_user.id if current_user.is_authenticated else None
        ))
    db.session.commit()
    return jsonify({'success': True, 'message': 'Push bildirimleri aktif edildi.'})


@push_bp.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    data = request.get_json(silent=True) or {}
    endpoint = data.get('endpoint')
    if endpoint:
        sub = PushSubscription.query.filter_by(endpoint=endpoint).first()
        if sub:
            db.session.delete(sub)
            db.session.commit()
    return jsonify({'success': True})
