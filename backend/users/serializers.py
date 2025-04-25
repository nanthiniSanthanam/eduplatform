"""
File: backend/users/serializers.py
Purpose: Provides API serializers for user data and authentication in EduPlatform.

This file contains:
- UserSerializer: General serializer for user data
- UserCreateSerializer: Serializer for user registration with validation
- UserDetailSerializer: Serializer for detailed user information including profile
- ProfileSerializer: Serializer for user profile data
- LoginSerializer: Serializer for user login requests
- PasswordResetRequestSerializer: Serializer for password reset requests
- PasswordResetConfirmSerializer: Serializer for password reset confirmation
- EmailVerificationSerializer: Serializer for email verification
- UserSessionSerializer: Serializer for user session data
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from datetime import timedelta
import uuid

from .models import Profile, EmailVerification, PasswordReset, UserSession

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the Profile model providing additional user information.
    """
    class Meta:
        model = Profile
        exclude = ('user', 'created_at', 'updated_at')
        read_only_fields = ('id',)


class UserSerializer(serializers.ModelSerializer):
    """
    Basic serializer for the User model.
    """
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'role',
                  'is_email_verified', 'date_joined', 'last_login')
        read_only_fields = ('id', 'date_joined',
                            'last_login', 'is_email_verified')


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with password validation.
    """
    password = serializers.CharField(write_only=True, required=True, style={
                                     'input_type': 'password'})
    password_confirm = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password_confirm',
                  'first_name', 'last_name', 'role')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate_email(self, value):
        """
        Validate email is unique.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists.")
        return value

    def validate_username(self, value):
        """
        Validate username is unique.
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "A user with this username already exists.")
        return value

    def validate_password(self, value):
        """
        Validate password meets requirements.
        """
        validate_password(value)
        return value

    def validate(self, attrs):
        """
        Validate that passwords match.
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {"password_confirm": "Password fields didn't match."})

        # Check if role is valid for registration
        if attrs.get('role') not in ['student', 'instructor']:
            raise serializers.ValidationError(
                {"role": "Only student and instructor roles are allowed for registration."})

        return attrs

    def create(self, validated_data):
        """
        Create and return a new user, with a profile and email verification token.
        """
        # Remove password confirmation field
        validated_data.pop('password_confirm')

        # Create the user
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data.get('role', 'student')
        )

        # Profile is automatically created in CustomUserManager.create_user

        # Create email verification token
        expiry = timezone.now() + timedelta(hours=48)
        EmailVerification.objects.create(
            user=user,
            token=uuid.uuid4(),
            expires_at=expiry
        )

        return user


class UserDetailSerializer(UserSerializer):
    """
    Detailed user serializer that includes profile information.
    """
    profile = ProfileSerializer(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('profile',)


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True,
        required=True
    )
    remember_me = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        """
        Validate credentials and handle login attempt tracking.
        """
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # Check if user exists
            try:
                user = User.objects.get(email=email)

                # Check if account is locked
                if user.is_account_locked():
                    raise serializers.ValidationError({
                        "non_field_errors": [_("This account is temporarily locked due to multiple failed login attempts. Please try again later.")]
                    })

                # Authenticate user
                user = authenticate(request=self.context.get('request'),
                                    username=email, password=password)

                if not user:
                    # Record failed login attempt
                    try:
                        failed_user = User.objects.get(email=email)
                        account_locked = failed_user.record_login_attempt(
                            successful=False)

                        if account_locked:
                            raise serializers.ValidationError({
                                "non_field_errors": [_("This account is now temporarily locked due to multiple failed login attempts. Please try again later.")]
                            })
                    except User.DoesNotExist:
                        pass

                    raise serializers.ValidationError({
                        "non_field_errors": [_("Unable to log in with provided credentials.")]
                    })

            except User.DoesNotExist:
                # Use a generic error message to prevent user enumeration
                raise serializers.ValidationError({
                    "non_field_errors": [_("Unable to log in with provided credentials.")]
                })

        else:
            raise serializers.ValidationError({
                "non_field_errors": [_("Must include 'email' and 'password'.")]
            })

        # Record successful login attempt
        user.record_login_attempt(successful=True)

        # Check if email is verified
        if not user.is_email_verified:
            raise serializers.ValidationError({
                "non_field_errors": [_("Please verify your email address before logging in.")]
            })

        # Check if user is active
        if not user.is_active:
            raise serializers.ValidationError({
                "non_field_errors": [_("This account has been deactivated.")]
            })

        attrs['user'] = user
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change using current password.
    """
    current_password = serializers.CharField(
        style={'input_type': 'password'},
        required=True,
        write_only=True
    )
    new_password = serializers.CharField(
        style={'input_type': 'password'},
        required=True,
        write_only=True
    )
    confirm_password = serializers.CharField(
        style={'input_type': 'password'},
        required=True,
        write_only=True
    )

    def validate_current_password(self, value):
        """
        Validate that the current password is correct.
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                _("Current password is incorrect."))
        return value

    def validate_new_password(self, value):
        """
        Validate that the new password meets requirements.
        """
        validate_password(value, self.context['request'].user)
        return value

    def validate(self, attrs):
        """
        Validate that the new password and confirmation match.
        """
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError(
                {"confirm_password": _("The passwords do not match.")})
        return attrs

    def save(self, **kwargs):
        """
        Save the new password.
        """
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset by email.
    """
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """
        Validate that a user with this email exists.
        We don't raise an error if the email doesn't exist for security reasons.
        """
        # Normalize email
        value = value.lower().strip()
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming a password reset with a token.
    """
    token = serializers.UUIDField(required=True)
    password = serializers.CharField(
        style={'input_type': 'password'},
        required=True,
        write_only=True
    )
    confirm_password = serializers.CharField(
        style={'input_type': 'password'},
        required=True,
        write_only=True
    )

    def validate_token(self, value):
        """
        Validate that the token exists and is valid.
        """
        try:
            reset = PasswordReset.objects.get(token=value)
            if not reset.is_valid():
                raise serializers.ValidationError(
                    _("This password reset link has expired or already been used."))
            return value
        except PasswordReset.DoesNotExist:
            raise serializers.ValidationError(
                _("Invalid password reset token."))

    def validate_password(self, value):
        """
        Validate that the new password meets requirements.
        """
        try:
            # Get the user for this token
            reset = PasswordReset.objects.get(token=self.initial_data['token'])
            validate_password(value, reset.user)
        except PasswordReset.DoesNotExist:
            # Token validation will catch this in validate_token
            pass
        return value

    def validate(self, attrs):
        """
        Validate that the passwords match.
        """
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError(
                {"confirm_password": _("The passwords do not match.")})
        return attrs


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification with a token.
    """
    token = serializers.UUIDField(required=True)

    def validate_token(self, value):
        """
        Validate that the token exists and is valid.
        """
        try:
            verification = EmailVerification.objects.get(token=value)
            if not verification.is_valid():
                raise serializers.ValidationError(
                    _("This verification link has expired or already been used."))
            return value
        except EmailVerification.DoesNotExist:
            raise serializers.ValidationError(_("Invalid verification token."))


class UserSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for user session data.
    """
    class Meta:
        model = UserSession
        fields = (
            'id', 'session_key', 'ip_address', 'user_agent',
            'created_at', 'expires_at', 'last_activity',
            'is_active', 'device_type', 'location'
        )
        read_only_fields = (
            'id', 'session_key', 'ip_address', 'user_agent',
            'created_at', 'expires_at', 'last_activity',
            'device_type', 'location'
        )

    def validate(self, attrs):
        """
        Only allow updating is_active field.
        """
        # In case there are any other fields in the request,
        # we only allow modifying is_active
        allowed_fields = ['is_active']
        for field in self.initial_data:
            if field not in allowed_fields and field in attrs:
                raise serializers.ValidationError({
                    field: _("This field cannot be updated.")
                })
        return attrs
