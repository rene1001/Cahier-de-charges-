"""
Modèles pour la gestion des transactions de paiement LigdiCash
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from .models import PlanAbonnement, Abonnement
import uuid


class TransactionLigdiCash(models.Model):
    """Modèle pour stocker les transactions LigdiCash"""
    
    STATUT_CHOICES = [
        ('pending', 'En attente'),
        ('successful', 'Réussie'),
        ('failed', 'Échouée'),
        ('expired', 'Expirée'),
        ('canceled', 'Annulée'),
    ]
    
    # Informations de la transaction
    transaction_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_token = models.CharField(max_length=255, unique=True, null=True, blank=True)
    
    # Références
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions_ligdicash')
    plan = models.ForeignKey(PlanAbonnement, on_delete=models.SET_NULL, null=True)
    abonnement = models.ForeignKey(Abonnement, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Détails de paiement
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    devise = models.CharField(max_length=3, default='XOF')
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='pending')
    
    # Réponse LigdiCash
    code_paiement = models.CharField(max_length=50, null=True, blank=True, help_text="Code de réponse LigdiCash")
    message = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Dates
    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)
    date_paiement = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Transaction LigdiCash"
        verbose_name_plural = "Transactions LigdiCash"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['-date_creation']),
            models.Index(fields=['utilisateur', 'statut']),
            models.Index(fields=['payment_token']),
        ]
    
    def __str__(self):
        return f"{self.utilisateur.email} - {self.get_statut_display()} - {self.montant} {self.devise}"
    
    def marquer_comme_reussie(self, code_paiement, message='Paiement accepté'):
        """Marque la transaction comme réussie et crée/met à jour l'abonnement"""
        self.statut = 'successful'
        self.code_paiement = code_paiement
        self.message = message
        self.date_paiement = timezone.now()
        self.save()
        
        # Créer ou mettre à jour l'abonnement
        if self.plan:
            self._creer_ou_mettre_a_jour_abonnement()
    
    def marquer_comme_echouee(self, message='Paiement échoué'):
        """Marque la transaction comme échouée"""
        self.statut = 'failed'
        self.message = message
        self.save()
    
    def marquer_comme_annulee(self, message='Paiement annulé'):
        """Marque la transaction comme annulée"""
        self.statut = 'canceled'
        self.message = message
        self.save()
    
    def _creer_ou_mettre_a_jour_abonnement(self):
        """Crée ou met à jour l'abonnement associé à la transaction"""
        from dateutil.relativedelta import relativedelta
        from datetime import date
        
        # Déterminer la durée de l'abonnement
        if self.plan.nom == 'pro_annuel':
            duree_mois = 12
        else:
            duree_mois = 1
        
        # Vérifier s'il existe déjà un abonnement actif
        abonnement_actif = Abonnement.objects.filter(
            utilisateur=self.utilisateur,
            statut='actif'
        ).first()
        
        if abonnement_actif:
            # Prolonger l'abonnement existant
            if abonnement_actif.date_fin >= date.today():
                # Si l'abonnement est encore actif, ajouter à la date de fin
                nouvelle_date_fin = abonnement_actif.date_fin + relativedelta(months=duree_mois)
            else:
                # Si l'abonnement est expiré, partir d'aujourd'hui
                nouvelle_date_fin = date.today() + relativedelta(months=duree_mois)
            
            abonnement_actif.date_fin = nouvelle_date_fin
            abonnement_actif.plan = self.plan
            abonnement_actif.save()
            
            self.abonnement = abonnement_actif
            self.save()
        else:
            # Créer un nouvel abonnement
            date_debut = date.today()
            date_fin = date_debut + relativedelta(months=duree_mois)
            
            abonnement = Abonnement.objects.create(
                utilisateur=self.utilisateur,
                plan=self.plan,
                date_debut=date_debut,
                date_fin=date_fin,
                statut='actif',
                paiement_recurrent=False
            )
            
            self.abonnement = abonnement
            self.save()
    
    def verifier_statut(self):
        """Vérifie le statut de la transaction auprès de LigdiCash"""
        from .ligdicash_client import LigdiCashClient
        
        if not self.payment_token:
            return {
                'success': False,
                'message': 'Aucun token de paiement disponible'
            }
        
        client = LigdiCashClient()
        return client.verifier_paiement(self.payment_token)
