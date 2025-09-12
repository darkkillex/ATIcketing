from django.conf import settings
from django.core.mail import send_mail

def send_new_ticket_notification(ticket):
    dept = ticket.department.code
    to_email = settings.TICKET_DEPARTMENT_EMAILS.get(dept)
    if not to_email:
        return
    subject = f"[{ticket.protocol}] Nuovo ticket - {ticket.title}"
    body = (
        f"Comparto: {ticket.department.code}\n"
        f"Protocollo: {ticket.protocol}\n"
        f"Priorità: {ticket.get_priority_display()}\n"
        f"Creato da: {ticket.created_by}\n"
        f"Data/Ora: {ticket.created_at:%Y-%m-%d %H:%M}\n\n"
        f"Descrizione:\n{ticket.description}\n"
    )
    send_mail(
        subject=subject,
        message=body,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com'),
        recipient_list=[to_email],
        fail_silently=True,
    )
