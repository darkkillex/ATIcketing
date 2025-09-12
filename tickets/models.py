from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MaxLengthValidator

User = get_user_model()

class Department(models.Model):
    CODE_CHOICES = [
        ('ICT', 'ICT'),
        ('WH', 'Magazzino (Warehouse)'),
        ('SP', 'Piano Turni (Scheduling)'),
    ]
    code = models.CharField(max_length=3, choices=CODE_CHOICES, unique=True)
    name = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.code} - {self.name}"

class Counter(models.Model):
    dept_code = models.CharField(max_length=3)
    iso_year = models.IntegerField()
    iso_week = models.IntegerField()
    last_number = models.IntegerField(default=0)

    class Meta:
        unique_together = ('dept_code', 'iso_year', 'iso_week')

    def __str__(self):
        return f"{self.dept_code}-{self.iso_year}-W{self.iso_week}: {self.last_number}"

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'Nuovo'),
        ('INP', 'In lavorazione'),
        ('WAI', 'In attesa utente'),
        ('RES', 'Risolto'),
        ('CLO', 'Chiuso'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Bassa'),
        ('MED', 'Media'),
        ('HIGH', 'Alta'),
        ('BLK', 'Bloccante'),
    ]

    IMPACT_CHOICES = [
        ('ONE', 'Utente singolo'),
        ('TEAM', 'Team'),
        ('DEPT', 'Reparto'),
        ('SITE', 'Sito'),
    ]

    URGENCY_CHOICES = [
        ('LOW', 'Bassa'),
        ('MED', 'Media'),
        ('HIGH', 'Alta'),
    ]

    SOURCE_CHOICES = [
        ('WEB', 'Portale'),
        ('EML', 'Email importata'),
        ('TEL', 'Telefono'),
    ]

    protocol = models.CharField(max_length=32, unique=True, editable=False)
    title = models.CharField(max_length=120)
    description = models.TextField(validators=[MaxLengthValidator(10000)])
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='NEW')
    priority = models.CharField(max_length=4, choices=PRIORITY_CHOICES, default='MED')
    impact = models.CharField(max_length=4, choices=IMPACT_CHOICES, default='ONE')
    urgency = models.CharField(max_length=4, choices=URGENCY_CHOICES, default='MED')
    source_channel = models.CharField(max_length=3, choices=SOURCE_CHOICES, default='WEB')

    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='tickets')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_tickets')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')

    location = models.CharField(max_length=120, blank=True)
    asset_code = models.CharField(max_length=60, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = [
            ("view_all_tickets", "Può visualizzare tutti i ticket"),
            ("assign_tickets", "Può assegnare ticket"),
        ]

    def __str__(self):
        return f"{self.protocol or '(no-proto)'} - {self.title[:40]}"

    @classmethod
    def generate_protocol(cls, dept_code: str) -> str:
        now = timezone.localtime()
        iso_year, iso_week, _ = now.isocalendar()
        with transaction.atomic():
            try:
                counter = Counter.objects.select_for_update().get(
                    dept_code=dept_code, iso_year=iso_year, iso_week=iso_week
                )
            except Counter.DoesNotExist:
                counter = Counter.objects.create(
                    dept_code=dept_code, iso_year=iso_year, iso_week=iso_week, last_number=0
                )
                counter = Counter.objects.select_for_update().get(pk=counter.pk)
            counter.last_number += 1
            counter.save(update_fields=['last_number'])
            number = f"{counter.last_number:04d}"
        return f"{dept_code}-{iso_year}-{iso_week:02d}-{number}"

    def save(self, *args, **kwargs):
        if not self.protocol and self.department_id:
            self.protocol = self.generate_protocol(self.department.code)
        super().save(*args, **kwargs)

class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    body = models.TextField()
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author} on {self.ticket.protocol}"
