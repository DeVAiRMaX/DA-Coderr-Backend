from django.contrib.auth.models import User
from rest_framework import serializers

from profiles_app.models import UserProfile


class RegistrationSerializer(serializers.ModelSerializer):
    """Validates the registration data and creates user and profile."""

    repeated_password = serializers.CharField(write_only=True)
    type = serializers.ChoiceField(
        choices=UserProfile.TYPE_CHOICES, write_only=True
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'repeated_password', 'type']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('This email is already in use.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['repeated_password']:
            raise serializers.ValidationError(
                {'repeated_password': 'Passwords do not match.'}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('repeated_password')
        profile_type = validated_data.pop('type')
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user, type=profile_type)
        return user
