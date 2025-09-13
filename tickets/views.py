from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import datetime, time
from django.utils import timezone


from .models import Ticket, Department, Attachment, Comment
from .serializers import TicketSerializer
from .services import create_ticket_with_notification
from .forms import NewTicketForm, CommentForm, AttachmentUploadForm, TicketFilterForm

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
    # Base: solo i ticket dell'utente
    qs = Ticket.objects.select_related('department').filter(created_by=request.user)

    # Filtri
    from .forms import TicketFilterForm
    form = TicketFilterForm(request.GET or None, user=request.user, is_team=False)
    if form.is_valid():
        cd = form.cleaned_data
        q = cd.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(protocol__icontains=q))
        if cd.get('status'):
            qs = qs.filter(status=cd['status'])
        if cd.get('priority'):
            qs = qs.filter(priority=cd['priority'])
        if cd.get('department'):
            qs = qs.filter(department_id=int(cd['department']))
        if cd.get('date_from'):
            start = timezone.make_aware(datetime.combine(cd['date_from'], time.min))
            qs = qs.filter(created_at__gte=start)
        if cd.get('date_to'):
            end = timezone.make_aware(datetime.combine(cd['date_to'], time.max))
            qs = qs.filter(created_at__lte=end)
        page_size = int(cd.get('page_size') or 25)
    else:
        page_size = 25

    qs = qs.order_by('-created_at')

    # Paginazione
    paginator = Paginator(qs, page_size)
    page_number = request.GET.get('page') or 1
    page_obj = paginator.get_page(page_number)

    return render(request, 'dash/operator.html', {
        'filter_form': form,
        'tickets': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
    })

@login_required
def team_dashboard(request):
    if not user_in_groups(request.user, ADMIN_GROUPS):
        return redirect('dash_operator')

    qs = Ticket.objects.select_related('department', 'created_by')

    from .forms import TicketFilterForm
    form = TicketFilterForm(request.GET or None, user=request.user, is_team=True)
    if form.is_valid():
        cd = form.cleaned_data
        q = cd.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(protocol__icontains=q))
        if cd.get('status'):
            qs = qs.filter(status=cd['status'])
        if cd.get('priority'):
            qs = qs.filter(priority=cd['priority'])
        if cd.get('department'):
            qs = qs.filter(department_id=int(cd['department']))
        if cd.get('date_from'):
            start = timezone.make_aware(datetime.combine(cd['date_from'], time.min))
            qs = qs.filter(created_at__gte=start)
        if cd.get('date_to'):
            end = timezone.make_aware(datetime.combine(cd['date_to'], time.max))
            qs = qs.filter(created_at__lte=end)
        if cd.get('mine_only'):
            qs = qs.filter(created_by=request.user)
        page_size = int(cd.get('page_size') or 25)
    else:
        page_size = 25

    qs = qs.order_by('-created_at')

    paginator = Paginator(qs, page_size)
    page_number = request.GET.get('page') or 1
    page_obj = paginator.get_page(page_number)

    return render(request, 'dash/team.html', {
        'filter_form': form,
        'tickets': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
    })

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
