"""
Extensions Flask (db, login_manager, mail)
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail

# Créer les extensions (sans les attacher à une application)
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()