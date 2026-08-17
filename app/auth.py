"""
Authentification des utilisateurs
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db, login_manager
from app.models import Stagiaire

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@login_manager.user_loader
def load_user(user_id):
    return Stagiaire.query.get(int(user_id))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        stagiaire = Stagiaire.query.filter_by(email=email).first()
        
        if stagiaire and stagiaire.check_password(password):
            login_user(stagiaire)
            session['stagiaire_id'] = stagiaire.id
            session['stagiaire_nom'] = f"{stagiaire.prenom} {stagiaire.nom}"
            return redirect(url_for('routes.dashboard'))
        else:
            flash('❌ Email ou mot de passe incorrect', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('✅ Vous êtes déconnecté', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'admin123':
            session['admin_logged_in'] = True
            return redirect(url_for('routes.admin_dashboard'))
        else:
            flash('❌ Mot de passe incorrect', 'danger')
    
    return render_template('admin_login.html')