from django.urls import path
from .views import new_ticket

urlpatterns = [
    path('tickets/new/', new_ticket, name='ticket_new'),
]
