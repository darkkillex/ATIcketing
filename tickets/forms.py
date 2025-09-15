from django import forms
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
import os

from .models import Ticket, Department
from .constants import ICT_CATEGORY_CHOICES, ICT_CATEGORY_OTHER

ALLOWED_EXTS = set(ext.strip().lower() for ext in settings.ATTACHMENTS_ALLOWED_EXTENSIONS)
MAX_SIZE_BYTES = settings.ATTACHMENTS_MAX_SIZE_MB * 1024 * 1024

# ✅ Widget che abilita l'upload multiplo (Django 5 richiede questa property)
class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

# ✅ Campo che accetta una LISTA di file (compatibile con MultiFileInput)
class MultiFileField(forms.FileField):
    widget = MultiFileInput

    default_error_messages = {
        'required': _("Seleziona almeno un file."),
        'invalid':  _("Carica un file valido."),
    }

    def to_python(self, data):
        if not data:
            return []
        if isinstance(data, (list, tuple)):
            return list(data)
        file_obj = super().to_python(data)
        return [file_obj] if file_obj else []

    def validate(self, data):
        # 'data' è sempre una lista (anche vuota)
        if self.required and not data:
            raise forms.ValidationError(self.error_messages['required'], code='required')

class NewTicketForm(forms.ModelForm):
    # Allegati (come già avevi)
    attachments = MultiFileField(required=False)

    # 👇 Nuovi campi per categoria ICT
    category = forms.ChoiceField(
        label="Categoria (ICT)",
        choices=[("", "— seleziona —")] + ICT_CATEGORY_CHOICES,
        required=False,
    )
    category_other = forms.CharField(
        label="Specificare (se Altro)",
        max_length=100,
        required=False,
    )

    class Meta:
        model = Ticket
        fields = [
            'title', 'description', 'department',
            'priority', 'impact', 'urgency', 'source_channel',
            'location', 'asset_code', 'category', 'category_other',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
        }

    def __init__(self, *args, department=None, **kwargs):
        """
        Passa `department` dalla view se vuoi pre-selezionare/filter logiche (es. ICT).
        """
        super().__init__(*args, **kwargs)

        # --- i tuoi settaggi esistenti ---
        self.fields['title'].widget.attrs.update({
            'class': 'validate',
            'placeholder': 'Titolo breve',
            'autocomplete': 'off',
        })
        self.fields['description'].widget.attrs.update({
            'class': 'materialize-textarea',
            'placeholder': 'Descrivi il problema / richiesta…',
            'rows': 4,
        })

        for name in ('department', 'priority', 'impact', 'urgency', 'source_channel'):
            if name in self.fields:
                self.fields[name].widget.attrs.update({'class': 'browser-default'})

        if 'location' in self.fields:
            self.fields['location'].widget.attrs.update({
                'class': 'validate', 'placeholder': 'es. Ufficio 2B', 'autocomplete': 'off',
            })
        if 'asset_code' in self.fields:
            self.fields['asset_code'].widget.attrs.update({
                'class': 'validate', 'placeholder': 'es. PC-123', 'autocomplete': 'off',
            })

        try:
            accept = ",".join(f".{ext}" for ext in ALLOWED_EXTS)
            self.fields['attachments'].widget.attrs.update({'accept': accept})
        except Exception:
            pass

        # --- stile per i nuovi campi categoria ---
        self.fields['category'].widget.attrs.update({'class': 'browser-default'})
        self.fields['category_other'].widget.attrs.update({
            'class': 'validate',
            'placeholder': 'Inserisci la categoria',
            'autocomplete': 'off',
        })

        # salva il reparto passato dalla view (se presente) per usarlo in clean()
        self._preset_department = department

    def clean(self):
        cleaned = super().clean()

        # quale reparto è selezionato effettivamente?
        dep = self._preset_department or cleaned.get('department')
        dep_code = getattr(dep, 'code', None)

        cat = (cleaned.get('category') or "").strip()
        other = (cleaned.get('category_other') or "").strip()

        if dep_code == "ICT":
            # per ICT: la categoria è richiesta
            if not cat:
                self.add_error('category', "Seleziona una categoria.")
            # se "Altro", richiedi specifica
            if cat == "OTHER" and not other:
                self.add_error('category_other', "Specifica la categoria se hai scelto 'Altro'.")
            # se NON "Altro", svuota l'eventuale testo digitato
            if cat != "OTHER":
                cleaned['category_other'] = ""
        else:
            # non ICT: non salviamo nulla per la categoria
            cleaned['category'] = ""
            cleaned['category_other'] = ""

        return cleaned

    def clean_attachments(self):
        files = self.cleaned_data.get('attachments') or []
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

# --- Commenti e upload aggiuntivo ---
class CommentForm(forms.Form):
    body = forms.CharField(
        label="Commento",
        widget=forms.Textarea(attrs={'rows': 4}),
        required=True
    )
    is_internal = forms.BooleanField(
        label="Commento interno (visibile solo allo staff)",
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['body'].widget.attrs.update({
            'class': 'materialize-textarea',
            'placeholder': 'Scrivi un commento…',
            'rows': 4,
        })


class AttachmentUploadForm(forms.Form):
    attachments = MultiFileField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            accept = ",".join(f".{ext}" for ext in ALLOWED_EXTS)
            self.fields['attachments'].widget.attrs.update({'accept': accept})
        except Exception:
            pass

    def clean_attachments(self):
        files = self.cleaned_data.get('attachments') or []
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

class TicketFilterForm(forms.Form):
    q = forms.CharField(label="Testo", required=False)
    status = forms.ChoiceField(label="Stato", required=False)
    priority = forms.ChoiceField(label="Priorità", required=False)
    department = forms.ChoiceField(label="Comparto", required=False)
    date_from = forms.DateField(
        label="Dal", required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d', '%d/%m/%Y']
    )
    date_to = forms.DateField(
        label="Al", required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d', '%d/%m/%Y']
    )
    page_size = forms.ChoiceField(
        label="Per pagina", required=False,
        choices=[('25', '25'), ('50', '50'), ('100', '100')], initial='25'
    )
    mine_only = forms.BooleanField(label="Solo miei", required=False)

    def __init__(self, *args, user=None, is_team=False, **kwargs):
        super().__init__(*args, **kwargs)
        # Scelte dinamiche
        self.fields['status'].choices = [('', 'Tutti')] + list(Ticket.STATUS_CHOICES)
        self.fields['priority'].choices = [('', 'Tutte')] + list(Ticket.PRIORITY_CHOICES)
        deps = Department.objects.all().order_by('code').values_list('id', 'code')
        self.fields['department'].choices = [('', 'Tutti')] + [(str(i), c) for i, c in deps]
        # Style Materialize per select
        for name in ('status', 'priority', 'department', 'page_size'):
            self.fields[name].widget.attrs['class'] = 'browser-default'
        # L'operatore non vede "Solo miei"
        if not is_team:
            self.fields.pop('mine_only', None)
        if 'q' in self.fields:
            self.fields['q'].widget.attrs.update({
                'class': 'validate',
                'placeholder': 'Cerca in titolo/descrizione/protocollo…',
                'autocomplete': 'off',
            })
        for name in ('date_from', 'date_to'):
            if name in self.fields:
                self.fields[name].widget.attrs.update({'class': 'validate'})

