from django.urls import path
from .views import new_ticket, ticket_detail, operator_export_csv, team_export_csv

urlpatterns = [
    path('tickets/new/', new_ticket, name='ticket_new'),
    path('tickets/<int:pk>/', ticket_detail, name='ticket_detail'),
    path('dash/operator/export/', operator_export_csv, name='dash_operator_export'),
    path('dash/team/export/', team_export_csv, name='dash_team_export'),
]
