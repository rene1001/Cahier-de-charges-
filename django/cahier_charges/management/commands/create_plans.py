from django.core.management.base import BaseCommand
from cahier_charges.models import PlanAbonnement
from decimal import Decimal

class Command(BaseCommand):
    help = 'Crée les plans d\'abonnement par défaut s\'ils n\'existent pas déjà.'

    def handle(self, *args, **options):
        plans = [
            {
                'nom': 'gratuit',
                'description': 'Accès aux fonctionnalités de base avec 3 cahiers et 1 téléchargement PDF par mois.',
                'prix_mensuel': Decimal('0.00'),
                'prix_annuel': Decimal('0.00'),
                'max_cahiers': 3,
                'telechargement_pdf': 1,
                'support_basique': True,
                'support_prioritaire': False,
                'support_premium': False,
                'partage_pdf': False,
                'collaboration': False,
                'historique_versions': False,
                'modeles_avances': False,
                'ordre_affichage': 1
            },
            {
                'nom': 'essentiel',
                'description': 'Idéal pour les petits projets avec 10 cahiers et 5 téléchargements PDF par mois.',
                'prix_mensuel': Decimal('10.00'),
                'prix_annuel': Decimal('100.00'),
                'max_cahiers': 10,
                'telechargement_pdf': 5,
                'support_basique': True,
                'support_prioritaire': True,
                'support_premium': False,
                'partage_pdf': True,
                'collaboration': False,
                'historique_versions': False,
                'modeles_avances': False,
                'ordre_affichage': 2
            },
            {
                'nom': 'pro_mensuel',
                'description': 'Pour les professionnels avec 100 cahiers et 50 téléchargements PDF par mois.',
                'prix_mensuel': Decimal('20.00'),
                'prix_annuel': Decimal('200.00'),
                'max_cahiers': 100,
                'telechargement_pdf': 50,
                'support_basique': True,
                'support_prioritaire': True,
                'support_premium': True,
                'partage_pdf': True,
                'collaboration': True,
                'historique_versions': True,
                'modeles_avances': True,
                'ordre_affichage': 3
            },
            {
                'nom': 'pro_annuel',
                'description': 'Abonnement annuel Pro avec 100 cahiers et 50 téléchargements PDF par mois. Économisez 2 mois !',
                'prix_mensuel': Decimal('20.00'),
                'prix_annuel': Decimal('200.00'),
                'max_cahiers': 100,
                'telechargement_pdf': 50,
                'support_basique': True,
                'support_prioritaire': True,
                'support_premium': True,
                'partage_pdf': True,
                'collaboration': True,
                'historique_versions': True,
                'modeles_avances': True,
                'ordre_affichage': 4
            }
        ]

        for plan_data in plans:
            nom = plan_data.pop('nom')
            plan, created = PlanAbonnement.objects.get_or_create(
                nom=nom,
                defaults=plan_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Plan {plan.get_nom_display()} créé avec succès.'))
            else:
                self.stdout.write(self.style.WARNING(f'Le plan {plan.get_nom_display()} existe déjà.'))
