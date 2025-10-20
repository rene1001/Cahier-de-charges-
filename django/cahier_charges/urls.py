
from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views
from . import views_abonnement
from . import views_paiement

urlpatterns = [
    # URLs principales
    path('', views.index, name='index'),
    path('mes-cahiers/', views.mes_cahiers, name='mes_cahiers'),
    
    # Gestion des cahiers
    path('cahier/nouveau/', login_required(views.creer_cahier), name='creer_cahier'),
    path('cahier/nouveau/<str:type_projet>/', login_required(views.creer_cahier), name='creer_cahier_type'),
    path('cahier/verifier-limite/', login_required(views.verifier_limite_cahiers), name='verifier_limite_cahiers'),
    path('cahier/supprimer/<int:cahier_id>/', login_required(views.supprimer_cahier), name='supprimer_cahier'),
    
    # Anciennes URLs maintenues pour compatibilité
    path('formulaire/<str:type_projet>/', views.creer_cahier, name='formulaire'),
    path('preview/<int:cahier_id>/', views.preview, name='preview'),
    path('generer-pdf/<int:cahier_id>/', views.generer_pdf, name='generer_pdf'),
    
    # Authentification
    path('authentification/', views.authentification, name='authentification'),
    path('authentification/<int:cahier_id>/', views.authentification, name='authentification_cahier'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    
    # Gestion des abonnements
    path('abonnement/', login_required(views_abonnement.choix_abonnement), name='choix_abonnement'),
    path('abonnement/choix/', login_required(views_abonnement.choix_abonnement), name='abonnement'),  # Alias for backward compatibility
    path('abonnement/nouveau/<int:plan_id>/', login_required(views_abonnement.creer_abonnement), name='creer_abonnement'),
    path('abonnement/annuler/<int:abonnement_id>/', login_required(views_abonnement.annuler_abonnement), name='annuler_abonnement'),
    path('tableau-de-bord/', login_required(views_abonnement.tableau_de_bord), name='tableau_de_bord'),
    
    # Paiements LigdiCash
    path('paiement/ligdicash/initier/<int:plan_id>/', login_required(views_paiement.initier_paiement_ligdicash), name='initier_paiement_ligdicash'),
    path('paiement/ligdicash/notify/', views_paiement.notification_ligdicash, name='notification_ligdicash'),
    path('paiement/ligdicash/retour/', views_paiement.retour_ligdicash, name='retour_ligdicash'),
    path('paiement/ligdicash/annulation/', views_paiement.annulation_ligdicash, name='annulation_ligdicash'),
]
