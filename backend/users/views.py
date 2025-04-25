"""
File: backend/users/views.py
Purpose: Provides API views for user management and authentication in EduPlatform.

This file contains:
- RegisterView: User registration and account creation
- LoginView: User authentication and token generation
- LogoutView: User logout and token invalidation
- UserView: Retrieve and update user information
- PasswordResetRequestView: Initiate password reset process
- PasswordResetConfirmView: Complete password reset with token
- EmailVerificationView: Verify user email with token
- PasswordChangeView: Change user password (authenticated)
- ProfileView: Retrieve and update user profile information
- UserSessionView: View and manage active user sessions
"""

from rest_framework import generics, status, views, viewsets, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from datetime import timedelta
import uuid
import socket
import logging

from .serializers import (
    UserSerializer, UserCreateSerializer, UserDetailSerializer,
    ProfileSerializer, LoginSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, EmailVerificationSerializer,
    PasswordChangeSerializer
)
from .models import Profile, EmailVerification, PasswordReset, UserSession
from .permissions import IsOwnerOrAdmin, IsUserOrAdmin

User = get_user_model()
logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    """
    API view to register a new user account.
    Creates a user, profile, and sends verification email.
    """
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Get the latest verification token for this user
        verification = EmailVerification.objects.filter(
            user=user,
            is_used=False
        ).latest('created_at')

        # Send verification email
        self._send_verification_email(user, verification.token)

        return Response(
            {"detail": "User registered successfully. Please check your email to verify your account."},
            status=status.HTTP_201_CREATED
        )

    def _send_verification_email(self, user, token):
        """
        Send email verification link to user.
        """
        try:
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
            subject = "Verify your EduPlatform account"
            message = render_to_string('users/email_verification.html', {
                'user': user,
                'verification_url': verification_url,
                'valid_hours': 48,
            })

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
                html_message=message
            )

            logger.info(f"Verification email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")


class LoginView(views.APIView):
    """
    API view to authenticate users and return tokens.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        remember_me = serializer.validated_data.get('remember_me', False)

        # Update last login timestamp
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        # Get tokens
        refresh = RefreshToken.for_user(user)

        # Create or update user session
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Set session expiry time
        if remember_me:
            expires_at = timezone.now() + timedelta(days=30)
        else:
            expires_at = timezone.now() + timedelta(hours=24)

        # Create user session
        UserSession.objects.create(
            user=user,
            session_key=refresh.access_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
            device_type=self._get_device_type(user_agent),
            location=self._get_location_from_ip(ip_address)
        )

        # Return authentication tokens
        data = {
            'user': UserDetailSerializer(user, context={'request': request}).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

        return Response(data, status=status.HTTP_200_OK)

    def _get_client_ip(self, request):
        """
        Get client IP address from request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _get_device_type(self, user_agent):
        """
        Determine device type from user agent.
        """
        if not user_agent:
            return 'Unknown'

        user_agent = user_agent.lower()

        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent or 'ipad' in user_agent:
            return 'Mobile'
        elif 'tablet' in user_agent:
            return 'Tablet'
        else:
            return 'Desktop'

    def _get_location_from_ip(self, ip):
        """
        Get approximate location from IP (simplified).
        In production, you'd use a proper geolocation service.
        """
        try:
            # This is a simplified example, in production use a geolocation service
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except:
            return 'Unknown'


class LogoutView(views.APIView):
    """
    API view to log out users by invalidating tokens.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            # Invalidate the current session
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if 'Bearer ' in auth_header:
                token = auth_header.split(' ')[1]
                sessions = UserSession.objects.filter(
                    user=request.user,
                    session_key=token,
                    is_active=True
                )
                for session in sessions:
                    session.invalidate()

            # If refresh token is provided, add it to blacklist
            refresh_token = request.data.get('refresh')
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                except Exception as e:
                    logger.warning(f"Error blacklisting token: {str(e)}")

            return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response({"detail": "Logout failed."}, status=status.HTTP_400_BAD_REQUEST)


class UserView(generics.RetrieveUpdateAPIView):
    """
    API view to retrieve or update user information.
    """
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_object(self):
        return self.request.user


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    API view to retrieve or update user profile.
    """
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsUserOrAdmin]

    def get_object(self):
        return get_object_or_404(Profile, user=self.request.user)


class PasswordChangeView(generics.GenericAPIView):
    """
    API view to change user password.
    """
    serializer_class = PasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Optional: Invalidate other sessions
        UserSession.objects.filter(user=request.user).exclude(
            session_key=request.auth.token
        ).update(is_active=False)

        return Response(
            {"detail": "Password changed successfully."},
            status=status.HTTP_200_OK
        )


class PasswordResetRequestView(generics.GenericAPIView):
    """
    API view to request a password reset.
    """
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        # Always return success even if user doesn't exist (for security)
        try:
            user = User.objects.get(email=email)

            # Create password reset token
            token = uuid.uuid4()
            expiry = timezone.now() + timedelta(hours=24)

            PasswordReset.objects.create(
                user=user,
                token=token,
                expires_at=expiry,
                ip_address=self._get_client_ip(request)
            )

            # Send email
            self._send_reset_email(user, token)

        except User.DoesNotExist:
            # Log that no user was found but don't inform the client
            logger.info(
                f"Password reset requested for non-existent email: {email}")

        return Response(
            {"detail": "If an account exists with this email, a password reset link has been sent."},
            status=status.HTTP_200_OK
        )

    def _get_client_ip(self, request):
        """
        Get client IP address from request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _send_reset_email(self, user, token):
        """
        Send password reset email to user.
        """
        try:
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
            subject = "Reset your EduPlatform password"
            message = render_to_string('users/password_reset_email.html', {
                'user': user,
                'reset_url': reset_url,
                'valid_hours': 24,
            })

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
                html_message=message
            )

            logger.info(f"Password reset email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    API view to confirm password reset with token.
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = serializer.validated_data['token']
            password = serializer.validated_data['password']

            # Get and validate token
            reset = get_object_or_404(PasswordReset, token=token)

            if not reset.is_valid():
                return Response(
                    {"detail": "This password reset link has expired or already been used."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update password
            user = reset.user
            user.set_password(password)
            user.save()

            # Mark token as used
            reset.use_token()

            # Invalidate all user sessions
            UserSession.objects.filter(user=user).update(is_active=False)

            return Response(
                {"detail": "Password has been reset successfully. You can now log in with your new password."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Password reset error: {str(e)}")
            return Response(
                {"detail": "Password reset failed."},
                status=status.HTTP_400_BAD_REQUEST
            )


class EmailVerificationView(generics.GenericAPIView):
    """
    API view to verify email with token.
    """
    serializer_class = EmailVerificationSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = serializer.validated_data['token']

            # Get and validate token
            verification = get_object_or_404(EmailVerification, token=token)

            if not verification.is_valid():
                return Response(
                    {"detail": "This verification link has expired or already been used."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Mark email as verified and token as used
            if verification.use_token():
                return Response(
                    {"detail": "Email verified successfully. You can now log in."},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"detail": "Email verification failed."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error(f"Email verification error: {str(e)}")
            return Response(
                {"detail": "Email verification failed."},
                status=status.HTTP_400_BAD_REQUEST
            )


class ResendVerificationView(generics.GenericAPIView):
    """
    API view to resend verification email.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            email = request.data.get('email')
            if not email:
                return Response(
                    {"detail": "Email address is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = get_object_or_404(User, email=email)

            # Check if email is already verified
            if user.is_email_verified:
                return Response(
                    {"detail": "Email address is already verified."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create new verification token
            token = uuid.uuid4()
            expiry = timezone.now() + timedelta(hours=48)

            EmailVerification.objects.create(
                user=user,
                token=token,
                expires_at=expiry
            )

            # Send verification email
            self._send_verification_email(user, token)

            return Response(
                {"detail": "Verification email has been sent."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Resend verification error: {str(e)}")
            return Response(
                {"detail": "Failed to resend verification email."},
                status=status.HTTP_400_BAD_REQUEST
            )

    def _send_verification_email(self, user, token):
        """
        Send email verification link to user.
        """
        try:
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
            subject = "Verify your EduPlatform account"
            message = render_to_string('users/email_verification.html', {
                'user': user,
                'verification_url': verification_url,
                'valid_hours': 48,
            })

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
                html_message=message
            )

            logger.info(f"Verification email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")


class UserSessionViewSet(viewsets.ModelViewSet):
    """
    API viewset to manage user sessions.
    """
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        return UserSession.objects.filter(user=self.request.user, is_active=True)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.invalidate()
        return Response(
            {"detail": "Session invalidated successfully."},
            status=status.HTTP_200_OK
        )
