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

Changes (2025-05-05):
- Fixed RegisterView.create() to explicitly create an EmailVerification record 
  instead of trying to retrieve a non-existent record
- This resolves the 500 error during user registration
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
from django.shortcuts import get_object_or_404
from datetime import timedelta
import uuid
import socket
import logging

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

        # ---- single, canonical session row using JTI ----
        # Create single user session with JTI (JSON Web Token ID)
        # This is required for CustomJWTAuthentication to validate the token
        UserSession.objects.create(
            user=user,
            # Store JTI (token ID), not the encoded token
            session_key=refresh.access_token['jti'],
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
            device_type=self._get_device_type(user_agent),
            location=self._get_location_from_ip(ip_address)
        )

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
