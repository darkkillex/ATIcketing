from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(choices=[('ICT', 'ICT'), ('WH', 'Magazzino (Warehouse)'), ('SP', 'Piano Turni (Scheduling)')], max_length=3, unique=True)),
                ('name', models.CharField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='Counter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dept_code', models.CharField(max_length=3)),
                ('iso_year', models.IntegerField()),
                ('iso_week', models.IntegerField()),
                ('last_number', models.IntegerField(default=0)),
            ],
            options={'unique_together': {('dept_code', 'iso_year', 'iso_week')}},
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('protocol', models.CharField(editable=False, max_length=32, unique=True)),
                ('title', models.CharField(max_length=120)),
                ('description', models.TextField()),
                ('status', models.CharField(choices=[('NEW', 'Nuovo'), ('INP', 'In lavorazione'), ('WAI', 'In attesa utente'), ('RES', 'Risolto'), ('CLO', 'Chiuso')], default='NEW', max_length=3)),
                ('priority', models.CharField(choices=[('LOW', 'Bassa'), ('MED', 'Media'), ('HIGH', 'Alta'), ('BLK', 'Bloccante')], default='MED', max_length=4)),
                ('impact', models.CharField(choices=[('ONE', 'Utente singolo'), ('TEAM', 'Team'), ('DEPT', 'Reparto'), ('SITE', 'Sito')], default='ONE', max_length=4)),
                ('urgency', models.CharField(choices=[('LOW', 'Bassa'), ('MED', 'Media'), ('HIGH', 'Alta')], default='MED', max_length=4)),
                ('source_channel', models.CharField(choices=[('WEB', 'Portale'), ('EML', 'Email importata'), ('TEL', 'Telefono')], default='WEB', max_length=3)),
                ('location', models.CharField(blank=True, max_length=120)),
                ('asset_code', models.CharField(blank=True, max_length=60)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assignee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_tickets', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_tickets', to=settings.AUTH_USER_MODEL)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='tickets', to='tickets.department')),
            ],
            options={
                'permissions': [('view_all_tickets', 'Può visualizzare tutti i ticket'), ('assign_tickets', 'Può assegnare ticket')],
            },
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField()),
                ('is_internal', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('ticket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='tickets.ticket')),
            ],
        ),
    ]
