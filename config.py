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
    GOOGLE_CLIENT_ID     = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    MAIL_SERVER   = os.environ.get('MAIL_SERVER',   'smtp.gmail.com')
    MAIL_PORT     = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS  = os.environ.get('MAIL_USE_TLS',  'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@omninexsus.com')
    SITE_URL      = os.environ.get('SITE_URL', 'https://www.omninexsus.com')
    VAPID_PUBLIC_KEY  = os.environ.get('VAPID_PUBLIC_KEY',  'BFpiirOZsoMKpDenm9Lr8rqLmWms4vc3IrjRO8KSj1AUCqpDFrFjbCh0AGp92mnKKy_R2YJIe-kbaCj7AMFhwSA')
    VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '0PS0l-BioW2ILRUkqYH70nms1imBikOmrdKHqhDvL10')
    VAPID_CLAIMS      = {'sub': 'mailto:' + os.environ.get('MAIL_USERNAME', 'admin@omninexsus.com')}
    LANGUAGES = ['en', 'tr', 'de', 'ja', 'fr', 'es']
    BABEL_DEFAULT_LOCALE = os.environ.get('BABEL_DEFAULT_LOCALE', 'tr')
