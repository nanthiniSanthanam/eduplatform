from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from rest_framework import status, generics, permissions, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser
from .serializers import (
    CustomUserSerializer,
    UserSignupSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    InstructorSerializer,
    AdminUserSerializer
)

from courses.models import Enrollment
from courses.serializers import EnrollmentSerializer


class UserEnrollmentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        enrollments = Enrollment.objects.filter(user=request.user)
        serializer = EnrollmentSerializer(
            enrollments, many=True, context={'request': request})
        return Response(serializer.data)


class IsAdminOrSelf(permissions.BasePermission):
    """
    Permission to allow users to edit only their own profile or admin to edit any.
    """

    def has_object_permission(self, request, view, obj):
        # Allow users to view their own profile
        if obj == request.user:
            return True
        # Allow admin users to view all profiles
        return request.user.user_type == 'admin'


class SignupView(generics.CreateAPIView):
    """
    View for user registration.
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserSignupSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens for the new user
        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserProfileSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    View for user login.
    """
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            refresh = RefreshToken.for_user(user)

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserProfileSerializer(user).data
            })

        return Response(
            {'error': 'Invalid username or password'},
            status=status.HTTP_401_UNAUTHORIZED
        )


class LogoutView(APIView):
    """
    View for user logout.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    View for retrieving and updating user profile.
    """
    queryset = CustomUser.objects.all()
    permission_classes = [IsAuthenticated, IsAdminOrSelf]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserProfileSerializer
        return UserUpdateSerializer

    def get_object(self):
        # If pk is 'me', return the current user
        pk = self.kwargs.get('pk')
        if pk == 'me':
            return self.request.user
        return super().get_object()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for admin management of users.
    """
    queryset = CustomUser.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Override to ensure only admins can access all users,
        but users can access their own profile.
        """
        if self.action == 'retrieve' and self.kwargs.get('pk') == 'me':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    def get_object(self):
        # If pk is 'me', return the current user
        pk = self.kwargs.get('pk')
        if pk == 'me':
            return self.request.user
        return super().get_object()

    def get_serializer_class(self):
        """
        Return appropriate serializer based on the action.
        """
        if self.action in ['list', 'retrieve', 'update', 'partial_update', 'destroy']:
            if self.request.user.user_type == 'admin':
                return AdminUserSerializer
            return UserProfileSerializer
        return CustomUserSerializer

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def instructors(self, request):
        """
        List all instructors for public display.
        """
        instructors = CustomUser.objects.filter(user_type='instructor')
        serializer = InstructorSerializer(instructors, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminOrSelf])
    def activate_subscription(self, request, pk=None):
        """
        Activate subscription for a user.
        """
        user = self.get_object()
        # Set subscription status and expiry (30 days from now)
        user.subscription_status = True
        user.subscription_expiry = timezone.now() + timezone.timedelta(days=30)
        user.save()

        return Response({
            'detail': 'Subscription activated successfully',
            'user': UserProfileSerializer(user).data
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminOrSelf])
    def cancel_subscription(self, request, pk=None):
        """
        Cancel subscription for a user.
        """
        user = self.get_object()
        user.subscription_status = False
        user.save()

        return Response({
            'detail': 'Subscription cancelled successfully',
            'user': UserProfileSerializer(user).data
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def check_username(request):
    """
    Check if a username is available.
    """
    username = request.query_params.get('username', None)
    if username is None:
        return Response(
            {"error": "Username parameter is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    exists = CustomUser.objects.filter(username=username).exists()
    return Response({"available": not exists})
