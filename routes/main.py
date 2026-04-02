from io import BytesIO
from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from flask_login import current_user
import requests

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html', user=current_user, config=current_app.config)


@main.route('/translate', methods=['POST'])
def translate():
    data = request.get_json()
    text = data.get('text', '')
    target_lang = data.get('target', 'en')

    google_key = current_app.config.get('GOOGLE_TRANSLATE_KEY', '')

    if google_key:
        try:
            resp = requests.post(
                'https://translation.googleapis.com/language/translate/v2',
                params={'key': google_key},
                json={'q': text, 'target': target_lang}
            )
            result = resp.json()
            translated = result['data']['translations'][0]['translatedText']
            return jsonify({'translated': translated})
        except Exception:
            pass

    # LibreTranslate fallback
    try:
        resp = requests.post(
            'https://libretranslate.de/translate',
            json={'q': text, 'source': 'auto', 'target': target_lang},
            timeout=5
        )
        result = resp.json()
        return jsonify({'translated': result.get('translatedText', text)})
    except Exception:
        return jsonify({'translated': text, 'error': 'Translation unavailable'})


@main.route('/health')
def health():
    return jsonify({'status': 'ok', 'app': 'OmniNexus'})


@main.route('/icon/<int:size>.png')
def pwa_icon(size):
    """Serve dynamically generated PNG icons for PWA manifest."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        m = max(2, size // 16)
        draw.ellipse([m, m, size - m, size - m], fill=(8, 12, 9, 255))
        font_size = int(size * 0.52)
        try:
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size)
        except Exception:
            font = ImageFont.load_default()
        text = 'N'
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((size // 2 - tw // 2, size // 2 - th // 2 - size // 24),
                  text, fill=(0, 255, 136, 255), font=font)
        buf = BytesIO()
        img.save(buf, 'PNG')
        buf.seek(0)
        return send_file(buf, mimetype='image/png',
                         max_age=86400,
                         download_name=f'icon-{size}.png')
    except ImportError:
        from flask import abort
        abort(404)
