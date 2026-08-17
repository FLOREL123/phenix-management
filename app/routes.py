"""
Routes de l'application
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Stagiaire, Pointage, Absence, Notification
from datetime import datetime, timedelta
import bcrypt
import io
import os

routes_bp = Blueprint('routes', __name__)

# ============================================================
# PAGE D'ACCUEIL / DASHBOARD STAGIAIRE
# ============================================================
@routes_bp.route('/')
@routes_bp.route('/dashboard')
@login_required
def dashboard():
    """Tableau de bord du stagiaire"""
    pointages = Pointage.query.filter_by(stagiaire_id=current_user.id).order_by(Pointage.date.desc()).all()
    dernier = pointages[0] if pointages else None
    
    stats = {
        'total_pointages': len(pointages),
        'presences': len([p for p in pointages if p.statut == 'Présent']),
        'absences': len([p for p in pointages if p.statut == 'Absent'])
    }
    
    jours_restants = (current_user.date_fin - datetime.now().date()).days if current_user.date_fin else None
    
    return render_template('dashboard.html',
        pointages=pointages,
        dernier_pointage=dernier,
        stats=stats,
        jours_restants=jours_restants
    )

# ============================================================
# POINTAGE AVEC GÉOLOCALISATION
# ============================================================
@routes_bp.route('/api/pointer', methods=['POST'])
@login_required
def api_pointer():
    """Enregistre un pointage avec géolocalisation"""
    data = request.json
    type_pointage = data.get('type')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if not latitude or not longitude:
        return jsonify({'success': False, 'message': 'Géolocalisation requise'}), 400
    
    aujourdhui = datetime.now().date()
    pointage_existant = Pointage.query.filter_by(
        stagiaire_id=current_user.id,
        date=aujourdhui
    ).first()
    
    if type_pointage == 'arrivee':
        if pointage_existant and pointage_existant.heure_arrivee:
            return jsonify({'success': False, 'message': 'Arrivée déjà pointée aujourd\'hui'}), 400
        if pointage_existant:
            pointage_existant.heure_arrivee = datetime.now().time()
            pointage_existant.latitude = latitude
            pointage_existant.longitude = longitude
            pointage_existant.statut = 'Présent'
        else:
            pointage = Pointage(
                stagiaire_id=current_user.id,
                date=aujourdhui,
                heure_arrivee=datetime.now().time(),
                latitude=latitude,
                longitude=longitude,
                statut='Présent'
            )
            db.session.add(pointage)
    
    elif type_pointage == 'depart':
        if not pointage_existant or not pointage_existant.heure_arrivee:
            return jsonify({'success': False, 'message': 'Vous devez d\'abord pointer votre arrivée'}), 400
        if pointage_existant.heure_depart:
            return jsonify({'success': False, 'message': 'Départ déjà pointé aujourd\'hui'}), 400
        pointage_existant.heure_depart = datetime.now().time()
    
    db.session.commit()
    return jsonify({'success': True, 'message': f'{type_pointage} enregistré avec succès'})

# ============================================================
# ADMIN - TABLEAU DE BORD
# ============================================================
@routes_bp.route('/admin')
@routes_bp.route('/admin/dashboard')
def admin_dashboard():
    """Tableau de bord administrateur"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('auth.admin_login'))
    
    stagiaires = Stagiaire.query.all()
    pointages = Pointage.query.all()
    aujourdhui = datetime.now().date()
    
    stats = {
        'total_stagiaires': len(stagiaires),
        'total_pointages': len(pointages),
        'presents_aujourdhui': len([p for p in pointages if p.date == aujourdhui])
    }
    
    return render_template('admin.html',
        stagiaires=stagiaires,
        pointages=pointages,
        stats=stats,
        today=aujourdhui
    )

# ============================================================
# ADMIN - LISTE DES STAGIAIRES (API)
# ============================================================
@routes_bp.route('/api/admin/stagiaires', methods=['GET'])
def api_admin_stagiaires():
    """API pour récupérer la liste des stagiaires"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Accès refusé'}), 401
    
    stagiaires = Stagiaire.query.all()
    
    return jsonify([{
        'id': s.id,
        'matricule': s.matricule,
        'nom': s.nom,
        'prenom': s.prenom,
        'genre': s.genre,
        'email': s.email,
        'telephone': s.telephone,
        'adresse': s.adresse,
        'type_stage': s.type_stage,
        'date_debut': s.date_debut.strftime('%d/%m/%Y'),
        'date_fin': s.date_fin.strftime('%d/%m/%Y'),
        'statut': s.statut,
        'dossiers_deposes': s.dossiers_deposes,
        'notification_generee': s.notification_generee,
        'attestation_generee': s.attestation_generee
    } for s in stagiaires])

# ============================================================
# ADMIN - LISTE DES STAGIAIRES PAR PÉRIODE (API)
# ============================================================
@routes_bp.route('/api/admin/stagiaires/periode')
def api_admin_stagiaires_periode():
    """API pour récupérer la liste des stagiaires sur une période donnée"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Accès refusé'}), 401
    
    date_debut = request.args.get('date_debut')
    date_fin = request.args.get('date_fin')
    
    if not date_debut or not date_fin:
        aujourdhui = datetime.now().date()
        date_debut = aujourdhui.replace(day=1).strftime('%Y-%m-%d')
        date_fin = aujourdhui.strftime('%Y-%m-%d')
    
    try:
        debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
        fin = datetime.strptime(date_fin, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Format de date invalide'}), 400
    
    query = Stagiaire.query.filter(
        Stagiaire.date_debut <= fin,
        Stagiaire.date_fin >= debut
    ).order_by(Stagiaire.nom)
    
    stagiaires = query.all()
    
    return jsonify([{
        'id': s.id,
        'matricule': s.matricule,
        'nom': s.nom,
        'prenom': s.prenom,
        'email': s.email,
        'type_stage': s.type_stage,
        'date_debut': s.date_debut.strftime('%d/%m/%Y'),
        'date_fin': s.date_fin.strftime('%d/%m/%Y')
    } for s in stagiaires])

# ============================================================
# ADMIN - AJOUTER UN STAGIAIRE (API)
# ============================================================
@routes_bp.route('/api/admin/stagiaires', methods=['POST'])
def api_admin_ajouter():
    """API pour ajouter un stagiaire"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Accès refusé'}), 401
    
    data = request.json
    
    if Stagiaire.query.filter_by(email=data.get('email')).first():
        return jsonify({'success': False, 'message': 'Cet email est déjà utilisé'}), 400
    
    if Stagiaire.query.filter_by(matricule=data.get('matricule')).first():
        return jsonify({'success': False, 'message': 'Ce matricule existe déjà'}), 400
    
    stagiaire = Stagiaire(
        matricule=data.get('matricule'),
        nom=data.get('nom'),
        prenom=data.get('prenom'),
        genre=data.get('genre', 'M.'),
        email=data.get('email'),
        telephone=data.get('telephone'),
        adresse=data.get('adresse'),
        type_stage=data.get('type_stage'),
        date_debut=datetime.strptime(data.get('date_debut'), '%Y-%m-%d').date(),
        date_fin=datetime.strptime(data.get('date_fin'), '%Y-%m-%d').date(),
        demande_stage=False,
        memoire=False,
        rapport=False,
        dossiers_deposes=data.get('dossiers_deposes', False),
        notification_generee=False,
        attestation_generee=False,
        statut='actif'
    )
    
    if data.get('password'):
        stagiaire.set_password(data.get('password'))
    else:
        stagiaire.set_password('1234')
    
    db.session.add(stagiaire)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': f'Stagiaire {data.get("prenom")} {data.get("nom")} ajouté avec succès',
        'id': stagiaire.id
    })

# ============================================================
# ADMIN - MODIFIER UN STAGIAIRE (API)
# ============================================================
@routes_bp.route('/api/admin/stagiaires/<int:id>', methods=['PUT'])
def api_admin_modifier(id):
    """API pour modifier un stagiaire"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Accès refusé'}), 401
    
    stagiaire = Stagiaire.query.get_or_404(id)
    data = request.json
    
    # Vérifier si l'email est déjà utilisé par un autre stagiaire
    existing = Stagiaire.query.filter(Stagiaire.email == data.get('email'), Stagiaire.id != id).first()
    if existing:
        return jsonify({'success': False, 'message': 'Cet email est déjà utilisé'}), 400
    
    # Vérifier si le matricule est déjà utilisé par un autre stagiaire
    existing = Stagiaire.query.filter(Stagiaire.matricule == data.get('matricule'), Stagiaire.id != id).first()
    if existing:
        return jsonify({'success': False, 'message': 'Ce matricule existe déjà'}), 400
    
    stagiaire.matricule = data.get('matricule')
    stagiaire.nom = data.get('nom')
    stagiaire.prenom = data.get('prenom')
    stagiaire.genre = data.get('genre', 'M.')
    stagiaire.email = data.get('email')
    stagiaire.telephone = data.get('telephone')
    stagiaire.adresse = data.get('adresse')
    stagiaire.type_stage = data.get('type_stage')
    stagiaire.date_debut = datetime.strptime(data.get('date_debut'), '%Y-%m-%d').date()
    stagiaire.date_fin = datetime.strptime(data.get('date_fin'), '%Y-%m-%d').date()
    stagiaire.dossiers_deposes = data.get('dossiers_deposes', False)
    
    if data.get('password') and data.get('password').strip():
        stagiaire.set_password(data.get('password'))
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Stagiaire {data.get("prenom")} {data.get("nom")} modifié avec succès'})

# ============================================================
# ADMIN - SUPPRIMER UN STAGIAIRE (API)
# ============================================================
@routes_bp.route('/api/admin/stagiaires/<int:id>', methods=['DELETE'])
def api_admin_supprimer(id):
    """API pour supprimer un stagiaire"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Accès refusé'}), 401
    
    stagiaire = Stagiaire.query.get_or_404(id)
    nom = f"{stagiaire.prenom} {stagiaire.nom}"
    
    Pointage.query.filter_by(stagiaire_id=id).delete()
    Absence.query.filter_by(stagiaire_id=id).delete()
    Notification.query.filter_by(stagiaire_id=id).delete()
    
    db.session.delete(stagiaire)
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Stagiaire {nom} supprimé avec succès'})

# ============================================================
# ADMIN - GÉNÉRER LA NOTIFICATION DE STAGE
# ============================================================
@routes_bp.route('/admin/notification/<int:stagiaire_id>')
def generer_notification(stagiaire_id):
    """Génère la notification de stage"""
    if not session.get('admin_logged_in'):
        return "Accès refusé", 401
    
    stagiaire = Stagiaire.query.get_or_404(stagiaire_id)
    
    if not stagiaire.dossiers_deposes:
        return "❌ Les dossiers de stage n'ont pas encore été déposés.", 400
    
    numero = f"000{stagiaire_id:04d}/{datetime.now().strftime('%m')}{datetime.now().strftime('%y')}/PHM"
    
    stagiaire.notification_generee = True
    stagiaire.date_notification = datetime.now()
    stagiaire.numero_notification = numero
    db.session.commit()
    
    return render_template('autorisation.html',
        stagiaire=stagiaire,
        numero=numero,
        date_aujourdhui=datetime.now().strftime('%d %B %Y'),
        type_stage=stagiaire.type_stage
    )

# ============================================================
# ADMIN - GÉNÉRER L'ATTESTATION DE FIN DE STAGE
# ============================================================
@routes_bp.route('/admin/attestation/<int:stagiaire_id>')
def generer_attestation(stagiaire_id):
    """Génère l'attestation de fin de stage"""
    if not session.get('admin_logged_in'):
        return "Accès refusé", 401
    
    stagiaire = Stagiaire.query.get_or_404(stagiaire_id)
    
    if stagiaire.date_fin > datetime.now().date():
        return "❌ Le stage n'est pas encore terminé.", 400
    
    if not stagiaire.dossiers_deposes:
        return "❌ Les dossiers de stage n'ont pas été déposés.", 400
    
    if not stagiaire.notification_generee:
        return "❌ La notification de stage n'a pas été générée.", 400
    
    numero = f"N°00{stagiaire_id:04d}/PHM/{datetime.now().strftime('%Y')}"
    
    stagiaire.attestation_generee = True
    stagiaire.date_attestation = datetime.now()
    stagiaire.numero_attestation = numero
    db.session.commit()
    
    return render_template('attestation_fin_stage.html',
        stagiaire=stagiaire,
        numero=numero,
        date_aujourdhui=datetime.now().strftime('%d %B %Y'),
        type_stage=stagiaire.type_stage
    )

# ============================================================
# ADMIN - PRÉSENCES DU JOUR AVEC LOCALISATION (API)
# ============================================================
@routes_bp.route('/api/admin/presences')
def api_admin_presences():
    """Récupère les présences du jour avec localisation"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Accès refusé'}), 401
    
    aujourdhui = datetime.now().date()
    pointages = Pointage.query.filter_by(date=aujourdhui).all()
    
    resultats = []
    for p in pointages:
        stagiaire = Stagiaire.query.get(p.stagiaire_id)
        if stagiaire:
            resultats.append({
                'id': p.id,
                'stagiaire': f"{stagiaire.prenom} {stagiaire.nom}",
                'matricule': stagiaire.matricule,
                'heure_arrivee': p.heure_arrivee.strftime('%H:%M') if p.heure_arrivee else '-',
                'heure_depart': p.heure_depart.strftime('%H:%M') if p.heure_depart else '-',
                'latitude': p.latitude,
                'longitude': p.longitude,
                'statut': p.statut or 'Présent'
            })
    
    return jsonify(resultats)

# ============================================================
# ADMIN - REDIRECT APRÈS ENREGISTREMENT
# ============================================================
@routes_bp.route('/admin/stagiaire/after-save/<int:stagiaire_id>')
def after_save_stagiaire(stagiaire_id):
    """Page après enregistrement d'un stagiaire avec options d'impression"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('auth.admin_login'))
    
    stagiaire = Stagiaire.query.get_or_404(stagiaire_id)
    
    return render_template('after_save.html',
        stagiaire=stagiaire,
        today=datetime.now().date()
    )

# ============================================================
# ADMIN - EXPORT PDF DES POINTAGES
# ============================================================
@routes_bp.route('/admin/export/pdf')
def export_pdf():
    """Exporte les pointages en PDF"""
    if not session.get('admin_logged_in'):
        return "Accès refusé", 401
    
    date_debut = request.args.get('date_debut')
    date_fin = request.args.get('date_fin')
    stagiaire_id = request.args.get('stagiaire_id')
    statut = request.args.get('statut')
    
    query = Pointage.query
    
    if date_debut:
        query = query.filter(Pointage.date >= datetime.strptime(date_debut, '%Y-%m-%d').date())
    if date_fin:
        query = query.filter(Pointage.date <= datetime.strptime(date_fin, '%Y-%m-%d').date())
    if stagiaire_id:
        query = query.filter(Pointage.stagiaire_id == stagiaire_id)
    if statut and statut != 'tous':
        query = query.filter(Pointage.statut == statut)
    
    pointages = query.order_by(Pointage.date.desc()).all()
    
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=72)
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#1a2e1a'),
        alignment=TA_CENTER,
        spaceAfter=6
    )
    
    story = []
    
    story.append(Paragraph("PHENIX Management", title_style))
    story.append(Paragraph(f"Rapport de pointage - {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    total = len(pointages)
    presents = len([p for p in pointages if p.statut == 'Présent'])
    absents = total - presents
    
    stats_data = [
        ['Total pointages', str(total)],
        ['Présents', str(presents)],
        ['Absents', str(absents)]
    ]
    
    stats_table = Table(stats_data, colWidths=[2.5*inch, 1.5*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8f5e9')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 0.3*inch))
    
    if pointages:
        data = [['ID', 'Stagiaire', 'Date', 'Arrivée', 'Départ', 'Statut']]
        
        for p in pointages[:200]:
            stagiaire = Stagiaire.query.get(p.stagiaire_id)
            nom = f"{stagiaire.prenom} {stagiaire.nom}" if stagiaire else 'Inconnu'
            data.append([
                str(p.id),
                nom[:30],
                p.date.strftime('%d/%m/%Y'),
                p.heure_arrivee.strftime('%H:%M') if p.heure_arrivee else '-',
                p.heure_depart.strftime('%H:%M') if p.heure_depart else '-',
                p.statut or 'Absent'
            ])
        
        table = Table(data, colWidths=[0.6*inch, 1.8*inch, 1*inch, 0.9*inch, 0.9*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e7d32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8faf8')])
        ]))
        story.append(table)
    else:
        story.append(Paragraph("Aucun pointage à afficher.", styles['Normal']))
    
    doc.build(story)
    
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return Response(pdf_content, 
                   content_type='application/pdf',
                   headers={'Content-Disposition': 'attachment; filename=rapport_pointages.pdf'})

# ============================================================
# ADMIN - EXPORT PDF DE LA LISTE DES STAGIAIRES PAR PÉRIODE
# ============================================================
@routes_bp.route('/admin/export/stagiaires-pdf')
def export_stagiaires_pdf():
    """Exporte la liste des stagiaires en PDF pour une période donnée"""
    if not session.get('admin_logged_in'):
        return "Accès refusé", 401
    
    date_debut = request.args.get('date_debut')
    date_fin = request.args.get('date_fin')
    
    query = Stagiaire.query
    
    if date_debut and date_fin:
        try:
            debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
            fin = datetime.strptime(date_fin, '%Y-%m-%d').date()
            query = query.filter(
                Stagiaire.date_debut <= fin,
                Stagiaire.date_fin >= debut
            )
        except ValueError:
            pass
    
    stagiaires = query.order_by(Stagiaire.nom).all()
    
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                          rightMargin=40, leftMargin=40,
                          topMargin=40, bottomMargin=40)
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a2e1a'),
        alignment=TA_CENTER,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#4a6a4a'),
        alignment=TA_CENTER,
        spaceAfter=10
    )
    
    story = []
    
    logo_path = os.path.join('static', 'images', 'logo.png')
    if os.path.exists(logo_path):
        try:
            img = Image(logo_path, width=1.2*inch, height=1.2*inch)
            img.hAlign = 'CENTER'
            story.append(img)
        except:
            pass
    
    story.append(Paragraph("PHENIX Management", title_style))
    story.append(Paragraph("Liste des stagiaires", subtitle_style))
    
    if date_debut and date_fin:
        debut_formate = datetime.strptime(date_debut, '%Y-%m-%d').strftime('%d/%m/%Y')
        fin_formate = datetime.strptime(date_fin, '%Y-%m-%d').strftime('%d/%m/%Y')
        periode_text = f"Période du {debut_formate} au {fin_formate}"
    else:
        periode_text = "Tous les stagiaires"
    
    story.append(Paragraph(f"<b>{periode_text}</b>", styles['Normal']))
    story.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    total = len(stagiaires)
    actifs = len([s for s in stagiaires if s.statut == 'actif'])
    professionnel = len([s for s in stagiaires if s.type_stage == 'professionnel'])
    academique = len([s for s in stagiaires if s.type_stage == 'academique'])
    dossiers_ok = len([s for s in stagiaires if s.dossiers_deposes])
    notif_ok = len([s for s in stagiaires if s.notification_generee])
    attest_ok = len([s for s in stagiaires if s.attestation_generee])
    
    stats_data = [
        ['📊 Total stagiaires', str(total)],
        ['✅ Actifs', str(actifs)],
        ['💼 Professionnel', str(professionnel)],
        ['📚 Académique', str(academique)],
        ['📄 Dossiers déposés', str(dossiers_ok)],
        ['📄 Notifications générées', str(notif_ok)],
        ['📜 Attestations générées', str(attest_ok)]
    ]
    
    stats_table = Table(stats_data, colWidths=[2*inch, 0.8*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8f5e9')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 0.2*inch))
    
    if stagiaires:
        data = [['N°', 'Matricule', 'Nom', 'Prénom', 'Email', 'Type', 'Début', 'Fin', 'Dossiers', 'Notif', 'Attest', 'Statut']]
        
        for i, s in enumerate(stagiaires, 1):
            data.append([
                str(i),
                s.matricule,
                s.nom[:20],
                s.prenom[:20],
                s.email[:30],
                'Pro' if s.type_stage == 'professionnel' else 'Aca',
                s.date_debut.strftime('%d/%m/%Y'),
                s.date_fin.strftime('%d/%m/%Y'),
                '✅' if s.dossiers_deposes else '❌',
                '✅' if s.notification_generee else '❌',
                '✅' if s.attestation_generee else '❌',
                s.statut
            ])
        
        col_widths = [0.4*inch, 0.7*inch, 1.2*inch, 1.2*inch, 1.5*inch, 0.5*inch, 0.8*inch, 0.8*inch, 0.6*inch, 0.5*inch, 0.5*inch, 0.6*inch]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e7d32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 3),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8faf8')]),
        ]))
        
        story.append(table)
        story.append(Paragraph(f"Total: {len(stagiaires)} stagiaires", styles['Normal']))
    else:
        story.append(Paragraph("Aucun stagiaire trouvé pour cette période.", styles['Normal']))
    
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("PHENIX Management - Système de gestion des stages", styles['Normal']))
    
    doc.build(story)
    
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return Response(pdf_content, 
                   content_type='application/pdf',
                   headers={'Content-Disposition': 'attachment; filename=liste_stagiaires.pdf'})