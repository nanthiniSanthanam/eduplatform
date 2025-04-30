"""
File: backend/users/serializers.py
Purpose: Serializers for user data, authentication, and subscription management

This file contains serializers for:
1. User registration, authentication, and profile management
2. Subscription management and tiered access control
3. Email verification and password reset functionality

These serializers convert database models to/from API-friendly formats and handle:
- Field validation and error handling
- Nested relationships (e.g., user profiles)
- Computed properties not directly stored in models
- Password hashing and verification
- Access control based on subscription tiers

Variables to modify:
- PASSWORD_MIN_LENGTH: Minimum password length for validation
- Role choices in UserCreateSerializer if user roles change

Connected files:
1. users/models.py - Database models being serialized
2. users/views.py - Views using these serializers
3. courses/serializers.py - Course serializers using user data
4. frontend/src/services/api.js - Frontend API client
5. frontend/src/contexts/AuthContext.jsx - Frontend authentication logic

Created by: Professor Santhanam
Last updated: 2025-04-28 17:09:49
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


from .models import Profile, EmailVerification, Subscription, UserSession

User = get_user_model()

# Constants for validation
PASSWORD_MIN_LENGTH = 8


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.

    This excludes user, created_at and updated_at fields as they're handled elsewhere
    or not needed by the frontend.
    """
    class Meta:
        model = Profile
        exclude = ['user', 'created_at', 'updated_at']


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for user subscription information.

    This adds computed fields needed by the frontend:
    - is_active: Whether subscription is currently active
    - days_remaining: Days left in current subscription period
    """
    # Computed fields
    is_active = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            'tier', 'status', 'start_date', 'end_date',
            'is_auto_renew', 'last_payment_date',
            'is_active', 'days_remaining'
        ]

    def get_is_active(self, obj):
        """Determine if subscription is active"""
        return obj.is_active()

    def get_days_remaining(self, obj):
        """Get days remaining in subscription"""
        return obj.days_remaining


class UserSerializer(serializers.ModelSerializer):
    """
    Base serializer for user information.

    This provides the standard user fields needed by the frontend.
    """
    profile = ProfileSerializer(read_only=True)
    subscription = SubscriptionSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'role', 'is_email_verified', 'date_joined', 'last_login',
            'profile', 'subscription'
        ]
        read_only_fields = [
            'id', 'date_joined', 'last_login', 'is_email_verified',
        ]


class UserDetailSerializer(UserSerializer):
    """
    Extended user serializer with more detailed information.

    This adds any additional user information needed by the frontend.
    """
    class Meta(UserSerializer.Meta):
        # Same as UserSerializer but could be extended with additional fields
        pass


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    This handles:
    - Password validation and confirmation
    - Creation of related profile
    - Initial subscription setup
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'password_confirm',
            'first_name', 'last_name', 'role'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'role': {'required': True}
        }

    def validate_password(self, value):
        """Validate password using Django's password validators"""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

        if len(value) < PASSWORD_MIN_LENGTH:
            raise serializers.ValidationError(
                f"Password must be at least {PASSWORD_MIN_LENGTH} characters long."
            )

        return value

    def validate(self, data):
        """
        Validate that passwords match and the role is valid
        """
        if data.get('password') != data.pop('password_confirm'):
            raise serializers.ValidationError(
                {"password_confirm": "Password fields didn't match."}
            )

        # Validate role - users can only register as students or instructors
        valid_roles = ['student', 'instructor']
        if data.get('role') not in valid_roles:
            raise serializers.ValidationError(
                {"role": f"Invalid role. Must be one of: {', '.join(valid_roles)}"}
            )

        return data

    def create(self, validated_data):
        """
        Create a new user with encrypted password and initial profile.
        """
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role=validated_data['role'],
        )

        # Profile is automatically created by model signal

        # Create default free subscription
        Subscription.objects.create(
            user=user,
            tier='free',
            status='active'
        )

        return user


class UpdateProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile information.

    This allows updating the user's name and profile details.
    """
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    profile = ProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'profile']

    def update(self, instance, validated_data):
        """
        Update user and profile information
        """
        profile_data = validated_data.pop('profile', None)

        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update profile fields
        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification tokens.
    """
    token = serializers.UUIDField(required=True)

    def validate_token(self, value):
        """
        Validate that the token exists and is not expired
        """
        try:
            verification = EmailVerification.objects.get(token=value)
        except EmailVerification.DoesNotExist:
            raise serializers.ValidationError("Invalid verification token.")

        if not verification.is_valid():
            raise serializers.ValidationError(
                "Verification token has expired. Please request a new one."
            )

        return value


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing password while logged in.
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        """
        Check if old password is correct
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        """
        Validate new password
        """
        try:
            validate_password(value, self.context['request'].user)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def save(self):
        """
        Update the user's password
        """
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting password reset.
    """
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """
        Check if email exists in the system
        """
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            # We don't want to reveal if email exists for security reasons
            # Just silently pass and create a dummy token
            pass

        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming password reset using token.
    """
    token = serializers.UUIDField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate_token(self, value):
        """
        Check if token is valid
        """
        try:
            reset = self.context['request'].user.password_resets.get(
                token=value,
                is_used=False
            )
            if not reset.is_valid():
                raise serializers.ValidationError("Reset token has expired.")
        except Exception:
            raise serializers.ValidationError("Invalid reset token.")

        return value

    def validate_password(self, value):
        """
        Validate new password
        """
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

        if len(value) < PASSWORD_MIN_LENGTH:
            raise serializers.ValidationError(
                f"Password must be at least {PASSWORD_MIN_LENGTH} characters long."
            )

        return value


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    remember_me = serializers.BooleanField(default=False)

    def validate(self, data):
        """
        Validate login credentials
        """
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            raise serializers.ValidationError(
                "Must provide email and password."
            )

        user = authenticate(
            request=self.context.get('request'),
            username=email,  # Using email as username field
            password=password
        )

        if not user:
            raise serializers.ValidationError(
                "Invalid email or password."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "This account is inactive or has been suspended."
            )

        # Check if account is temporarily locked
        if user.is_account_locked():
            raise serializers.ValidationError(
                "This account is temporarily locked due to too many failed login attempts. "
                "Please try again later."
            )

        # Store user in validated_data for view to use
        data['user'] = user
        return data


class UserSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSession  # Use the actual model directly
        fields = [
            'id',
            'session_key',
            'ip_address',
            'user_agent',
            'created_at',
            'expires_at',
            'last_activity',
            'is_active',
            'device_type',
            'location'
        ]
