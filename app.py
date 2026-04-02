import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_babel import Babel
from flask_mail import Mail
from authlib.integrations.flask_client import OAuth
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db            = SQLAlchemy()
login_manager = LoginManager()
babel         = Babel()
oauth         = OAuth()
mail          = Mail()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    import re
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    masked = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', db_url)
    logger.info(f"[OmniNexus] DB: {masked}")

    db.init_app(app)
    login_manager.init_app(app)
    babel.init_app(app)
    oauth.init_app(app)
    mail.init_app(app)

    login_manager.login_view    = 'auth.login'
    login_manager.login_message = 'Lutfen giris yapin.'

    if app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET'):
        oauth.register(
            name='google',
            client_id=app.config.get('GOOGLE_CLIENT_ID'),
            client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'},
        )
        logger.info("[OmniNexus] Google OAuth configured.")

    from routes.main     import main     as main_bp
    from routes.auth     import auth     as auth_bp
    from routes.news     import news     as news_bp
    from routes.comments import comments as comments_bp
    from routes.admin    import admin_bp
    from routes.push     import push_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp,     url_prefix='/auth')
    app.register_blueprint(news_bp,     url_prefix='/news')
    app.register_blueprint(comments_bp, url_prefix='/comments')
    app.register_blueprint(admin_bp,    url_prefix='/admin')
    app.register_blueprint(push_bp,     url_prefix='/push')

    with app.app_context():
        try:
            db.create_all()
            _safe_migrate(db)
            logger.info("[OmniNexus] Database ready.")
        except Exception as e:
            logger.error(f"[OmniNexus] DB init failed: {e}")

    return app


def _safe_migrate(db):
    try:
        with db.engine.connect() as conn:
            for sql in [
                "ALTER TABLE users ADD COLUMN google_id VARCHAR(128) UNIQUE NULL",
                "ALTER TABLE users MODIFY COLUMN password_hash VARCHAR(256) NULL",
                "ALTER TABLE users MODIFY COLUMN avatar VARCHAR(500) NULL DEFAULT ''",
                "ALTER TABLE users ADD COLUMN email_verified TINYINT(1) NOT NULL DEFAULT 0",
                "ALTER TABLE users ADD COLUMN verification_token VARCHAR(128) NULL",
                "ALTER TABLE users MODIFY COLUMN is_active TINYINT(1) NOT NULL DEFAULT 0",
                "CREATE UNIQUE INDEX uq_vtok ON users(verification_token)",
            ]:
                try:
                    conn.execute(db.text(sql))
                    conn.commit()
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f"[OmniNexus] Migration: {e}")


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
