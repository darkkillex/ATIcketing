from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from tickets.views import TicketViewSet, landing, operator_dashboard, team_dashboard
from django.contrib.auth import views as auth_views

router = DefaultRouter()
router.register(r'tickets', TicketViewSet, basename='ticket')

urlpatterns = [
    path('', landing, name='landing'),
    path('dash/operator/', operator_dashboard, name='dash_operator'),
    path('dash/team/', team_dashboard, name='dash_team'),

    path('accounts/login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
