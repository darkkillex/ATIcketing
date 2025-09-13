from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def _dedupe(seq):
    seen = set()
    out = []
    for x in seq:
        if x and x not in seen:
            out.append(x)
            seen.add(x)
    return out

def _department_email(ticket):
    return settings.TICKET_DEPARTMENT_EMAILS.get(ticket.department.code)

def _ticket_url(ticket):
    base = getattr(settings, 'SITE_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
    return f"{base}/tickets/{ticket.id}/"

def _send_templated(subject_tpl, txt_tpl, html_tpl, ctx, to_list):
    to = _dedupe([e for e in to_list if e])
    if not to:
        return
    subject = render_to_string(subject_tpl, ctx).strip()
    html_body = render_to_string(html_tpl, ctx)
    text_body = render_to_string(txt_tpl, ctx)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=strip_tags(html_body) or text_body,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
        to=to,
    )
    msg.attach_alternative(html_body, "text/html")
    try:
        msg.send(fail_silently=True)
    except Exception:
        # In dev con MailHog di solito non succede; fail_silently per robustezza
        pass

def _recipients(ticket, include_department=True, include_creator=True, include_assignee=True):
    out = []
    if include_department:
        out.append(_department_email(ticket))
    if include_creator and getattr(ticket.created_by, 'email', None):
        out.append(ticket.created_by.email)
    if include_assignee and ticket.assignee and getattr(ticket.assignee, 'email', None):
        out.append(ticket.assignee.email)
    return _dedupe(out)

def send_new_ticket_notification(ticket):
    ctx = {
        'ticket': ticket,
        'base_url': getattr(settings, 'SITE_BASE_URL', 'http://127.0.0.1:8000'),
        'ticket_url': _ticket_url(ticket),
    }
    to = _recipients(ticket, include_department=True, include_creator=True, include_assignee=True)
    _send_templated(
        'emails/new_ticket_subject.txt',
        'emails/new_ticket.txt',
        'emails/new_ticket.html',
        ctx, to
    )

def send_ticket_status_changed(ticket, old_status_display, actor):
    ctx = {
        'ticket': ticket,
        'old_status_display': old_status_display,
        'actor': actor,
        'base_url': getattr(settings, 'SITE_BASE_URL', 'http://127.0.0.1:8000'),
        'ticket_url': _ticket_url(ticket),
    }
    to = _recipients(ticket, include_department=True, include_creator=True, include_assignee=True)
    _send_templated(
        'emails/status_changed_subject.txt',
        'emails/status_changed.txt',
        'emails/status_changed.html',
        ctx, to
    )

def send_new_public_comment(comment):
    # Invia solo per commenti NON interni
    if getattr(comment, 'is_internal', False):
        return
    ticket = comment.ticket
    ctx = {
        'ticket': ticket,
        'comment': comment,
        'base_url': getattr(settings, 'SITE_BASE_URL', 'http://127.0.0.1:8000'),
        'ticket_url': _ticket_url(ticket),
    }
    to = _recipients(ticket, include_department=True, include_creator=True, include_assignee=True)
    _send_templated(
        'emails/new_comment_subject.txt',
        'emails/new_comment.txt',
        'emails/new_comment.html',
        ctx, to
    )

def send_new_attachments(ticket, attachments, actor):
    if not attachments:
        return
    ctx = {
        'ticket': ticket,
        'attachments': attachments,
        'actor': actor,
        'base_url': getattr(settings, 'SITE_BASE_URL', 'http://127.0.0.1:8000'),
        'ticket_url': _ticket_url(ticket),
    }
    to = _recipients(ticket, include_department=True, include_creator=True, include_assignee=True)
    _send_templated(
        'emails/new_attachment_subject.txt',
        'emails/new_attachment.txt',
        'emails/new_attachment.html',
        ctx, to
    )
