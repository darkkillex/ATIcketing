from django.urls import path
from .views import new_ticket, ticket_detail

urlpatterns = [
    path('tickets/new/', new_ticket, name='ticket_new'),
    path('tickets/<int:pk>/', ticket_detail, name='ticket_detail'),
]
