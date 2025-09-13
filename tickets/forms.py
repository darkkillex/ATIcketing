from django import forms
from django.conf import settings
import os

from .models import Ticket

ALLOWED_EXTS = set(ext.strip().lower() for ext in settings.ATTACHMENTS_ALLOWED_EXTENSIONS)
MAX_SIZE_BYTES = settings.ATTACHMENTS_MAX_SIZE_MB * 1024 * 1024

# ✅ Widget che abilita l'upload multiplo (Django 5 richiede questa property)
class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class NewTicketForm(forms.ModelForm):
    attachments = forms.FileField(
        required=False,
        widget=MultiFileInput(attrs={'multiple': True})
    )

    class Meta:
        model = Ticket
        fields = [
            'title', 'description', 'department',
            'priority', 'impact', 'urgency', 'source_channel',
            'location', 'asset_code',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
        }

    def clean_attachments(self):
        files = self.files.getlist('attachments')
        errors = []
        for f in files:
            # Estensione
            _, ext = os.path.splitext(f.name)
            ext = (ext or '').replace('.', '').lower()
            if ext not in ALLOWED_EXTS:
                errors.append(f"File non consentito: {f.name} (estensione .{ext})")

            # Dimensione
            if f.size > MAX_SIZE_BYTES:
                errors.append(
                    f"{f.name}: dimensione {int(f.size/1024/1024)}MB oltre il limite di "
                    f"{settings.ATTACHMENTS_MAX_SIZE_MB}MB"
                )
        if errors:
            raise forms.ValidationError(errors)
        return files
