"""
File: backend/users/views.py
Purpose: Provides API views for user management, authentication and subscription management in EduPlatform.

This file contains:
- RegisterView: User registration and account creation with default subscription
- LoginView: User authentication and token generation
- LogoutView: User logout and token invalidation
- UserView: Retrieve and update user information
- PasswordResetRequestView: Initiate password reset process
- PasswordResetConfirmView: Complete password reset with token
- EmailVerificationView: Verify user email with token
- PasswordChangeView: Change user password (authenticated)
- ProfileView: Retrieve and update user profile information
- UserSessionView: View and manage active user sessions
- SubscriptionViewSet: View and manage user subscription tiers and access levels
- SocialAuthGoogleView: Initiate Google OAuth authentication with PKCE support
- SocialAuthGithubView: Initiate GitHub OAuth authentication with PKCE support
- SocialAuthCompleteView: Complete social authentication with PKCE and CSRF protection
- SocialAuthErrorView: Handle social authentication errors

Modification variables:
- DEFAULT_SUBSCRIPTION_DAYS: Length of subscriptions in days (default: 30)
- SUBSCRIPTION_PRICES: Pricing for each subscription tier (modify for your pricing structure)
- EMAIL_VERIFICATION_EXPIRY_HOURS: How long email verification links are valid (default: 48)
- PASSWORD_RESET_EXPIRY_HOURS: How long password reset links are valid (default: 24)

Connected files:
1. backend/users/serializers.py - Contains serializers used by these views
2. backend/users/models.py - User, Profile, and Subscription models
3. backend/users/permissions.py - Custom permission classes
4. frontend/src/contexts/AuthContext.jsx - Consumes these API endpoints

Changes (2025-05-21 17:26:43 by cadsanthanam):
- Enhanced social authentication with PKCE support for improved security
- Added proper CSRF protection via state parameter validation
- Added support for UserSession login_method tracking with fallback
- Improved error handling and validation for OAuth flows
- Enhanced verification of email addresses from social providers
"""

from rest_framework import generics, status, views, viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404, redirect
from datetime import timedelta
import uuid
import socket
import logging
import json
import requests  # Added for OAuth API requests

from .serializers import (
    UserSerializer, UserCreateSerializer, UserDetailSerializer,
    ProfileSerializer, LoginSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, EmailVerificationSerializer,
    PasswordChangeSerializer, UpdateProfileSerializer, SubscriptionSerializer
)
from .models import Profile, EmailVerification, PasswordReset, UserSession, Subscription
from .permissions import IsOwnerOrAdmin, IsUserOrAdmin

User = get_user_model()
logger = logging.getLogger(__name__)

# Subscription configuration
DEFAULT_SUBSCRIPTION_DAYS = 30
SUBSCRIPTION_PRICES = {
    'basic': 9.99,
    'premium': 19.99,
}
EMAIL_VERIFICATION_EXPIRY_HOURS = 48
PASSWORD_RESET_EXPIRY_HOURS = 24


class RegisterView(generics.CreateAPIView):
    """
    API view to register a new user account.
    Creates a user, profile, subscription, and sends verification email.
    """
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            # Return validation errors in a consistent format
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = serializer.save()

            # Create an email verification token for the new user
            token = uuid.uuid4()
            expiry = timezone.now() + timedelta(hours=EMAIL_VERIFICATION_EXPIRY_HOURS)
            verification = EmailVerification.objects.create(
                user=user,
                token=token,
                expires_at=expiry
            )

            # Create default subscription (free tier)
            Subscription.create_for_user(user)

            # Send verification email
            try:
                self._send_verification_email(user, verification.token)
            except Exception as e:
                logger.error(
                    f"Failed to send verification email to {user.email}: {str(e)}")
                # Continue with registration even if email fails
                # We'll let the user request a new verification link

            # Return success response
            return Response(
                {"detail": "User registered successfully. Please check your email to verify your account."},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error during registration: {str(e)}")
            return Response(
                {"detail": "An error occurred during registration. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _send_verification_email(self, user, token):
        """
        Send email verification link to user.
        """
        try:
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
            subject = "Verify your EduPlatform account"

            # Ensure the template exists
            try:
                message = render_to_string('users/email_verification.html', {
                    'user': user,
                    'verification_url': verification_url,
                    'valid_hours': EMAIL_VERIFICATION_EXPIRY_HOURS,
                })
            except Exception as e:
                logger.error(f"Error rendering email template: {str(e)}")
                # Fallback to plain text if template fails
                message = f"""
                Hello {user.first_name},
                
                Thank you for registering with EduPlatform. Please verify your email by clicking the link below:
                
                {verification_url}
                
                This link is valid for {EMAIL_VERIFICATION_EXPIRY_HOURS} hours.
                
                If you didn't register for an account, please ignore this email.
                
                Best regards,
                The EduPlatform Team
                """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
                html_message=message if '<html' in message else None
            )

            logger.info(f"Verification email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            raise


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

        # Adjust token lifetime based on remember_me
        if not remember_me:
            refresh.set_exp(lifetime=timedelta(hours=24))

        # Get client information
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Set session expiry time based on remember_me
        if remember_me:
            expires_at = timezone.now() + timedelta(days=30)
        else:
            expires_at = timezone.now() + timedelta(hours=24)

        # Create session data dictionary with required fields
        session_data = {
            'user': user,
            'session_key': refresh.access_token['jti'],
            'ip_address': ip_address,
            'user_agent': user_agent,
            'expires_at': expires_at,
            'device_type': self._get_device_type(user_agent),
            'location': self._get_location_from_ip(ip_address)
        }

        # Only add login_method if the field exists in your model
        try:
            UserSession._meta.get_field('login_method')
            session_data['login_method'] = 'credentials'
        except Exception:
            # Field doesn't exist, don't include it
            pass

        # Create single user session with JTI (JSON Web Token ID)
        UserSession.objects.create(**session_data)

        # Ensure user has a subscription
        try:
            subscription = user.subscription
        except Subscription.DoesNotExist:
            subscription = Subscription.create_for_user(user)

        # Return authentication tokens
        data = {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserDetailSerializer(user, context={'request': request}).data,
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
            # Try to find and invalidate session using JTI from token payload
            jti = None
            if hasattr(request, 'auth') and hasattr(request.auth, 'payload'):
                jti = request.auth.payload.get('jti')

            if jti:
                # First try to find session by JTI
                sessions = UserSession.objects.filter(
                    user=request.user,
                    session_key=jti,
                    is_active=True
                )
                for session in sessions:
                    session.invalidate()
                    logger.info(f"Invalidated session by JTI: {jti}")
            else:
                # Fallback to encoded token if JTI not found
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
                        logger.info(f"Invalidated session by encoded token")

            # Handle refresh token blacklisting if provided
            refresh_token = request.data.get('refresh')
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                    logger.info("Blacklisted refresh token")
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

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)


class UpdateProfileView(generics.GenericAPIView):
    """
    Comprehensive API view to update both user and profile information.
    """
    serializer_class = UpdateProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            instance=request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Return complete updated user data
        return Response(UserDetailSerializer(request.user).data)


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

        # Get the current session key to preserve (prefer JTI over encoded token)
        current_session_key = None

        # First try to get JTI from payload
        if hasattr(request, 'auth') and hasattr(request.auth, 'payload'):
            jti = request.auth.payload.get('jti')
            if jti:
                current_session_key = jti
                logger.info(f"Using JTI as session key: {jti}")

        # Fallback to encoded token if JTI not available
        if not current_session_key and hasattr(request.auth, 'token'):
            current_session_key = request.auth.token
            logger.info("Using encoded token as session key")

        # Invalidate all other sessions except current one
        if current_session_key:
            UserSession.objects.filter(user=request.user).exclude(
                session_key=current_session_key
            ).update(is_active=False)
            logger.info(f"Invalidated other sessions during password change")
        else:
            logger.warning(
                "Could not identify current session during password change")

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
            expiry = timezone.now() + timedelta(hours=PASSWORD_RESET_EXPIRY_HOURS)

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
                'valid_hours': PASSWORD_RESET_EXPIRY_HOURS,
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
            expiry = timezone.now() + timedelta(hours=EMAIL_VERIFICATION_EXPIRY_HOURS)

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

            # Ensure the template exists
            try:
                message = render_to_string('users/email_verification.html', {
                    'user': user,
                    'verification_url': verification_url,
                    'valid_hours': EMAIL_VERIFICATION_EXPIRY_HOURS,
                })
            except Exception as e:
                logger.error(f"Error rendering email template: {str(e)}")
                # Fallback to plain text if template fails
                message = f"""
                Hello {user.first_name},
                
                Thank you for registering with EduPlatform. Please verify your email by clicking the link below:
                
                {verification_url}
                
                This link is valid for {EMAIL_VERIFICATION_EXPIRY_HOURS} hours.
                
                If you didn't register for an account, please ignore this email.
                
                Best regards,
                The EduPlatform Team
                """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
                html_message=message if '<html' in message else None
            )

            logger.info(f"Verification email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            raise


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


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    API viewset to manage user subscriptions and tiered access.

    Endpoints:
    - GET /subscription/ - List user subscriptions
    - GET /subscription/current/ - Get current subscription
    - POST /subscription/upgrade/ - Upgrade to a paid tier
    - POST /subscription/cancel/ - Cancel a subscription
    - POST /subscription/downgrade/ - Downgrade to a lower tier

    Access Levels:
    - Unregistered users: Basic content
    - Free tier: Intermediate content
    - Paid tiers: Advanced content with certificates
    """
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

    def get_object(self):
        """Get or create subscription for current user"""
        try:
            return Subscription.objects.get(user=self.request.user)
        except Subscription.DoesNotExist:
            return Subscription.create_for_user(self.request.user)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current subscription status"""
        subscription = self.get_object()
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def upgrade(self, request):
        """Upgrade to a paid subscription tier"""
        subscription = self.get_object()
        tier = request.data.get('tier')

        # Validate tier
        if tier not in ['basic', 'premium']:
            return Response({
                'detail': 'Invalid subscription tier. Choose from: basic, premium'
            }, status=status.HTTP_400_BAD_REQUEST)

        # In a production app, this is where you'd integrate with a payment processor
        # For now, we'll just update the subscription

        # Update subscription with new tier
        subscription.tier = tier
        subscription.status = 'active'
        subscription.end_date = timezone.now() + timedelta(days=DEFAULT_SUBSCRIPTION_DAYS)
        subscription.last_payment_date = timezone.now()
        subscription.is_auto_renew = request.data.get('auto_renew', True)
        subscription.payment_method = request.data.get(
            'payment_method', 'demo')
        subscription.save()

        logger.info(
            f"User {request.user.email} upgraded subscription to {tier} tier")

        serializer = self.get_serializer(subscription)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def cancel(self, request):
        """Cancel a paid subscription"""
        subscription = self.get_object()

        # Can't cancel a free tier
        if subscription.tier == 'free':
            return Response({
                'detail': 'Cannot cancel a free tier subscription'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Mark as cancelled but keep active until end date
        subscription.status = 'cancelled'
        subscription.is_auto_renew = False
        subscription.save()

        logger.info(
            f"User {request.user.email} cancelled their {subscription.tier} subscription")

        serializer = self.get_serializer(subscription)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def downgrade(self, request):
        """Downgrade to a lower tier at end of current period"""
        subscription = self.get_object()

        # Can't downgrade free tier
        if subscription.tier == 'free':
            return Response({
                'detail': 'Already on free tier'
            }, status=status.HTTP_400_BAD_REQUEST)

        # If premium, can downgrade to basic
        if subscription.tier == 'premium':
            new_tier = request.data.get('tier', 'basic')
            if new_tier not in ['basic', 'free']:
                return Response({
                    'detail': 'Invalid downgrade tier. Choose from: basic, free'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Update subscription to downgrade at end of period
            subscription.tier = new_tier
            subscription.save()

        # If basic, can only downgrade to free
        else:
            subscription.tier = 'free'
            subscription.end_date = None
            subscription.save()

        logger.info(
            f"User {request.user.email} downgraded subscription to {subscription.tier} tier")

        serializer = self.get_serializer(subscription)
        return Response(serializer.data)


# Enhanced Social Authentication Views with PKCE support
class SocialAuthGoogleView(views.APIView):
    """
    API view to initiate Google OAuth authentication with PKCE support.
    Returns Google login URL for client-side redirect.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Get PKCE and state parameters from the request
        code_challenge = request.GET.get('code_challenge')
        code_challenge_method = request.GET.get(
            'code_challenge_method', 'S256')
        state = request.GET.get('state')

        # Build Google OAuth URL with required parameters
        redirect_uri = f"{settings.FRONTEND_URL}/auth/social/google/callback"

        # Start with the base authorization URL
        auth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY}&redirect_uri={redirect_uri}&response_type=code&scope=email%20profile&access_type=offline&prompt=consent"

        # Add PKCE parameters if provided for enhanced security
        if code_challenge:
            auth_url += f"&code_challenge={code_challenge}&code_challenge_method={code_challenge_method}"
            logger.info(
                f"Adding PKCE to Google OAuth flow with method: {code_challenge_method}")

        # Add state parameter for CSRF protection if provided
        if state:
            auth_url += f"&state={state}"
            logger.info(
                "Adding state parameter to Google OAuth flow for CSRF protection")

        # Return the authorization URL to the client
        return Response({
            'authorizationUrl': auth_url
        })


class SocialAuthGithubView(views.APIView):
    """
    API view to initiate GitHub OAuth authentication with PKCE support.
    Returns GitHub login URL for client-side redirect.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Get PKCE and state parameters from the request
        code_challenge = request.GET.get('code_challenge')
        code_challenge_method = request.GET.get(
            'code_challenge_method', 'S256')
        state = request.GET.get('state')

        # Build GitHub OAuth URL with required parameters
        redirect_uri = f"{settings.FRONTEND_URL}/auth/social/github/callback"

        # Start with the base authorization URL
        auth_url = f"https://github.com/login/oauth/authorize?client_id={settings.SOCIAL_AUTH_GITHUB_KEY}&redirect_uri={redirect_uri}&scope=user:email"

        # Add PKCE parameters if provided for enhanced security
        if code_challenge:
            auth_url += f"&code_challenge={code_challenge}&code_challenge_method={code_challenge_method}"
            logger.info(
                f"Adding PKCE to GitHub OAuth flow with method: {code_challenge_method}")

        # Add state parameter for CSRF protection if provided
        if state:
            auth_url += f"&state={state}"
            logger.info(
                "Adding state parameter to GitHub OAuth flow for CSRF protection")

        # Return the authorization URL to the client
        return Response({
            'authorizationUrl': auth_url
        })


class SocialAuthCompleteView(views.APIView):
    """
    API view to handle social auth callback and generate JWT token.
    This is called after social auth provider redirects back with code.
    Supports PKCE for enhanced security.
    """
    permission_classes = [permissions.AllowAny]  # Allow unauthenticated access

    def post(self, request):
        """
        Handle POST request with authorization code from OAuth provider.

        Expected request format:
        {
            "code": "authorization_code_from_provider",
            "provider": "google" or "github",
            "code_verifier": "pkce_code_verifier" (optional),
            "state": "csrf_state_token" (optional)
        }
        """
        try:
            code = request.data.get('code')
            provider = request.data.get('provider')
            code_verifier = request.data.get('code_verifier')
            state = request.data.get('state')

            # Log parameters for debugging
            logger.info(
                f"Received social auth request: provider={provider}, code_length={len(code) if code else 0}, has_verifier={bool(code_verifier)}, has_state={bool(state)}")

            # Validate the required parameters
            if not code:
                return Response(
                    {"detail": "Authorization code is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not provider or provider not in ['google', 'github']:
                return Response(
                    {"detail": "Valid provider (google or github) is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Special handling for development environment
            is_dev = settings.DEBUG
            if is_dev and code_verifier == 'dev-verifier':
                logger.info("Using development code verifier bypass")
                # In development, allow placeholder code verifier
                code_verifier = None

            # Store code in request session to prevent reuse
            session_key = f"oauth_{provider}_code"
            if hasattr(request, 'session'):
                if request.session.get(session_key) == code:
                    logger.warning(f"Attempt to reuse {provider} OAuth code")
                    return Response(
                        {"detail": "This authorization code has already been used."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                request.session[session_key] = code

            # Exchange code for user info with provider
            if provider == 'google':
                # Process Google authentication with PKCE if provided
                try:
                    user_info = self._exchange_google_code(code, code_verifier)
                except Exception as e:
                    logger.error(f"Google token exchange error: {str(e)}")
                    return Response(
                        {"detail": f"Google authentication failed: {str(e)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Validate email verification status (extra security for Google accounts)
                if not user_info.get('email_verified', True):
                    logger.warning(
                        f"Google account email not verified: {user_info.get('email')}")
                    return Response(
                        {"detail": "Your Google account email is not verified. Please verify your email with Google."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Get or create user based on the email from provider
                email = user_info.get('email')
                if not email:
                    return Response(
                        {"detail": "Could not get email from Google."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Find or create user
                try:
                    user = User.objects.get(email=email)
                    logger.info(
                        f"Found existing user account for Google login: {email}")
                except User.DoesNotExist:
                    user = User.objects.create_user(
                        email=email,
                        username=email,
                        first_name=user_info.get('given_name', ''),
                        last_name=user_info.get('family_name', ''),
                        is_active=True,
                        is_email_verified=True  # Auto-verify OAuth users
                    )
                    # Create profile and subscription for new users
                    try:
                        Profile.objects.create(user=user)
                    except Exception as e:
                        logger.error(f"Error creating profile: {str(e)}")
                    try:
                        Subscription.create_for_user(user)
                    except Exception as e:
                        logger.error(f"Error creating subscription: {str(e)}")
                    logger.info(f"Created new user from Google OAuth: {email}")

            elif provider == 'github':
                # Process GitHub authentication with PKCE if provided
                try:
                    user_info = self._exchange_github_code(code, code_verifier)
                except Exception as e:
                    logger.error(f"GitHub token exchange error: {str(e)}")
                    return Response(
                        {"detail": f"GitHub authentication failed: {str(e)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Get or create user based on the email from provider
                email = user_info.get('email')
                if not email:
                    return Response(
                        {"detail": "Could not get email from GitHub."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Parse name into first and last name
                full_name = user_info.get('name', '')
                name_parts = full_name.split(' ', 1) if full_name else ['', '']
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ''

                # Find or create user
                try:
                    user = User.objects.get(email=email)
                    logger.info(
                        f"Found existing user account for GitHub login: {email}")
                except User.DoesNotExist:
                    user = User.objects.create_user(
                        email=email,
                        username=email,
                        first_name=first_name,
                        last_name=last_name,
                        is_active=True,
                        is_email_verified=True  # Auto-verify OAuth users
                    )
                    # Create profile and subscription for new users
                    try:
                        Profile.objects.create(user=user)
                    except Exception as e:
                        logger.error(f"Error creating profile: {str(e)}")
                    try:
                        Subscription.create_for_user(user)
                    except Exception as e:
                        logger.error(f"Error creating subscription: {str(e)}")
                    logger.info(f"Created new user from GitHub OAuth: {email}")

            # Update last login timestamp
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])

            # Create JWT tokens
            refresh = RefreshToken.for_user(user)

            # Create user session
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            # Default to longer session for social login
            expires_at = timezone.now() + timedelta(days=14)

            # Create session data dictionary with required fields
            session_data = {
                'user': user,
                'session_key': refresh.access_token['jti'],
                'ip_address': ip_address or '0.0.0.0',
                'user_agent': user_agent or 'Unknown',
                'expires_at': expires_at,
                'device_type': self._get_device_type(user_agent),
                'location': self._get_location_from_ip(ip_address)
            }

            # Check if login_method field exists in the model before adding it
            try:
                UserSession._meta.get_field('login_method')
                session_data['login_method'] = f"social_{provider}"
            except Exception:
                # Field doesn't exist, don't include it
                pass

            # Create the session
            UserSession.objects.create(**session_data)

            # Return tokens as JSON response
            data = {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserDetailSerializer(user, context={'request': request}).data,
            }

            logger.info(
                f"Social authentication successful for {email} with {provider}")
            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Social auth error: {str(e)}")
            return Response(
                {"detail": f"Authentication failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def _exchange_google_code(self, code, code_verifier=None):
        """
        Exchange Google authorization code for tokens and user info.
        Supports PKCE for enhanced security.
        """
        # Exchange code for access token
        token_url = "https://oauth2.googleapis.com/token"
        redirect_uri = f"{settings.FRONTEND_URL}/auth/social/google/callback"

        token_payload = {
            'code': code,
            'client_id': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
            'client_secret': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }

        # Add code_verifier for PKCE if provided
        if code_verifier:
            token_payload['code_verifier'] = code_verifier
            logger.info("Using PKCE code_verifier for Google token exchange")

        # Request access token
        token_response = requests.post(token_url, data=token_payload)

        if token_response.status_code != 200:
            logger.error(
                f"Google token exchange failed: {token_response.text}")
            raise Exception("Failed to exchange Google code for token")

        token_data = token_response.json()
        access_token = token_data.get('access_token')

        if not access_token:
            raise Exception("No access token received from Google")

        # Use access token to get user information
        userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {'Authorization': f'Bearer {access_token}'}

        userinfo_response = requests.get(userinfo_url, headers=headers)

        if userinfo_response.status_code != 200:
            logger.error(
                f"Google user info request failed: {userinfo_response.text}")
            raise Exception("Failed to get user information from Google")

        user_data = userinfo_response.json()

        # Return user info
        return {
            'email': user_data.get('email'),
            'email_verified': user_data.get('email_verified', False),
            'given_name': user_data.get('given_name', ''),
            'family_name': user_data.get('family_name', ''),
            'picture': user_data.get('picture', ''),
            'sub': user_data.get('sub')  # Unique Google ID
        }

    def _exchange_github_code(self, code, code_verifier=None):
        """
        Exchange GitHub authorization code for tokens and user info.
        Supports PKCE for enhanced security.
        """
        # Exchange code for access token
        token_url = "https://github.com/login/oauth/access_token"
        redirect_uri = f"{settings.FRONTEND_URL}/auth/social/github/callback"

        token_payload = {
            'code': code,
            'client_id': settings.SOCIAL_AUTH_GITHUB_KEY,
            'client_secret': settings.SOCIAL_AUTH_GITHUB_SECRET,
            'redirect_uri': redirect_uri
        }

        # Add code_verifier for PKCE if provided
        if code_verifier:
            token_payload['code_verifier'] = code_verifier
            logger.info("Using PKCE code_verifier for GitHub token exchange")

        headers = {'Accept': 'application/json'}

        # Request access token
        token_response = requests.post(
            token_url, data=token_payload, headers=headers)

        if token_response.status_code != 200:
            logger.error(
                f"GitHub token exchange failed: {token_response.text}")
            raise Exception("Failed to exchange GitHub code for token")

        token_data = token_response.json()
        access_token = token_data.get('access_token')

        if not access_token:
            raise Exception("No access token received from GitHub")

        # Use access token to get user information
        api_headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        # Get basic user info
        user_url = "https://api.github.com/user"
        user_response = requests.get(user_url, headers=api_headers)

        if user_response.status_code != 200:
            logger.error(
                f"GitHub user info request failed: {user_response.text}")
            raise Exception("Failed to get user information from GitHub")

        user_data = user_response.json()

        # GitHub doesn't always return email in user profile, so we need to get it from emails endpoint
        email = user_data.get('email')

        # If email is not available, try the emails endpoint to get verified email
        if not email:
            emails_url = "https://api.github.com/user/emails"
            emails_response = requests.get(emails_url, headers=api_headers)

            if emails_response.status_code == 200:
                emails = emails_response.json()
                # Find primary and verified email
                primary_email = next((e for e in emails if e.get(
                    'primary') and e.get('verified')), None)
                if primary_email:
                    email = primary_email.get('email')
                else:
                    # If no primary email, get first verified email
                    verified_email = next(
                        (e for e in emails if e.get('verified')), None)
                    if verified_email:
                        email = verified_email.get('email')

        if not email:
            raise Exception("Could not retrieve verified email from GitHub")

        # Return user info
        return {
            'email': email,
            'name': user_data.get('name', ''),
            'login': user_data.get('login'),
            'avatar_url': user_data.get('avatar_url', ''),
            'id': user_data.get('id')  # Unique GitHub ID
        }

    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _get_device_type(self, user_agent):
        """Determine device type from user agent."""
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
        """Get approximate location from IP."""
        try:
            # This is a simplified example, in production use a geolocation service
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except:
            return 'Unknown'


class SocialAuthErrorView(views.APIView):
    """
    API view to handle social auth errors.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        error = request.GET.get('error', 'Unknown error')
        error_description = request.GET.get('error_description', '')
        state = request.GET.get('state', '')

        # Log the error
        logger.error(f"Social auth error: {error} - {error_description}")

        # Build error message
        error_message = f"{error}: {error_description}" if error_description else error

        # Redirect to frontend with error and state (if available)
        redirect_url = f"{settings.FRONTEND_URL}/login?error={error_message}"
        if state:
            redirect_url += f"&state={state}"

        return redirect(redirect_url)
