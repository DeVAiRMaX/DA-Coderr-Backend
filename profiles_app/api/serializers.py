from django.contrib.auth.models import User
from rest_framework import serializers

from profiles_app.models import UserProfile


class ProfileDetailSerializer(serializers.ModelSerializer):
    """Full profile of a user. Name and email are stored on the User model."""

    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(
        source='user.first_name', required=False, allow_blank=True
    )
    last_name = serializers.CharField(
        source='user.last_name', required=False, allow_blank=True
    )
    email = serializers.EmailField(source='user.email', required=False)

    class Meta:
        model = UserProfile
        fields = [
            'user', 'username', 'first_name', 'last_name', 'file',
            'location', 'tel', 'description', 'working_hours', 'type',
            'email', 'created_at',
        ]
        read_only_fields = ['user', 'type', 'created_at']

    def validate_email(self, value):
        other_users = User.objects.exclude(pk=self.instance.user.pk)
        if other_users.filter(email=value).exists():
            raise serializers.ValidationError('This email is already in use.')
        return value

    def update(self, instance, validated_data):
        """Saves the user fields first, then the profile fields."""
        user_data = validated_data.pop('user', {})
        for field, value in user_data.items():
            setattr(instance.user, field, value)
        instance.user.save()
        return super().update(instance, validated_data)


class BusinessProfileListSerializer(serializers.ModelSerializer):
    """Profile data shown in the list of all business users."""

    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(
        source='user.first_name', read_only=True
    )
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'user', 'username', 'first_name', 'last_name', 'file',
            'location', 'tel', 'description', 'working_hours', 'type',
        ]


class CustomerProfileListSerializer(serializers.ModelSerializer):
    """Profile data shown in the list of all customers."""

    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(
        source='user.first_name', read_only=True
    )
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    # The docs call this field uploaded_at, we use the profile creation date
    uploaded_at = serializers.DateTimeField(
        source='created_at', read_only=True
    )

    class Meta:
        model = UserProfile
        fields = [
            'user', 'username', 'first_name', 'last_name', 'file',
            'uploaded_at', 'type',
        ]
