from rest_framework.permissions import BasePermission, SAFE_METHODS

ADMIN_GROUPS = {'Admin', 'SuperUser', 'Coordinatore'}

def is_staffish(user):
    return user.is_superuser or user.groups.filter(name__in=ADMIN_GROUPS).exists()

class TicketPermissions(BasePermission):
    """
    Staff (Admin/SuperUser/Coordinatore): full access.
    Operatore: può creare e vedere/modificare SOLO i propri ticket.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # Creazione ticket consentita a tutti gli utenti autenticati
        # (se vuoi restringere: consenti solo a gruppi specifici)
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        if is_staffish(user):
            return True
        # Operatore (o altro utente non staff): solo i propri
        return obj.created_by_id == user.id
