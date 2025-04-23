from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone

CustomUser = get_user_model()


class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer for the CustomUser model with all fields.
    """
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'user_type',
                  'profile_picture', 'bio', 'subscription_status', 'subscription_expiry']
        read_only_fields = ['id']


class UserSignupSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with password confirmation.
    """
    password = serializers.CharField(
        write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(
        write_only=True, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'confirm_password', 'first_name',
                  'last_name', 'user_type', 'profile_picture', 'bio']

        extra_kwargs = {
            'user_type': {'required': False},   # <-- ONE‑LINE FIX
        }

    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login with username/email and password.
    """
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(
        write_only=True, style={'input_type': 'password'})


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    """
    subscription_active = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'user_type', 'profile_picture', 'bio',
                  'subscription_status', 'subscription_expiry', 'subscription_active']
        read_only_fields = ['id', 'username', 'email', 'subscription_status',
                            'subscription_expiry', 'subscription_active']

    def get_subscription_active(self, obj):
        if obj.subscription_status and obj.subscription_expiry:
            return obj.subscription_expiry > timezone.now()
        return False


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile information.
    """
    current_password = serializers.CharField(
        write_only=True, required=False, style={'input_type': 'password'})
    new_password = serializers.CharField(
        write_only=True, required=False, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'profile_picture', 'bio',
                  'current_password', 'new_password']

    def validate(self, data):
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        # If new password is provided, current password is required
        if new_password and not current_password:
            raise serializers.ValidationError(
                {"current_password": "Current password is required to set a new password."})

        # If current password is provided, verify it
        if current_password and not self.instance.check_password(current_password):
            raise serializers.ValidationError(
                {"current_password": "Current password is incorrect."})

        return data

    def update(self, instance, validated_data):
        # Handle password update separately
        new_password = validated_data.pop('new_password', None)
        if 'current_password' in validated_data:
            validated_data.pop('current_password')

        # Update the instance with the remaining validated data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Set new password if provided and validated
        if new_password:
            instance.set_password(new_password)

        instance.save()
        return instance


class InstructorSerializer(serializers.ModelSerializer):
    """
    Serializer for instructor public profile information.
    """
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name',
                  'last_name', 'profile_picture', 'bio']
        read_only_fields = fields


class AdminUserSerializer(serializers.ModelSerializer):
    """
    Serializer for admin to manage users with all fields.
    """
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'is_active', 'date_joined', 'last_login', 'user_type',
                  'profile_picture', 'bio', 'subscription_status', 'subscription_expiry']
        read_only_fields = ['id', 'date_joined', 'last_login']
