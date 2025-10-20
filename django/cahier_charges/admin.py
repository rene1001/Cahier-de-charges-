from django.contrib import admin
from .models import PlanAbonnement, Abonnement, UtilisateurProfile, CahierUtilisation, CahierCharges
from .models_paiement import TransactionLigdiCash

@admin.register(PlanAbonnement)
class PlanAbonnementAdmin(admin.ModelAdmin):
    list_display = ('get_nom_display', 'get_prix_mensuel_display', 'get_prix_annuel_display', 'max_cahiers', 'telechargement_pdf', 'partage_pdf', 'collaboration')
    list_filter = ('partage_pdf', 'collaboration', 'historique_versions', 'modeles_avances')
    search_fields = ('nom', 'description')
    
    def get_prix_mensuel_display(self, obj):
        return obj.get_prix_formate('mensuel')
    get_prix_mensuel_display.short_description = 'Prix Mensuel'
    
    def get_prix_annuel_display(self, obj):
        return obj.get_prix_formate('annuel') if obj.prix_annuel_usd else 'N/A'
    get_prix_annuel_display.short_description = 'Prix Annuel'
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'description')
        }),
        ('Prix en USD', {
            'fields': ('prix_mensuel_usd', 'prix_annuel_usd'),
            'description': 'Définir les prix en USD. Les équivalents en FCFA seront calculés automatiquement.'
        }),
        ('Limites', {
            'fields': ('max_cahiers', 'telechargement_pdf')
        }),
        ('Fonctionnalités', {
            'fields': ('partage_pdf', 'collaboration', 'historique_versions', 'modeles_avances')
        }),
        ('Support', {
            'fields': ('support_basique', 'support_prioritaire', 'support_premium'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Abonnement)
class AbonnementAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'plan', 'date_debut', 'date_fin', 'statut', 'paiement_recurrent')
    list_filter = ('statut', 'paiement_recurrent', 'plan')
    search_fields = ('utilisateur__username', 'utilisateur__email')
    date_hierarchy = 'date_debut'

@admin.register(UtilisateurProfile)
class UtilisateurProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'entreprise', 'telephone')
    search_fields = ('user__username', 'user__email', 'entreprise', 'telephone')

@admin.register(CahierUtilisation)
class CahierUtilisationAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'mois', 'nb_cahiers_crees', 'nb_pdf_generes')
    list_filter = ('mois',)
    search_fields = ('utilisateur__username',)
    date_hierarchy = 'mois'

@admin.register(CahierCharges)
class CahierChargesAdmin(admin.ModelAdmin):
    list_display = ('nom_projet', 'utilisateur', 'type_projet', 'date_creation')
    list_filter = ('type_projet', 'date_creation')
    search_fields = ('nom_projet', 'description', 'utilisateur__username')
    date_hierarchy = 'date_creation'

@admin.register(TransactionLigdiCash)
class TransactionLigdiCashAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'utilisateur', 'plan', 'montant', 'devise', 'statut', 'date_creation', 'date_paiement')
    list_filter = ('statut', 'devise', 'date_creation', 'plan')
    search_fields = ('transaction_id', 'payment_token', 'utilisateur__username', 'utilisateur__email')
    readonly_fields = ('transaction_id', 'payment_token', 'date_creation', 'date_mise_a_jour', 'date_paiement', 'metadata')
    date_hierarchy = 'date_creation'
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('transaction_id', 'payment_token', 'statut')
        }),
        ('Utilisateur et Plan', {
            'fields': ('utilisateur', 'plan', 'abonnement')
        }),
        ('Détails de paiement', {
            'fields': ('montant', 'devise', 'code_paiement', 'message')
        }),
        ('Métadonnées', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_mise_a_jour', 'date_paiement')
        }),
    )
    
    def has_add_permission(self, request):
        # Empêcher la création manuelle de transactions
        return False
