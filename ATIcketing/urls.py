import os

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

#Easter Eggs
def boom(request):
    raise Exception("Boom di test 500!")

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
         name='login'
    ),

    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Admin
    path('admin/', admin.site.urls),

    # UI Tickets (importiamo tutti gli urls contenuti già in tickets\urls.py)
    path('', include('tickets.urls')),

    # API DRF (una sola volta)
    path('api/', include(router.urls)),


    path("_boom/", boom),
]

# Media in dev (o se forzato con SERVE_MEDIA=1)
if settings.DEBUG or os.getenv("SERVE_MEDIA") == "1":
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 404 custom: OK a livello di modulo, non dentro if
def custom_404(request, exception):
    return render(request, "404.html", status=404)

def custom_403(request, exception):
    # Passa RequestContext con i context processors (auth, request, ecc.)
    return render(request, "403.html", status=403)

def custom_500(request):
    # Nota: handler500 NON riceve 'exception'
    return render(request, "500.html", status=500)

handler404 = "ATIcketing.urls.custom_404"
handler403 = "ATIcketing.urls.custom_403"
handler500 = "ATIcketing.urls.custom_500"

