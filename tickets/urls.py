# tickets/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # UI
    path('tickets/new/', views.new_ticket, name='ticket_new'),
    path('tickets/<int:pk>/', views.ticket_detail, name='ticket_detail'),

    # Export CSV (nomi “canonici” usati nei template)
    path('tickets/operator.csv', views.operator_export_csv, name='operator_export_csv'),
    path('tickets/team.csv', views.team_export_csv, name='team_export_csv'),

    # Alias "legacy" (se qualche template o link vecchio usa ancora questi nomi)
    path('dash/operator/export.csv', views.operator_export_csv, name='dash_operator_export'),
    path('dash/team/export.csv', views.team_export_csv, name='dash_team_export'),

    # Export audit del singolo ticket (comodo dalla detail page)
    path('tickets/<int:pk>/audit.csv', views.ticket_audit_csv, name='ticket_audit_csv'),
]
