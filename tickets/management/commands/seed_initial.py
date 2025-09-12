from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from tickets.models import Department, Ticket

class Command(BaseCommand):
    help = "Crea reparti (ICT/WH/SP) e ruoli/permessi base"

    def handle(self, *args, **options):
        deps = [('ICT', 'ICT'), ('WH', 'Magazzino'), ('SP', 'Piano Turni')]
        for code, name in deps:
            d, created = Department.objects.get_or_create(code=code, defaults={'name': name})
            self.stdout.write(self.style.SUCCESS(f"Department {code} {'created' if created else 'exists'}"))

        groups = ['Admin', 'SuperUser', 'Coordinatore', 'Operatore']
        group_objs = {g: Group.objects.get_or_create(name=g)[0] for g in groups}

        ct = ContentType.objects.get_for_model(Ticket)
        perms = {
            'view_all_tickets': Permission.objects.get_or_create(
                codename='view_all_tickets',
                name='Può visualizzare tutti i ticket',
                content_type=ct,
            )[0],
            'assign_tickets': Permission.objects.get_or_create(
                codename='assign_tickets',
                name='Può assegnare ticket',
                content_type=ct,
            )[0],
            'add_ticket': Permission.objects.get(codename='add_ticket', content_type=ct),
            'change_ticket': Permission.objects.get(codename='change_ticket', content_type=ct),
            'view_ticket': Permission.objects.get(codename='view_ticket', content_type=ct),
            'delete_ticket': Permission.objects.get(codename='delete_ticket', content_type=ct),
        }

        group_objs['Admin'].permissions.set(Permission.objects.filter(content_type=ct))
        group_objs['SuperUser'].permissions.set([
            perms['view_all_tickets'], perms['add_ticket'], perms['change_ticket'], perms['view_ticket']
        ])
        group_objs['Coordinatore'].permissions.set([
            perms['view_all_tickets'], perms['add_ticket'], perms['change_ticket'], perms['view_ticket']
        ])
        group_objs['Operatore'].permissions.set([
            perms['add_ticket'], perms['view_ticket']
        ])

        self.stdout.write(self.style.SUCCESS("Seed completato."))
