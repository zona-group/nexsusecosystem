import os
import logging
import re
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_babel import Babel
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = SQLAlchemy()
login_manager = LoginManager()
babel = Babel()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Log DB URL (password masked) for debugging
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    masked = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', db_url)
    logger.info(f"[OmniNexus] DB: {masked}")

    db.init_app(app)
    login_manager.init_app(app)
    babel.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    from routes.main import main as main_bp
    from routes.auth import auth as auth_bp
    from routes.news import news as news_bp
    from routes.comments import comments as comments_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(news_bp, url_prefix='/news')
    app.register_blueprint(comments_bp, url_prefix='/comments')

    with app.app_context():
        try:
            db.create_all()
            logger.info("[OmniNexus] DB tables OK.")
        except Exception as e:
            logger.error(f"[OmniNexus] DB init error: {e}")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
