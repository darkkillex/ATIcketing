from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages

from .models import Ticket, Department, Attachment, Comment
from .serializers import TicketSerializer
from .services import create_ticket_with_notification
from .forms import NewTicketForm, CommentForm, AttachmentUploadForm

ADMIN_GROUPS = {'Admin', 'SuperUser', 'Coordinatore'}

def user_in_groups(user, group_names):
    return user.is_superuser or bool(set(g.name for g in user.groups.all()) & set(group_names))

# -------- API REST (già presenti) --------
class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Ticket.objects.select_related('department', 'created_by', 'assignee').order_by('-created_at')
        if user_in_groups(user, ADMIN_GROUPS):
            return qs
        return qs.filter(created_by=user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        data['created_by'] = request.user
        ticket = create_ticket_with_notification(**data)
        out = self.get_serializer(ticket)
        headers = self.get_success_headers(out.data)
        return Response(out.data, status=status.HTTP_201_CREATED, headers=headers)

# -------- Landing + Dashboard (già presenti) --------
def landing(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if user_in_groups(request.user, ADMIN_GROUPS):
        return redirect('dash_team')
    return redirect('dash_operator')

@login_required
def operator_dashboard(request):
    qs = Ticket.objects.select_related('department').filter(created_by=request.user).order_by('-created_at')[:50]
    return render(request, 'dash/operator.html', {'tickets': qs})

@login_required
def team_dashboard(request):
    if not user_in_groups(request.user, ADMIN_GROUPS):
        return redirect('dash_operator')
    qs = Ticket.objects.select_related('department', 'created_by').order_by('-created_at')[:100]
    return render(request, 'dash/team.html', {'tickets': qs})

@login_required
def ticket_detail(request, pk: int):
    ticket = get_object_or_404(
        Ticket.objects.select_related('department', 'created_by', 'assignee')
                      .prefetch_related('comments', 'attachments'),
        pk=pk
    )

    # Autorizzazione: creatore → ok; staff (Admin/SuperUser/Coordinatore) → ok
    if not (ticket.created_by_id == request.user.id or user_in_groups(request.user, ADMIN_GROUPS)):
        return HttpResponseForbidden("Non autorizzato")

    can_change_status = user_in_groups(request.user, ADMIN_GROUPS)

    # Form vuoti per GET
    comment_form = CommentForm()
    attach_form = AttachmentUploadForm()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_comment':
            form = CommentForm(request.POST)
            if form.is_valid():
                is_internal = form.cleaned_data.get('is_internal') if can_change_status else False
                Comment.objects.create(
                    ticket=ticket,
                    author=request.user,
                    body=form.cleaned_data['body'],
                    is_internal=is_internal
                )
                messages.success(request, "Commento aggiunto.")
                return redirect('ticket_detail', pk=ticket.pk)
            else:
                comment_form = form
                messages.error(request, "Correggi gli errori nel commento.")

        elif action == 'add_attachments':
            form = AttachmentUploadForm(request.POST, request.FILES)
            if form.is_valid():
                for f in request.FILES.getlist('attachments'):
                    Attachment.objects.create(
                        ticket=ticket,
                        file=f,
                        original_name=f.name,
                        mime_type=getattr(f, 'content_type', '') or '',
                        size=f.size,
                        uploaded_by=request.user,
                    )
                messages.success(request, "Allegati caricati.")
                return redirect('ticket_detail', pk=ticket.pk)
            else:
                attach_form = form
                messages.error(request, "Verifica i file allegati.")

        elif action == 'change_status' and can_change_status:
            new_status = request.POST.get('status')
            valid = dict(Ticket.STATUS_CHOICES)
            if new_status in valid:
                ticket.status = new_status
                ticket.save(update_fields=['status', 'updated_at'])
                messages.success(request, f"Stato aggiornato a: {valid[new_status]}")
                return redirect('ticket_detail', pk=ticket.pk)
            else:
                messages.error(request, "Stato non valido.")

    # Ordina timeline commenti
    comments = ticket.comments.select_related('author').order_by('created_at')
    attachments = ticket.attachments.order_by('-uploaded_at')

    return render(request, 'tickets/detail.html', {
        'ticket': ticket,
        'comments': comments,
        'attachments': attachments,
        'comment_form': comment_form,
        'attach_form': attach_form,
        'can_change_status': can_change_status,
        'status_choices': Ticket.STATUS_CHOICES,
    })

# -------- UI: Nuovo Ticket (+ allegati) --------
@login_required
def new_ticket(request):
    if request.method == 'POST':
        form = NewTicketForm(request.POST, request.FILES)
        if form.is_valid():
            data = {k: v for k, v in form.cleaned_data.items() if k != 'attachments'}
            data['created_by'] = request.user
            ticket = create_ticket_with_notification(**data)

            # Allegati
            files = request.FILES.getlist('attachments')
            for f in files:
                Attachment.objects.create(
                    ticket=ticket,
                    file=f,
                    original_name=f.name,
                    mime_type=getattr(f, 'content_type', '') or '',
                    size=f.size,
                    uploaded_by=request.user,
                )

            messages.success(request, f"Ticket creato: {ticket.protocol}")
            # Redireziona alla dashboard coerente con il ruolo
            if user_in_groups(request.user, ADMIN_GROUPS):
                return redirect('dash_team')
            return redirect('dash_operator')
        else:
            messages.error(request, "Correggi gli errori nel form.")
    else:
        form = NewTicketForm()

    return render(request, 'tickets/new.html', {'form': form})
