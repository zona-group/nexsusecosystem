import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'omninexus-secret-key-change-in-production'

    # MySQL - GoDaddy cPanel bilgilerini buraya gir
    MYSQL_HOST     = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER     = os.environ.get('MYSQL_USER', 'your_db_user')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'your_db_password')
    MYSQL_DB       = os.environ.get('MYSQL_DB', 'omninexus')

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # NewsAPI — https://newsapi.org ücretsiz hesap aç, API key al
    NEWS_API_KEY = os.environ.get('NEWS_API_KEY', 'YOUR_NEWSAPI_KEY_HERE')
    NEWS_CACHE_MINUTES = 15  # Her 15 dakikada bir haberleri yenile

    # Google Translate API (opsiyonel - ücretsiz kota var)
    GOOGLE_TRANSLATE_KEY = os.environ.get('GOOGLE_TRANSLATE_KEY', '')

    # Desteklenen diller
    LANGUAGES = ['en', 'tr', 'de', 'ja', 'fr', 'es']
    BABEL_DEFAULT_LOCALE = 'en'
