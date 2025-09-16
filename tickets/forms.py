from django import forms
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import os

from .models import Ticket, Department
from .constants import (
    ICT_CATEGORY_CHOICES, WH_CATEGORY_CHOICES, SP_CATEGORY_CHOICES, OTHER_CODE
)

# Mappa reparto → scelte categoria
CATEGORY_CHOICES_BY_DEPARTMENT = {
    "ICT": ICT_CATEGORY_CHOICES,
    "WH":  WH_CATEGORY_CHOICES,
    "SP":  SP_CATEGORY_CHOICES,
}

# Unione di tutte le scelte categoria, così il POST inviato dal JS è sempre valido lato form
ALL_CATEGORY_CHOICES = [("", "— seleziona —")] + ICT_CATEGORY_CHOICES + WH_CATEGORY_CHOICES + SP_CATEGORY_CHOICES

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
    # Allegati
    attachments = MultiFileField(required=False)

    # Campi categoria (form-only: category_other)
    category = forms.ChoiceField(
        label="Categoria",
        choices=ALL_CATEGORY_CHOICES,
        required=False,
    )
    category_other = forms.CharField(
        label="Dettaglio (se Altro)",
        max_length=150,
        required=False,
    )

    class Meta:
        model = Ticket
        fields = [
            'title', 'description', 'department',
            'priority', 'impact', 'urgency', 'source_channel',
            'location', 'asset_code',
            'category',            #  è un field del MODELLO
            # 'category_other',    #  form-only: NON inserirlo nei fields del modello
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
        }

    def __init__(self, *args, department=None, **kwargs):
        """
        `department` può essere passato dalla view se vuoi pre-selezionare e bloccare il reparto.
        """
        super().__init__(*args, **kwargs)

        # Style/UX
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

        # nuovi campi
        self.fields['category'].widget.attrs.update({'class': 'browser-default'})
        self.fields['category_other'].widget.attrs.update({
            'class': 'validate',
            'placeholder': 'Specifica se scegli "Altro"',
            'autocomplete': 'off',
        })

        # reparto passato dalla view (opzionale, usato in clean)
        self._preset_department = department

    def clean(self):
        cleaned = super().clean()

        dep = getattr(self, "_preset_department", None) or cleaned.get('department')
        dep_code = getattr(dep, 'code', None) or ""
        cat = (cleaned.get('category') or "").strip()
        other = (cleaned.get('category_other') or "").strip()

        # Reparti che hanno categorie
        dep_has_categories = dep_code in ("ICT", "WH", "SP")

        if dep_has_categories:
            # categoria richiesta
            if not cat:
                self.add_error('category', "Seleziona una categoria.")
            # se 'Altro', obbliga specifica
            if cat == OTHER_CODE and not other:
                self.add_error('category_other', "Specifica la categoria se hai scelto 'Altro'.")
            # se NON 'Altro', svuota l'eventuale testo
            if cat != OTHER_CODE:
                cleaned['category_other'] = ""
        else:
            # reparti senza categorie: non salvare nulla
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
            _, ext = os.path.splitext(f.name)
            ext = (ext or '').replace('.', '').lower()
            if ext not in ALLOWED_EXTS:
                errors.append(f"File non consentito: {f.name} (estensione .{ext})")
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

    # 👇 nuovi campi filtro
    category = forms.ChoiceField(label="Categoria", required=False)
    category_other = forms.CharField(label="Specifica (se Altro)", required=False)

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

        # Scelte dinamiche base
        self.fields['status'].choices = [('', 'Tutti')] + list(Ticket.STATUS_CHOICES)
        self.fields['priority'].choices = [('', 'Tutte')] + list(Ticket.PRIORITY_CHOICES)
        deps = Department.objects.all().order_by('code').values_list('id', 'code')
        self.fields['department'].choices = [('', 'Tutti')] + [(str(i), c) for i, c in deps]

        # Style Materialize per select
        for name in ('status', 'priority', 'department', 'page_size', 'category'):
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

        # --- Scelte dinamiche per CATEGORIA in base al reparto selezionato ---
        dep_choice_id = (self.data.get('department') or self.initial.get('department') or '').strip()
        cat_choices = [('', 'Tutte')]
        if dep_choice_id:
            try:
                dep_code = Department.objects.filter(id=int(dep_choice_id)).values_list('code', flat=True).first()
            except (ValueError, TypeError):
                dep_code = None
            if dep_code and dep_code in CATEGORY_CHOICES_BY_DEPARTMENT:
                cat_choices += CATEGORY_CHOICES_BY_DEPARTMENT[dep_code]
        self.fields['category'].choices = cat_choices
