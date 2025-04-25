"""
File: backend/users/models.py
Purpose: Defines custom user models and authentication-related models for EduPlatform.

This file contains:
- CustomUser: Extended user model with roles and permissions
- Profile: Additional user profile information
- EmailVerification: Email verification tokens and tracking
- PasswordReset: Password reset tokens and tracking
- LoginLog: Track login attempts for security auditing

Related files to create:
1. managers.py - Custom user manager for email-based authentication
2. serializers.py - API serializers for user data and authentication
3. views.py - API views for user management and authentication
4. urls.py - URL routing for user endpoints
5. permissions.py - Custom permission classes for role-based access
6. authentication.py - JWT authentication configuration
7. admin.py - Admin interface configurations

Frontend files needed:
1. AuthContext.js - React context for authentication state management
2. PrivateRoute.js - Route protection component
3. Login.js, Register.js, ResetPassword.js, VerifyEmail.js components
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
import uuid
from datetime import timedelta


class CustomUserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier
    instead of username for authentication.
    """

    def create_user(self, email, username, password=None, **extra_fields):
        """
        Create and save a user with the given email, username and password.
        """
        if not email:
            raise ValueError(_('The Email field must be set'))
        if not username:
            raise ValueError(_('The Username field must be set'))

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        # Create profile automatically
        Profile.objects.create(user=user)

        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email, username and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, username, password, **extra_fields)


class CustomUser(AbstractUser, PermissionsMixin):
    """
    Custom User model with email authentication and role-based permissions.
    This extends Django's AbstractUser with additional fields and functionality.
    """
    USER_ROLES = (
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('admin', 'Administrator'),
        ('staff', 'Staff'),
    )

    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(_('username'), max_length=150, unique=True)
    role = models.CharField(
        max_length=20, choices=USER_ROLES, default='student')
    is_email_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    # Additional security fields
    failed_login_attempts = models.PositiveIntegerField(default=0)
    temporary_ban_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Use email for authentication instead of username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()

    def has_role(self, role):
        """
        Check if the user has a specific role.
        """
        return self.role == role

    def record_login_attempt(self, successful=False):
        """
        Record a login attempt and handle failed attempt security measures.
        Returns True if the account is temporarily locked.
        """
        # Record the login attempt
        LoginLog.objects.create(
            user=self,
            ip_address='0.0.0.0',  # Should be replaced with actual IP
            user_agent='',         # Should be replaced with actual user agent
            successful=successful
        )

        if successful:
            # Reset failed attempts on successful login
            self.failed_login_attempts = 0
            self.temporary_ban_until = None
            self.save(update_fields=[
                      'failed_login_attempts', 'temporary_ban_until'])
            return False

        # Handle failed login attempt
        self.failed_login_attempts += 1

        # Implement exponential backoff for repeated failed attempts
        if self.failed_login_attempts >= 10:
            # Ban for 24 hours after 10 failed attempts
            self.temporary_ban_until = timezone.now() + timedelta(hours=24)
        elif self.failed_login_attempts >= 5:
            # Ban for 15 minutes after 5 failed attempts
            self.temporary_ban_until = timezone.now() + timedelta(minutes=15)

        self.save(update_fields=[
                  'failed_login_attempts', 'temporary_ban_until'])

        # Return whether the account is now locked
        return self.temporary_ban_until is not None and self.temporary_ban_until > timezone.now()

    def is_account_locked(self):
        """
        Check if the account is temporarily locked due to failed login attempts.
        """
        if not self.temporary_ban_until:
            return False

        if self.temporary_ban_until < timezone.now():
            # Ban period has expired
            self.temporary_ban_until = None
            self.failed_login_attempts = 0
            self.save(update_fields=[
                      'temporary_ban_until', 'failed_login_attempts'])
            return False

        return True

    def is_student(self):
        """Check if user is a student."""
        return self.role == 'student'

    def is_instructor(self):
        """Check if user is an instructor."""
        return self.role == 'instructor'

    def is_admin(self):
        """Check if user is an admin."""
        return self.role == 'admin' or self.is_superuser

    def is_staff_member(self):
        """Check if user is a staff member."""
        return self.role == 'staff' or self.is_staff


class Profile(models.Model):
    """
    Extended user profile information.
    Contains additional user data beyond authentication needs.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True
    )
    bio = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    twitter = models.CharField(max_length=100, blank=True)
    github = models.CharField(max_length=100, blank=True)

    # Instructor-specific fields
    expertise = models.CharField(max_length=200, blank=True)
    teaching_experience = models.PositiveIntegerField(default=0)

    # Student-specific fields
    educational_background = models.TextField(blank=True)
    interests = models.TextField(blank=True)

    # Notification preferences
    receive_email_notifications = models.BooleanField(default=True)
    receive_marketing_emails = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.email}"


class EmailVerification(models.Model):
    """
    Email verification token management.
    Used for verifying user email addresses during registration.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_verifications'
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Email verification for {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Set expiration to 48 hours from creation
            self.expires_at = timezone.now() + timedelta(hours=48)
        super().save(*args, **kwargs)

    def is_valid(self):
        """
        Check if the verification token is still valid.
        """
        if self.is_used:
            return False
        return timezone.now() <= self.expires_at

    def use_token(self):
        """
        Mark the token as used and the user's email as verified.
        """
        if self.is_valid():
            self.is_used = True
            self.verified_at = timezone.now()
            self.save()

            # Update user's email verification status
            user = self.user
            user.is_email_verified = True
            user.save(update_fields=['is_email_verified'])
            return True
        return False


class PasswordReset(models.Model):
    """
    Password reset token management.
    Used for secure password reset functionality.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='password_resets'
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"Password reset for {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Set expiration to 24 hours from creation
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_valid(self):
        """
        Check if the password reset token is still valid.
        """
        if self.is_used:
            return False
        return timezone.now() <= self.expires_at

    def use_token(self):
        """
        Mark the token as used.
        """
        if self.is_valid():
            self.is_used = True
            self.used_at = timezone.now()
            self.save(update_fields=['is_used', 'used_at'])
            return True
        return False


class LoginLog(models.Model):
    """
    Log of user login attempts.
    Used for security auditing and detecting suspicious activity.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='login_logs'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    successful = models.BooleanField(default=False)

    def __str__(self):
        status = "successful" if self.successful else "failed"
        return f"{status} login for {self.user.email} at {self.timestamp}"


class UserSession(models.Model):
    """
    Track active user sessions.
    Useful for managing concurrent logins and session invalidation.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    session_key = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    device_type = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Session for {self.user.email} from {self.ip_address}"

    def is_valid(self):
        """
        Check if session is still valid.
        """
        return self.is_active and timezone.now() <= self.expires_at

    def extend_session(self, duration_hours=24):
        """
        Extend the session expiration time.
        """
        self.expires_at = timezone.now() + timedelta(hours=duration_hours)
        self.save(update_fields=['expires_at'])

    def invalidate(self):
        """
        Invalidate this session.
        """
        self.is_active = False
        self.save(update_fields=['is_active'])
