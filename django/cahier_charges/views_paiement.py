"""
Vues pour la gestion des paiements avec LigdiCash - SÉCURISÉES
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.urls import reverse
from functools import wraps
import json
import uuid
import hmac
import hashlib
import logging

from .models import PlanAbonnement, Abonnement
from .models_paiement import TransactionLigdiCash
from .ligdicash_client import LigdiCashClient
from .ligdicash_config import LIGDICASH_CONFIG

logger = logging.getLogger(__name__)


def verify_ligdicash_signature(payload, signature):
    """
    CORRECTION: Vérification signature webhook (problème critique #8)
    Vérifie la signature HMAC du webhook LigdiCash pour éviter la fraude
    """
    if not signature:
        logger.warning("Webhook reçu sans signature")
        return False
    
    secret = LIGDICASH_CONFIG['WEBHOOK_SECRET']
    if secret == 'change_me_in_production':
        logger.error("WEBHOOK_SECRET non configuré!")
        # En développement, accepter quand même
        if LIGDICASH_CONFIG['TEST_MODE']:
            logger.warning("Mode test: signature ignorée")
            return True
        return False
    
    # Calculer la signature HMAC
    computed_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Comparaison sécurisée contre timing attacks
    is_valid = hmac.compare_digest(computed_signature, signature)
    
    if not is_valid:
        logger.warning(f"Signature webhook invalide: attendu {computed_signature[:10]}..., reçu {signature[:10]}...")
    
    return is_valid


def handle_options_request(view_func):
    """Décorateur pour gérer les requêtes OPTIONS (prévol) pour CORS"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.method == 'OPTIONS':
            response = HttpResponse()
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken, X-Requested-With, X-Api-Key'
            response['Access-Control-Max-Age'] = '86400'  # 24 heures
            return response
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@login_required
@require_http_methods(["GET", "POST"])
def initier_paiement_ligdicash(request, plan_id):
    """Vue pour initialiser un paiement LigdiCash"""
    print(f"\n=== INITIER PAIEMENT LIGDICASH - Début ===")
    print(f"Méthode: {request.method}, Plan ID: {plan_id}, Utilisateur: {request.user.username} ({request.user.email})")
    
    try:
        plan = get_object_or_404(PlanAbonnement, id=plan_id)
        print(f"Plan trouvé: {plan.nom} (ID: {plan.id})")
        
        # Vérifier si l'utilisateur a déjà un abonnement actif pour ce plan
        abonnement_actif = Abonnement.objects.filter(
            utilisateur=request.user,
            statut='actif',
            date_fin__gte=timezone.now().date()
        ).first()
        
        if abonnement_actif and abonnement_actif.plan == plan:
            msg = f"Vous avez déjà un abonnement {plan.get_nom_display()} actif"
            print(f"INFO: {msg}")
            messages.info(request, msg)
            return redirect('choix_abonnement')
        
        # Calculer le montant en XOF
        if plan.nom == 'pro_annuel':
            montant_usd = plan.prix_annuel_usd
            montant_xof = plan.get_prix_annuel_xof()
            periode = 'annuel'
        else:
            montant_usd = plan.prix_mensuel_usd
            montant_xof = plan.get_prix_mensuel_xof()
            periode = 'mensuel'
        
        print(f"Montant: {montant_usd} USD = {montant_xof} XOF ({periode})")
        
        # Créer une transaction
        try:
            transaction = TransactionLigdiCash.objects.create(
                utilisateur=request.user,
                plan=plan,
                montant=montant_xof,  # LigdiCash utilise XOF
                devise='XOF',
                statut='pending',
                metadata={
                    'plan_nom': plan.nom,
                    'plan_description': plan.description,
                    'user_email': request.user.email,
                    'user_id': str(request.user.id),
                    'periode': periode,
                    'montant_usd': float(montant_usd) if montant_usd else 0,
                    'montant_xof': float(montant_xof) if montant_xof else 0
                }
            )
            print(f"Transaction créée - ID: {transaction.transaction_id}")
        except Exception as e:
            print(f"ERREUR lors de la création de la transaction: {str(e)}")
            messages.error(request, f"Erreur lors de la création de la transaction: {str(e)}")
            return redirect('choix_abonnement')
        
        # Initialiser le client LigdiCash
        print("Initialisation du client LigdiCash...")
        client = LigdiCashClient()
        
        # Préparer les données du client
        customer_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
        customer_email = request.user.email
        customer_phone = getattr(request.user.profile, 'telephone', '') if hasattr(request.user, 'profile') else ''
        
        print(f"Client: {customer_name}, {customer_email}, {customer_phone}")
        
        # Générer le paiement
        print(f"Initialisation du paiement pour {montant_xof} XOF...")
        result = client.initier_paiement(
            montant=montant_xof,
            transaction_id=str(transaction.transaction_id),
            description=f"Abonnement {plan.get_nom_display()} - {periode}",
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone
        )
        
        if result.get('success', False):
            # Mettre à jour la transaction avec le token
            transaction.payment_token = result.get('payment_token')
            transaction.save()
            
            payment_url = result.get('payment_url')
            if payment_url:
                print(f"[OK] Redirection vers: {payment_url}")
                print("=== INITIER PAIEMENT LIGDICASH - Succès ===\n")
                return redirect(payment_url)
            else:
                error_msg = "URL de paiement manquante"
                print(f"[ERREUR] {error_msg}")
                transaction.marquer_comme_echouee(error_msg)
                messages.error(request, "Erreur: Impossible d'accéder à la page de paiement")
                return redirect('choix_abonnement')
        else:
            # En cas d'erreur
            error_msg = result.get('message', 'Erreur inconnue')
            print(f"[ERREUR] {error_msg}")
            transaction.marquer_comme_echouee(error_msg)
            messages.error(request, f"Erreur lors de l'initialisation du paiement: {error_msg}")
            print("=== INITIER PAIEMENT LIGDICASH - Échec ===\n")
            return redirect('choix_abonnement')
            
    except Exception as e:
        error_msg = f"Erreur inattendue: {str(e)}"
        print(f"[ERREUR CRITIQUE] {error_msg}")
        import traceback
        traceback.print_exc()
        messages.error(request, "Une erreur inattendue s'est produite. Veuillez réessayer.")
        print("=== INITIER PAIEMENT LIGDICASH - Erreur critique ===\n")
        return redirect('choix_abonnement')


@csrf_exempt
@handle_options_request
@require_http_methods(["POST", "GET"])
def notification_ligdicash(request):
    """
    Webhook SÉCURISÉ pour recevoir les notifications de paiement de LigdiCash
    CORRECTION: Vérification de signature ajoutée (problème critique #8)
    """
    logger.info("=== NOTIFICATION LIGDICASH ===")
    
    if request.method == 'POST':
        try:
            # SÉCURITÉ: Vérifier la signature du webhook
            signature = request.headers.get('X-Ligdicash-Signature', '')
            if not verify_ligdicash_signature(request.body, signature):
                logger.error(f"Tentative de webhook non autorisée depuis {request.META.get('REMOTE_ADDR')}")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Signature invalide'
                }, status=401)
            
            # Récupérer les données
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()
            
            logger.info(f"Données webhook validées: {data.get('token', 'NO_TOKEN')}")
            
            # Extraire le token de paiement
            payment_token = data.get('token') or data.get('payment_token')
            
            if not payment_token:
                print("[ERREUR] Token de paiement manquant")
                return JsonResponse({'status': 'error', 'message': 'Token manquant'}, status=400)
            
            # Récupérer la transaction
            try:
                transaction = TransactionLigdiCash.objects.get(payment_token=payment_token)
                print(f"Transaction trouvée: {transaction.transaction_id}")
            except TransactionLigdiCash.DoesNotExist:
                print(f"[ERREUR] Transaction non trouvee pour le token: {payment_token}")
                return JsonResponse({'status': 'error', 'message': 'Transaction non trouvée'}, status=404)
            
            # Vérifier le statut du paiement
            client = LigdiCashClient()
            statut = client.verifier_paiement(payment_token)
            
            if statut['success'] and statut['status'] == 'SUCCESS':
                print("[OK] Paiement confirme!")
                transaction.marquer_comme_reussie(
                    code_paiement=statut.get('transaction', {}).get('response_code', '00'),
                    message="Paiement accepté avec succès"
                )
                return JsonResponse({'status': 'success', 'message': 'Paiement confirmé'})
            elif statut['status'] == 'FAILED':
                print("[ERREUR] Paiement echoue")
                transaction.marquer_comme_echouee("Paiement échoué")
                return JsonResponse({'status': 'failed', 'message': 'Paiement échoué'})
            else:
                print(f"Status: {statut['status']}")
                return JsonResponse({'status': statut['status'], 'message': statut.get('message', 'Statut inconnu')})
                
        except json.JSONDecodeError:
            print("[ERREUR] Erreur de decodage JSON")
            return JsonResponse({'status': 'error', 'message': 'Données JSON invalides'}, status=400)
        except Exception as e:
            print(f"[ERREUR] {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)


@csrf_exempt
@handle_options_request
def retour_ligdicash(request):
    """Page de retour après un paiement LigdiCash"""
    print("\n=== RETOUR LIGDICASH ===")
    
    payment_token = request.GET.get('token') or request.GET.get('payment_token')
    transaction_id = request.GET.get('transaction_id')
    
    print(f"Token: {payment_token}, Transaction ID: {transaction_id}")
    
    if not payment_token and not transaction_id:
        messages.error(request, "Paramètres de transaction manquants")
        return redirect('choix_abonnement')
    
    try:
        # Essayer de trouver la transaction
        if payment_token:
            transaction = TransactionLigdiCash.objects.get(payment_token=payment_token)
        elif transaction_id:
            transaction = TransactionLigdiCash.objects.get(transaction_id=transaction_id)
        else:
            raise TransactionLigdiCash.DoesNotExist
        
        print(f"Transaction trouvée: {transaction.transaction_id}")
        
        # Vérifier le statut du paiement
        client = LigdiCashClient()
        statut = client.verifier_paiement(payment_token or transaction.payment_token)
        
        if statut['success'] and statut['status'] == 'SUCCESS':
            print("[OK] Paiement confirme!")
            transaction.marquer_comme_reussie(
                code_paiement=statut.get('transaction', {}).get('response_code', '00'),
                message="Paiement accepté avec succès"
            )
            messages.success(request, "Votre paiement a été effectué avec succès ! Votre abonnement est maintenant actif.")
            return redirect('tableau_de_bord')
        elif statut['status'] == 'PENDING':
            print("[ATTENTE] Paiement en attente")
            messages.warning(request, "Votre paiement est en cours de traitement. Vous recevrez une confirmation par email.")
            return redirect('tableau_de_bord')
        else:
            print(f"[ERREUR] Paiement echoue: {statut.get('message')}")
            messages.warning(request, f"Votre paiement n'a pas abouti. Statut: {statut.get('message', 'INCONNU')}")
            return redirect('choix_abonnement')
            
    except TransactionLigdiCash.DoesNotExist:
        print("[ERREUR] Transaction introuvable")
        messages.error(request, "Transaction introuvable")
        return redirect('choix_abonnement')
    except Exception as e:
        print(f"[ERREUR] {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"Une erreur est survenue: {str(e)}")
        return redirect('choix_abonnement')


@csrf_exempt
@handle_options_request
def annulation_ligdicash(request):
    """Page d'annulation de paiement LigdiCash"""
    print("\n=== ANNULATION LIGDICASH ===")
    
    payment_token = request.GET.get('token') or request.GET.get('payment_token')
    transaction_id = request.GET.get('transaction_id')
    
    print(f"Token: {payment_token}, Transaction ID: {transaction_id}")
    
    if payment_token or transaction_id:
        try:
            if payment_token:
                transaction = TransactionLigdiCash.objects.get(payment_token=payment_token)
            else:
                transaction = TransactionLigdiCash.objects.get(transaction_id=transaction_id)
            
            print(f"Transaction trouvee: {transaction.transaction_id}")
            transaction.marquer_comme_annulee("Paiement annule par l'utilisateur")
            print("[OK] Transaction marquee comme annulee")
        except TransactionLigdiCash.DoesNotExist:
            print("[ERREUR] Transaction non trouvee")
            pass
    
    messages.warning(request, "Votre paiement a été annulé.")
    return redirect('choix_abonnement')
