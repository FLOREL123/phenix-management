"""
SCRIPT D'INITIALISATION DE LA BASE DE DONNÉES
Commande : python init_db.py
"""

from app import create_app
from app.extensions import db
from app.models import Stagiaire, Pointage, Absence, Notification
from datetime import datetime, timedelta
import random

def init_db():
    print("🚀 Initialisation de la base de données...")

    app = create_app()

    with app.app_context():
        # Supprimer et recréer les tables
        db.drop_all()
        print("🗑️ Anciennes tables supprimées")

        db.create_all()
        print("✅ Nouvelles tables créées avec la structure complète")

        # ============================================================
        # CRÉER LES DONNÉES DE TEST
        # ============================================================
        print("📝 Création des données de test...")

        # Admin
        admin = Stagiaire(
            matricule='ADMIN001',
            nom='Admin',
            prenom='PHENIX',
            genre='M.',
            email='admin@phenix.com',
            telephone='+229 01 02 03 04',
            adresse='Cotonou, Bénin',
            type_stage='professionnel',
            date_debut=datetime.now().date(),
            date_fin=(datetime.now() + timedelta(days=365)).date(),
            statut='actif',
            demande_stage=True,
            rapport=True,
            dossiers_deposes=True,
            autorisation_generee=True,
            notification_generee=True,
            documents_physiques=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("   ✅ Admin créé")

        # Stagiaires de test
        stagiaires_data = [
            {
                'matricule': 'STU001',
                'nom': 'Kouassi',
                'prenom': 'Alice',
                'genre': 'Mme',
                'email': 'alice@email.com',
                'telephone': '+229 61 12 34 56',
                'adresse': 'Cotonou, Bénin',
                'type_stage': 'academique',
                'date_debut': datetime.now().date(),
                'date_fin': (datetime.now() + timedelta(days=90)).date(),
                'demande_stage': True,
                'memoire': False,
                'rapport': False,
                'dossiers_deposes': False,
                'statut': 'actif'
            },
            {
                'matricule': 'STU002',
                'nom': 'Traoré',
                'prenom': 'Bob',
                'genre': 'M.',
                'email': 'bob@email.com',
                'telephone': '+229 62 23 45 67',
                'adresse': 'Porto-Novo, Bénin',
                'type_stage': 'professionnel',
                'date_debut': (datetime.now() - timedelta(days=30)).date(),
                'date_fin': (datetime.now() + timedelta(days=60)).date(),
                'demande_stage': True,
                'memoire': False,
                'rapport': True,
                'dossiers_deposes': True,
                'statut': 'actif'
            }
        ]

        for data in stagiaires_data:
            existing = Stagiaire.query.filter_by(email=data['email']).first()
            if not existing:
                s = Stagiaire(
                    matricule=data['matricule'],
                    nom=data['nom'],
                    prenom=data['prenom'],
                    genre=data.get('genre', 'M.'),
                    email=data['email'],
                    telephone=data.get('telephone'),
                    adresse=data.get('adresse'),
                    type_stage=data['type_stage'],
                    date_debut=data['date_debut'],
                    date_fin=data['date_fin'],
                    demande_stage=data.get('demande_stage', False),
                    memoire=data.get('memoire', False),
                    rapport=data.get('rapport', False),
                    dossiers_deposes=data.get('dossiers_deposes', False),
                    statut=data.get('statut', 'actif')
                )
                s.set_password('1234')
                db.session.add(s)
                print(f"   ✅ Stagiaire {data['prenom']} {data['nom']} créé")

        db.session.commit()

        # ============================================================
        # POINTAGES DE TEST
        # ============================================================
        print("   📊 Création des pointages de test...")

        stagiaires = Stagiaire.query.filter(Stagiaire.matricule != 'ADMIN001').all()

        for s in stagiaires:
            for i in range(5):
                date_pointage = datetime.now().date() - timedelta(days=i)
                if date_pointage.weekday() >= 5:
                    continue

                existing = Pointage.query.filter_by(
                    stagiaire_id=s.id,
                    date=date_pointage
                ).first()

                if not existing:
                    if random.random() < 0.8:
                        p = Pointage(
                            stagiaire_id=s.id,
                            date=date_pointage,
                            heure_arrivee=datetime.strptime(f"{random.randint(8, 9)}:{random.randint(0, 59):02d}", '%H:%M').time(),
                            heure_depart=datetime.strptime(f"{random.randint(16, 18)}:{random.randint(0, 59):02d}", '%H:%M').time(),
                            statut='Présent',
                            latitude=6.3600 + (random.random() - 0.5) * 0.002,
                            longitude=2.4150 + (random.random() - 0.5) * 0.002
                        )
                        db.session.add(p)

        db.session.commit()
        print("   ✅ Pointages de test créés")

        # ============================================================
        # RÉCAPITULATIF
        # ============================================================
        print("✅ Initialisation terminée avec succès !")
        print("\n📋 RÉCAPITULATIF :")
        print(f"   - Stagiaires : {Stagiaire.query.count()}")
        print(f"   - Pointages : {Pointage.query.count()}")
        print("\n🔑 ADMIN :")
        print("   - Email : admin@phenix.com")
        print("   - Mot de passe : admin123")
        print("\n🔑 STAGIAIRES DE TEST :")
        print("   - alice@email.com / 1234")
        print("   - bob@email.com / 1234")

if __name__ == '__main__':
    init_db()