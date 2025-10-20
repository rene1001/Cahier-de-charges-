
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime

def generate_pdf(cahier):
    """Génère un PDF structuré pour le cahier de charges"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        textColor=colors.darkblue,
        alignment=1  # Centré
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    # Contenu du PDF
    story = []
    
    # Titre
    story.append(Paragraph(f"CAHIER DE CHARGES - {cahier.nom_projet.upper()}", title_style))
    story.append(Spacer(1, 12))
    
    # Informations générales
    story.append(Paragraph("INFORMATIONS GÉNÉRALES", heading_style))
    
    data = [
        ['Type de projet:', cahier.get_type_projet_display()],
        ['Nom du projet:', cahier.nom_projet],
        ['Date de création:', cahier.date_creation.strftime('%d/%m/%Y')],
    ]
    
    if cahier.budget:
        data.append(['Budget:', f"{cahier.budget} €"])
    if cahier.delai:
        data.append(['Délai:', cahier.delai])
    
    table = Table(data, colWidths=[2*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 0), (-1, 0), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 12))
    
    # Description
    story.append(Paragraph("DESCRIPTION DU PROJET", heading_style))
    story.append(Paragraph(cahier.description, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Contenu spécifique selon le type de projet
    if cahier.type_projet in ['site_web', 'app_mobile']:
        _add_web_mobile_content(story, cahier, styles, heading_style)
    elif cahier.type_projet == 'ia':
        _add_ia_content(story, cahier, styles, heading_style)
    elif cahier.type_projet == 'mariage':
        _add_mariage_content(story, cahier, styles, heading_style)
    elif cahier.type_projet == 'construction':
        _add_construction_content(story, cahier, styles, heading_style)
    
    # Génération du PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def _add_web_mobile_content(story, cahier, styles, heading_style):
    """Ajoute le contenu spécifique aux projets web/mobile"""
    if cahier.fonctionnalites:
        story.append(Paragraph("FONCTIONNALITÉS", heading_style))
        story.append(Paragraph(cahier.fonctionnalites, styles['Normal']))
        story.append(Spacer(1, 12))
    
    if cahier.technologies:
        story.append(Paragraph("TECHNOLOGIES", heading_style))
        story.append(Paragraph(cahier.technologies, styles['Normal']))
        story.append(Spacer(1, 12))
    
    if cahier.public_cible:
        story.append(Paragraph("PUBLIC CIBLE", heading_style))
        story.append(Paragraph(cahier.public_cible, styles['Normal']))
        story.append(Spacer(1, 12))
    
    if cahier.contraintes_techniques:
        story.append(Paragraph("CONTRAINTES TECHNIQUES", heading_style))
        story.append(Paragraph(cahier.contraintes_techniques, styles['Normal']))
        story.append(Spacer(1, 12))

def _add_ia_content(story, cahier, styles, heading_style):
    """Ajoute le contenu spécifique aux projets IA"""
    if cahier.type_ia:
        story.append(Paragraph("TYPE D'INTELLIGENCE ARTIFICIELLE", heading_style))
        story.append(Paragraph(cahier.type_ia, styles['Normal']))
        story.append(Spacer(1, 12))
    
    if cahier.donnees_requises:
        story.append(Paragraph("DONNÉES REQUISES", heading_style))
        story.append(Paragraph(cahier.donnees_requises, styles['Normal']))
        story.append(Spacer(1, 12))
    
    if cahier.performance_attendue:
        story.append(Paragraph("PERFORMANCE ATTENDUE", heading_style))
        story.append(Paragraph(cahier.performance_attendue, styles['Normal']))
        story.append(Spacer(1, 12))

def _add_mariage_content(story, cahier, styles, heading_style):
    """Ajoute le contenu spécifique aux mariages"""
    data = []
    if cahier.date_mariage:
        data.append(['Date du mariage:', cahier.date_mariage.strftime('%d/%m/%Y')])
    if cahier.lieu_mariage:
        data.append(['Lieu:', cahier.lieu_mariage])
    if cahier.nombre_invites:
        data.append(['Nombre d\'invités:', str(cahier.nombre_invites)])
    if cahier.style_mariage:
        data.append(['Style de mariage:', cahier.style_mariage])
    
    if data:
        story.append(Paragraph("DÉTAILS DU MARIAGE", heading_style))
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(Spacer(1, 12))
    
    if cahier.services_requis:
        story.append(Paragraph("SERVICES REQUIS", heading_style))
        story.append(Paragraph(cahier.services_requis, styles['Normal']))
        story.append(Spacer(1, 12))

def _add_construction_content(story, cahier, styles, heading_style):
    """Ajoute le contenu spécifique à la construction"""
    data = []
    if cahier.type_construction:
        data.append(['Type de construction:', cahier.type_construction])
    if cahier.surface:
        data.append(['Surface:', cahier.surface])
    if cahier.localisation:
        data.append(['Localisation:', cahier.localisation])
    
    if data:
        story.append(Paragraph("DÉTAILS DE LA CONSTRUCTION", heading_style))
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(Spacer(1, 12))
    
    if cahier.materiaux:
        story.append(Paragraph("MATÉRIAUX", heading_style))
        story.append(Paragraph(cahier.materiaux, styles['Normal']))
        story.append(Spacer(1, 12))
    
    if cahier.normes:
        story.append(Paragraph("NORMES ET RÉGLEMENTATIONS", heading_style))
        story.append(Paragraph(cahier.normes, styles['Normal']))
        story.append(Spacer(1, 12))
