from rest_framework import serializers

from .models import Visitor


class VisitorSerializer(serializers.ModelSerializer):
    security_username = serializers.CharField(source="security.username", read_only=True)

    class Meta:
        model = Visitor
        fields = "__all__"
        read_only_fields = [
            "entry_time",
            "exit_time",
            "security",
        ]
