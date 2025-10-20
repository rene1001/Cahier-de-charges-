from django.core.management.base import BaseCommand
from cahier_charges.models import PlanAbonnement

class Command(BaseCommand):
    help = 'Initialise les plans d\'abonnement avec les valeurs par défaut'

    def handle(self, *args, **options):
        # Plan Starter (Gratuit)
        starter, created = PlanAbonnement.objects.update_or_create(
            nom='gratuit',
            defaults={
                'description': 'Accès aux fonctionnalités de base avec des limites',
                'prix_mensuel_usd': 0,
                'prix_annuel_usd': 0,
                'max_cahiers': 3,
                'telechargement_pdf': 1,
                'partage_pdf': False,
                'collaboration': False,
                'historique_versions': False,
                'modeles_avances': False,
                'support_basique': True,
                'support_prioritaire': False,
                'support_premium': False,
                'ordre_affichage': 1
            }
        )
        
        # Plan Essentiel (10$/mois)
        essentiel, created = PlanAbonnement.objects.update_or_create(
            nom='essentiel',
            defaults={
                'description': 'Idéal pour les professionnels indépendants',
                'prix_mensuel_usd': 10,
                'prix_annuel_usd': 100,  # Prix mensuel x 10 (2 mois gratuits)
                'max_cahiers': 10,
                'telechargement_pdf': 10,  # 10 PDF/mois
                'partage_pdf': True,
                'collaboration': False,
                'historique_versions': False,
                'modeles_avances': False,
                'support_basique': False,
                'support_prioritaire': True,
                'support_premium': False,
                'ordre_affichage': 2
            }
        )
        
        # Plan Pro (20$/mois)
        pro_mensuel, created = PlanAbonnement.objects.update_or_create(
            nom='pro_mensuel',
            defaults={
                'description': 'Solution complète pour les professionnels exigeants',
                'prix_mensuel_usd': 20,
                'prix_annuel_usd': 200,  # Prix mensuel x 10 (2 mois gratuits)
                'max_cahiers': 0,  # Illimité
                'telechargement_pdf': 0,  # Illimité
                'partage_pdf': True,
                'collaboration': True,
                'historique_versions': True,
                'modeles_avances': True,
                'support_basique': False,
                'support_prioritaire': False,
                'support_premium': True,
                'ordre_affichage': 3
            }
        )
        
        # Plan Pro (100$/an)
        pro_annuel, created = PlanAbonnement.objects.update_or_create(
            nom='pro_annuel',
            defaults={
                'description': 'Solution complète avec économie annuelle (équivaut à 8,33€/mois)',
                'prix_mensuel_usd': 20,  # Prix de référence mensuel
                'prix_annuel_usd': 100,  # 58% d'économie sur l'année
                'max_cahiers': 0,  # Illimité
                'telechargement_pdf': 0,  # Illimité
                'partage_pdf': True,
                'collaboration': True,
                'historique_versions': True,
                'modeles_avances': True,
                'support_basique': False,
                'support_prioritaire': False,
                'support_premium': True,
                'ordre_affichage': 4
            }
        )
        
        self.stdout.write(self.style.SUCCESS('Plans d\'abonnement initialisés avec succès!'))
