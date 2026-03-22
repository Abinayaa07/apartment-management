from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "block_name",
            "flat_number",
            "vehicle_number",
            "id_proof",
            "address_proof",
            "role",
            "is_approved",
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "phone",
            "block_name",
            "flat_number",
            "vehicle_number",
            "id_proof",
            "address_proof",
            "role",
            "password",
            "confirm_password",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        if attrs.get("role") == "admin":
            raise serializers.ValidationError(
                {"role": "Admin accounts cannot be created from registration."}
            )
        if attrs.get("role") == "resident":
            if not attrs.get("id_proof"):
                raise serializers.ValidationError(
                    {"id_proof": "Residents must upload an ID proof."}
                )
            if not attrs.get("address_proof"):
                raise serializers.ValidationError(
                    {"address_proof": "Residents must upload an address proof."}
                )
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.is_approved = user.role != "resident"
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        request = self.context.get("request")
        user = authenticate(
            request=request,
            username=attrs.get("username"),
            password=attrs.get("password"),
        )

        if user is None:
            raise serializers.ValidationError(
                {"detail": "Invalid credentials."}
            )

        if not user.is_approved:
            raise serializers.ValidationError(
                {"detail": "Account not approved by admin."}
            )

        attrs["user"] = user
        return attrs
