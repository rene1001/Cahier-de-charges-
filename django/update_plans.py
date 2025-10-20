from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder

def check_migrations():
    """Vérifie si toutes les migrations ont été appliquées"""
    executor = MigrationExecutor(connection)
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
    return not bool(plan)

def update_subscription_plans():
    from cahier_charges.models import PlanAbonnement
    
    # Mise à jour des plans avec les prix en USD
    plans_data = [
        {
            'nom': 'gratuit',
            'prix_mensuel_usd': 0,
            'prix_annuel_usd': 0,
            'max_cahiers': 3,
            'telechargement_pdf': 1,
            'partage_pdf': False,
            'collaboration': False,
            'historique_versions': False,
            'modeles_avances': False,
            'support_prioritaire': False,
            'support_premium': False
        },
        {
            'nom': 'essentiel',
            'prix_mensuel_usd': 10,
            'prix_annuel_usd': 100,  # 2 mois gratuits
            'max_cahiers': 10,
            'telechargement_pdf': 10,
            'partage_pdf': True,
            'collaboration': False,
            'historique_versions': False,
            'modeles_avances': False,
            'support_prioritaire': True,
            'support_premium': False
        },
        {
            'nom': 'pro_mensuel',
            'prix_mensuel_usd': 20,
            'prix_annuel_usd': 200,  # 2 mois gratuits
            'max_cahiers': 50,
            'telechargement_pdf': 50,
            'partage_pdf': True,
            'collaboration': True,
            'historique_versions': True,
            'modeles_avances': True,
            'support_prioritaire': True,
            'support_premium': False
        },
        {
            'nom': 'pro_annuel',
            'prix_mensuel_usd': 16.67,  # 20 * 10 / 12
            'prix_annuel_usd': 200,     # 2 mois gratuits
            'max_cahiers': 50,
            'telechargement_pdf': 0,  # illimité
            'partage_pdf': True,
            'collaboration': True,
            'historique_versions': True,
            'modeles_avances': True,
            'support_prioritaire': True,
            'support_premium': True
        }
    ]
    
    for plan_data in plans_data:
        nom = plan_data.pop('nom')
        PlanAbonnement.objects.update_or_create(
            nom=nom,
            defaults=plan_data
        )
        print(f"Plan mis à jour : {nom}")

if __name__ == "__main__":
    import os
    import django
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
    django.setup()
    
    if not check_migrations():
        print("Erreur : Toutes les migrations n'ont pas été appliquées.")
        print("Veuillez exécuter 'python manage.py migrate' avant de continuer.")
    else:
        update_subscription_plans()
        print("Mise à jour des plans d'abonnement terminée avec succès !")
