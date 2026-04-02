from flask import Blueprint, jsonify, request, current_app, Response
from flask_login import login_required, current_user
from app import db
from models import SavedArticle
import requests
import hashlib
import time

news = Blueprint('news', __name__)

_cache = {}

# Language code → NewsAPI country code
LANG_TO_COUNTRY = {
    'en': 'us',
    'tr': 'tr',
    'de': 'de',
    'fr': 'fr',
    'es': 'mx',
    'ja': 'jp',
    'ar': 'ae',
    'pt': 'br',
    'ru': 'ru',
    'zh': 'cn',
}

# Category fallback images (Unsplash topic-based)
CATEGORY_IMAGES = {
    'general':       'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600&q=80',
    'technology':    'https://images.unsplash.com/photo-1518770660439-4636190af475?w=600&q=80',
    'business':      'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=600&q=80',
    'science':       'https://images.unsplash.com/photo-1532094349884-543559be69d2?w=600&q=80',
    'health':        'https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=600&q=80',
    'sports':        'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=600&q=80',
    'entertainment': 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=600&q=80',
}


def _cache_get(key):
    entry = _cache.get(key)
    if entry:
        ts, data = entry
        ttl = current_app.config.get('NEWS_CACHE_MINUTES', 15) * 60
        if time.time() - ts < ttl:
            return data
    return None


def _cache_set(key, data):
    _cache[key] = (time.time(), data)


def fetch_news(category='general', country='us', page_size=20, page=1):
    cache_key = f'{category}_{country}_{page}'
    cached = _cache_get(cache_key)
    if cached:
        return cached

    api_key = current_app.config.get('NEWS_API_KEY', '')
    if not api_key or api_key == 'YOUR_NEWSAPI_KEY_HERE':
        return {'articles': [], 'error': 'NewsAPI key not configured'}

    params = {
        'apiKey': api_key,
        'category': category,
        'country': country,
        'pageSize': page_size,
        'page': page,
    }
    try:
        resp = requests.get('https://newsapi.org/v2/top-headlines', params=params, timeout=10)
        data = resp.json()
        if data.get('status') == 'ok':
            articles = data.get('articles', [])
            fallback = CATEGORY_IMAGES.get(category, CATEGORY_IMAGES['general'])
            for a in articles:
                url = a.get('url', '')
                a['id'] = hashlib.md5(url.encode()).hexdigest()
                # Fill in fallback image if missing
                if not a.get('urlToImage'):
                    a['urlToImage'] = fallback
            result = {'articles': articles, 'totalResults': data.get('totalResults', 0)}
            _cache_set(cache_key, result)
            return result
        return {'articles': [], 'error': data.get('message', 'API error')}
    except Exception as e:
        return {'articles': [], 'error': str(e)}


@news.route('/')
def index():
    category = request.args.get('category', 'general')
    country  = request.args.get('country', 'us')
    page     = int(request.args.get('page', 1))
    return jsonify(fetch_news(category, country, page=page))


@news.route('/imgproxy')
def img_proxy():
    """Proxy news images to avoid CORS/hotlink issues on mobile."""
    url = request.args.get('url', '')
    if not url or not url.startswith('http'):
        return '', 400
    try:
        r = requests.get(url, timeout=8, stream=True,
                         headers={'User-Agent': 'Mozilla/5.0'})
        ct = r.headers.get('Content-Type', 'image/jpeg')
        return Response(r.content, content_type=ct,
                        headers={'Cache-Control': 'public, max-age=86400'})
    except Exception:
        return '', 502


@news.route('/search')
def search():
    q = request.args.get('q', '')
    if not q:
        return jsonify({'articles': [], 'error': 'Query required'})

    api_key = current_app.config.get('NEWS_API_KEY', '')
    if not api_key or api_key == 'YOUR_NEWSAPI_KEY_HERE':
        return jsonify({'articles': [], 'error': 'NewsAPI key not configured'})

    cached = _cache_get(f'search_{q}')
    if cached:
        return jsonify(cached)

    try:
        resp = requests.get(
            'https://newsapi.org/v2/everything',
            params={'apiKey': api_key, 'q': q, 'sortBy': 'publishedAt', 'pageSize': 20},
            timeout=10
        )
        data = resp.json()
        articles = data.get('articles', [])
        for a in articles:
            a['id'] = hashlib.md5(a.get('url', '').encode()).hexdigest()
        result = {'articles': articles}
        _cache_set(f'search_{q}', result)
        return jsonify(result)
    except Exception as e:
        return jsonify({'articles': [], 'error': str(e)})


@news.route('/save', methods=['POST'])
@login_required
def save_article():
    data = request.get_json() or {}
    article_id = data.get('article_id')
    if not article_id:
        return jsonify({'success': False, 'error': 'article_id required'}), 400

    existing = SavedArticle.query.filter_by(
        user_id=current_user.id, article_id=article_id
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'success': True, 'saved': False})

    saved = SavedArticle(
        user_id=current_user.id,
        article_id=article_id,
        title=data.get('title', ''),
        url=data.get('url', ''),
        image=data.get('image', ''),
        source=data.get('source', '')
    )
    db.session.add(saved)
    db.session.commit()
    return jsonify({'success': True, 'saved': True})


@news.route('/saved')
@login_required
def saved_articles():
    articles = SavedArticle.query.filter_by(user_id=current_user.id)\
        .order_by(SavedArticle.saved_at.desc()).all()
    return jsonify({'articles': [
        {
            'id': a.article_id,
            'title': a.title,
            'url': a.url,
            'image': a.image,
            'source': a.source,
            'saved_at': a.saved_at.isoformat()
        } for a in articles
    ]})
