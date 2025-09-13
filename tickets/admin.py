from django.contrib import admin
from .models import Department, Counter, Ticket, Comment, Attachment, AuditLog

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')

@admin.register(Counter)
class CounterAdmin(admin.ModelAdmin):
    list_display = ('dept_code', 'iso_year', 'iso_week', 'last_number')
    list_filter = ('dept_code', 'iso_year', 'iso_week')

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('protocol', 'title', 'department', 'status', 'priority', 'created_by', 'assignee', 'created_at')
    list_filter = ('department', 'status', 'priority', 'created_at')
    search_fields = ('protocol', 'title', 'description')
    readonly_fields = ('protocol', 'created_at', 'updated_at')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'author', 'created_at', 'is_internal')
    search_fields = ('ticket__protocol', 'author__username', 'body')
    list_filter = ('is_internal', 'created_at')

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'original_name', 'mime_type', 'size', 'uploaded_by', 'uploaded_at')
    search_fields = ('original_name', 'ticket__protocol', 'uploaded_by__username')
    list_filter = ('mime_type', 'uploaded_at')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'action', 'actor', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('ticket__protocol', 'actor__username', 'note')
