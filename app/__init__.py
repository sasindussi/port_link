from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

db = SQLAlchemy()

def create_app():
    # Templates folder eka root eke thiyena nisa template_folder path eka explicit denawa
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(base_dir, '../templates')
    
    app = Flask(__name__, template_folder=template_dir)
    CORS(app)
    
    # Supabase Connection URI
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Sas2019%402022ok@db.votwxipamylcvrthtdhg.supabase.co:5432/postgres'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        from . import routes, models
        db.create_all()  # Tables auto create wenawa Supabase wala
        
    return app