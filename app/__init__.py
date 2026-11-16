from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_mail import Mail
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

db = SQLAlchemy()
mail = Mail()

def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(base_dir, '../templates')
    
    app = Flask(__name__, template_folder=template_dir)
    CORS(app)
    
    app.secret_key = 'super_secret_key_port_link_2026'
    
    # Secure Database URI loaded from .env environment variable
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 🚀 Secure SMTP Configuration (Gmail)
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'gamagehashan53@gmail.com'
    app.config['MAIL_PASSWORD'] = 'ryrfyypbvehtsmsr'
    app.config['MAIL_DEFAULT_SENDER'] = 'Port Link <gamagehashan53@gmail.com>'
    
    db.init_app(app)
    mail.init_app(app)
    
    with app.app_context():
        from . import models, routes
        app.register_blueprint(routes.main_bp)
        db.create_all()
        
    return app