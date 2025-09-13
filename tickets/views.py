from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Ticket, Department, Attachment
from .serializers import TicketSerializer
from .services import create_ticket_with_notification
from .forms import NewTicketForm

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
