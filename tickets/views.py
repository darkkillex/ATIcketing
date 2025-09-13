import csv

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import datetime, time
from django.utils import timezone

from .models import Ticket, Attachment, Comment
from .serializers import TicketSerializer
from .services import create_ticket_with_notification
from .forms import NewTicketForm, CommentForm, AttachmentUploadForm, TicketFilterForm
from .permissions import TicketPermissions, is_staffish
from .emails import (
    send_ticket_status_changed,
    send_new_public_comment,
    send_new_attachments,
)
from .audit import log_status_change, log_comment, log_attachments

# ---------------------- API ----------------------
class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated, TicketPermissions]

    def get_queryset(self):
        user = self.request.user
        qs = Ticket.objects.select_related('department', 'created_by', 'assignee').order_by('-created_at')
        return qs if is_staffish(user) else qs.filter(created_by=user)

    # create custom per usare il service che invia la mail e assegna il protocollo
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        data['created_by'] = request.user
        ticket = create_ticket_with_notification(**data)
        out = self.get_serializer(ticket)
        headers = self.get_success_headers(out.data)
        return Response(out.data, status=status.HTTP_201_CREATED, headers=headers)

# ------------------- LANDING & DASHBOARD -------------------
def landing(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return redirect('dash_team' if is_staffish(request.user) else 'dash_operator')

@login_required
def operator_dashboard(request):
    qs = Ticket.objects.select_related('department').filter(created_by=request.user)

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
    if not is_staffish(request.user):
        return redirect('dash_operator')

    qs = Ticket.objects.select_related('department', 'created_by')

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

# ------------------- EXPORT CSV -------------------
@login_required
def operator_export_csv(request):
    qs = Ticket.objects.select_related('department', 'created_by', 'assignee').filter(created_by=request.user)

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

    qs = qs.order_by('-created_at')[:10000]

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="tickets_operator.csv"'
    response.write('\ufeff')
    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'Protocollo','Titolo','Comparto','Priorità','Stato',
        'Creato da','Creato il','Assegnato a','Impatto','Urgenza','Location','Asset'
    ])
    for t in qs:
        writer.writerow([
            t.protocol, t.title, t.department.code, t.get_priority_display(), t.get_status_display(),
            getattr(t.created_by, 'username', ''), t.created_at.strftime('%d/%m/%Y %H:%M'),
            getattr(t.assignee, 'username', ''), t.get_impact_display(), t.get_urgency_display(),
            t.location or '', t.asset_code or '',
        ])
    return response

@login_required
def team_export_csv(request):
    if not is_staffish(request.user):
        return redirect('dash_operator')

    qs = Ticket.objects.select_related('department', 'created_by', 'assignee')

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

    qs = qs.order_by('-created_at')[:10000]

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="tickets_team.csv"'
    response.write('\ufeff')
    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'Protocollo','Titolo','Comparto','Priorità','Stato',
        'Creato da','Creato il','Assegnato a','Impatto','Urgenza','Location','Asset'
    ])
    for t in qs:
        writer.writerow([
            t.protocol, t.title, t.department.code, t.get_priority_display(), t.get_status_display(),
            getattr(t.created_by, 'username', ''), t.created_at.strftime('%d/%m/%Y %H:%M'),
            getattr(t.assignee, 'username', ''), t.get_impact_display(), t.get_urgency_display(),
            t.location or '', t.asset_code or '',
        ])
    return response

# ------------------- DETTAGLIO & CREAZIONE -------------------
@login_required
def ticket_detail(request, pk: int):
    ticket = get_object_or_404(
        Ticket.objects.select_related('department', 'created_by', 'assignee')
                      .prefetch_related('comments', 'attachments', 'audits'),
        pk=pk
    )

    # Autorizzazione
    if not (ticket.created_by_id == request.user.id or is_staffish(request.user)):
        return HttpResponseForbidden("Non autorizzato")

    can_change_status = is_staffish(request.user)

    comment_form = CommentForm()
    attach_form = AttachmentUploadForm()

    if request.method == 'POST':
        action = request.POST.get('action')

        # ---- Nuovo commento ----
        if action == 'add_comment':
            form = CommentForm(request.POST)
            if form.is_valid():
                is_internal = form.cleaned_data.get('is_internal') if can_change_status else False
                c = Comment.objects.create(
                    ticket=ticket,
                    author=request.user,
                    body=form.cleaned_data['body'],
                    is_internal=is_internal
                )
                # notifica solo se pubblico
                send_new_public_comment(c)
                messages.success(request, "Commento aggiunto.")
                return redirect('ticket_detail', pk=ticket.pk)
            else:
                comment_form = form
                messages.error(request, "Correggi gli errori nel commento.")

        # ---- Nuovi allegati ----
        elif action == 'add_attachments':
            form = AttachmentUploadForm(request.POST, request.FILES)
            if form.is_valid():
                created = []
                for f in request.FILES.getlist('attachments'):
                    created.append(Attachment.objects.create(
                        ticket=ticket,
                        file=f,
                        original_name=f.name,
                        mime_type=getattr(f, 'content_type', '') or '',
                        size=f.size,
                        uploaded_by=request.user,
                    ))
                send_new_attachments(ticket, created, actor=request.user)
                messages.success(request, "Allegati caricati.")
                return redirect('ticket_detail', pk=ticket.pk)
            else:
                attach_form = form
                messages.error(request, "Verifica i file allegati.")

        # ---- Cambio stato (solo staff) ----
        elif action == 'change_status' and can_change_status:
            new_status = request.POST.get('status')
            valid = dict(Ticket.STATUS_CHOICES)
            if new_status in valid:
                old_status_display = ticket.get_status_display()
                ticket.status = new_status
                ticket.save(update_fields=['status', 'updated_at'])
                send_ticket_status_changed(ticket, old_status_display, actor=request.user)
                messages.success(request, f"Stato aggiornato a: {valid[new_status]}")
                return redirect('ticket_detail', pk=ticket.pk)
            else:
                messages.error(request, "Stato non valido.")

        # (nessun altro ramo usa new_status: fuori da qui non viene mai toccata)

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

@login_required
def new_ticket(request):
    if request.method == 'POST':
        form = NewTicketForm(request.POST, request.FILES)
        if form.is_valid():
            data = {k: v for k, v in form.cleaned_data.items() if k != 'attachments'}
            data['created_by'] = request.user
            ticket = create_ticket_with_notification(**data)

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
            return redirect('dash_team' if is_staffish(request.user) else 'dash_operator')
        else:
            messages.error(request, "Correggi gli errori nel form.")
    else:
        form = NewTicketForm()

    return render(request, 'tickets/new.html', {'form': form})


@login_required
def ticket_audit_csv(request, pk: int):
    ticket = get_object_or_404(Ticket, pk=pk)
    if not (ticket.created_by_id == request.user.id or is_staffish(request.user)):
        return HttpResponseForbidden("Non autorizzato")

    audits = ticket.audits.select_related('actor').order_by('created_at')

    resp = HttpResponse(content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = f'attachment; filename="audit_{ticket.protocol}.csv"'
    resp.write('\ufeff')

    w = csv.writer(resp, delimiter=';')
    w.writerow(['Quando', 'Azione', 'Attore', 'Nota', 'Meta(JSON)'])
    for a in audits:
        w.writerow([
            a.created_at.strftime('%d/%m/%Y %H:%M'),
            a.get_action_display(),
            getattr(a.actor, 'username', ''),
            a.note or '',
            (a.meta or {}),
        ])
    return resp

