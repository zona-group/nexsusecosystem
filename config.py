import os


def _build_db_url():
    url = os.environ.get('DATABASE_URL', '')
    if url:
        if url.startswith('mysql://'):
            url = url.replace('mysql://', 'mysql+pymysql://', 1)
        return url
    url = os.environ.get('MYSQL_URL', '')
    if url:
        if url.startswith('mysql://'):
            url = url.replace('mysql://', 'mysql+pymysql://', 1)
        return url
    host     = (os.environ.get('MYSQLHOST')     or os.environ.get('MYSQL_HOST',     'localhost'))
    user     = (os.environ.get('MYSQLUSER')     or os.environ.get('MYSQL_USER',     'root'))
    password = (os.environ.get('MYSQLPASSWORD') or os.environ.get('MYSQL_PASSWORD', ''))
    database = (os.environ.get('MYSQLDATABASE') or os.environ.get('MYSQL_DB',       'railway'))
    port     = (os.environ.get('MYSQLPORT')     or os.environ.get('MYSQL_PORT',     '3306'))
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'omninexus-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = _build_db_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 280,
        'connect_args': {'connect_timeout': 10},
    }
    NEWS_API_KEY = os.environ.get('NEWS_API_KEY', 'YOUR_NEWSAPI_KEY_HERE')
    NEWS_CACHE_MINUTES = 15
    GOOGLE_TRANSLATE_KEY = os.environ.get('GOOGLE_TRANSLATE_KEY', '')
    LANGUAGES = ['en', 'tr', 'de', 'ja', 'fr', 'es']
    BABEL_DEFAULT_LOCALE = os.environ.get('BABEL_DEFAULT_LOCALE', 'tr')
