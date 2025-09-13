from .models import AuditLog

def log_created(ticket, actor):
    AuditLog.objects.create(ticket=ticket, action=AuditLog.Action.CREATED, actor=actor)

def log_status_change(ticket, actor, old_status, new_status):
    AuditLog.objects.create(
        ticket=ticket,
        action=AuditLog.Action.STATUS_CHANGED,
        actor=actor,
        meta={'old': old_status, 'new': new_status},
        note=f"{old_status} → {new_status}"
    )

def log_comment(ticket, actor, is_internal):
    AuditLog.objects.create(
        ticket=ticket,
        action=AuditLog.Action.COMMENT_ADDED,
        actor=actor,
        meta={'internal': bool(is_internal)},
        note="Commento interno" if is_internal else "Commento pubblico"
    )

def log_attachments(ticket, actor, filenames):
    AuditLog.objects.create(
        ticket=ticket,
        action=AuditLog.Action.ATTACHMENT_ADDED,
        actor=actor,
        meta={'files': filenames},
        note=f"{len(filenames)} allegato/i"
    )
