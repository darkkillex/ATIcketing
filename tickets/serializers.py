from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Ticket, Department, Comment

User = get_user_model()

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'code', 'name']

class TicketSerializer(serializers.ModelSerializer):
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all())

    class Meta:
        model = Ticket
        read_only_fields = ['id', 'protocol', 'status', 'created_at', 'updated_at']
        fields = [
            'id', 'protocol', 'title', 'description',
            'status', 'priority', 'impact', 'urgency', 'source_channel',
            'department', 'created_by', 'assignee',
            'location', 'asset_code',
            'created_at', 'updated_at',
        ]
        extra_kwargs = {
            'created_by': {'read_only': True},
        }

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        return super().create(validated_data)

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        read_only_fields = ['id', 'created_at']
        fields = ['id', 'ticket', 'author', 'body', 'is_internal', 'created_at']
