from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    resident_username = serializers.CharField(source="resident.username", read_only=True)

    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = [
            "created_at",
        ]
