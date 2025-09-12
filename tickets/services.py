from django.db import transaction
from .models import Ticket
from .emails import send_new_ticket_notification

@transaction.atomic
def create_ticket_with_notification(**kwargs) -> Ticket:
    ticket = Ticket.objects.create(**kwargs)
    send_new_ticket_notification(ticket)
    return ticket
