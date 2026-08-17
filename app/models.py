"""
Modèles de base de données
"""
from app.extensions import db
from datetime import datetime
import bcrypt

class Stagiaire(db.Model):
    __tablename__ = 'stagiaires'
    
    # ============================================================
    # CLÉ PRIMAIRE
    # ============================================================
    id = db.Column(db.Integer, primary_key=True)
    
    # ============================================================
    # INFORMATIONS PERSONNELLES
    # ============================================================
    matricule = db.Column(db.String(20), unique=True, nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(10), default='M.')
    email = db.Column(db.String(100), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    telephone = db.Column(db.String(20))
    adresse = db.Column(db.String(255))
    
    # ============================================================
    # INFORMATIONS DE STAGE
    # ============================================================
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=False)
    type_stage = db.Column(db.String(50), nullable=False)
    statut = db.Column(db.String(50), default='actif')
    
    # ============================================================
    # DOCUMENTS ET DOSSIERS
    # ============================================================
    demande_stage = db.Column(db.Boolean, default=False)
    memoire = db.Column(db.Boolean, default=False)
    rapport = db.Column(db.Boolean, default=False)
    dossiers_deposes = db.Column(db.Boolean, default=False)
    date_depot_dossiers = db.Column(db.DateTime)
    
    # ============================================================
    # GÉNÉRATION DES DOCUMENTS
    # ============================================================
    autorisation_generee = db.Column(db.Boolean, default=False)
    date_autorisation = db.Column(db.DateTime)
    numero_autorisation = db.Column(db.String(50))
    notification_generee = db.Column(db.Boolean, default=False)
    date_notification = db.Column(db.DateTime)
    numero_notification = db.Column(db.String(50))
    attestation_generee = db.Column(db.Boolean, default=False)
    date_attestation = db.Column(db.DateTime)
    numero_attestation = db.Column(db.String(50))
    
    # ============================================================
    # DOCUMENTS PHYSIQUES
    # ============================================================
    documents_physiques = db.Column(db.Boolean, default=False)
    date_depot_physique = db.Column(db.DateTime)
    
    # ============================================================
    # CHAMPS FLASK-LOGIN
    # ============================================================
    is_active = db.Column(db.Boolean, default=True)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # ============================================================
    # MÉTHODES FLASK-LOGIN
    # ============================================================
    def get_id(self):
        return str(self.id)
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    # ============================================================
    # MÉTHODES DE GESTION DES MOTS DE PASSE
    # ============================================================
    def set_password(self, password):
        self.mot_de_passe = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.mot_de_passe.encode('utf-8'))
    
    # ============================================================
    # MÉTHODES DE GESTION DU GENRE
    # ============================================================
    def get_titre(self):
        """Retourne le titre selon le genre (M. ou Mme)"""
        return 'Mme' if self.genre == 'Mme' else 'M.'
    
    def get_genre_complet(self):
        """Retourne le genre complet (Madame ou Monsieur)"""
        if self.genre == 'Mme':
            return 'Madame'
        return 'Monsieur'
    
    # ============================================================
    # MÉTHODES DE GESTION DES DATES EN FRANÇAIS
    # ============================================================
    def date_debut_fr(self):
        """Retourne la date de début en français (ex: 15 Août 2026)"""
        if not self.date_debut:
            return ""
        mois_fr = {
            'January': 'Janvier', 'February': 'Février', 'March': 'Mars',
            'April': 'Avril', 'May': 'Mai', 'June': 'Juin',
            'July': 'Juillet', 'August': 'Août', 'September': 'Septembre',
            'October': 'Octobre', 'November': 'Novembre', 'December': 'Décembre'
        }
        date_str = self.date_debut.strftime('%d %B %Y')
        for en, fr in mois_fr.items():
            date_str = date_str.replace(en, fr)
        return date_str
    
    def date_fin_fr(self):
        """Retourne la date de fin en français (ex: 15 Août 2026)"""
        if not self.date_fin:
            return ""
        mois_fr = {
            'January': 'Janvier', 'February': 'Février', 'March': 'Mars',
            'April': 'Avril', 'May': 'Mai', 'June': 'Juin',
            'July': 'Juillet', 'August': 'Août', 'September': 'Septembre',
            'October': 'Octobre', 'November': 'Novembre', 'December': 'Décembre'
        }
        date_str = self.date_fin.strftime('%d %B %Y')
        for en, fr in mois_fr.items():
            date_str = date_str.replace(en, fr)
        return date_str
    
    # ============================================================
    # MÉTHODES DE GESTION DES DOCUMENTS
    # ============================================================
    def get_documents_requis(self):
        if self.type_stage == 'academique':
            return ['demande_stage', 'memoire']
        else:
            return ['demande_stage', 'rapport']
    
    def documents_soumis(self):
        docs = self.get_documents_requis()
        for doc in docs:
            if not getattr(self, doc):
                return False
        return True
    
    def __repr__(self):
        return f"{self.prenom} {self.nom}"


# ============================================================
# MODÈLE POINTAGE
# ============================================================
class Pointage(db.Model):
    __tablename__ = 'pointages'
    
    id = db.Column(db.Integer, primary_key=True)
    stagiaire_id = db.Column(db.Integer, db.ForeignKey('stagiaires.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.now().date)
    heure_arrivee = db.Column(db.Time)
    heure_depart = db.Column(db.Time)
    statut = db.Column(db.String(50), default='Présent')
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    commentaire = db.Column(db.String(255))
    justifie = db.Column(db.Boolean, default=False)
    
    stagiaire = db.relationship('Stagiaire', backref='pointages', lazy=True)


# ============================================================
# MODÈLE ABSENCE
# ============================================================
class Absence(db.Model):
    __tablename__ = 'absences'
    
    id = db.Column(db.Integer, primary_key=True)
    stagiaire_id = db.Column(db.Integer, db.ForeignKey('stagiaires.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    justifiee = db.Column(db.Boolean, default=False)
    motif = db.Column(db.String(255))
    date_justification = db.Column(db.DateTime)
    
    stagiaire = db.relationship('Stagiaire', backref='absences', lazy=True)


# ============================================================
# MODÈLE NOTIFICATION
# ============================================================
class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    stagiaire_id = db.Column(db.Integer, db.ForeignKey('stagiaires.id'), nullable=False)
    titre = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50))
    lu = db.Column(db.Boolean, default=False)
    email_envoye = db.Column(db.Boolean, default=False)
    date_envoi = db.Column(db.DateTime, default=datetime.now)
    
    stagiaire = db.relationship('Stagiaire', backref='notifications', lazy=True)