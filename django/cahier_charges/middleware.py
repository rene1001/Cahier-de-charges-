from django.http import HttpResponseForbidden, HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from .models import CahierUtilisation, Abonnement, PlanAbonnement
import logging

logger = logging.getLogger(__name__)

class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Gérer d'abord les requêtes OPTIONS (prévol)
        if request.method == 'OPTIONS':
            response = HttpResponse()
            response['Content-Length'] = '0'
            response['Content-Type'] = 'text/plain'
            
            # Récupérer l'origine de la requête
            origin = request.META.get('HTTP_ORIGIN', '')
            
            # Vérifier si l'origine est autorisée
            allowed_origins = settings.CORS_ALLOWED_ORIGINS
            if origin in allowed_origins or settings.DEBUG:
                response['Access-Control-Allow-Origin'] = origin
                response['Access-Control-Allow-Methods'] = ', '.join(settings.CORS_ALLOW_METHODS)
                response['Access-Control-Allow-Headers'] = ', '.join(settings.CORS_ALLOW_HEADERS)
                response['Access-Control-Allow-Credentials'] = 'true'
                response['Access-Control-Max-Age'] = '86400'  # 24 heures
            
            return response
            
        # Pour les autres méthodes, laisser passer la requête
        response = self.get_response(request)
        
        # Ajouter les en-têtes CORS à toutes les réponses
        origin = request.META.get('HTTP_ORIGIN', '')
        if origin in settings.CORS_ALLOWED_ORIGINS or settings.DEBUG:
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Methods'] = ', '.join(settings.CORS_ALLOW_METHODS)
            response['Access-Control-Allow-Headers'] = ', '.join(settings.CORS_ALLOW_HEADERS)
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Expose-Headers'] = ', '.join(settings.CORS_EXPOSE_HEADERS)
        
        return response

class SubscriptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Ne pas vérifier pour les utilisateurs non connectés
        if not request.user.is_authenticated:
            return None
            
        # Chemins exclus de la vérification d'abonnement
        excluded_paths = [
            '/admin/',
            '/accounts/',
            '/authentification/',
            '/abonnement/',
            '/i18n/',
            '/static/',
            '/media/',
            '/favicon.ico'
        ]
        
        # Vérifier si la vue actuelle est exclue
        if any(path in request.path for path in excluded_paths):
            return None
            
        # Vérifier si l'utilisateur est un superutilisateur
        if request.user.is_superuser:
            return None
            
        # Vérifier si l'utilisateur a un abonnement actif
        try:
            abonnement = Abonnement.objects.filter(
                utilisateur=request.user,
                statut='actif',
                date_fin__gte=timezone.now().date()
            ).first()
            
            if not abonnement:
                # Pas d'abonnement actif, vérifier s'il y a un abonnement expiré
                abonnement = Abonnement.objects.filter(
                    utilisateur=request.user,
                    statut='actif'
                ).order_by('-date_fin').first()
                
                if abonnement:
                    # Mettre à jour le statut de l'abonnement expiré
                    abonnement.statut = 'expire'
                    abonnement.save()
                    
                # Créer un abonnement gratuit pour l'utilisateur
                plan_gratuit = PlanAbonnement.objects.get(nom='gratuit')
                abonnement = Abonnement.objects.create(
                    utilisateur=request.user,
                    plan=plan_gratuit,
                    date_debut=timezone.now().date(),
                    date_fin=timezone.now().date() + timezone.timedelta(days=30),
                    statut='actif',
                    paiement_recurrent=False
                )
                messages.info(request, "Un abonnement gratuit vous a été attribué.")
                return None
                
        except PlanAbonnement.DoesNotExist:
            logger.error("Le plan d'abonnement gratuit n'existe pas dans la base de données.")
            messages.error(request, "Une erreur est survenue lors de la configuration de votre compte. Veuillez contacter le support.")
            return redirect('index')
            
        except Exception as e:
            logger.error(f"Erreur dans le middleware d'abonnement: {str(e)}")
            # Ne pas bloquer l'utilisateur en cas d'erreur
            return None
            
        return None

def check_subscription_limits(view_func):
    """
    Décorateur pour vérifier les limites d'abonnement avant d'exécuter une vue.
    À utiliser avec @check_subscription_limits sur les vues qui nécessitent une vérification d'abonnement.
    """
    def wrapper(request, *args, **kwargs):
        # Si l'utilisateur n'est pas connecté, rediriger vers la page de connexion
        if not request.user.is_authenticated:
            messages.warning(request, "Veuillez vous connecter pour accéder à cette page.")
            return redirect('authentification')
            
        # Vérifier si l'utilisateur est un superutilisateur (accès illimité)
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
            
        # Récupérer l'abonnement actif de l'utilisateur
        try:
            abonnement = Abonnement.objects.filter(
                utilisateur=request.user,
                statut='actif',
                date_fin__gte=timezone.now().date()
            ).first()
            
            # Si pas d'abonnement actif, essayer d'en créer un gratuit
            if not abonnement:
                plan_gratuit = PlanAbonnement.objects.get(nom='gratuit')
                abonnement = Abonnement.objects.create(
                    utilisateur=request.user,
                    plan=plan_gratuit,
                    date_debut=timezone.now().date(),
                    date_fin=timezone.now().date() + timezone.timedelta(days=30),
                    statut='actif',
                    paiement_recurrent=False
                )
                messages.info(request, "Un abonnement gratuit vous a été attribué.")
            
            # Vérifier les limites d'abonnement pour la création de cahiers
            if request.path == '/nouveau-cahier/' or 'creer_cahier' in request.path:
                mois_courant = timezone.now().date().replace(day=1)
                utilisation, created = CahierUtilisation.objects.get_or_create(
                    utilisateur=request.user,
                    mois=mois_courant,
                    defaults={'nb_cahiers_crees': 0, 'nb_pdf_generes': 0}
                )
                
                # Vérifier si l'utilisateur a atteint sa limite de cahiers
                if abonnement.plan.max_cahiers > 0 and utilisation.nb_cahiers_crees >= abonnement.plan.max_cahiers:
                    messages.error(request, f"Vous avez atteint la limite de {abonnement.plan.max_cahiers} cahiers pour votre abonnement actuel.")
                    return redirect('tableau_de_bord')
            
            # Si tout est OK, continuer vers la vue demandée
            return view_func(request, *args, **kwargs)
            
        except PlanAbonnement.DoesNotExist:
            logger.error("Le plan d'abonnement gratuit n'existe pas dans la base de données.")
            messages.error(request, "Une erreur est survenue lors de la vérification de votre abonnement. Veuillez contacter le support.")
            return redirect('index')
            
        except Exception as e:
            logger.error(f"Erreur dans le décorateur check_subscription_limits: {str(e)}")
            # En cas d'erreur, autoriser l'accès pour ne pas bloquer l'utilisateur
            return view_func(request, *args, **kwargs)
    
    return wrapper
