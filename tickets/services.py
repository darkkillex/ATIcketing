from django.db import transaction
from .models import Ticket
from .emails import send_new_ticket_notification
from .audit import log_created

@transaction.atomic
def create_ticket_with_notification(**kwargs) -> Ticket:
    ticket = Ticket.objects.create(**kwargs)

    # Audit: registra la creazione (actor = created_by se presente)
    actor = kwargs.get('created_by')
    log_created(ticket, actor)

    # Notifica di nuovo ticket
    send_new_ticket_notification(ticket)
    return ticket
