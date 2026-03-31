from flask import Blueprint, render_template, jsonify, request, current_app, Response
from flask_login import current_user
import requests
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html', user=current_user)

@main.route('/privacy')
def privacy():
    return render_template('privacy.html')

@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/contact')
def contact():
    return render_template('about.html')  # şimdilik about ile aynı

@main.route('/sitemap.xml')
def sitemap():
    pages = [
        ('/', '1.0', 'daily'),
        ('/about', '0.5', 'monthly'),
        ('/privacy', '0.3', 'monthly'),
    ]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for loc, priority, freq in pages:
        xml += f'''  <url>
    <loc>https://omninexus.com{loc}</loc>
    <lastmod>{datetime.utcnow().strftime('%Y-%m-%d')}</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{priority}</priority>
  </url>\n'''
    xml += '</urlset>'
    return Response(xml, mimetype='application/xml')

@main.route('/robots.txt')
def robots():
    txt = "User-agent: *\nAllow: /\nSitemap: https://omninexus.com/sitemap.xml\n"
    return Response(txt, mimetype='text/plain')

@main.route('/article/<article_id>')
def article(article_id):
    return render_template('index.html', article_id=article_id, user=current_user)

@main.route('/api/translate', methods=['POST'])
def translate():
    data   = request.get_json()
    text   = data.get('text','')
    target = data.get('target','en')
    api_key = current_app.config.get('GOOGLE_TRANSLATE_KEY','')

    if not text:
        return jsonify({'translated': ''})

    if api_key:
        try:
            resp = requests.post(
                'https://translation.googleapis.com/language/translate/v2',
                params={'key': api_key},
                json={'q': text, 'target': target, 'format': 'text'},
                timeout=5
            )
            result = resp.json()
            translated = result['data']['translations'][0]['translatedText']
            return jsonify({'translated': translated})
        except Exception as e:
            current_app.logger.error(f"Translate error: {e}")

    try:
        resp = requests.post(
            'https://libretranslate.com/translate',
            json={'q': text, 'source': 'en', 'target': target, 'format': 'text'},
            timeout=8
        )
        result = resp.json()
        return jsonify({'translated': result.get('translatedText', text)})
    except:
        return jsonify({'translated': text, 'error': 'Translation unavailable'})

@main.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'app': 'OmniNexus'})
