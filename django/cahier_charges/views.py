from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import CahierCharges, TypeProjet, PlanAbonnement, Abonnement, CahierUtilisation
from .forms import CahierChargesForm, UtilisateurForm
from .pdf_generator import generate_pdf
from datetime import datetime, date
import json


def index(request):
    """Page d'accueil avec choix du type de projet"""
    return render(request, 'cahier_charges/index.html', {
        'types_projet': TypeProjet.choices
    })

def formulaire(request, type_projet):
    """Affiche le formulaire selon le type de projet choisi"""
    if type_projet not in dict(TypeProjet.choices):
        messages.error(request, "Type de projet invalide")
        return redirect('index')
    
    if request.method == 'POST':
        form = CahierChargesForm(request.POST, type_projet=type_projet)
        if form.is_valid():
            cahier = form.save()
            messages.success(request, "Cahier de charges créé avec succès!")
            return redirect('preview', cahier_id=cahier.id)
    else:
        form = CahierChargesForm(type_projet=type_projet)
    
    return render(request, 'cahier_charges/formulaire.html', {
        'form': form,
        'type_projet': type_projet,
        'type_projet_display': dict(TypeProjet.choices)[type_projet]
    })

@login_required
def preview(request, cahier_id):
    """Prévisualisation du cahier de charges avant génération PDF"""
    cahier = get_object_or_404(CahierCharges, id=cahier_id, utilisateur=request.user)
    
    # Vérifier les limites d'abonnement pour l'affichage
    abonnement = Abonnement.objects.filter(utilisateur=request.user, statut='actif').first()
    mois_courant = timezone.now().date().replace(day=1)
    
    # Récupérer ou créer l'objet d'utilisation du mois
    utilisation, _ = CahierUtilisation.objects.get_or_create(
        utilisateur=request.user,
        mois=mois_courant,
        defaults={'nb_cahiers_crees': 0, 'nb_pdf_generes': 0}
    )
    
    # Déterminer si l'utilisateur peut générer un PDF
    peut_generer_pdf = True
    limite_pdf = None
    pdf_restants = None
    
    if abonnement and abonnement.plan:
        limite_pdf = abonnement.plan.telechargement_pdf
        if limite_pdf == 0:  # Aucun PDF autorisé
            peut_generer_pdf = False
        elif limite_pdf > 0:  # Limite de PDF
            pdf_restants = max(0, limite_pdf - utilisation.nb_pdf_generes)
            peut_generer_pdf = pdf_restants > 0
    else:
        # Utilisateur sans abonnement (gratuit) - 1 seul PDF autorisé
        limite_pdf = 1
        pdf_restants = 1 - utilisation.nb_pdf_generes
        peut_generer_pdf = pdf_restants > 0
    
    return render(request, 'cahier_charges/preview.html', {
        'cahier': cahier,
        'peut_generer_pdf': peut_generer_pdf,
        'limite_pdf': limite_pdf,
        'pdf_restants': pdf_restants,
        'abonnement': abonnement,
        'utilisation': utilisation
    })

@login_required
def generer_pdf(request, cahier_id):
    """Génère et télécharge le PDF du cahier de charges"""
    cahier = get_object_or_404(CahierCharges, id=cahier_id, utilisateur=request.user)
    
    # Vérifier les limites d'abonnement
    abonnement = Abonnement.objects.filter(utilisateur=request.user, statut='actif').first()
    mois_courant = timezone.now().date().replace(day=1)
    
    # Récupérer ou créer l'objet d'utilisation du mois
    utilisation, _ = CahierUtilisation.objects.get_or_create(
        utilisateur=request.user,
        mois=mois_courant,
        defaults={'nb_cahiers_crees': 0, 'nb_pdf_generes': 0}
    )
    
    # Vérifier si l'utilisateur peut générer un PDF
    peut_generer_pdf = True
    message_erreur = None
    
    if abonnement and abonnement.plan:
        if abonnement.plan.telechargement_pdf == 0:  # Aucun PDF autorisé
            peut_generer_pdf = False
            message_erreur = "Votre forfait actuel ne permet pas de télécharger de PDF."
        elif abonnement.plan.telechargement_pdf > 0:  # Limite de PDF
            if utilisation.nb_pdf_generes >= abonnement.plan.telechargement_pdf:
                peut_generer_pdf = False
                message_erreur = f"Vous avez atteint la limite de {abonnement.plan.telechargement_pdf} PDF pour ce mois-ci."
    else:
        # Utilisateur sans abonnement (gratuit) - 1 seul PDF autorisé
        if utilisation.nb_pdf_generes >= 1:
            peut_generer_pdf = False
            message_erreur = "La version gratuite est limitée à 1 PDF par mois. Passez à un forfait payant pour plus de fonctionnalités."
    
    if not peut_generer_pdf:
        messages.error(request, message_erreur)
        return redirect('choix_abonnement')
    
    # Génération du PDF
    pdf_buffer = generate_pdf(cahier)
    
    # Mettre à jour le compteur de PDF générés
    utilisation.nb_pdf_generes += 1
    utilisation.save()
    
    # Retour de la réponse HTTP avec le PDF
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="cahier_charges_{cahier.nom_projet}.pdf"'
    
    return response

@login_required
def mes_cahiers(request):
    """Liste des cahiers de charges de l'utilisateur connecté"""
    cahiers = CahierCharges.objects.filter(utilisateur=request.user).order_by('-date_creation')
    
    # Récupérer l'abonnement actif de l'utilisateur
    abonnement = Abonnement.objects.filter(utilisateur=request.user, statut='actif').first()
    
    # Vérifier les limites d'utilisation
    mois_courant = date.today().replace(day=1)
    utilisation, _ = CahierUtilisation.objects.get_or_create(
        utilisateur=request.user,
        mois=mois_courant,
        defaults={'nb_cahiers_crees': 0, 'nb_pdf_generes': 0}
    )
    
    # Vérifier si l'utilisateur peut créer un nouveau cahier
    peut_creer_cahier = True
    if abonnement and abonnement.plan:
        if abonnement.plan.max_cahiers > 0:  # Si limité
            peut_creer_cahier = utilisation.nb_cahiers_crees < abonnement.plan.max_cahiers
    else:
        # Utilisateur sans abonnement (gratuit)
        peut_creer_cahier = utilisation.nb_cahiers_crees < 3  # Limite gratuite
    
    return render(request, 'cahier_charges/mes_cahiers.html', {
        'cahiers': cahiers,
        'abonnement': abonnement,
        'peut_creer_cahier': peut_creer_cahier,
        'utilisation': utilisation
    })


def authentification(request, cahier_id=None):
    """Page d'authentification/inscription"""
    if cahier_id:
        request.session['cahier_id'] = cahier_id
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'login':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                auth_login(request, user)
                messages.success(request, 'Connexion réussie!')
                
                # Rediriger vers la génération PDF si un cahier est en attente
                cahier_id = request.session.get('cahier_id')
                if cahier_id:
                    # Mettre à jour l'utilisateur du cahier si nécessaire
                    cahier = get_object_or_404(CahierCharges, id=cahier_id)
                    if not cahier.utilisateur:
                        cahier.utilisateur = user
                        cahier.save()
                    return redirect('generer_pdf', cahier_id=cahier_id)
                return redirect('mes_cahiers')
            else:
                messages.error(request, 'Identifiants invalides. Veuillez réessayer.')
                
            # Préparer le contexte pour réafficher le formulaire avec les erreurs
            form = UtilisateurForm(initial={
                'username': username,
            })
            return render(request, 'cahier_charges/authentification.html', {
                'form': form,
                'login_username': username
            })
        
        elif action == 'register':
            form = UtilisateurForm(request.POST)
            if form.is_valid():
                user = form.save()
                
                # Connecter automatiquement l'utilisateur après inscription
                auth_login(request, user)
                messages.success(request, 'Inscription réussie! Bienvenue!')
                
                # Lier le cahier à l'utilisateur si applicable
                cahier_id = request.session.get('cahier_id')
                if cahier_id:
                    cahier = get_object_or_404(CahierCharges, id=cahier_id)
                    cahier.utilisateur = user
                    cahier.save()
                    return redirect('generer_pdf', cahier_id=cahier_id)
                
                return redirect('mes_cahiers')
            
            # Si le formulaire n'est pas valide, on le réaffiche avec les erreurs
            return render(request, 'cahier_charges/authentification.html', {
                'form': form,
                'register_data': request.POST
            })
    
    # Si méthode GET, afficher le formulaire vide
    return render(request, 'cahier_charges/authentification.html', {
        'form': UtilisateurForm()
    })

def deconnexion(request):
    """Déconnexion utilisateur"""
    auth_logout(request)
    messages.success(request, 'Déconnexion réussie!')
    return redirect('index')

@login_required
def verifier_limite_cahiers(request):
    """Vérifie si l'utilisateur peut créer un nouveau cahier"""
    # Récupérer l'abonnement actif de l'utilisateur
    abonnement = Abonnement.objects.filter(utilisateur=request.user, statut='actif').first()
    
    # Vérifier les limites d'utilisation
    mois_courant = timezone.now().date().replace(day=1)
    utilisation, _ = CahierUtilisation.objects.get_or_create(
        utilisateur=request.user,
        mois=mois_courant,
        defaults={'nb_cahiers_crees': 0, 'nb_pdf_generes': 0}
    )
    
    # Vérifier si l'utilisateur peut créer un nouveau cahier
    peut_creer = True
    message = "Vous pouvez créer un nouveau cahier."
    
    if abonnement and abonnement.plan:
        if abonnement.plan.max_cahiers > 0:  # Si limité
            if utilisation.nb_cahiers_crees >= abonnement.plan.max_cahiers:
                peut_creer = False
                message = f"Vous avez atteint la limite de {abonnement.plan.max_cahiers} cahiers pour votre forfait actuel."
    else:
        # Utilisateur sans abonnement (gratuit)
        if utilisation.nb_cahiers_crees >= 3:  # Limite gratuite
            peut_creer = False
            message = "Vous avez atteint la limite de 3 cahiers pour le forfait gratuit. Passez à un forfait payant pour créer plus de cahiers."
    
    return JsonResponse({
        'peut_creer': peut_creer,
        'message': message,
        'limite_atteinte': not peut_creer
    })

@login_required
def creer_cahier(request, type_projet=None):
    """Vue pour créer un nouveau cahier de charges"""
    # Vérifier si le type de projet est valide
    if type_projet and type_projet not in dict(TypeProjet.choices):
        messages.error(request, "Type de projet invalide")
        return redirect('index')
    
    # Si pas de type de projet spécifié, afficher la page de sélection
    if not type_projet:
        return render(request, 'cahier_charges/choisir_type.html', {
            'types_projet': TypeProjet.choices
        })
    
    # Vérifier les limites d'abonnement
    abonnement = Abonnement.objects.filter(utilisateur=request.user, statut='actif').first()
    mois_courant = timezone.now().date().replace(day=1)
    utilisation, _ = CahierUtilisation.objects.get_or_create(
        utilisateur=request.user,
        mois=mois_courant,
        defaults={'nb_cahiers_crees': 0, 'nb_pdf_generes': 0}
    )
    
    # Vérifier si l'utilisateur peut créer un nouveau cahier
    if abonnement and abonnement.plan:
        if abonnement.plan.max_cahiers > 0 and utilisation.nb_cahiers_crees >= abonnement.plan.max_cahiers:
            messages.error(request, f"Vous avez atteint la limite de {abonnement.plan.max_cahiers} cahiers pour votre forfait actuel.")
            return redirect('choix_abonnement')
    elif utilisation.nb_cahiers_crees >= 3:  # Limite gratuite
        messages.error(request, "Vous avez atteint la limite de 3 cahiers pour le forfait gratuit. Passez à un forfait payant pour créer plus de cahiers.")
        return redirect('choix_abonnement')
    
    # Traitement du formulaire
    if request.method == 'POST':
        form = CahierChargesForm(request.POST, type_projet=type_projet)
        if form.is_valid():
            cahier = form.save(commit=False)
            cahier.utilisateur = request.user
            cahier.save()
            
            # Mettre à jour le compteur de cahiers créés
            utilisation.nb_cahiers_crees += 1
            utilisation.save()
            
            messages.success(request, "Cahier de charges créé avec succès!")
            return redirect('preview', cahier_id=cahier.id)
    else:
        form = CahierChargesForm(type_projet=type_projet)
    
    return render(request, 'cahier_charges/formulaire.html', {
        'form': form,
        'type_projet': type_projet,
        'type_projet_display': dict(TypeProjet.choices)[type_projet]
    })

@login_required
def supprimer_cahier(request, cahier_id):
    """Vue pour supprimer un cahier de charges"""
    # Vérifier si l'utilisateur a un abonnement actif
    abonnement = Abonnement.objects.filter(utilisateur=request.user, statut='actif').first()
    
    # Récupérer le cahier à supprimer
    cahier = get_object_or_404(CahierCharges, id=cahier_id, utilisateur=request.user)
    
    if request.method == 'POST':
        # Vérifier si l'utilisateur a le droit de supprimer ce cahier
        if not abonnement and not request.user.is_superuser:
            messages.error(request, "Vous devez avoir un abonnement actif pour effectuer cette action.")
            return redirect('choix_abonnement')
        
        # Récupérer la date de création du cahier pour déterminer le mois d'utilisation
        mois_creation = cahier.date_creation.replace(day=1)
        
        # Supprimer le cahier
        cahier.delete()
        
        # Mettre à jour le compteur d'utilisation pour le mois de création
        try:
            utilisation = CahierUtilisation.objects.get(
                utilisateur=request.user,
                mois=mois_creation
            )
            if utilisation.nb_cahiers_crees > 0:
                utilisation.nb_cahiers_crees -= 1
                utilisation.save()
                
                # Mettre à jour l'abonnement si nécessaire
                if abonnement and abonnement.plan:
                    abonnement.date_mise_a_jour = timezone.now()
                    abonnement.save()
                    
        except CahierUtilisation.DoesNotExist:
            pass  # Si l'utilisation n'existe pas, rien à mettre à jour
        
        messages.success(request, "Le cahier de charges a été supprimé avec succès.")
        return redirect('mes_cahiers')
    
    # Si la méthode n'est pas POST, afficher la page de confirmation
    return render(request, 'cahier_charges/confirmer_suppression.html', {
        'cahier': cahier,
        'abonnement': abonnement
    })
