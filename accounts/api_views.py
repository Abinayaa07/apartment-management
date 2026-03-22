from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class ApprovedTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        token["role"] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        if not self.user.is_approved:
            raise AuthenticationFailed("Account not approved by admin.")

        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "role": self.user.role,
            "flat_number": self.user.flat_number,
        }
        return data


class ApprovedTokenObtainPairView(TokenObtainPairView):
    serializer_class = ApprovedTokenObtainPairSerializer
