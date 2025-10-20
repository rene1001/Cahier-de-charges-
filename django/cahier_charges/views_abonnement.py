from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import PlanAbonnement, Abonnement, CahierUtilisation
from datetime import timedelta

@login_required
def choix_abonnement(request):
    """Affiche la page de choix d'abonnement et gère le changement de forfait"""
    # Récupérer tous les plans triés par ordre d'affichage
    plans = PlanAbonnement.objects.all().order_by('ordre_affichage')
    
    # Récupérer l'abonnement actif de l'utilisateur s'il existe
    abonnement_actuel = Abonnement.objects.filter(
        utilisateur=request.user, 
        statut='actif',
        date_fin__gte=timezone.now().date()
    ).first()
    
    # Gérer la soumission du formulaire de changement de forfait
    if request.method == 'POST' and 'changer_abonnement' in request.POST:
        nouveau_plan_id = request.POST.get('nouveau_plan')
        try:
            nouveau_plan = PlanAbonnement.objects.get(id=nouveau_plan_id)
            
            # Vérifier si l'utilisateur a déjà ce plan actif
            if abonnement_actuel and abonnement_actuel.plan == nouveau_plan:
                messages.info(request, f"Vous avez déjà l'abonnement {nouveau_plan.get_nom_display()}.")
            else:
                # Créer un nouvel abonnement
                return creer_abonnement(request, nouveau_plan.id)
                
        except (PlanAbonnement.DoesNotExist, ValueError):
            messages.error(request, "Plan d'abonnement invalide.")
    
    # Préparer les données pour le template
    for plan in plans:
        plan.est_actuel = (abonnement_actuel and abonnement_actuel.plan == plan)
        
        # Définir le prix affiché
        if plan.nom == 'pro_annuel':
            plan.prix_affiche = f"{int(plan.prix_annuel)}€/an" if plan.prix_annuel else "Gratuit"
        else:
            plan.prix_affiche = f"{int(plan.prix_mensuel)}€/mois" if plan.prix_mensuel else "Gratuit"
    
    return render(request, 'cahier_charges/abonnement/choix.html', {
        'plans': plans,
        'abonnement_actuel': abonnement_actuel,
    })

def creer_abonnement(request, plan_id):
    """Crée un nouvel abonnement pour l'utilisateur"""
    if not request.user.is_authenticated:
        messages.error(request, "Vous devez être connecté pour souscrire à un abonnement.")
        return redirect('login')
    
    plan = get_object_or_404(PlanAbonnement, id=plan_id)
    
    # Récupérer l'abonnement actuel s'il existe
    abonnement_actuel = Abonnement.objects.filter(
        utilisateur=request.user, 
        statut='actif',
        date_fin__gte=timezone.now().date()
    ).first()
    
    # Calculer la date de fin (1 mois ou 1 an selon le plan)
    aujourdhui = timezone.now().date()
    if plan.nom == 'pro_annuel':
        date_fin = aujourdhui + timedelta(days=365)
        paiement_recurrent = True
        duree = "annuel"
    else:
        date_fin = aujourdhui + timedelta(days=30)
        paiement_recurrent = (plan.nom != 'gratuit')
        duree = "mensuel"
    
    # Si l'utilisateur a déjà un abonnement actif
    if abonnement_actuel:
        # Si c'est le même plan, on ne fait rien
        if abonnement_actuel.plan == plan:
            messages.info(request, f"Vous avez déjà l'abonnement {plan.get_nom_display()}.")
            return redirect('choix_abonnement')
        
        # Sinon, on désactive l'ancien abonnement
        abonnement_actuel.statut = 'annule'
        abonnement_actuel.date_fin = aujourdhui
        abonnement_actuel.save()
        
        # Message d'information sur le changement
        messages.info(request, f"Votre ancien abonnement a été annulé.")
    
    # Créer ou mettre à jour l'abonnement existant
    abonnement, created = Abonnement.objects.update_or_create(
        utilisateur=request.user,
        defaults={
            'plan': plan,
            'date_debut': aujourdhui,
            'date_fin': date_fin,
            'statut': 'actif',
            'paiement_recurrent': paiement_recurrent
        }
    )
    
    # Envoyer un email de confirmation (à implémenter)
    # send_abonnement_confirmation_email(request.user, abonnement)
    
    # Message de succès avec les détails
    if plan.nom == 'gratuit':
        message = f"Vous êtes maintenant sur le plan {plan.get_nom_display()}. "
    else:
        message = f"Votre abonnement {plan.get_nom_display()} a été activé avec succès pour une période {duree}."
    
    messages.success(request, message)
    
    # Rediriger vers le tableau de bord
    return redirect('tableau_de_bord')

@login_required
def tableau_de_bord(request):
    """Tableau de bord utilisateur avec l'utilisation actuelle"""
    try:
        abonnement = Abonnement.objects.get(utilisateur=request.user, statut='actif')
    except Abonnement.DoesNotExist:
        abonnement = None
    
    # Récupérer l'utilisation du mois en cours
    mois_courant = timezone.now().date().replace(day=1)
    utilisation, created = CahierUtilisation.objects.get_or_create(
        utilisateur=request.user,
        mois=mois_courant,
        defaults={'nb_cahiers_crees': 0, 'nb_pdf_generes': 0}
    )
    
    # Récupérer les 5 derniers cahiers créés par l'utilisateur
    from cahier_charges.models import CahierCharges
    derniers_cahiers = CahierCharges.objects.filter(
        utilisateur=request.user
    ).order_by('-date_creation')[:5]
    
    # Calculer le pourcentage d'utilisation des cahiers
    if abonnement and abonnement.plan:
        if abonnement.plan.max_cahiers > 0:  # Si limité
            pourcentage_cahiers = (utilisation.nb_cahiers_crees / abonnement.plan.max_cahiers) * 100
            limite_cahiers_atteinte = utilisation.nb_cahiers_crees >= abonnement.plan.max_cahiers
        else:  # Illimité
            pourcentage_cahiers = 0
            limite_cahiers_atteinte = False
            
        # Calculer le pourcentage d'utilisation des PDF
        if abonnement.plan.telechargement_pdf > 0:  # Si limité
            pourcentage_pdf = (utilisation.nb_pdf_generes / abonnement.plan.telechargement_pdf) * 100
            limite_pdf_atteinte = utilisation.nb_pdf_generes >= abonnement.plan.telechargement_pdf
        else:  # Illimité
            pourcentage_pdf = 0
            limite_pdf_atteinte = False
    else:
        # Par défaut pour les utilisateurs sans abonnement actif
        pourcentage_cahiers = 0
        pourcentage_pdf = 0
        limite_cahiers_atteinte = False
        limite_pdf_atteinte = False
    
    # Déterminer si l'utilisateur peut créer plus de cahiers
    peut_creer_cahier = not limite_cahiers_atteinte
    peut_generer_pdf = not limite_pdf_atteinte
    
    return render(request, 'cahier_charges/abonnement/tableau_de_bord.html', {
        'abonnement': abonnement,
        'utilisation': utilisation,
        'derniers_cahiers': derniers_cahiers,
        'pourcentage_cahiers': min(round(pourcentage_cahiers), 100),  # Ne pas dépasser 100%
        'pourcentage_pdf': min(round(pourcentage_pdf), 100),  # Ne pas dépasser 100%
        'limite_cahiers_atteinte': limite_cahiers_atteinte,
        'limite_pdf_atteinte': limite_pdf_atteinte,
        'peut_creer_cahier': peut_creer_cahier,
        'peut_generer_pdf': peut_generer_pdf,
    })

def annuler_abonnement(request, abonnement_id):
    """Annule un abonnement récurrent"""
    abonnement = get_object_or_404(Abonnement, id=abonnement_id, utilisateur=request.user)
    
    if abonnement.paiement_recurrent:
        abonnement.paiement_recurrent = False
        abonnement.save()
        messages.success(request, "Votre abonnement ne sera pas renouvelé à la fin de la période en cours.")
    else:
        messages.warning(request, "Cet abonnement n'est pas récurrent.")
    
    return redirect('tableau_de_bord')
