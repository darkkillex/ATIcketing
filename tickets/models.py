from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MaxLengthValidator
from django.conf import settings

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
    # categorizzazione generica (verrà pilotata da JS e validata lato server)
    category = models.CharField(max_length=100, blank=True, null=True, default="")
    category_other = models.CharField(max_length=100, blank=True, null=True, default="")

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

class Attachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='attachments/%Y/%m/%d/')
    original_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100, blank=True)
    size = models.PositiveIntegerField()
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.original_name} ({self.size} B)"

class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATED = "CREATED", "Creato"
        STATUS_CHANGED = "STATUS_CHANGED", "Cambio stato"
        COMMENT_ADDED = "COMMENT_ADDED", "Nuovo commento"
        ATTACHMENT_ADDED = "ATTACHMENT_ADDED", "Nuovi allegati"
        ASSIGNED = "ASSIGNED", "Assegnato"

    ticket = models.ForeignKey('Ticket', related_name='audits', on_delete=models.CASCADE)
    action = models.CharField(max_length=32, choices=Action.choices)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    note = models.TextField(blank=True, default="")
    meta = models.JSONField(blank=True, null=True)  # dettagli (old/new, filename, ecc.)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        who = self.actor.username if self.actor else "system"
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.action} by {who}"
