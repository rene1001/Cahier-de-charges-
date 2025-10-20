"""
Client API LigdiCash pour l'intégration des paiements
Documentation: https://developers.ligdicash.com/
"""

import requests
import json
import hashlib
import time
import decimal
from django.conf import settings
from django.urls import reverse
from .ligdicash_config import LIGDICASH_CONFIG


class DecimalEncoder(json.JSONEncoder):
    """Encodeur JSON personnalisé pour les objets Decimal"""
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


class LigdiCashClient:
    """Client pour interagir avec l'API LigdiCash"""
    
    def __init__(self):
        self.api_key = LIGDICASH_CONFIG['API_KEY']
        self.auth_token = LIGDICASH_CONFIG['AUTH_TOKEN']
        self.api_url = LIGDICASH_CONFIG['API_URL']
        self.verify_url = LIGDICASH_CONFIG['VERIFY_URL']
        self.notify_url = LIGDICASH_CONFIG['NOTIFY_URL']
        self.return_url = LIGDICASH_CONFIG['RETURN_URL']
        self.cancel_url = LIGDICASH_CONFIG['CANCEL_URL']
        self.currency = LIGDICASH_CONFIG['CURRENCY']
        self.lang = LIGDICASH_CONFIG['LANG']
        self.test_mode = LIGDICASH_CONFIG['TEST_MODE']
    
    def initier_paiement(self, montant, transaction_id, description, customer_name, customer_email, customer_phone=None):
        """
        Initialise un paiement avec LigdiCash
        
        Args:
            montant: Montant en XOF (ou devise configurée)
            transaction_id: ID unique de la transaction
            description: Description du paiement
            customer_name: Nom du client
            customer_email: Email du client
            customer_phone: Téléphone du client (optionnel)
            
        Returns:
            dict: Résultat de l'initialisation avec success, payment_url, token, etc.
        """
        try:
            # Convertir le montant en entier (LigdiCash utilise des centimes)
            montant_cents = int(round(float(montant), 0))
            
            print(f"\n=== LIGDICASH - Initialisation du paiement ===")
            print(f"Montant: {montant_cents} {self.currency}")
            print(f"Transaction ID: {transaction_id}")
            print(f"Client: {customer_name} ({customer_email})")
            
            # Préparer les données de la requête selon la documentation LigdiCash
            data = {
                'commande': {
                    'invoice': {
                        'items': [{
                            'name': description,
                            'description': description,
                            'quantity': 1,
                            'unit_price': montant_cents,
                            'total_price': montant_cents
                        }],
                        'total_amount': montant_cents,
                        'devise': self.currency,
                        'description': description,
                        'customer': customer_name,
                        'customer_email': customer_email,
                        'customer_phone_number': customer_phone or '',
                        'external_id': str(transaction_id),
                        'otp': str(transaction_id)[:6] if len(str(transaction_id)) >= 6 else str(transaction_id).zfill(6),
                    },
                    'store': {
                        'name': LIGDICASH_CONFIG['CUSTOMER'],
                        'website_url': self.return_url.rsplit('/', 3)[0] if '/' in self.return_url else 'http://localhost:8000'
                    },
                    'actions': {
                        'cancel_url': self.cancel_url,
                        'return_url': self.return_url,
                        'callback_url': self.notify_url
                    }
                }
            }
            
            # En-têtes HTTP
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Apikey': self.api_key,
                'Authorization': f'Bearer {self.auth_token}',
                'User-Agent': 'CahierDeCharges/1.0'
            }
            
            print(f"\nURL API: {self.api_url}")
            print(f"En-têtes: Content-Type, Accept, Apikey, Authorization")
            
            # Convertir les données en JSON
            json_data = json.dumps(data, cls=DecimalEncoder)
            print(f"\nCorps de la requête:")
            print(json.dumps(data, indent=2, cls=DecimalEncoder))
            
            # Envoyer la requête
            response = requests.post(
                self.api_url,
                data=json_data,
                headers=headers,
                timeout=30
            )
            
            print(f"\nRéponse HTTP: {response.status_code}")
            print(f"Contenu: {response.text}")
            
            # Analyser la réponse
            if response.status_code in [200, 201]:
                try:
                    result = response.json()
                    
                    # Vérifier si la réponse contient les informations nécessaires
                    if result.get('response_code') == '00' or result.get('status') == 'success':
                        payment_token = result.get('token') or result.get('payment_token')
                        payment_url = result.get('response_text') or result.get('payment_url')
                        
                        if payment_token and payment_url:
                            print(f"\n[OK] Paiement initialise avec succes!")
                            print(f"Token: {payment_token}")
                            print(f"URL: {payment_url}")
                            
                            return {
                                'success': True,
                                'payment_token': payment_token,
                                'payment_url': payment_url,
                                'message': 'Paiement initialisé avec succès'
                            }
                    
                    # Erreur dans la réponse
                    error_msg = result.get('response_text') or result.get('message') or 'Erreur inconnue'
                    print(f"\n[ERREUR] Erreur LigdiCash: {error_msg}")
                    
                    return {
                        'success': False,
                        'message': f'Erreur LigdiCash: {error_msg}',
                        'response': result
                    }
                    
                except json.JSONDecodeError as e:
                    print(f"\n[ERREUR] Erreur de decodage JSON: {str(e)}")
                    return {
                        'success': False,
                        'message': f'Erreur de format de réponse: {str(e)}',
                        'response_text': response.text
                    }
            else:
                error_msg = f'Erreur HTTP {response.status_code}'
                print(f"\n[ERREUR] {error_msg}")
                
                return {
                    'success': False,
                    'message': error_msg,
                    'http_status': response.status_code,
                    'response_text': response.text
                }
                
        except requests.exceptions.Timeout:
            print("\n[ERREUR] Timeout de la requete (30 secondes)")
            return {
                'success': False,
                'message': 'Timeout de la connexion à LigdiCash (30 secondes)'
            }
            
        except requests.exceptions.RequestException as e:
            print(f"\n[ERREUR] Erreur de requete: {str(e)}")
            return {
                'success': False,
                'message': f'Erreur de connexion à LigdiCash: {str(e)}'
            }
            
        except Exception as e:
            print(f"\n[ERREUR] Erreur inattendue: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f'Erreur inattendue: {str(e)}'
            }
    
    def verifier_paiement(self, payment_token):
        """
        Vérifie le statut d'un paiement
        
        Args:
            payment_token: Token du paiement à vérifier
            
        Returns:
            dict: Résultat de la vérification avec success, status, etc.
        """
        try:
            print(f"\n=== LIGDICASH - Vérification du paiement ===")
            print(f"Token: {payment_token}")
            
            # Préparer la requête de vérification
            data = {
                'token': payment_token
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Apikey': self.api_key,
                'Authorization': f'Bearer {self.auth_token}',
                'User-Agent': 'CahierDeCharges/1.0'
            }
            
            print(f"URL de vérification: {self.verify_url}")
            
            # Envoyer la requête
            response = requests.post(
                self.verify_url,
                json=data,
                headers=headers,
                timeout=15
            )
            
            print(f"Réponse HTTP: {response.status_code}")
            print(f"Contenu: {response.text}")
            
            # Analyser la réponse
            if response.status_code == 200:
                result = response.json()
                
                # Code 00 = Paiement réussi
                if result.get('response_code') == '00':
                    print("[OK] Paiement confirme!")
                    return {
                        'success': True,
                        'status': 'SUCCESS',
                        'transaction': result,
                        'message': 'Paiement confirmé avec succès'
                    }
                # Code 01 = En attente
                elif result.get('response_code') == '01':
                    return {
                        'success': False,
                        'status': 'PENDING',
                        'message': 'Paiement en attente',
                        'transaction': result
                    }
                # Code 02 = Échoué
                elif result.get('response_code') == '02':
                    return {
                        'success': False,
                        'status': 'FAILED',
                        'message': 'Paiement échoué',
                        'transaction': result
                    }
                else:
                    return {
                        'success': False,
                        'status': 'UNKNOWN',
                        'message': result.get('response_text', 'Statut inconnu'),
                        'transaction': result
                    }
            else:
                return {
                    'success': False,
                    'status': 'HTTP_ERROR',
                    'message': f'Erreur HTTP {response.status_code}',
                    'response_text': response.text
                }
                
        except requests.exceptions.RequestException as e:
            print(f"[ERREUR] Erreur de requete: {str(e)}")
            return {
                'success': False,
                'status': 'CONNECTION_ERROR',
                'message': f'Erreur de connexion: {str(e)}'
            }
            
        except Exception as e:
            print(f"[ERREUR] Erreur inattendue: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'status': 'ERROR',
                'message': f'Erreur: {str(e)}'
            }
