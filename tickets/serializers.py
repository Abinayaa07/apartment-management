from rest_framework import serializers

from .models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    resident_username = serializers.CharField(source="resident.username", read_only=True)

    class Meta:
        model = Ticket
        fields = "__all__"
        read_only_fields = [
            "resident",
            "created_at",
            "updated_at",
        ]
