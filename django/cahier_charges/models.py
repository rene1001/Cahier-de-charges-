
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class PlanAbonnement(models.Model):
    NOM_CHOICES = [
        ('gratuit', 'Starter (Gratuit)'),
        ('essentiel', 'Essentiel (10$/mois)'),
        ('pro_mensuel', 'Pro (20$/mois)'),
        ('pro_annuel', 'Pro (100$/an)'),
    ]
    
    # Informations de base
    nom = models.CharField(max_length=50, choices=NOM_CHOICES, unique=True)
    description = models.TextField(blank=True, help_text="Description du plan pour l'affichage")
    
    # Prix en USD
    prix_mensuel_usd = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        default=0,
        help_text="Prix mensuel en USD"
    )
    prix_annuel_usd = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Prix annuel en USD (avec remise)"
    )
    
    # Propriétés calculées pour la rétrocompatibilité
    @property
    def prix_mensuel(self):
        return self.prix_mensuel_usd
        
    @property
    def prix_annuel(self):
        return self.prix_annuel_usd
    
    # Méthodes de conversion
    @staticmethod
    def usd_to_xof(amount_usd):
        """Convertit un montant USD en FCFA (taux approximatif)"""
        if amount_usd is None:
            return None
        return round(float(amount_usd) * 600, 2)  # 1 USD ≈ 600 FCFA
    
    def get_prix_mensuel_xof(self):
        """Retourne le prix mensuel en FCFA"""
        return self.usd_to_xof(self.prix_mensuel_usd)
    
    def get_prix_annuel_xof(self):
        """Retourne le prix annuel en FCFA"""
        return self.usd_to_xof(self.prix_annuel_usd)
    
    def get_prix_formate(self, periode='mensuel'):
        """Retourne une chaîne formatée avec les prix en USD et FCFA"""
        if periode == 'mensuel':
            usd = self.prix_mensuel_usd
            xof = self.get_prix_mensuel_xof()
            suffix = '/mois'
        else:
            usd = self.prix_annuel_usd
            xof = self.get_prix_annuel_xof()
            suffix = '/an'
            
        if usd is None or usd == 0:
            return "Gratuit"
            
        return f"{usd:.2f}${suffix} (~{xof:,.0f} FCFA)"
    
    # Limites d'utilisation
    max_cahiers = models.PositiveIntegerField(
        default=3,
        help_text="Nombre maximum de cahiers par mois (0 pour illimité)",
        verbose_name="Cahiers de charges / mois"
    )
    telechargement_pdf = models.PositiveIntegerField(
        default=1,
        help_text="Nombre de PDF téléchargeables (0 pour illimité, -1 pour prévisualisation uniquement)",
        verbose_name="Téléchargement PDF"
    )
    
    # Fonctionnalités
    partage_pdf = models.BooleanField(
        default=False,
        help_text="Possibilité de partager les PDF",
        verbose_name="Partage PDF"
    )
    collaboration = models.BooleanField(
        default=False,
        help_text="Fonctionnalités de collaboration en équipe",
        verbose_name="Collaboration"
    )
    historique_versions = models.BooleanField(
        default=False,
        help_text="Historique des versions des cahiers",
        verbose_name="Historique versions"
    )
    modeles_avances = models.BooleanField(
        default=False,
        help_text="Accès aux modèles avancés",
        verbose_name="Modèles avancés"
    )
    
    # Support
    support_basique = models.BooleanField(
        default=True,
        help_text="Support de base par email",
        verbose_name="Support basique"
    )
    support_prioritaire = models.BooleanField(
        default=False,
        help_text="Support prioritaire par email",
        verbose_name="Support prioritaire"
    )
    support_premium = models.BooleanField(
        default=False,
        help_text="Support chat + email prioritaire",
        verbose_name="Support premium"
    )
    
    # Ordre d'affichage
    ordre_affichage = models.PositiveIntegerField(
        default=0,
        help_text="Ordre d'affichage dans la liste des plans (du plus petit au plus grand)"
    )
    
    class Meta:
        verbose_name = "Plan d'abonnement"
        verbose_name_plural = "Plans d'abonnement"
        ordering = ['ordre_affichage']
    
    def __str__(self):
        return self.get_nom_display()


class Abonnement(models.Model):
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('en_attente', 'En attente de paiement'),
        ('expire', 'Expiré'),
        ('annule', 'Annulé'),
    ]
    
    utilisateur = models.OneToOneField(User, on_delete=models.CASCADE, related_name='abonnement')
    plan = models.ForeignKey(PlanAbonnement, on_delete=models.SET_NULL, null=True)
    date_debut = models.DateField(auto_now_add=True)
    date_fin = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif')
    paiement_recurrent = models.BooleanField(default=False)
    derniere_facture = models.DateField(null=True, blank=True)
    prochaine_facture = models.DateField(null=True, blank=True)
    
    def est_actif(self):
        if self.statut != 'actif':
            return False
        if self.date_fin and self.date_fin < timezone.now().date():
            self.statut = 'expire'
            self.save()
            return False
        return True
    
    def __str__(self):
        plan_nom = self.plan.get_nom_display() if self.plan else 'Aucun plan'
        return f"{self.utilisateur.email} - {plan_nom}"


class UtilisateurProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    entreprise = models.CharField(max_length=200, blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    code_postal = models.CharField(max_length=10, blank=True, null=True)
    ville = models.CharField(max_length=100, blank=True, null=True)
    pays = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"Profil de {self.user.email}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Créer automatiquement un abonnement gratuit pour les nouveaux utilisateurs
        profil = UtilisateurProfile.objects.create(user=instance)
        plan_gratuit = PlanAbonnement.objects.get_or_create(nom='gratuit')[0]
        Abonnement.objects.create(
            utilisateur=instance,
            plan=plan_gratuit,
            date_fin=timezone.now().date() + timezone.timedelta(days=30),
            statut='actif'
        )


class CahierUtilisation(models.Model):
    """Suivi de l'utilisation des cahiers par utilisateur"""
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    mois = models.DateField()  # Premier jour du mois suivi
    nb_cahiers_crees = models.PositiveIntegerField(default=0)
    nb_pdf_generes = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ('utilisateur', 'mois')
    
    def __str__(self):
        return f"Utilisation de {self.utilisateur.email} - {self.mois.strftime('%B %Y')}"

class TypeProjet(models.TextChoices):
    SITE_WEB = 'site_web', 'Site Web'
    APPLICATION_MOBILE = 'app_mobile', 'Application Mobile'
    IA = 'ia', 'Intelligence Artificielle'
    MARIAGE = 'mariage', 'Cahier de charges Mariage'
    CONSTRUCTION = 'construction', 'Chantier de Construction'

class CahierCharges(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    type_projet = models.CharField(max_length=20, choices=TypeProjet.choices)
    nom_projet = models.CharField(max_length=200)
    description = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    
    # Champs pour Site Web / App Mobile
    fonctionnalites = models.TextField(blank=True)
    technologies = models.TextField(blank=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    delai = models.CharField(max_length=100, blank=True)
    public_cible = models.TextField(blank=True)
    contraintes_techniques = models.TextField(blank=True)
    
    # Champs pour IA
    type_ia = models.CharField(max_length=200, blank=True)
    donnees_requises = models.TextField(blank=True)
    performance_attendue = models.TextField(blank=True)
    
    # Champs pour Mariage
    date_mariage = models.DateField(null=True, blank=True)
    lieu_mariage = models.CharField(max_length=200, blank=True)
    nombre_invites = models.IntegerField(null=True, blank=True)
    style_mariage = models.CharField(max_length=200, blank=True)
    services_requis = models.TextField(blank=True)
    
    # Champs pour Construction
    type_construction = models.CharField(max_length=200, blank=True)
    surface = models.CharField(max_length=100, blank=True)
    localisation = models.CharField(max_length=200, blank=True)
    materiaux = models.TextField(blank=True)
    normes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.nom_projet} - {self.get_type_projet_display()}"
