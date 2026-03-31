from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
import requests, hashlib, json, os

news = Blueprint('news', __name__)

_cache = {}

CATEGORIES = {
    'gaming':    'gaming OR "video games" OR PlayStation OR Xbox OR Nintendo OR Steam',
    'ai':        'artificial intelligence OR "machine learning" OR ChatGPT OR OpenAI OR Claude AI',
    'tech':      'technology OR Apple OR Google OR Microsoft OR NVIDIA OR semiconductor',
    'arduino':   'Arduino OR "Raspberry Pi" OR IoT OR "maker project" OR microcontroller',
}

def get_news(category='tech', lang='en', page=1):
    cache_key = f"{category}_{lang}_{page}"
    now = datetime.utcnow()

    if cache_key in _cache:
        cached_time, cached_data = _cache[cache_key]
        ttl = current_app.config.get('NEWS_CACHE_MINUTES', 15)
        if now - cached_time < timedelta(minutes=ttl):
            return cached_data

    api_key = current_app.config.get('NEWS_API_KEY', '')
    if not api_key or api_key == 'YOUR_NEWSAPI_KEY_HERE':
        return _mock_news(category)

    query = CATEGORIES.get(category, category)
    url = 'https://newsapi.org/v2/everything'
    params = {
        'q':        query,
        'language': lang if lang in ['en','de','fr','es'] else 'en',
        'sortBy':   'publishedAt',
        'pageSize': 12,
        'page':     page,
        'apiKey':   api_key,
    }

    try:
        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        articles = _format_articles(data.get('articles', []), category)
        _cache[cache_key] = (now, articles)
        return articles
    except Exception as e:
        current_app.logger.error(f"NewsAPI error: {e}")
        return _mock_news(category)


def _format_articles(articles, category):
    result = []
    for a in articles:
        if not a.get('title') or a['title'] == '[Removed]':
            continue
        article_id = hashlib.md5(a.get('url','').encode()).hexdigest()
        result.append({
            'id':          article_id,
            'title':       a.get('title',''),
            'description': a.get('description',''),
            'url':         a.get('url',''),
            'image':       a.get('urlToImage',''),
            'source':      a.get('source',{}).get('name',''),
            'published':   a.get('publishedAt',''),
            'category':    category,
        })
    return result


def _mock_news(category):
    mock = {
        'gaming': [
            {'id':'g1','title':'GTA VI Release Window Officially Confirmed','description':'Rockstar reveals firm launch date with explosive new footage.','url':'#','image':'','source':'IGN','published':'2025-03-31T10:00:00Z','category':'gaming'},
            {'id':'g2','title':'Steam Hits 40 Million Concurrent Users Record','description':'Valve platform shatters records driven by massive launches.','url':'#','image':'','source':'PC Gamer','published':'2025-03-31T08:00:00Z','category':'gaming'},
            {'id':'g3','title':'PS5 Pro vs Xbox Series X — 2025 Definitive Comparison','description':'Which console wins the performance crown this generation?','url':'#','image':'','source':'Digital Foundry','published':'2025-03-30T14:00:00Z','category':'gaming'},
        ],
        'ai': [
            {'id':'a1','title':'GPT-5 Multimodal Breaks All Benchmarks','description':'OpenAI model scores unprecedented results across vision, code and reasoning.','url':'#','image':'','source':'The Verge','published':'2025-03-31T09:00:00Z','category':'ai'},
            {'id':'a2','title':'Claude 4 Tops Enterprise AI Adoption Charts Worldwide','description':'Anthropic model overtakes competitors in B2B deployments globally.','url':'#','image':'','source':'VentureBeat','published':'2025-03-31T07:00:00Z','category':'ai'},
            {'id':'a3','title':'Google Gemini Ultra 2 Scores Human-Level on MMLU','description':'DeepMind achieves landmark milestone in general intelligence benchmarks.','url':'#','image':'','source':'TechCrunch','published':'2025-03-30T12:00:00Z','category':'ai'},
        ],
        'tech': [
            {'id':'t1','title':'Apple M4 Ultra Benchmarks Leak — Destroys Every Record','description':'2x performance leap over M3 Ultra with 40% lower power draw.','url':'#','image':'','source':'MacRumors','published':'2025-03-31T06:00:00Z','category':'tech'},
            {'id':'t2','title':'NVIDIA Blackwell Ultra 1000W TDP Monster Enters Testing','description':'Engineering samples of GB202 confirm extreme performance targets.','url':'#','image':'','source':'AnandTech','published':'2025-03-30T16:00:00Z','category':'tech'},
        ],
        'arduino': [
            {'id':'ar1','title':'Arduino Nano ESP32 Complete IoT Dashboard Guide 2025','description':'Build Wi-Fi sensor dashboard with MQTT in under 2 hours.','url':'#','image':'','source':'Hackster.io','published':'2025-03-31T05:00:00Z','category':'arduino'},
            {'id':'ar2','title':'Arduino Uno R4 WiFi Sells Out Globally Within 48 Hours','description':'Demand far exceeds supply as maker community adopts new platform.','url':'#','image':'','source':'Arduino Blog','published':'2025-03-30T10:00:00Z','category':'arduino'},
        ],
    }
    return mock.get(category, mock['tech'])


@news.route('/api/news')
def api_news():
    category = request.args.get('cat', 'tech')
    lang     = request.args.get('lang', 'en')
    page     = int(request.args.get('page', 1))
    articles = get_news(category, lang, page)
    return jsonify({'articles': articles, 'category': category})


@news.route('/api/news/all')
def api_news_all():
    lang = request.args.get('lang', 'en')
    all_articles = []
    for cat in CATEGORIES:
        articles = get_news(cat, lang, 1)
        all_articles.extend(articles[:3])
    all_articles.sort(key=lambda x: x.get('published',''), reverse=True)
    return jsonify({'articles': all_articles})
