from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render

from tickets.views import (
    TicketViewSet,
    landing,
    operator_dashboard,
    team_dashboard,
    new_ticket,
    ticket_detail,
    operator_export_csv,
    team_export_csv,
    ticket_audit_csv,
)

router = DefaultRouter()
router.register(r'tickets', TicketViewSet, basename='ticket')

urlpatterns = [
    # Landing & dashboard
    path('', landing, name='landing'),
    path('dash/operator/', operator_dashboard, name='dash_operator'),
    path('dash/team/', team_dashboard, name='dash_team'),

    # Auth
    path(
        'accounts/login/',
         auth_views.LoginView.as_view(
            template_name='auth/login.html',
            redirect_authenticated_user=True
         ),
         name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Admin
    path('admin/', admin.site.urls),

    # UI Tickets (una sola volta)
    path('tickets/new/', new_ticket, name='ticket_new'),
    path('tickets/<int:pk>/', ticket_detail, name='ticket_detail'),
    path('tickets/operator.csv', operator_export_csv, name='operator_export_csv'),
    path('tickets/team.csv', team_export_csv, name='team_export_csv'),
    path('tickets/<int:pk>/audit.csv', ticket_audit_csv, name='ticket_audit_csv'),

    # API DRF (una sola volta)
    path('api/', include(router.urls)),

    # Alias legacy (tienili solo finché non aggiorni i template)
    path('dash/operator/export.csv', operator_export_csv, name='dash_operator_export'),
    path('dash/team/export.csv', team_export_csv, name='dash_team_export'),
]

# Media (solo in dev)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 404 custom: OK a livello di modulo, non dentro if
def custom_404(request, exception):
    return render(request, "404.html", status=404)

handler404 = "ATIcketing.urls.custom_404"
